import json
from datetime import timedelta
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
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_features import maya_id, switch_for_user
from tests.test_post_conversation import processing_answer, quiet_gap

STUCK = "the launch keeps slipping and I can't decide what 'done' means"
SITUATION = "Their launch kept slipping; they couldn't say what done meant."
FEELING = "frustrated, a bit stuck"
WHY = "Pinning down a finish line gave them a next step they took."
PORTRAIT = "A builder who likes a clear finish line."


def move_outcome(
    move: int,
    result: str = "helped",
    situation: str = SITUATION,
    feeling: str = FEELING,
    why: str = WHY,
) -> dict[str, Any]:
    """Build one Move Outcome as the keeping model writes it."""
    return {
        "move": move,
        "situation": situation,
        "feeling": feeling,
        "result": result,
        "why": why,
    }


def move_outcome_keeping_answer(outcomes: list[dict[str, Any]]) -> str:
    """Build the JSON the Move Outcome keeping model answers with."""
    return json.dumps({"move_outcomes": outcomes})


def send_with_moves(
    client: TestClient,
    chat_model: ScriptedChatModel,
    message: str = STUCK,
    **answer: Any,
) -> None:
    """Send a Message whose Understanding picks the given Need and Moves."""
    chat_model.script_understanding(understanding_answer(**answer))
    chat_model.script("ok, let's pin it down")
    send_to_webhook(client, telegram_text_update(message))


def end_the_conversation(
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    outcomes: list[dict[str, Any]],
) -> None:
    """Let the quiet gap pass and end the Conversation keeping the given outcomes."""
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(processing_answer(summary="Talked about a launch."))
    chat_model.script_move_outcome_keeping(move_outcome_keeping_answer(outcomes))
    scheduler.tick()


def push_then_end(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    outcomes: list[dict[str, Any]],
) -> None:
    """Lead with Push and support with Plan steps, then end the Conversation."""
    send_with_moves(
        client,
        chat_model,
        need="Accountability",
        lead_move="Push",
        support_move="Plan steps",
    )
    end_the_conversation(chat_model, clock, scheduler, seeded_settings, outcomes)


def move_outcomes(client: TestClient, headers: dict[str, str]) -> list[dict[str, Any]]:
    """Get the User's Move Outcomes through the Dashboard API."""
    response = client.get("/api/move-outcomes", headers=headers)
    assert response.status_code == 200, response.text
    outcomes: list[dict[str, Any]] = response.json()["move_outcomes"]
    return outcomes


def stored_embeddings(engine: Engine) -> list[Any]:
    """Read every saved Move Outcome's embedding."""
    with engine.connect() as connection:
        return list(
            connection.execute(text("SELECT embedding FROM move_outcomes")).scalars()
        )


def maya_headers(auth_verifier: FakeAuthVerifier) -> dict[str, str]:
    """Build the Dashboard API headers for the User the tests talk as."""
    return auth_headers(auth_verifier, "user_maya")


def test_a_conversation_end_keeps_an_outcome_for_each_move_made(
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

    push_then_end(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [
            move_outcome(1),
            move_outcome(2, result="mixed", why="Too many steps at once."),
        ],
    )

    keeper_saw = chat_model.move_outcome_keeping_calls[-1].history[0].text
    assert "[1] Push (lead)" in keeper_saw
    assert "[2] Plan steps (support)" in keeper_saw
    assert STUCK in keeper_saw
    outcomes = move_outcomes(client, maya_headers(auth_verifier))
    assert [
        (
            outcome["move"],
            outcome["role"],
            outcome["situation"],
            outcome["feeling"],
            outcome["result"],
            outcome["why"],
        )
        for outcome in outcomes
    ] == [
        ("Push", "lead", SITUATION, FEELING, "helped", WHY),
        (
            "Plan steps",
            "support",
            SITUATION,
            FEELING,
            "mixed",
            "Too many steps at once.",
        ),
    ]
    assert outcomes[0]["made_at"] == "2026-11-11T09:00:00Z"
    assert all(embedding is not None for embedding in stored_embeddings(engine))


def test_the_same_move_made_twice_is_shown_once(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    send_with_moves(client, chat_model, need="Accountability", lead_move="Push")
    send_with_moves(
        client, chat_model, "fine, Friday", need="Accountability", lead_move="Push"
    )

    end_the_conversation(chat_model, clock, scheduler, seeded_settings, [])

    keeper_saw = chat_model.move_outcome_keeping_calls[-1].history[0].text
    assert keeper_saw.count("Push (lead)") == 1
    assert "[2]" not in keeper_saw


def test_odd_outcomes_are_skipped_and_the_good_one_kept(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    push_then_end(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [
            move_outcome(7),
            move_outcome(1, result="loved it"),
            move_outcome(2, situation=""),
            move_outcome(2, result="didnt_help"),
            move_outcome(2, result="helped"),
            "not an outcome",
        ],
    )

    outcomes = move_outcomes(client, maya_headers(auth_verifier))
    assert [(outcome["move"], outcome["result"]) for outcome in outcomes] == [
        ("Plan steps", "didnt_help")
    ]


def test_an_unreadable_answer_is_asked_again_once_then_nothing_is_kept(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    send_with_moves(client, chat_model, need="Accountability", lead_move="Push")
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(processing_answer())
    chat_model.script_move_outcome_keeping("not json", "still not json")

    scheduler.tick()
    scheduler.tick()

    assert len(chat_model.move_outcome_keeping_calls) == 2
    assert move_outcomes(client, maya_headers(auth_verifier)) == []


def test_a_conversation_with_no_moves_asks_nothing(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    send_with_moves(client, chat_model, "hey, how's it going")

    end_the_conversation(chat_model, clock, scheduler, seeded_settings, [])

    assert chat_model.move_outcome_keeping_calls == []


def test_with_user_memory_off_no_outcomes_are_kept(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = maya_headers(auth_verifier)
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)

    push_then_end(
        client, chat_model, clock, scheduler, seeded_settings, [move_outcome(1)]
    )

    assert chat_model.move_outcome_keeping_calls == []
    assert move_outcomes(client, headers) == []


def test_with_user_memory_off_by_an_admin_no_outcomes_are_kept(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    switch_for_user(client, admin, maya_id(client, auth_verifier), "user_memory", "off")

    push_then_end(
        client, chat_model, clock, scheduler, seeded_settings, [move_outcome(1)]
    )

    assert chat_model.move_outcome_keeping_calls == []


def test_a_failing_keeper_still_writes_the_portrait(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    send_with_moves(client, chat_model, need="Accountability", lead_move="Push")
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(processing_answer())
    chat_model.script_move_outcome_keeping(RuntimeError("model down"))
    chat_model.script_portrait(PORTRAIT)

    scheduler.tick()

    headers = maya_headers(auth_verifier)
    portrait = client.get("/api/user-portrait", headers=headers).json()["portrait"]
    assert portrait["text"] == PORTRAIT


def test_the_portrait_is_given_the_move_outcomes(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    push_then_end(
        client, chat_model, clock, scheduler, seeded_settings, [move_outcome(1)]
    )

    portrait_saw = chat_model.portrait_calls[-1].history[0].text
    assert "What has helped and what hasn't:" in portrait_saw
    assert f"Push (lead) helped. {SITUATION} Felt: {FEELING}. Why: {WHY}" in (
        portrait_saw
    )
    assert chat_model.call_order.index("move_outcome_keeping") < (
        chat_model.call_order.index("portrait")
    )


def test_deleting_an_outcome_rewrites_the_portrait_without_it(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = maya_headers(auth_verifier)
    chat_model.script_portrait(PORTRAIT)
    push_then_end(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [move_outcome(1), move_outcome(2, why="A short list landed well.")],
    )
    push = move_outcomes(client, headers)[0]

    response = client.delete(f"/api/move-outcomes/{push['id']}", headers=headers)
    chat_model.script_portrait("Rewritten without Push.")
    scheduler.tick()

    assert response.status_code == 204
    assert [outcome["move"] for outcome in move_outcomes(client, headers)] == [
        "Plan steps"
    ]
    rewrite_input = chat_model.portrait_calls[-1].history[0].text
    assert WHY not in rewrite_input
    assert "A short list landed well." in rewrite_input
    portrait = client.get("/api/user-portrait", headers=headers).json()["portrait"]
    assert portrait["text"] == "Rewritten without Push."


def test_a_user_cannot_see_or_delete_another_users_outcome(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    push_then_end(
        client, chat_model, clock, scheduler, seeded_settings, [move_outcome(1)]
    )
    [outcome] = move_outcomes(client, maya_headers(auth_verifier))
    ren = auth_headers(auth_verifier, "user_ren")

    response = client.delete(f"/api/move-outcomes/{outcome['id']}", headers=ren)

    assert move_outcomes(client, ren) == []
    assert response.status_code == 404
    assert len(move_outcomes(client, maya_headers(auth_verifier))) == 1


def test_move_outcome_routes_need_sign_in(client: TestClient) -> None:
    assert client.get("/api/move-outcomes").status_code == 401
    assert (
        client.delete(
            "/api/move-outcomes/00000000-0000-0000-0000-000000000000"
        ).status_code
        == 401
    )


def test_message_retention_leaves_move_outcomes(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    push_then_end(
        client, chat_model, clock, scheduler, seeded_settings, [move_outcome(1)]
    )

    clock.advance(timedelta(days=seeded_settings["message_retention_days"] + 1))
    scheduler.tick()

    assert len(move_outcomes(client, maya_headers(auth_verifier))) == 1


def test_admins_see_only_how_many_outcomes_a_user_has(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    push_then_end(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [move_outcome(1), move_outcome(2)],
    )

    response = client.get(
        "/api/admin/users", headers=owner_headers(client, auth_verifier)
    )

    [maya] = [
        user
        for user in response.json()["users"]
        if user["email"] == "user_maya@example.com"
    ]
    assert maya["move_outcome_count"] == 2
    assert SITUATION not in response.text
    assert WHY not in response.text


def test_an_outcome_that_cannot_be_embedded_is_still_kept(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    embedder: FakeEmbedder,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    send_with_moves(client, chat_model, need="Accountability", lead_move="Push")
    embedder.failure = RuntimeError("embedder down")

    end_the_conversation(
        chat_model, clock, scheduler, seeded_settings, [move_outcome(1)]
    )

    assert len(move_outcomes(client, maya_headers(auth_verifier))) == 1
    assert stored_embeddings(engine) == [None]
