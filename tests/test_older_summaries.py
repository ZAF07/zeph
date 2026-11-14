from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeEmbedder,
    FakeScheduler,
    ScriptedChatModel,
    understanding_answer,
)
from tests.telegram_helpers import (
    OWNER_TELEGRAM_USER_ID,
    auth_headers,
    connect_owner_telegram,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_post_conversation import (
    have_conversation,
    processing_answer,
    quiet_gap,
)

INTERVIEW_SUMMARY = "Had the interview at Acme for the design role; felt hopeful."
MATCHING_PHRASE = "Acme interview design role"
OTHER_SUMMARIES = (
    "Chatted about cooking pasta.",
    "Talked about a rainy weekend.",
    "Went over plans for a garden.",
)


def have_conversations(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    summaries: tuple[str, ...],
) -> None:
    """Have one processed Conversation per summary, oldest first."""
    for summary in summaries:
        have_conversation(
            client,
            chat_model,
            clock,
            scheduler,
            seeded_settings,
            "hi again",
            processing_answer(summary=summary, mood="fine"),
        )
    chat_model.calls.clear()
    chat_model.understanding_calls.clear()


def ask_with_look_up_past(
    client: TestClient, chat_model: ScriptedChatModel, look_up_past: list[str]
) -> str:
    """Send a message whose Understanding looks up the past.

    Returns the reply call's instructions.
    """
    chat_model.script_understanding(understanding_answer(look_up_past=look_up_past))
    chat_model.script("oh yes, I remember")
    send_to_webhook(client, telegram_text_update("how did that go, did I tell you?"))
    reply_call = chat_model.calls[-1]
    return reply_call.instructions


def set_settings(
    client: TestClient, auth_verifier: FakeAuthVerifier, values: dict[str, Any]
) -> None:
    """Save platform settings as the initial Admin."""
    response = client.patch(
        "/api/admin/settings",
        json={"values": values},
        headers=owner_headers(client, auth_verifier),
    )
    assert response.status_code == 200, response.text


def test_new_summaries_are_embedded_when_written(
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

    have_conversations(
        client, chat_model, clock, scheduler, seeded_settings, (INTERVIEW_SUMMARY,)
    )

    with engine.connect() as connection:
        embedded = connection.execute(
            text("SELECT embedding IS NOT NULL FROM conversation_summaries")
        ).scalar_one()
    assert embedded


def test_a_summary_is_still_saved_when_embedding_it_fails(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    embedder: FakeEmbedder,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    embedder.failure = RuntimeError("embedding model is down")

    have_conversations(
        client, chat_model, clock, scheduler, seeded_settings, (INTERVIEW_SUMMARY,)
    )

    summaries = client.get("/api/conversation-summaries", headers=headers).json()
    assert [item["summary"] for item in summaries["summaries"]] == [INTERVIEW_SUMMARY]


def test_a_look_up_past_phrase_brings_an_old_summary_into_the_reply_with_its_date(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    have_conversations(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        (INTERVIEW_SUMMARY, *OTHER_SUMMARIES),
    )

    instructions = ask_with_look_up_past(client, chat_model, [MATCHING_PHRASE])

    assert "Older Conversations that may matter:" in instructions
    assert f"- 11 Nov 2026: {INTERVIEW_SUMMARY} They seemed fine." in instructions
    for summary in OTHER_SUMMARIES:
        assert instructions.count(summary) == 1


def test_a_weak_match_adds_nothing(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    have_conversations(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        (INTERVIEW_SUMMARY, *OTHER_SUMMARIES),
    )

    instructions = ask_with_look_up_past(client, chat_model, ["holiday in Spain"])

    assert INTERVIEW_SUMMARY not in instructions
    assert "Older Conversations that may matter:" not in instructions


def test_an_empty_look_up_past_searches_nothing(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    embedder: FakeEmbedder,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    have_conversations(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        (INTERVIEW_SUMMARY, *OTHER_SUMMARIES),
    )
    embedder.queries.clear()

    instructions = ask_with_look_up_past(client, chat_model, [])

    assert INTERVIEW_SUMMARY not in instructions
    assert set(embedder.queries) == {"how did that go, did I tell you?"}


def test_only_the_users_own_summaries_are_searched(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_owner_telegram(client, auth_verifier, chat_channel)
    chat_model.script("mm, I hear you")
    send_to_webhook(
        client,
        telegram_text_update("big day", OWNER_TELEGRAM_USER_ID, username="owner_tg"),
    )
    clock.advance(quiet_gap(seeded_settings) * 2)
    chat_model.script_processing(processing_answer(summary=INTERVIEW_SUMMARY))
    scheduler.tick()
    connect_telegram(client, auth_verifier, chat_channel)
    have_conversations(
        client, chat_model, clock, scheduler, seeded_settings, OTHER_SUMMARIES
    )

    instructions = ask_with_look_up_past(client, chat_model, [MATCHING_PHRASE])

    assert INTERVIEW_SUMMARY not in instructions


def test_the_admin_sets_how_many_older_summaries_go_in_and_how_close_they_must_be(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    second_interview = "Second Acme interview went badly."
    have_conversations(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        (INTERVIEW_SUMMARY, second_interview, *OTHER_SUMMARIES),
    )

    set_settings(
        client,
        auth_verifier,
        {"older_summaries_per_reply": 1, "older_summaries_closeness_percent": 10},
    )
    one_only = ask_with_look_up_past(client, chat_model, ["Second Acme interview"])
    set_settings(client, auth_verifier, {"older_summaries_closeness_percent": 100})
    too_strict = ask_with_look_up_past(client, chat_model, [MATCHING_PHRASE])

    assert second_interview in one_only
    assert INTERVIEW_SUMMARY not in one_only
    assert INTERVIEW_SUMMARY not in too_strict
    assert second_interview not in too_strict


def test_a_deleted_summary_is_no_longer_found(
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
    have_conversations(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        (INTERVIEW_SUMMARY, *OTHER_SUMMARIES),
    )
    summaries = client.get("/api/conversation-summaries", headers=headers).json()
    [interview_id] = [
        item["id"]
        for item in summaries["summaries"]
        if item["summary"] == INTERVIEW_SUMMARY
    ]

    client.delete(f"/api/conversation-summaries/{interview_id}", headers=headers)
    instructions = ask_with_look_up_past(client, chat_model, [MATCHING_PHRASE])

    assert INTERVIEW_SUMMARY not in instructions
    with engine.connect() as connection:
        embeddings_left = connection.execute(
            text("SELECT count(*) FROM conversation_summaries WHERE id = :id"),
            {"id": interview_id},
        ).scalar_one()
    assert embeddings_left == 0
