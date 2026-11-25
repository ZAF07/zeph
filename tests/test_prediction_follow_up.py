import json
from datetime import timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import (
    Curiosity,
    CuriosityState,
    PatternMoveReason,
    PatternState,
    PredictionOutcome,
)
from companion.core.predictions import GIVEN_CHECK_PROMPT
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import owner_headers
from tests.test_conversation import set_platform_setting
from tests.test_explorations import talk
from tests.test_features import switch_for_user
from tests.test_life_threads import thread_keeping_answer
from tests.test_moves_migration import downgrade_to
from tests.test_pattern_sharing import (
    APPROVED_WORDING,
    PREDICTION,
    PREDICTION_WORDING,
    predictions_of,
    ready_to_share,
    share,
)
from tests.test_pattern_states import moves_of, states_and_causes
from tests.test_pattern_tagging import observation_entry, observations_of
from tests.test_post_conversation import processing_answer, quiet_gap
from tests.test_ready_gate import belonging

FOLLOW_UP = "You asked them to watch for this"
GIVE_NEW = "watching for one new thing"
OPEN_PREDICTIONS_HEADER = "Predictions Zeph gave them, still open:"
PORTRAIT_PATTERNS_HEADER = "Patterns they agreed with:"
SECOND_PREDICTION = "This week, notice what you do when Jun asks a favour."
FOLLOW_UP_SETTINGS = (
    "prediction_follow_up_wait_days",
    "prediction_follow_up_drop_days",
    "predictions_to_confirm",
    "pattern_confirm_points_after_sharing",
)
CAME_TRUE = [{"prediction": 1, "outcome": "came_true"}]
DID_NOT = [{"prediction": 1, "outcome": "did_not"}]
NOT_COME_UP = [{"prediction": 1, "outcome": "not_come_up"}]
ASK_FIRST = {
    "need": "Think it through",
    "bring_up": [{"curiosity": 1, "how": "weave"}],
}


def prediction_curiosities(engine: Engine, user_id: str) -> list[Curiosity]:
    """List a User's Curiosities about Predictions, oldest first."""
    return build_postgres_repositories(engine).curiosities.list_about_predictions(
        UUID(user_id)
    )


def waiting(engine: Engine, user_id: str) -> list[Curiosity]:
    """List a User's waiting Curiosities about Predictions."""
    return [
        curiosity
        for curiosity in prediction_curiosities(engine, user_id)
        if curiosity.state == CuriosityState.WAITING
    ]


def end(
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    outcomes: list[dict[str, Any]] | None = None,
    observations: list[dict[str, Any]] | None = None,
) -> str:
    """End the open Conversation, tagged as given; return what tagging was given."""
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(processing_answer(summary="Talked about Mei."))
    chat_model.script_thread_keeping(thread_keeping_answer([]))
    chat_model.script_pattern_tagging(
        json.dumps(
            {"observations": observations or [], "prediction_outcomes": outcomes or []}
        )
    )
    scheduler.tick()
    return chat_model.pattern_tagging_calls[-1].history[0].text


def share_and_end(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    **share_changes: Any,
) -> str:
    """Tell Maya her ready Pattern with a Prediction and end that Conversation."""
    user_id = ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    share(client, chat_model, clock, **share_changes)
    end(chat_model, clock, scheduler, seeded_settings)
    return user_id


def ask_and_answer(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    answer: str = "yes, it happened just like you said",
) -> str:
    """Have a reply ask the first due Curiosity and the User answer it.

    Two more replies follow, so the pace allows the next Curiosity. Returns
    what the Reply Plan was given when it picked the Curiosity.
    """
    plan_saw = talk(client, chat_model, clock, "hey", **ASK_FIRST)
    talk(client, chat_model, clock, answer, curiosity_taken="engaged")
    talk(client, chat_model, clock, "anyway")
    talk(client, chat_model, clock, "that's all for now")
    return plan_saw


def portrait_patterns(chat_model: ScriptedChatModel) -> str:
    """The Patterns part of what the newest Portrait call was given."""
    described = chat_model.portrait_calls[-1].history[0].text
    return described[described.index(PORTRAIT_PATTERNS_HEADER) :].split("\n\n")[0]


def test_a_prediction_gets_a_follow_up_curiosity_not_before_the_admin_set_wait(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = share_and_end(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )

    [prediction] = predictions_of(client.engine, user_id)
    [follow_up] = waiting(client.engine, user_id)
    made_on = prediction.made_at.date()
    assert follow_up.prediction_id == prediction.id
    assert follow_up.pattern_id == belonging(client.engine, user_id).id
    assert follow_up.not_before == made_on + timedelta(days=7)
    assert follow_up.not_after == made_on + timedelta(days=21)

    clock.advance(timedelta(days=5))
    too_early = talk(client, chat_model, clock, "hi again")
    end(chat_model, clock, scheduler, seeded_settings)
    clock.advance(timedelta(days=2))
    in_time = talk(client, chat_model, clock, "hello")

    assert FOLLOW_UP not in too_early
    assert FOLLOW_UP in in_time
    offered = next(line for line in in_time.splitlines() if FOLLOW_UP in line)
    assert offered.startswith("[1] ")
    assert PREDICTION in offered
    assert APPROVED_WORDING in offered
    assert "how a Prediction went" in offered
    assert len(waiting(client.engine, user_id)) == 1


def test_a_follow_up_not_asked_within_the_longer_time_is_closed(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = share_and_end(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    [follow_up] = waiting(client.engine, user_id)

    clock.advance(timedelta(days=22))
    too_late = talk(client, chat_model, clock, "it's been a while")
    end(chat_model, clock, scheduler, seeded_settings)

    assert FOLLOW_UP not in too_late
    by_id = {
        curiosity.id: curiosity
        for curiosity in prediction_curiosities(client.engine, user_id)
    }
    assert by_id[follow_up.id].state == CuriosityState.CLOSED
    assert by_id[follow_up.id].raised_at is None
    [prediction] = predictions_of(client.engine, user_id)
    assert prediction.outcome == PredictionOutcome.NOT_FOLLOWED_UP
    assert belonging(client.engine, user_id).state == PatternState.SHARED
    [give] = waiting(client.engine, user_id)
    assert give.prediction_id is None


def test_predictions_that_came_true_confirm_a_pattern_and_it_joins_the_portrait(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = share_and_end(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    assert portrait_patterns(chat_model).endswith("None yet.")
    clock.advance(timedelta(days=7))

    ask_and_answer(client, chat_model, clock)
    tagging_saw = end(chat_model, clock, scheduler, seeded_settings, CAME_TRUE)

    shown = tagging_saw[tagging_saw.index(OPEN_PREDICTIONS_HEADER) :].split("\n\n")[0]
    assert shown.splitlines()[1].startswith("[1] (given ")
    assert shown.endswith(PREDICTION)
    [first] = predictions_of(client.engine, user_id)
    assert first.outcome == PredictionOutcome.CAME_TRUE
    assert belonging(client.engine, user_id).state == PatternState.SHARED
    assert portrait_patterns(chat_model).endswith("None yet.")
    [give] = waiting(client.engine, user_id)
    assert give.prediction_id is None

    clock.advance(timedelta(days=1))
    chat_model.script_given_check(
        json.dumps({"given": True, "prediction": SECOND_PREDICTION})
    )
    plan_saw = ask_and_answer(client, chat_model, clock, "ok, I'll watch for that")

    assert GIVE_NEW in plan_saw
    assert PREDICTION_WORDING in plan_saw
    [check] = chat_model.given_check_calls
    assert check.instructions == GIVEN_CHECK_PROMPT
    assert check.model == seeded_settings["check_in_model"]
    assert check.thinking is False
    assert "mm, tell me more" in check.history[0].text
    second = predictions_of(client.engine, user_id)[-1]
    assert (second.wording, second.outcome) == (SECOND_PREDICTION, None)

    end(chat_model, clock, scheduler, seeded_settings)
    [second_follow_up] = waiting(client.engine, user_id)
    assert second_follow_up.prediction_id == second.id
    clock.advance(timedelta(days=7))
    ask_and_answer(client, chat_model, clock)
    end(chat_model, clock, scheduler, seeded_settings, CAME_TRUE)

    assert belonging(client.engine, user_id).state == PatternState.CONFIRMED
    move = moves_of(client.engine, user_id)[-1]
    assert states_and_causes([move]) == [("shared", "confirmed", "conversation_tagged")]
    assert move.reason == PatternMoveReason.PREDICTIONS_CAME_TRUE
    assert move.conversation_id is not None
    assert waiting(client.engine, user_id) == []
    assert portrait_patterns(chat_model).splitlines()[1:] == [
        f"- {APPROVED_WORDING}, even when they matter to you."
        " It shows with family, friend; not with partner."
    ]


def test_came_true_counts_as_a_strong_sign_for_the_pattern(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = share_and_end(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    shared_at_points = moves_of(client.engine, user_id)[-1].points
    set_platform_setting(client.engine, "predictions_to_confirm", 1)
    set_platform_setting(client.engine, "pattern_half_life_days", 100000)
    clock.advance(timedelta(days=7))

    ask_and_answer(client, chat_model, clock)
    end(chat_model, clock, scheduler, seeded_settings, CAME_TRUE)

    move = moves_of(client.engine, user_id)[-1]
    assert move.to_state == PatternState.CONFIRMED
    assert move.points == pytest.approx(shared_at_points + 140, abs=1)


def test_hasnt_come_up_adds_nothing_and_a_later_follow_up_is_made(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = share_and_end(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    moves_before = len(moves_of(client.engine, user_id))
    clock.advance(timedelta(days=7))

    ask_and_answer(client, chat_model, clock, "it hasn't come up, Mei's been away")
    end(chat_model, clock, scheduler, seeded_settings, NOT_COME_UP)

    [prediction] = predictions_of(client.engine, user_id)
    assert prediction.outcome == PredictionOutcome.NOT_COME_UP
    assert prediction.outcome_at is not None
    assert belonging(client.engine, user_id).state == PatternState.SHARED
    assert len(moves_of(client.engine, user_id)) == moves_before
    [later] = waiting(client.engine, user_id)
    said_on = prediction.outcome_at.date()
    assert later.prediction_id == prediction.id
    assert later.not_before == said_on + timedelta(days=7)
    assert later.not_after == said_on + timedelta(days=21)

    clock.advance(timedelta(days=7))
    assert FOLLOW_UP in talk(client, chat_model, clock, "hi")


def test_a_prediction_that_didnt_is_a_strong_sign_against_and_can_close_the_pattern(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = share_and_end(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    shared_at_points = moves_of(client.engine, user_id)[-1].points
    set_platform_setting(client.engine, "pattern_half_life_days", 100000)
    set_platform_setting(
        client.engine, "pattern_closed_under_points", int(shared_at_points) - 100
    )
    clock.advance(timedelta(days=7))

    ask_and_answer(client, chat_model, clock, "no, I actually said no to her")
    end(chat_model, clock, scheduler, seeded_settings, DID_NOT)

    [prediction] = predictions_of(client.engine, user_id)
    assert prediction.outcome == PredictionOutcome.DID_NOT
    assert belonging(client.engine, user_id).state == PatternState.CLOSED
    move = moves_of(client.engine, user_id)[-1]
    assert states_and_causes([move]) == [("shared", "closed", "conversation_tagged")]
    assert move.reason == PatternMoveReason.SCORE_UNDER_FLOOR
    assert move.points == pytest.approx(shared_at_points - 140, abs=1)
    assert waiting(client.engine, user_id) == []

    set_platform_setting(client.engine, "pattern_closed_under_points", -150)
    clock.advance(timedelta(days=1))
    talk(client, chat_model, clock, "I said yes to Mei again")
    end(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        observations=[observation_entry(thread=None)],
    )

    assert belonging(client.engine, user_id).state == PatternState.CLOSED
    assert moves_of(client.engine, user_id)[-1].id == move.id


def test_strong_evidence_after_sharing_confirms_a_shared_pattern(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = share_and_end(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    set_platform_setting(client.engine, "pattern_confirm_points_after_sharing", 100)
    clock.advance(timedelta(days=1))

    talk(client, chat_model, clock, "I said yes to Mei again")
    end(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        observations=[observation_entry(thread=None)],
    )

    assert belonging(client.engine, user_id).state == PatternState.CONFIRMED
    move = moves_of(client.engine, user_id)[-1]
    assert move.reason == PatternMoveReason.STRONG_EVIDENCE_AFTER_SHARING


def test_a_pattern_shared_with_no_prediction_gets_one_only_when_the_check_says_so(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = share_and_end(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        check=json.dumps({"shared": True, "prediction": ""}),
    )
    assert predictions_of(client.engine, user_id) == []
    [give] = waiting(client.engine, user_id)
    assert give.prediction_id is None
    clock.advance(timedelta(days=1))

    chat_model.script_given_check(json.dumps({"given": False, "prediction": ""}))
    ask_and_answer(client, chat_model, clock, "hm ok")
    end(chat_model, clock, scheduler, seeded_settings)

    assert predictions_of(client.engine, user_id) == []
    [again] = waiting(client.engine, user_id)
    assert again.id != give.id

    clock.advance(timedelta(days=1))
    chat_model.script_given_check(RuntimeError("model down"))
    ask_and_answer(client, chat_model, clock, "sure")

    assert predictions_of(client.engine, user_id) == []
    assert len(chat_model.given_check_calls) == 2


def test_with_pattern_sharing_off_no_follow_up_is_offered_or_written(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = share_and_end(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    switch_for_user(
        client, owner_headers(client, auth_verifier), user_id, "pattern_sharing", "off"
    )
    clock.advance(timedelta(days=30))

    plan_saw = talk(client, chat_model, clock, "hello")
    end(chat_model, clock, scheduler, seeded_settings)

    assert FOLLOW_UP not in plan_saw
    [prediction] = predictions_of(client.engine, user_id)
    assert prediction.outcome is None
    assert len(waiting(client.engine, user_id)) == 1


def test_the_four_follow_up_numbers_are_settings_with_hints_and_eval_overrides(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    settings = client.get("/api/admin/settings", headers=admin).json()["settings"]
    choices = client.get("/api/admin/setting-override-choices", headers=admin).json()

    assert {key: settings[key]["value"] for key in FOLLOW_UP_SETTINGS} == {
        "prediction_follow_up_wait_days": 7,
        "prediction_follow_up_drop_days": 21,
        "predictions_to_confirm": 2,
        "pattern_confirm_points_after_sharing": 300,
    }
    assert all(settings[key]["hint"] for key in FOLLOW_UP_SETTINGS)
    assert set(FOLLOW_UP_SETTINGS) <= {
        setting["key"] for setting in choices["settings"]
    }


def test_the_migration_keeps_user_data_and_reloads_the_tagging_prompt(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    database_url: str,
) -> None:
    user_id = share_and_end(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    set_platform_setting(client.engine, "predictions_to_confirm", 1)
    clock.advance(timedelta(days=7))
    ask_and_answer(client, chat_model, clock)
    end(chat_model, clock, scheduler, seeded_settings, CAME_TRUE)
    assert belonging(client.engine, user_id).state == PatternState.CONFIRMED
    observations_before = observations_of(client.engine, user_id)
    moves_before = len(moves_of(client.engine, user_id))
    set_platform_setting(client.engine, "pattern_tagging_prompt", "edited")

    downgrade_to(database_url, "0100")
    try:
        with client.engine.connect() as connection:
            states = connection.execute(text("SELECT state FROM patterns")).scalars()
            assert list(states) == ["shared"]
            about_predictions = connection.execute(
                text("SELECT count(*) FROM curiosities WHERE aim = 'prediction'")
            ).scalar_one()
            assert about_predictions == 0
    finally:
        migrate(database_url)

    assert observations_of(client.engine, user_id) == observations_before
    assert len(moves_of(client.engine, user_id)) == moves_before
    assert [item.wording for item in predictions_of(client.engine, user_id)] == [
        PREDICTION
    ]
    with client.engine.connect() as connection:
        stored = connection.execute(
            text(
                "SELECT count(*) FROM platform_settings "
                "WHERE key = 'pattern_tagging_prompt'"
            )
        ).scalar_one()
    assert stored == 0
