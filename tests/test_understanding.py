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


def seeded_needs() -> dict[str, dict[str, Any]]:
    """The seeded Needs, by name."""
    needs: list[dict[str, Any]] = yaml.safe_load(NEEDS_SEED_FILE.read_text())
    return {need["name"]: need for need in needs}


def how_to_reply(need: str) -> str:
    """The seeded "how to reply" of a Need."""
    reply_guidance: str = seeded_needs()[need]["how_to_reply"]
    return reply_guidance


def saved_understandings(engine: Engine) -> list[dict[str, Any]]:
    """Every saved Understanding, oldest first."""
    with engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(
                text(
                    "SELECT need, form, asked_why, message_id "
                    "FROM understandings ORDER BY position"
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
        "Ask more",
        "Just chatting",
    ]
    assert [name for name, need in needs.items() if need.get("fallback")] == [
        FALLBACK_NEED
    ]
    for need in needs.values():
        assert need["when_it_fits"].strip()
        assert need["how_to_reply"].strip()


def test_every_message_gets_an_understanding_before_the_reply(
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

    assert chat_model.call_order == ["safeguard", "understanding", "reply"]
    [understanding_call] = chat_model.understanding_calls
    assert understanding_call.model == seeded_settings["understanding_model"]
    asked = understanding_call.history[0].text
    assert "hello there" in asked
    for name, need in seeded_needs().items():
        assert f"- {name}: {need['when_it_fits'].strip()}" in asked
    assert "Wednesday 11 Nov 2026, 17:00" in asked
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey you"]


def test_the_reply_follows_the_picked_needs_how_to_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_understanding(
        understanding_answer(
            need="Advice",
            nuance="They want a concrete plan for the interview.",
            mood="nervous",
            intensity="medium",
        )
    )
    chat_model.script("here's a plan")

    send_to_webhook(client, telegram_text_update("how do I prep for my interview?"))

    [reply_call] = chat_model.calls
    assert how_to_reply("Advice").strip() in reply_call.instructions
    assert how_to_reply("Be heard").strip() not in reply_call.instructions
    assert "They want a concrete plan for the interview." in reply_call.instructions
    assert "nervous" in reply_call.instructions


def test_the_understanding_sees_the_users_goals(
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
    chat_model.script("nice")

    send_to_webhook(client, telegram_text_update("skipped my run today"))

    [understanding_call] = chat_model.understanding_calls
    assert "Run a marathon" in understanding_call.history[0].text


def test_the_next_understanding_in_the_conversation_sees_the_earlier_ones(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_understanding(
        understanding_answer(need="Be heard", mood="furious", intensity="high"),
        understanding_answer(need="Think it through", mood="calmer"),
    )
    chat_model.script("that sounds awful", "what do you think?")

    send_to_webhook(client, telegram_text_update("my boss yelled at me"))
    send_to_webhook(client, telegram_text_update("I'm calmer now"))

    first, second = chat_model.understanding_calls
    assert "furious" not in first.history[0].text
    assert "Be heard" in second.history[0].text.split("Earlier Understandings")[1]
    assert "furious (high)" in second.history[0].text


def test_a_standout_mood_with_an_unknown_cause_asks_the_reply_to_gently_ask_why(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_understanding(
        understanding_answer(mood="low", intensity="high", cause_known=False)
    )
    chat_model.script("hey, you ok?")

    send_to_webhook(client, telegram_text_update("meh"))

    [reply_call] = chat_model.calls
    assert seeded_settings["reply_ask_why_note"] in reply_call.instructions
    [saved] = saved_understandings(client.engine)  # type: ignore[attr-defined]
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
    chat_model.script_understanding(
        understanding_answer(need="Cheerleading", mood="excited")
    )
    chat_model.script("tell me more")

    send_to_webhook(client, telegram_text_update("guess what"))

    [reply_call] = chat_model.calls
    assert how_to_reply(FALLBACK_NEED).strip() in reply_call.instructions
    assert "excited" in reply_call.instructions
    [saved] = saved_understandings(engine)
    assert saved["need"] == FALLBACK_NEED


def test_an_unreadable_form_falls_back_to_the_fallback_need(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_understanding("I think they want advice")
    chat_model.script("tell me more")

    send_to_webhook(client, telegram_text_update("guess what"))

    [reply_call] = chat_model.calls
    assert how_to_reply(FALLBACK_NEED).strip() in reply_call.instructions
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["tell me more"]
    [saved] = saved_understandings(engine)
    assert saved["need"] == FALLBACK_NEED


def test_a_failed_understanding_still_replies_with_the_fallback_and_shows_in_the_log(
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
    chat_model.script_understanding(TimeoutError("DeepSeek timed out"))
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
        ("understanding", "TimeoutError"),
        ("reply", None),
    ]


def test_each_understanding_is_saved_with_its_message_and_the_need_by_name(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_understanding(
        understanding_answer(need="Advice", mood="unsure", intensity="medium")
    )
    chat_model.script("try this")

    send_to_webhook(client, telegram_text_update("what should I do?"))

    [saved] = saved_understandings(engine)
    assert saved["need"] == "Advice"
    assert saved["form"]["mood"] == "unsure"
    assert saved["form"]["intensity"] == "medium"
    with engine.connect() as connection:
        message = connection.execute(
            text("SELECT content FROM conversation_messages WHERE id = :id"),
            {"id": saved["message_id"]},
        ).scalar_one()
    assert message == "what should I do?"


def test_message_retention_removes_understandings_with_their_messages(
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

    clock.advance(retention(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(processing_answer())
    scheduler.tick()

    assert saved_understandings(engine) == []


def test_a_changed_understanding_prompt_and_model_are_used_for_the_next_message(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    other_model = next(
        model
        for model in seeded_settings["available_models"]
        if model != seeded_settings["understanding_model"]
    )
    response = client.patch(
        "/api/admin/settings",
        json={
            "values": {
                "understanding_prompt": "Read the person closely.",
                "understanding_model": other_model,
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
    assert understanding_call.model == other_model
