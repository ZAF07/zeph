import json
from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
    understanding_answer,
)
from tests.telegram_helpers import (
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_features import maya_id, switch_for_everyone, switch_for_user
from tests.test_life_threads import new_thread, thread_keeping_answer
from tests.test_older_summaries import set_settings
from tests.test_post_conversation import processing_answer, quiet_gap

PRESENTATION = "How did the big presentation go?"
PRESENTATION_WHY = "They were nervous about presenting to the board on Thursday."
FRIDAY = "2026-11-13"


def curiosity_keeping_answer(curiosities: list[dict[str, Any]]) -> str:
    """Build the JSON the Curiosity keeping model answers with."""
    return json.dumps({"curiosities": curiosities})


def new_curiosity(
    ask: str = PRESENTATION,
    why: str = PRESENTATION_WHY,
    not_before: str | None = FRIDAY,
    sensitivity: str = "low",
    **source: int,
) -> dict[str, Any]:
    """Build a new Curiosity as the keeping model writes it."""
    return {
        "ask": ask,
        "why": why,
        "not_before": not_before,
        "sensitivity": sensitivity,
        **source,
    }


def end_conversation(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    text: str,
    curiosities: list[dict[str, Any]],
    operations: list[dict[str, Any]] | None = None,
    threads: list[dict[str, Any]] | None = None,
) -> None:
    """Send one message, then end the Conversation keeping the given Curiosities."""
    chat_model.script("mm, I hear you")
    send_to_webhook(client, telegram_text_update(text))
    end_current_conversation(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        curiosities,
        operations,
        threads,
    )


def end_current_conversation(
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    curiosities: list[dict[str, Any]],
    operations: list[dict[str, Any]] | None = None,
    threads: list[dict[str, Any]] | None = None,
) -> None:
    """Let the quiet gap pass and end the Conversation with the given answers."""
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(
        processing_answer(summary="Talked about work.", operations=operations)
    )
    chat_model.script_thread_keeping(thread_keeping_answer(threads or []))
    chat_model.script_curiosity_keeping(curiosity_keeping_answer(curiosities))
    scheduler.tick()


def understanding_sees(
    client: TestClient, chat_model: ScriptedChatModel, text: str
) -> str:
    """Send a message and return what its Understanding was given."""
    chat_model.script("mm, tell me more")
    send_to_webhook(client, telegram_text_update(text))
    return chat_model.understanding_calls[-1].history[0].text


def reply_instructions(
    client: TestClient, chat_model: ScriptedChatModel, text: str
) -> str:
    """Send a message and return what its reply call was told."""
    chat_model.script("mm, tell me more")
    send_to_webhook(client, telegram_text_update(text))
    return chat_model.calls[-1].instructions


def bring_up_curiosity(chat_model: ScriptedChatModel, *numbers: int) -> None:
    """Script the next Understanding to bring up the given Curiosities."""
    chat_model.script_understanding(
        understanding_answer(
            bring_up=[{"curiosity": number, "how": "lead"} for number in numbers]
        )
    )


def stored_curiosities(engine: Engine) -> list[dict[str, Any]]:
    """Read every saved Curiosity, oldest first."""
    with engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(
                text("SELECT * FROM curiosities ORDER BY position")
            ).mappings()
        ]


def presentation_is_due(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    """Save the presentation Curiosity and move on to the Friday it is due."""
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "big presentation to the board on Thursday, so nervous",
        [new_curiosity()],
    )
    clock.advance(timedelta(days=2))


def test_a_conversation_end_saves_a_curiosity_offered_once_its_day_has_come(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "big presentation to the board on Thursday, so nervous",
        [new_curiosity()],
    )
    keeper_saw = chat_model.curiosity_keeping_calls[-1].history[0].text

    clock.advance(timedelta(days=1))
    thursday = understanding_sees(client, chat_model, "morning!")
    clock.advance(timedelta(days=1))
    friday = understanding_sees(client, chat_model, "hey you")

    assert "Today: Wednesday 11 Nov 2026" in keeper_saw
    assert "big presentation to the board on Thursday" in keeper_saw
    assert PRESENTATION not in thursday
    assert f"[1] {PRESENTATION} Why: {PRESENTATION_WHY}" in friday
    assert "Sensitivity: low." in friday
    assert "raised 0 of at most 1 in this Conversation" in friday


def test_a_curiosity_brought_up_reaches_the_reply_and_is_marked_raised(
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
    presentation_is_due(client, chat_model, clock, scheduler, seeded_settings)

    bring_up_curiosity(chat_model, 1)
    instructions = reply_instructions(client, chat_model, "hey you")
    [curiosity] = stored_curiosities(engine)
    next_message = understanding_sees(client, chat_model, "busy day today")

    assert "Something you've been wondering about them" in instructions
    assert (
        f"- {PRESENTATION} Open with it. Why you wonder: {PRESENTATION_WHY}"
    ) in instructions
    assert curiosity["state"] == "raised"
    assert curiosity["raised_at"] is not None
    assert curiosity["raised_conversation_id"] is not None
    assert PRESENTATION not in next_message


def test_a_curiosity_woven_in_is_still_asked_in_this_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    presentation_is_due(client, chat_model, clock, scheduler, seeded_settings)

    chat_model.script_understanding(
        understanding_answer(bring_up=[{"curiosity": 1, "how": "weave"}])
    )
    instructions = reply_instructions(client, chat_model, "work was long today")

    assert f"- {PRESENTATION} Ask it in this reply, after answering" in instructions


def test_no_curiosity_is_offered_once_the_admin_set_number_was_raised(
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
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "work is a lot",
        [
            new_curiosity(),
            new_curiosity(ask="Did the new desk arrive?", not_before=None),
            new_curiosity(ask="How is the cat?", not_before=None),
        ],
    )
    clock.advance(timedelta(days=2))
    set_settings(client, auth_verifier, {"curiosities_per_conversation": 2})

    bring_up_curiosity(chat_model, 1)
    first = understanding_sees(client, chat_model, "hey you")
    second = understanding_sees(client, chat_model, "so anyway")
    bring_up_curiosity(chat_model, 1, 2)
    reply_instructions(client, chat_model, "what's new with you")
    third = understanding_sees(client, chat_model, "ok")
    raised = [row for row in stored_curiosities(engine) if row["state"] == "raised"]

    assert "raised 0 of at most 2 in this Conversation" in first
    assert "raised 1 of at most 2 in this Conversation" in second
    assert "[1] Did the new desk arrive?" in second
    assert "How is the cat?" in second
    assert "Did the new desk arrive?" not in third
    assert "How is the cat?" not in third
    assert len(raised) == 2


def test_a_raised_curiosity_records_how_the_user_took_it_when_the_conversation_ends(
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
    presentation_is_due(client, chat_model, clock, scheduler, seeded_settings)
    bring_up_curiosity(chat_model, 1)
    reply_instructions(client, chat_model, "hey you")
    reply_instructions(client, chat_model, "it went great, the board loved it!")

    end_current_conversation(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [{"curiosity": 1, "reaction": "engaged"}],
    )
    keeper_saw = chat_model.curiosity_keeping_calls[-1].history[0].text
    [curiosity] = stored_curiosities(engine)
    end_conversation(
        client, chat_model, clock, scheduler, seeded_settings, "hi again", []
    )
    later_keeper_saw = chat_model.curiosity_keeping_calls[-1].history[0].text

    assert f"[1] (brought up in this Conversation) {PRESENTATION}" in keeper_saw
    assert curiosity["state"] == "raised"
    assert curiosity["reaction"] == "engaged"
    assert f"- {PRESENTATION} (they engaged)" in later_keeper_saw


def test_a_conversation_end_updates_and_closes_waiting_curiosities(
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
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "presentation Thursday, and I might quit piano",
        [new_curiosity(), new_curiosity(ask="Still playing piano?", not_before=None)],
    )

    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "presentation moved to next Monday, and I sold the piano",
        [
            {"curiosity": 1, "not_before": "2026-11-17", "why": "Moved to Monday."},
            {"curiosity": 2, "close": True},
        ],
    )
    keeper_saw = chat_model.curiosity_keeping_calls[-1].history[0].text
    rows = {row["question"]: row for row in stored_curiosities(engine)}

    assert f"[1] (waiting; not before 13 Nov 2026; sensitivity low) {PRESENTATION}" in (
        keeper_saw
    )
    assert "[2] (waiting; any day; sensitivity low) Still playing piano?" in keeper_saw
    assert str(rows[PRESENTATION]["not_before"]) == "2026-11-17"
    assert rows[PRESENTATION]["why"] == "Moved to Monday."
    assert rows[PRESENTATION]["state"] == "waiting"
    assert rows["Still playing piano?"]["state"] == "closed"


def test_the_waiting_limit_closes_the_oldest_waiting_curiosities(
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
    set_settings(client, auth_verifier, {"curiosities_waiting_limit": 2})
    for text_sent, question in (
        ("lots going on", "Oldest?"),
        ("and more", "Older?"),
        ("and even more", "Newest?"),
    ):
        end_conversation(
            client,
            chat_model,
            clock,
            scheduler,
            seeded_settings,
            text_sent,
            [new_curiosity(ask=question)],
        )
    states = {row["question"]: row["state"] for row in stored_curiosities(engine)}

    assert states == {"Oldest?": "closed", "Older?": "waiting", "Newest?": "waiting"}


def test_an_unreadable_curiosity_or_one_for_an_unknown_number_is_skipped(
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

    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "lots going on",
        [
            new_curiosity(ask="Bad day?", not_before="next Thursday"),
            new_curiosity(ask="", why="No question."),
            {"curiosity": 7, "close": True},
            new_curiosity(ask="Odd source?", memory_item=9, thread=9),
            new_curiosity(ask="Odd sensitivity?", sensitivity="very"),
        ],
    )
    rows = stored_curiosities(engine)

    assert [row["question"] for row in rows] == ["Odd source?", "Odd sensitivity?"]
    assert rows[0]["source_memory_item_id"] is None
    assert rows[0]["source_life_thread_id"] is None
    assert rows[1]["sensitivity"] == "low"


def test_deleting_the_memory_item_or_thread_a_curiosity_came_from_removes_it(
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
    headers = auth_headers(auth_verifier, "user_maya")
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "presenting to the board Thursday, and Mei and I fell out",
        [
            new_curiosity(memory_item=1),
            new_curiosity(ask="Have you talked to Mei?", not_before=None, thread=1),
            new_curiosity(ask="How is the cat?", not_before=None),
        ],
        operations=[
            {
                "action": "add",
                "category": "Life details",
                "content": "Presenting to the board on Thursday",
            }
        ],
        threads=[new_thread()],
    )
    keeper_saw = chat_model.curiosity_keeping_calls[-1].history[0].text
    [item] = client.get("/api/memory-items", headers=headers).json()["groups"][0][
        "items"
    ]
    [thread] = client.get("/api/life-threads", headers=headers).json()["threads"]

    client.delete(f"/api/memory-items/{item['id']}", headers=headers)
    after_item = [row["question"] for row in stored_curiosities(engine)]
    client.delete(f"/api/life-threads/{thread['id']}", headers=headers)
    after_thread = [row["question"] for row in stored_curiosities(engine)]

    assert "[1] (Life details) Presenting to the board on Thursday" in keeper_saw
    assert "[1] Falling-out with Mei (open" in keeper_saw
    assert after_item == ["Have you talked to Mei?", "How is the cat?"]
    assert after_thread == ["How is the cat?"]


def test_with_curiosities_off_for_everyone_none_are_made_or_offered_or_deleted(
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
    presentation_is_due(client, chat_model, clock, scheduler, seeded_settings)
    switch_for_everyone(
        client, owner_headers(client, auth_verifier), "curiosities", False
    )

    bring_up_curiosity(chat_model, 1)
    instructions = reply_instructions(client, chat_model, "hey you")
    seen = chat_model.understanding_calls[-1].history[0].text
    end_current_conversation(
        chat_model, clock, scheduler, seeded_settings, [new_curiosity(ask="New?")]
    )
    rows = stored_curiosities(engine)

    assert PRESENTATION not in seen
    assert PRESENTATION not in instructions
    assert len(chat_model.curiosity_keeping_calls) == 1
    assert [(row["question"], row["state"]) for row in rows] == [
        (PRESENTATION, "waiting")
    ]


def test_with_curiosities_off_for_one_user_none_are_offered_to_them(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    presentation_is_due(client, chat_model, clock, scheduler, seeded_settings)
    admin = owner_headers(client, auth_verifier)
    user_id = maya_id(client, auth_verifier)

    switch_for_user(client, admin, user_id, "curiosities", "off")
    off = understanding_sees(client, chat_model, "hey you")
    end_current_conversation(
        chat_model, clock, scheduler, seeded_settings, [new_curiosity(ask="New?")]
    )
    switch_for_user(client, admin, user_id, "curiosities", "default")
    back_on = understanding_sees(client, chat_model, "hey again")

    assert PRESENTATION not in off
    assert len(chat_model.curiosity_keeping_calls) == 1
    assert PRESENTATION in back_on


def test_with_user_memory_off_none_are_made_but_waiting_ones_are_still_raised(
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
    headers = auth_headers(auth_verifier, "user_maya")
    presentation_is_due(client, chat_model, clock, scheduler, seeded_settings)
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)

    bring_up_curiosity(chat_model, 1)
    instructions = reply_instructions(client, chat_model, "hey you")
    end_current_conversation(
        chat_model, clock, scheduler, seeded_settings, [new_curiosity(ask="New?")]
    )
    rows = stored_curiosities(engine)

    assert PRESENTATION in instructions
    assert len(chat_model.curiosity_keeping_calls) == 1
    assert [(row["question"], row["state"]) for row in rows] == [
        (PRESENTATION, "raised")
    ]


def test_a_failing_curiosity_keeper_still_saves_the_summary_and_is_not_retried(
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
    chat_model.script("mm")
    send_to_webhook(client, telegram_text_update("presentation Thursday"))
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(processing_answer(summary="Talked about work."))
    chat_model.script_curiosity_keeping(RuntimeError("model down"))

    scheduler.tick()
    scheduler.tick()

    with engine.connect() as connection:
        summaries = connection.execute(
            text("SELECT summary FROM conversation_summaries")
        ).scalars()
        assert list(summaries) == ["Talked about work."]
    assert len(chat_model.curiosity_keeping_calls) == 1
    assert stored_curiosities(engine) == []


def test_no_dashboard_or_user_api_shows_curiosities(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    admin = owner_headers(client, auth_verifier)
    presentation_is_due(client, chat_model, clock, scheduler, seeded_settings)
    user_id = maya_id(client, auth_verifier)

    responses = [
        client.get(path, headers=headers).text
        for path in (
            "/api/me",
            "/api/memory-items",
            "/api/life-threads",
            "/api/conversation-summaries",
        )
    ] + [
        client.get(path, headers=admin).text
        for path in ("/api/admin/users", f"/api/admin/users/{user_id}/features")
    ]

    assert all(PRESENTATION not in response for response in responses)
