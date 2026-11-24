from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import (
    CatalogPattern,
    PatternMove,
    PatternState,
)
from tests.eval_run_helpers import CRISIS_CASE, add_cases
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import auth_headers, connect_telegram, owner_headers
from tests.test_features import maya_id
from tests.test_life_threads import end_conversation, new_thread
from tests.test_moves_migration import downgrade_to
from tests.test_pattern_tagging import (
    MEI,
    TEXT,
    observation_entry,
    tagging_answer,
    turn_noticing_on,
)
from tests.test_patterns import GOES_QUIET, start_goes_quiet_pattern
from tests.test_patterns import patterns_of as old_patterns_of
from tests.test_recent_messages import change_settings

BELONG = "CONF.AVOID.BELONG"
WORK = new_thread(
    title="New manager at work",
    story="Their new manager keeps piling on work and they never say no.",
    people=("manager",),
)
MEI_STORY = observation_entry()
WORK_STORY = observation_entry(
    quote="Then I stewed on it all night", about="their manager", thread=2
)
SCORING_SETTINGS = (
    "pattern_weak_sign_points",
    "pattern_moderate_sign_points",
    "pattern_strong_sign_points",
    "pattern_real_story_percent",
    "pattern_reported_habit_percent",
    "pattern_what_if_percent",
    "pattern_own_opinion_percent",
    "pattern_unclear_percent",
    "pattern_half_life_days",
    "pattern_people_per_situation",
    "pattern_suspected_situations",
    "pattern_suspected_points",
    "pattern_closed_under_points",
)


def patterns_of(engine: Engine, user_id: str) -> list[CatalogPattern]:
    """List a User's Patterns of Pattern Types through the Pattern repository."""
    return build_postgres_repositories(engine).patterns.list_of_pattern_types(
        UUID(user_id)
    )


def moves_of(engine: Engine, user_id: str) -> list[PatternMove]:
    """List the log of a User's Pattern moves through the Pattern repository."""
    return build_postgres_repositories(engine).patterns.list_moves(UUID(user_id))


def end_tagged_conversation(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    *entries: dict[str, Any],
) -> None:
    """End a Conversation touching Mei (Thread 1) and work (Thread 2), tagged so."""
    chat_model.script_pattern_tagging(tagging_answer(*entries))
    end_conversation(
        client, chat_model, clock, scheduler, seeded_settings, TEXT, [MEI, WORK]
    )


def states_and_causes(moves: list[PatternMove]) -> list[tuple[Any, ...]]:
    """Each move's from, to and cause, as plain values."""
    return [
        (
            move.from_state.value if move.from_state else None,
            move.to_state.value,
            move.cause.value,
        )
        for move in moves
    ]


def test_a_first_observation_notices_a_pattern_and_logs_why(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_noticing_on(client, auth_verifier)

    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, MEI_STORY
    )

    [pattern] = patterns_of(client.engine, user_id)
    assert (pattern.pattern_type_id, pattern.state) == (BELONG, PatternState.NOTICED)
    [move] = moves_of(client.engine, user_id)
    assert states_and_causes([move]) == [(None, "noticed", "conversation_tagged")]
    assert move.pattern_id == pattern.id
    assert move.conversation_id is not None
    assert (move.points, move.situations) == (pytest.approx(140), 1)


def test_two_situations_with_enough_score_make_it_suspected(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_noticing_on(client, auth_verifier)

    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, MEI_STORY, WORK_STORY
    )

    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.state == PatternState.SUSPECTED
    assert states_and_causes(moves_of(client.engine, user_id)) == [
        (None, "noticed", "conversation_tagged"),
        ("noticed", "suspected", "conversation_tagged"),
    ]


def test_the_admin_set_bars_decide_when_it_is_suspected_and_closed(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_noticing_on(client, auth_verifier)
    change_settings(
        client,
        auth_verifier,
        {"pattern_suspected_situations": 1, "pattern_closed_under_points": -100},
    )

    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, MEI_STORY
    )
    end_tagged_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        observation_entry(
            sign="D1", direction="against", about="their manager", thread=2
        ),
        observation_entry(
            sign="D1",
            direction="against",
            quote="Then I stewed on it all night",
            about="their manager",
            thread=2,
        ),
        observation_entry(
            sign="D1",
            direction="against",
            quote="it's fine honestly",
            about="their boss",
            thread=2,
        ),
    )

    assert [
        state for _, state, _ in states_and_causes(moves_of(client.engine, user_id))
    ] == [
        "noticed",
        "suspected",
        "closed",
    ]


def test_deleting_its_observations_moves_it_back_at_once_and_the_log_stays(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_noticing_on(client, auth_verifier)
    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, MEI_STORY, WORK_STORY
    )
    headers = auth_headers(auth_verifier, "user_maya")
    threads = client.get("/api/life-threads", headers=headers).json()["threads"]
    work, mei = sorted(threads, key=lambda thread: thread["title"] != WORK["title"])

    client.delete(f"/api/life-threads/{work['id']}", headers=headers)

    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.state == PatternState.NOTICED
    assert states_and_causes(moves_of(client.engine, user_id))[-1] == (
        "suspected",
        "noticed",
        "observations_deleted",
    )

    client.delete(f"/api/life-threads/{mei['id']}", headers=headers)

    assert patterns_of(client.engine, user_id) == []
    assert len(moves_of(client.engine, user_id)) == 3


@pytest.mark.parametrize("route", ["/api/me/data", "/api/me"])
def test_delete_my_data_and_account_deletion_remove_patterns_and_their_log(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    route: str,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_noticing_on(client, auth_verifier)
    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, MEI_STORY
    )

    response = client.delete(route, headers=auth_headers(auth_verifier, "user_maya"))

    assert response.status_code == 204
    assert patterns_of(client.engine, user_id) == []
    assert moves_of(client.engine, user_id) == []


def test_admins_see_how_many_patterns_a_user_has_in_each_state_never_content(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    turn_noticing_on(client, auth_verifier)
    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, MEI_STORY, WORK_STORY
    )

    response = client.get(
        "/api/admin/users", headers=owner_headers(client, auth_verifier)
    )

    [maya] = [row for row in response.json()["users"] if row["role"] == "user"]
    assert maya["pattern_counts"]["suspected"] == 1
    assert sum(maya["pattern_counts"].values()) == 1
    assert BELONG not in response.text
    assert "Mei" not in response.text


def test_patterns_of_pattern_types_reach_no_reply_and_no_old_pattern_step(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_noticing_on(client, auth_verifier)
    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, MEI_STORY, WORK_STORY
    )
    keeping_before = len(chat_model.pattern_keeping_calls)

    end_tagged_conversation(client, chat_model, clock, scheduler, seeded_settings)

    assert patterns_of(client.engine, user_id)[0].state == PatternState.SUSPECTED
    later_calls = [
        *chat_model.calls,
        *chat_model.reply_plan_calls,
        *chat_model.understanding_calls,
        *chat_model.pattern_keeping_calls[keeping_before:],
    ]
    assert not any(BELONG in line.text for call in later_calls for line in call.history)
    patterns_tab = client.get(
        "/api/patterns", headers=auth_headers(auth_verifier, "user_maya")
    )
    assert patterns_tab.json()["patterns"] == []


def test_every_scoring_number_is_a_setting_with_a_hint_and_an_eval_override(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    add_cases(engine, CRISIS_CASE)

    settings = client.get("/api/admin/settings", headers=admin).json()["settings"]
    choices = client.get("/api/admin/setting-override-choices", headers=admin).json()
    run = client.post(
        "/api/admin/eval-runs",
        json={
            "evals": ["safeguard"],
            "variants": [{}, {"pattern_suspected_situations": 1}],
        },
        headers=admin,
    )

    assert all(settings[key]["hint"] for key in SCORING_SETTINGS)
    assert {key: settings[key]["value"] for key in SCORING_SETTINGS} == {
        "pattern_weak_sign_points": 30,
        "pattern_moderate_sign_points": 70,
        "pattern_strong_sign_points": 140,
        "pattern_real_story_percent": 100,
        "pattern_reported_habit_percent": 70,
        "pattern_what_if_percent": 40,
        "pattern_own_opinion_percent": 30,
        "pattern_unclear_percent": 25,
        "pattern_half_life_days": 75,
        "pattern_people_per_situation": 3,
        "pattern_suspected_situations": 2,
        "pattern_suspected_points": 100,
        "pattern_closed_under_points": -150,
    }
    assert set(SCORING_SETTINGS) <= {setting["key"] for setting in choices["settings"]}
    assert run.status_code == 201, run.text


def test_the_migration_keeps_every_old_pattern_with_its_evidence(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    database_url: str,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_goes_quiet_pattern(client, chat_model, clock, scheduler, seeded_settings)
    user_id = maya_id(client, auth_verifier)
    before = old_patterns_of(client.engine, user_id)

    downgrade_to(database_url, "0082")
    try:
        with client.engine.connect() as connection:
            rows = connection.execute(text("SELECT pattern, state FROM patterns")).all()
        assert [tuple(row) for row in rows] == [(GOES_QUIET, "suspected")]
    finally:
        migrate(database_url)

    assert old_patterns_of(client.engine, user_id) == before
    assert len(before[0].evidence) == 2
    assert patterns_of(client.engine, user_id) == []
