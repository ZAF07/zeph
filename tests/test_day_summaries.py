from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import (
    auth_headers,
    connect_telegram,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_moves_migration import downgrade_to
from tests.test_post_conversation import (
    have_conversation,
    processing_answer,
    quiet_gap,
)
from tests.test_user_portrait import end_conversation_with_portrait


def day_summaries(client: TestClient, headers: dict[str, str]) -> list[Any]:
    """List the User's Day Summaries through the Dashboard API."""
    response = client.get("/api/day-summaries", headers=headers)
    assert response.status_code == 200
    return list(response.json()["summaries"])


def live_in_singapore(client: TestClient, headers: dict[str, str]) -> None:
    """Set the User's time zone to Singapore (UTC+8) through the Dashboard API."""
    response = client.patch(
        "/api/me", json={"time_zone": "Asia/Singapore"}, headers=headers
    )
    assert response.status_code == 200


def test_two_conversations_on_one_day_leave_one_summary_written_from_both(
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
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "I'm moving flat on Saturday",
        processing_answer(summary="Planning a move on Saturday."),
    )
    clock.advance(timedelta(hours=1))
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "the movers just cancelled on me",
        processing_answer(
            summary="Planning a Saturday move; the movers cancelled.",
            mood="calm, then stressed",
        ),
    )

    [summary] = day_summaries(client, headers)
    assert summary["summary"] == "Planning a Saturday move; the movers cancelled."
    assert summary["mood"] == "calm, then stressed"
    assert summary["day"] == "2026-11-11"
    second_call = chat_model.processing_calls[1].history[0].text
    assert "Person: I'm moving flat on Saturday" in second_call
    assert "Person: the movers just cancelled on me" in second_call
    assert "Planning a move on Saturday." not in second_call


def test_a_conversation_past_midnight_belongs_to_the_day_it_started(
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
    live_in_singapore(client, headers)
    clock.advance(timedelta(hours=6, minutes=50))
    chat_model.script("oh no, what happened?")
    send_to_webhook(client, telegram_text_update("can't sleep, big fight with Sam"))
    for minutes in (10, 10, 10, 10):
        clock.advance(timedelta(minutes=minutes))
        chat_model.script("mm, go on")
        send_to_webhook(client, telegram_text_update("and he just left"))
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(processing_answer(summary="A late fight with Sam."))
    scheduler.tick()

    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "morning, slept a little in the end",
        processing_answer(summary="Slept a little after the fight."),
    )

    summaries = day_summaries(client, headers)
    assert [(entry["day"], entry["summary"]) for entry in summaries] == [
        ("2026-11-12", "Slept a little after the fight."),
        ("2026-11-11", "A late fight with Sam."),
    ]
    next_day_call = chat_model.processing_calls[1].history[0].text
    assert "big fight with Sam" not in next_day_call


def test_the_memory_processing_prompt_asks_for_facts_and_feelings(
    seeded_settings: dict[str, Any],
) -> None:
    prompt = " ".join(seeded_settings["memory_processing_prompt"].split())
    for asked_for in (
        "all of today's messages",
        "what Zeph advised and how they answered",
        "how they felt and why",
        "what it meant to them",
        "how their mood moved and what moved it",
    ):
        assert asked_for in prompt


def test_only_the_conversation_that_ended_is_learned_from(
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
        "I'm moving flat on Saturday",
        processing_answer(),
    )
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "the movers cancelled",
        processing_answer(),
    )

    second_call = chat_model.processing_calls[1].history[0].text
    earlier, just_ended = second_call.split("The Conversation that just ended:")
    assert "Person: I'm moving flat on Saturday" in earlier
    assert "Person: the movers cancelled" in just_ended
    assert "moving flat" not in just_ended


def test_deleting_a_day_summary_removes_it_and_rewrites_the_portrait(
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
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )
    [summary] = day_summaries(client, headers)

    response = client.delete(f"/api/day-summaries/{summary['id']}", headers=headers)
    chat_model.script_portrait("Maya is a teacher.")
    scheduler.tick()
    scheduler.tick()

    assert response.status_code == 204
    assert day_summaries(client, headers) == []
    rewrite_input = chat_model.portrait_calls[1].history[0].text
    assert "Talked about a long day at school." not in rewrite_input


def test_delete_my_data_removes_day_summaries(
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
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "hi",
        processing_answer(),
    )
    assert len(day_summaries(client, headers)) == 1

    response = client.delete("/api/me/data", headers=headers)

    assert response.status_code == 204
    assert day_summaries(client, headers) == []
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT count(*) FROM day_summaries")).scalar_one()
            == 0
        )


def old_summary_rows(user_id: Any, embedding: str | None) -> list[dict[str, Any]]:
    """Conversations and their per-Conversation Summaries, as stored before 0064.

    Times are UTC; the User lives in Singapore (UTC+8), so the first two
    Conversations start on 11 Nov there and the third on 12 Nov.
    """
    return [
        {
            "started_at": "2026-11-11 02:00+00",
            "summary": "Talked about the move.",
            "mood": "calm",
            "offered": "",
            "embedding": embedding,
        },
        {
            "started_at": "2026-11-11 15:55+00",
            "summary": "The movers cancelled.",
            "mood": "stressed",
            "offered": "Suggested calling another firm; they said they would.",
            "embedding": embedding,
        },
        {
            "started_at": "2026-11-11 16:30+00",
            "summary": "Found new movers.",
            "mood": "relieved",
            "offered": "",
            "embedding": None,
        },
    ]


def test_the_migration_joins_same_day_summaries_into_one(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    engine: Engine,
    database_url: str,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    live_in_singapore(client, auth_headers(auth_verifier, "user_maya"))
    with engine.connect() as connection:
        user_id = connection.execute(
            text("SELECT id FROM users WHERE time_zone = 'Asia/Singapore'")
        ).scalar_one()
    embedding = "[" + ",".join(["1"] + ["0"] * 383) + "]"
    downgrade_to(database_url, "0063")
    try:
        with engine.begin() as connection:
            for number, row in enumerate(old_summary_rows(user_id, embedding)):
                conversation_id = connection.execute(
                    text(
                        "INSERT INTO conversations "
                        "(id, user_id, started_at, last_message_at) "
                        "VALUES (gen_random_uuid(), :user_id, :started_at, "
                        ":started_at) RETURNING id"
                    ),
                    {"user_id": user_id, "started_at": row["started_at"]},
                ).scalar_one()
                connection.execute(
                    text(
                        "INSERT INTO conversation_summaries "
                        "(id, conversation_id, user_id, summary, mood, offered, "
                        "created_at, embedding) VALUES (gen_random_uuid(), "
                        ":conversation_id, :user_id, :summary, :mood, :offered, "
                        ":created_at, :embedding)"
                    ),
                    {
                        **row,
                        "conversation_id": conversation_id,
                        "user_id": user_id,
                        "created_at": f"2026-11-1{1 + number // 2} 18:00+00",
                    },
                )
    finally:
        migrate(database_url)

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT day::text, summary, mood, offered, embedding IS NOT NULL "
                "FROM day_summaries ORDER BY day"
            )
        ).all()
    assert [tuple(row) for row in rows] == [
        (
            "2026-11-11",
            "Talked about the move. The movers cancelled.",
            "calm, then stressed",
            "Suggested calling another firm; they said they would.",
            True,
        ),
        ("2026-11-12", "Found new movers.", "relieved", "", False),
    ]
