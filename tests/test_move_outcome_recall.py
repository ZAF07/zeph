from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient

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
    connect_owner_telegram,
    connect_telegram,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_move_outcomes import (
    end_the_conversation,
    maya_headers,
    move_outcome,
    move_outcomes,
)
from tests.test_older_summaries import set_settings

EXHAUSTED_SITUATION = "Asked to push through their task list late at night."
EXHAUSTED_FEELING = "exhausted, running on empty"
EXHAUSTED_WHY = "They had nothing left; the push made them feel worse."
GRIEF_SITUATION = "Their grandmother had just passed away."
GRIEF_FEELING = "grieving, numb"


def keep_outcomes(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    outcomes: list[dict[str, Any]],
    telegram_user_id: int | None = None,
) -> None:
    """Have a Conversation leading with Push and supporting with Calm, and end it.

    Its end keeps the given Move Outcomes, numbered 1 for Push and 2 for Calm.
    """
    chat_model.script_understanding(
        understanding_answer(need="Accountability", lead_move="Push")
    )
    chat_model.script("come on, one more")
    update = (
        telegram_text_update("still going", telegram_user_id, username="owner_tg")
        if telegram_user_id
        else telegram_text_update("still going")
    )
    send_to_webhook(client, update)
    chat_model.script_understanding(
        understanding_answer(need="Be heard", lead_move="Calm")
    )
    chat_model.script("breathe")
    send_to_webhook(client, update)
    end_the_conversation(chat_model, clock, scheduler, seeded_settings, outcomes)
    clock.advance(timedelta(days=3))


def push_backfired_when_exhausted() -> dict[str, Any]:
    """Build the outcome of a Push that backfired while the User was exhausted."""
    return move_outcome(
        1,
        result="didnt_help",
        situation=EXHAUSTED_SITUATION,
        feeling=EXHAUSTED_FEELING,
        why=EXHAUSTED_WHY,
    )


def calm_while_grieving() -> dict[str, Any]:
    """Build the outcome of a Calm that helped while the User was grieving."""
    return move_outcome(
        2, situation=GRIEF_SITUATION, feeling=GRIEF_FEELING, why="It let them rest."
    )


def understanding_sees(
    client: TestClient, chat_model: ScriptedChatModel, text: str
) -> str:
    """Send a message and return what its Understanding was given."""
    chat_model.script("mm, I hear you")
    send_to_webhook(client, telegram_text_update(text))
    return chat_model.understanding_calls[-1].history[0].text


def test_close_outcomes_reach_the_understanding_with_their_dates(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    keep_outcomes(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [push_backfired_when_exhausted(), calm_while_grieving()],
    )
    set_settings(client, auth_verifier, {"move_outcomes_closeness_percent": 30})

    seen = understanding_sees(
        client, chat_model, "so exhausted, running on empty, still have my task list"
    )

    assert "11 Nov 2026: Push (lead) didn't help." in seen
    assert EXHAUSTED_SITUATION in seen
    assert EXHAUSTED_WHY in seen
    assert GRIEF_SITUATION not in seen


def test_only_the_users_own_outcomes_reach_the_understanding(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    owner = connect_owner_telegram(client, auth_verifier, chat_channel)
    keep_outcomes(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [push_backfired_when_exhausted()],
        telegram_user_id=OWNER_TELEGRAM_USER_ID,
    )
    assert len(move_outcomes(client, owner)) == 1
    connect_telegram(client, auth_verifier, chat_channel)
    set_settings(client, auth_verifier, {"move_outcomes_closeness_percent": 0})

    seen = understanding_sees(client, chat_model, "so exhausted, running on empty")

    assert EXHAUSTED_SITUATION not in seen


def test_the_admin_sets_how_many_reach_it_and_how_close_they_must_be(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    keep_outcomes(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [push_backfired_when_exhausted(), calm_while_grieving()],
    )

    set_settings(
        client,
        auth_verifier,
        {"move_outcomes_per_understanding": 1, "move_outcomes_closeness_percent": 0},
    )
    one_only = understanding_sees(client, chat_model, "exhausted and running on empty")
    set_settings(client, auth_verifier, {"move_outcomes_per_understanding": 0})
    none_wanted = understanding_sees(client, chat_model, "exhausted again")
    set_settings(
        client,
        auth_verifier,
        {"move_outcomes_per_understanding": 3, "move_outcomes_closeness_percent": 100},
    )
    too_strict = understanding_sees(client, chat_model, "exhausted, empty")

    assert EXHAUSTED_SITUATION in one_only
    assert GRIEF_SITUATION not in one_only
    assert EXHAUSTED_SITUATION not in none_wanted
    assert EXHAUSTED_SITUATION not in too_strict


def test_outcomes_still_reach_the_understanding_with_user_memory_off(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    keep_outcomes(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [push_backfired_when_exhausted()],
    )
    client.patch(
        "/api/me",
        json={"user_memory_enabled": False},
        headers=maya_headers(auth_verifier),
    )
    set_settings(client, auth_verifier, {"move_outcomes_closeness_percent": 30})

    seen = understanding_sees(client, chat_model, "so exhausted, running on empty")

    assert EXHAUSTED_SITUATION in seen


def test_the_reply_still_goes_when_outcomes_cannot_be_searched(
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
    keep_outcomes(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [push_backfired_when_exhausted()],
    )
    embedder.failure = RuntimeError("embedder down")

    seen = understanding_sees(client, chat_model, "so exhausted, running on empty")

    assert EXHAUSTED_SITUATION not in seen
    assert chat_channel.sent[-1].text == "mm, I hear you"
