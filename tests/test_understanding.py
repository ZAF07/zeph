import json
from datetime import timedelta
from typing import Any

import yaml
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from tests.conftest import NEEDS_SEED_FILE
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
    reply_plan_answer,
    understanding_answer,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_memory_retrieval import remember_some_things
from tests.test_message_retention import retention
from tests.test_post_conversation import have_conversation, processing_answer

FALLBACK_NEED = "Ask more"
DECIDING_FIELDS = (
    '"need"',
    "lead_move",
    "support_move",
    "next_move",
    "bring_up",
    "left_alone",
    "threads_touched",
    "memory_categories",
    "knowledge",
)


def seeded_needs() -> dict[str, dict[str, Any]]:
    """The seeded Needs, by name."""
    needs: list[dict[str, Any]] = yaml.safe_load(NEEDS_SEED_FILE.read_text())
    return {need["name"]: need for need in needs}


def how_to_reply(need: str) -> str:
    """The seeded "how to reply" of a Need."""
    reply_guidance: str = seeded_needs()[need]["how_to_reply"]
    return reply_guidance


def need_when_it_fits(need: str) -> str:
    """The seeded "when it fits" of a Need."""
    wording: str = seeded_needs()[need]["when_it_fits"]
    return wording.strip()


def saved_understandings(engine: Engine) -> list[dict[str, Any]]:
    """Every saved Understanding, oldest first."""
    with engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(
                text(
                    "SELECT form, is_fallback, message_id "
                    "FROM understandings ORDER BY position"
                )
            ).mappings()
        ]


def saved_reply_plans(engine: Engine) -> list[dict[str, Any]]:
    """Every saved Reply Plan, oldest first."""
    with engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(
                text(
                    "SELECT need, form, asked_why, is_fallback, message_id "
                    "FROM reply_plans ORDER BY position"
                )
            ).mappings()
        ]


def test_seeded_needs_have_ask_more_as_the_only_fallback() -> None:
    needs = seeded_needs()

    assert list(needs) == [
        "Be heard",
        "Think it through",
        "Advice",
        "Accountability",
        "Get it done",
        "Ask more",
        "Just chatting",
    ]
    assert [name for name, need in needs.items() if need.get("fallback")] == [
        FALLBACK_NEED
    ]
    for need in needs.values():
        assert need["when_it_fits"].strip()
        assert need["how_to_reply"].strip()


def test_the_seeded_understanding_prompt_asks_for_no_decisions(
    seeded_settings: dict[str, Any],
) -> None:
    prompt = seeded_settings["understanding_prompt"]

    for field in DECIDING_FIELDS:
        assert field not in prompt
    for field in ('"said"', '"means"', '"feelings"', '"wants"', '"unclear"'):
        assert field in prompt
    for field in DECIDING_FIELDS:
        assert field in seeded_settings["reply_plan_prompt"]


def test_every_message_gets_an_understanding_then_a_reply_plan_before_the_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    client.patch(
        "/api/me",
        json={"time_zone": "Asia/Singapore"},
        headers=auth_headers(auth_verifier, "user_maya"),
    )
    chat_model.script("hey you")

    send_to_webhook(client, telegram_text_update("hello there"))

    assert chat_model.call_order == [
        "safeguard",
        "understanding",
        "reply_plan",
        "reply",
    ]
    [understanding_call] = chat_model.understanding_calls
    [reply_plan_call] = chat_model.reply_plan_calls
    assert understanding_call.model == seeded_settings["understanding_model"]
    assert reply_plan_call.model == seeded_settings["reply_plan_model"]
    assert reply_plan_call.thinking is True
    read = understanding_call.history[0].text
    planned = reply_plan_call.history[0].text
    assert "hello there" in read
    assert "Wednesday 11 Nov 2026, 17:00" in read
    for heading in ("Needs:", "Moves:", "Life Threads", "Knowledge", "Goals"):
        assert heading not in read
    for name, need in seeded_needs().items():
        assert need["when_it_fits"].strip() not in read
        assert f"- {name}: {need['when_it_fits'].strip()}" in planned
    assert "hello there" in planned
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey you"]


def test_said_read_and_unclear_stay_apart_and_reach_the_reply_plan(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_understanding(
        understanding_answer(
            said="Their PM overruled them again.",
            means="They feel unheard at work.",
            feelings={
                "said": "annoyed",
                "read": "hurt underneath.",
                "unclear": "",
            },
            wants={
                "said": "",
                "read": "to vent",
                "unclear": "whether they want advice",
            },
        )
    )
    chat_model.script("that sounds rough")

    send_to_webhook(client, telegram_text_update("PM overruled me AGAIN"))

    [reply_plan_call] = chat_model.reply_plan_calls
    planned = reply_plan_call.history[0].text
    assert "They said: Their PM overruled them again." in planned
    assert "They mean: They feel unheard at work." in planned
    assert "Feelings: said: annoyed; read (a guess): hurt underneath." in planned
    assert (
        "What they want: read (a guess): to vent; "
        "unclear: whether they want advice." in planned
    )
    [saved] = saved_understandings(engine)
    assert saved["form"]["feelings"] == {
        "said": "annoyed",
        "read": "hurt underneath.",
        "unclear": "",
    }
    assert saved["form"]["wants"]["unclear"] == "whether they want advice"


def test_the_reply_follows_the_reply_plans_need(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_understanding(
        understanding_answer(mood="nervous", intensity="medium")
    )
    chat_model.script_reply_plan(
        reply_plan_answer(
            need="Advice", guidance="They want a concrete plan for the interview."
        )
    )
    chat_model.script("here's a plan")

    send_to_webhook(client, telegram_text_update("how do I prep for my interview?"))

    [reply_call] = chat_model.calls
    assert how_to_reply("Advice").strip() in reply_call.instructions
    assert how_to_reply("Be heard").strip() not in reply_call.instructions
    assert "They want a concrete plan for the interview." in reply_call.instructions
    assert "nervous (medium)" in reply_call.instructions


def test_the_reply_plan_sees_the_users_goals_and_the_understanding_does_not(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "I want to run a marathon",
        processing_answer(
            operations=[
                {"action": "add", "category": "Goals", "content": "Run a marathon"}
            ]
        ),
    )
    chat_model.understanding_calls.clear()
    chat_model.reply_plan_calls.clear()
    chat_model.script("nice")

    send_to_webhook(client, telegram_text_update("skipped my run today"))

    [understanding_call] = chat_model.understanding_calls
    [reply_plan_call] = chat_model.reply_plan_calls
    assert "Run a marathon" not in understanding_call.history[0].text
    assert "Run a marathon" in reply_plan_call.history[0].text


def test_the_next_understanding_and_reply_plan_see_the_earlier_ones(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_understanding(
        understanding_answer(mood="furious", intensity="high"),
        understanding_answer(mood="calmer"),
    )
    chat_model.script_reply_plan(
        reply_plan_answer(need="Be heard", guidance="Let them vent first."),
        reply_plan_answer(need="Think it through"),
    )
    chat_model.script("that sounds awful", "what do you think?")

    send_to_webhook(client, telegram_text_update("my boss yelled at me"))
    send_to_webhook(client, telegram_text_update("I'm calmer now"))

    first_read, second_read = chat_model.understanding_calls
    first_plan, second_plan = chat_model.reply_plan_calls
    assert "furious" not in first_read.history[0].text
    assert "furious (high)" in second_read.history[0].text
    earlier_plans = second_plan.history[0].text.split("Earlier Reply Plans")[1]
    assert "Need: Be heard" in earlier_plans
    assert "Let them vent first." in earlier_plans
    assert "Be heard" not in first_plan.history[0].text.split("Earlier Reply Plans")[1]


def test_a_standout_mood_with_an_unknown_cause_asks_the_reply_to_gently_ask_why(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_understanding(
        understanding_answer(mood="low", intensity="high", cause_known=False)
    )
    chat_model.script("hey, you ok?")

    send_to_webhook(client, telegram_text_update("meh"))

    [reply_call] = chat_model.calls
    assert seeded_settings["reply_ask_why_note"] in reply_call.instructions
    [saved] = saved_reply_plans(engine)
    assert saved["asked_why"] is True


def test_no_gentle_ask_when_the_cause_is_known_or_the_mood_is_mild(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_understanding(
        understanding_answer(mood="low", intensity="high", cause_known=True),
        understanding_answer(mood="low", intensity="medium", cause_known=False),
    )
    chat_model.script("oh no", "hm")

    send_to_webhook(client, telegram_text_update("my cat is sick, feeling low"))
    send_to_webhook(client, telegram_text_update("meh"))

    for reply_call in chat_model.calls:
        assert seeded_settings["reply_ask_why_note"] not in reply_call.instructions


def test_the_gentle_ask_is_not_made_twice_in_a_row(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    standout = understanding_answer(mood="low", intensity="high", cause_known=False)
    chat_model.script_understanding(standout, standout, standout)
    chat_model.script_reply_plan(
        reply_plan_answer(ask_why=True),
        reply_plan_answer(ask_why=True),
        reply_plan_answer(ask_why=True),
    )
    chat_model.script("you ok?", "I'm here", "what's up?")

    for text_sent in ("meh", "dunno", "whatever"):
        send_to_webhook(client, telegram_text_update(text_sent))

    note = seeded_settings["reply_ask_why_note"]
    assert [note in call.instructions for call in chat_model.calls] == [
        True,
        False,
        True,
    ]


def test_an_unknown_need_falls_back_to_the_fallback_need(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_understanding(understanding_answer(mood="excited"))
    chat_model.script_reply_plan(reply_plan_answer(need="Cheerleading"))
    chat_model.script("tell me more")

    send_to_webhook(client, telegram_text_update("guess what"))

    [reply_call] = chat_model.calls
    assert how_to_reply(FALLBACK_NEED).strip() in reply_call.instructions
    assert "excited" in reply_call.instructions
    [saved] = saved_reply_plans(engine)
    assert saved["need"] == FALLBACK_NEED


def test_an_unreadable_reply_plan_falls_back_to_the_fallback_need(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_reply_plan("I think they want advice")
    chat_model.script("tell me more")

    send_to_webhook(client, telegram_text_update("guess what"))

    [reply_call] = chat_model.calls
    assert how_to_reply(FALLBACK_NEED).strip() in reply_call.instructions
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["tell me more"]
    [saved] = saved_reply_plans(engine)
    assert (saved["need"], saved["is_fallback"]) == (FALLBACK_NEED, True)


def test_an_unreadable_understanding_falls_back_and_the_reply_plan_still_decides(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_understanding("they seem fine")
    chat_model.script_reply_plan(reply_plan_answer(need="Advice"))
    chat_model.script("try this")

    send_to_webhook(client, telegram_text_update("what should I do?"))

    [reply_call] = chat_model.calls
    assert how_to_reply("Advice").strip() in reply_call.instructions
    [understanding] = saved_understandings(engine)
    assert understanding["is_fallback"] is True
    assert understanding["form"]["cause_known"] is True
    [reply_plan] = saved_reply_plans(engine)
    assert (reply_plan["need"], reply_plan["is_fallback"]) == ("Advice", False)


def test_a_failed_reply_plan_still_replies_with_the_fallback_and_shows_in_the_log(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    remember_some_things(client, chat_model, clock, scheduler, seeded_settings)
    chat_model.script_reply_plan(TimeoutError("DeepSeek timed out"))
    chat_model.script("hey")

    send_to_webhook(client, telegram_text_update("my sister called"))

    [reply_call] = chat_model.calls
    assert how_to_reply(FALLBACK_NEED).strip() in reply_call.instructions
    assert "Likes Stoicism" in reply_call.instructions
    assert "Sister Jo" not in reply_call.instructions
    assert "Talked about work and family." in reply_call.instructions
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)[-1] == "hey"
    admin = owner_headers(client, auth_verifier)
    [failed_trace] = client.get(
        "/api/admin/model-calls",
        params={"errors_only": True},
        headers=admin,
    ).json()["traces"]
    calls = client.get(
        f"/api/admin/model-calls/{failed_trace['trace_id']}", headers=admin
    ).json()["calls"]
    assert [(call["step"], call["error"]) for call in calls] == [
        ("safeguard", None),
        ("understanding", None),
        ("reply_plan", "TimeoutError"),
        ("reply", None),
    ]
    assert calls[2]["reply_plan_shape"]["need"] == FALLBACK_NEED


def test_a_failed_understanding_still_replies_and_shows_in_the_log(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_understanding(TimeoutError("DeepSeek timed out"))
    chat_model.script("hey")

    send_to_webhook(client, telegram_text_update("my sister called"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey"]
    [reply_plan_call] = chat_model.reply_plan_calls
    assert "Mood: unclear (low)." in reply_plan_call.history[0].text
    admin = owner_headers(client, auth_verifier)
    [failed_trace] = client.get(
        "/api/admin/model-calls",
        params={"errors_only": True},
        headers=admin,
    ).json()["traces"]
    calls = client.get(
        f"/api/admin/model-calls/{failed_trace['trace_id']}", headers=admin
    ).json()["calls"]
    assert [(call["step"], call["error"]) for call in calls] == [
        ("safeguard", None),
        ("understanding", "TimeoutError"),
        ("reply_plan", None),
        ("reply", None),
    ]


def test_each_understanding_and_reply_plan_is_saved_with_its_message(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_understanding(
        understanding_answer(mood="unsure", intensity="medium")
    )
    chat_model.script_reply_plan(reply_plan_answer(need="Advice"))
    chat_model.script("try this")

    send_to_webhook(client, telegram_text_update("what should I do?"))

    [understanding] = saved_understandings(engine)
    [reply_plan] = saved_reply_plans(engine)
    assert understanding["form"]["mood"] == "unsure"
    assert understanding["form"]["intensity"] == "medium"
    assert "need" not in understanding["form"]
    assert reply_plan["need"] == "Advice"
    assert understanding["message_id"] == reply_plan["message_id"]
    with engine.connect() as connection:
        message = connection.execute(
            text("SELECT content FROM conversation_messages WHERE id = :id"),
            {"id": understanding["message_id"]},
        ).scalar_one()
    assert message == "what should I do?"


def test_struggling_and_asked_for_photo_are_saved_and_odd_values_read_as_false(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    odd = json.loads(understanding_answer())
    odd.update(struggling="yes", asked_for_photo=1)
    chat_model.script_understanding(
        understanding_answer(struggling=True, asked_for_photo=True), json.dumps(odd)
    )
    chat_model.script("I'm here", "ok")

    send_to_webhook(client, telegram_text_update("I'm scared, send me mum's photo"))
    send_to_webhook(client, telegram_text_update("hmm"))

    [first, second] = saved_understandings(engine)
    assert (first["form"]["struggling"], first["form"]["asked_for_photo"]) == (
        True,
        True,
    )
    assert (second["form"]["struggling"], second["form"]["asked_for_photo"]) == (
        False,
        False,
    )


def test_message_retention_removes_understandings_and_reply_plans_with_messages(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("hi")
    send_to_webhook(client, telegram_text_update("hello"))
    assert len(saved_understandings(engine)) == 1
    assert len(saved_reply_plans(engine)) == 1

    clock.advance(retention(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(processing_answer())
    scheduler.tick()

    assert saved_understandings(engine) == []
    assert saved_reply_plans(engine) == []


def test_a_changed_understanding_prompt_and_thinking_are_used_for_the_next_message(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    other_thinking = not seeded_settings["understanding_thinking"]
    response = client.patch(
        "/api/admin/settings",
        json={
            "values": {
                "understanding_prompt": "Read the person closely.",
                "understanding_thinking": other_thinking,
            }
        },
        headers=owner_headers(client, auth_verifier),
    )
    assert response.status_code == 200
    chat_model.understanding_prompt = "Read the person closely."
    chat_model.script("hey")

    send_to_webhook(client, telegram_text_update("hello"))

    [understanding_call] = chat_model.understanding_calls
    assert understanding_call.instructions == "Read the person closely."
    assert understanding_call.model == seeded_settings["understanding_model"]
    assert understanding_call.thinking is other_thinking


def test_a_changed_reply_plan_prompt_and_thinking_are_used_for_the_next_message(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    response = client.patch(
        "/api/admin/settings",
        json={
            "values": {
                "reply_plan_prompt": "Decide what helps them most.",
                "reply_plan_thinking": False,
            }
        },
        headers=owner_headers(client, auth_verifier),
    )
    assert response.status_code == 200
    chat_model.reply_plan_prompt = "Decide what helps them most."
    chat_model.script("hey")

    send_to_webhook(client, telegram_text_update("hello"))

    [reply_plan_call] = chat_model.reply_plan_calls
    assert reply_plan_call.instructions.endswith("\n\nDecide what helps them most.")
    assert reply_plan_call.model == seeded_settings["reply_plan_model"]
    assert reply_plan_call.thinking is False


def test_a_failed_reply_plan_never_asks_why_even_when_the_mood_stands_out(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_understanding(
        understanding_answer(mood="low", intensity="high", cause_known=False)
    )
    chat_model.script_reply_plan(TimeoutError("DeepSeek timed out"))
    chat_model.script("I'm here")

    send_to_webhook(client, telegram_text_update("meh"))

    [reply_call] = chat_model.calls
    assert seeded_settings["reply_ask_why_note"] not in reply_call.instructions
    [saved] = saved_reply_plans(engine)
    assert (saved["is_fallback"], saved["asked_why"]) == (True, False)
