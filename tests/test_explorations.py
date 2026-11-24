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
    CuriosityAim,
    CuriosityState,
    Exploration,
    ExplorationNeed,
    ExplorationState,
    ExplorationTry,
    ExplorationWay,
    TryOutcome,
)
from companion.core.timing import users_today
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
    reply_plan_answer,
)
from tests.telegram_helpers import (
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_features import switch_for_user, user_features_by_key
from tests.test_life_threads import thread_keeping_answer
from tests.test_moves_migration import downgrade_to
from tests.test_pattern_states import end_tagged_conversation
from tests.test_pattern_tagging import (
    TEXT,
    observation_entry,
    observations_of,
    turn_noticing_on,
)
from tests.test_post_conversation import processing_answer, quiet_gap
from tests.test_recent_messages import change_settings

BELONG = "CONF.AVOID.BELONG"
WORTH = "ACH.WORTH.PERF"
UNCLEAR_MEI = observation_entry(pattern_types=[BELONG, WORTH])
CLEAR_WORK = observation_entry(
    quote="Then I stewed on it all night",
    about="their manager",
    thread=2,
    relationship="colleague",
    power="equal",
    setting="work",
)
AGENDA_SETTINGS = (
    "agenda_size",
    "exploration_wait_days",
    "exploration_rest_after_tries",
)
AGENDA_HEADER = "What you are exploring about them (the Agenda)"
MEI_STORY_POINTER = "Go back to what they told you about Mei, their sister on"


def turn_exploring_on(client: TestClient, auth_verifier: FakeAuthVerifier) -> str:
    """Turn Pattern noticing and Pattern exploring on for Maya only."""
    user_id = turn_noticing_on(client, auth_verifier)
    switch_for_user(
        client, owner_headers(client, auth_verifier), user_id, "pattern_exploring", "on"
    )
    return user_id


def explorations_of(engine: Engine, user_id: str) -> list[Exploration]:
    """List a User's Explorations through their repository."""
    return build_postgres_repositories(engine).explorations.list_for_user(UUID(user_id))


def tries_of(engine: Engine, user_id: str) -> list[ExplorationTry]:
    """List a User's tries through their repository."""
    return build_postgres_repositories(engine).explorations.list_tries(UUID(user_id))


def aimed_of(engine: Engine, user_id: str) -> list[Any]:
    """List a User's aimed Curiosities, oldest first."""
    return build_postgres_repositories(engine).curiosities.list_aimed(UUID(user_id))


def suspect_belonging(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    """End a Conversation that makes CONF.AVOID.BELONG suspected, with Mei unclear."""
    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, UNCLEAR_MEI, CLEAR_WORK
    )


def talk(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    message: str,
    **plan: Any,
) -> str:
    """Send a message a minute later under a scripted Reply Plan; return its input."""
    clock.advance(timedelta(minutes=1))
    chat_model.script_reply_plan(reply_plan_answer(**plan))
    chat_model.script("mm, tell me more")
    send_to_webhook(client, telegram_text_update(message))
    return chat_model.reply_plan_calls[-1].history[0].text


def end_now(
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    observations: list[dict[str, Any]] | None = None,
    settled: list[dict[str, Any]] | None = None,
) -> None:
    """Let the quiet gap pass and end the Conversation, tagged as given."""
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(processing_answer(summary="Talked about Mei."))
    chat_model.script_thread_keeping(thread_keeping_answer([]))
    chat_model.script_pattern_tagging(
        json.dumps({"observations": observations or [], "settled": settled or []})
    )
    scheduler.tick()


def test_a_suspected_pattern_gets_an_exploration_and_an_aimed_curiosity(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_exploring_on(client, auth_verifier)

    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)

    [exploration] = explorations_of(client.engine, user_id)
    assert (exploration.pattern_type_id, exploration.state) == (
        BELONG,
        ExplorationState.ACTIVE,
    )
    [curiosity] = aimed_of(client.engine, user_id)
    assert curiosity.aim == CuriosityAim.EXPLORATION
    assert curiosity.state == CuriosityState.WAITING
    assert curiosity.exploration_id == exploration.id
    assert curiosity.question.startswith(MEI_STORY_POINTER)
    assert "Conflict avoidance" not in curiosity.question + curiosity.why
    unclear = next(o for o in observations_of(client.engine, user_id) if o.unclear)
    assert curiosity.source_observation_id == unclear.id
    [attempt] = tries_of(client.engine, user_id)
    assert (attempt.need, attempt.way, attempt.observation_id, attempt.outcome) == (
        ExplorationNeed.UNCLEAR,
        ExplorationWay.STORY_FOLLOW_UP,
        unclear.id,
        None,
    )


def test_only_the_admin_set_number_of_explorations_are_active(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_exploring_on(client, auth_verifier)
    change_settings(client, auth_verifier, {"agenda_size": 0})

    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)

    [exploration] = explorations_of(client.engine, user_id)
    assert exploration.state == ExplorationState.WAITING
    assert aimed_of(client.engine, user_id) == []


def test_the_reply_plan_sees_the_agenda_and_the_aimed_curiosity_first(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    turn_exploring_on(client, auth_verifier)
    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)
    clock.advance(timedelta(days=1))

    saw = talk(client, chat_model, clock, "hey, how are you")

    assert AGENDA_HEADER in saw
    assert "[1] Conflict avoidance to preserve belonging: if disagreement" in saw
    assert "Still to learn: what drove what they told you about Mei" in saw
    assert "  - Nothing yet." in saw
    assert "such as Get curious, aim it at something still to learn" in saw
    assert f"[1] {MEI_STORY_POINTER}" in saw
    assert "Aim: something Zeph is exploring about them (the Agenda)" in saw


def test_a_move_that_asks_a_question_is_given_the_open_needs(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    turn_exploring_on(client, auth_verifier)
    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)
    clock.advance(timedelta(days=1))

    talk(
        client,
        chat_model,
        clock,
        "my sister is moving again",
        need="Think it through",
        lead_move="Get curious",
    )

    told = chat_model.calls[-1].instructions
    assert "Lead with: Get curious." in told
    assert "aim it at one of these: what drove what they told you about Mei" in (told)
    assert "Conflict avoidance" not in told


def test_an_answer_that_settles_the_unclear_story_is_tagged_clear_and_useful(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_exploring_on(client, auth_verifier)
    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)
    clock.advance(timedelta(days=1))

    talk(
        client,
        chat_model,
        clock,
        "hey",
        need="Think it through",
        bring_up=[{"curiosity": 1, "how": "weave"}],
    )
    talk(
        client,
        chat_model,
        clock,
        "honestly I was scared she'd stop talking to me",
        curiosity_taken="engaged",
    )
    end_now(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        settled=[{"unclear": 1, "pattern_type": BELONG, "sign": "I2"}],
    )

    tagging_input = chat_model.pattern_tagging_calls[-1].history[0].text
    assert "Unclear stories Zeph asked about in this Conversation:\n[1] " in (
        tagging_input
    )
    assert f"{BELONG} or {WORTH}" in tagging_input
    unclear_before = [o for o in observations_of(client.engine, user_id) if o.unclear]
    assert unclear_before == []
    [attempt] = tries_of(client.engine, user_id)
    assert attempt.outcome == TryOutcome.USEFUL
    [curiosity] = aimed_of(client.engine, user_id)
    assert curiosity.state == CuriosityState.RAISED
    assert curiosity.reaction is not None


def test_never_two_conversations_in_a_row_and_a_try_with_nothing_waits_a_new_way(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_exploring_on(client, auth_verifier)
    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)
    clock.advance(timedelta(days=1))
    talk(
        client,
        chat_model,
        clock,
        "hey",
        need="Think it through",
        bring_up=[{"curiosity": 1, "how": "weave"}],
    )
    talk(client, chat_model, clock, "eh dunno", curiosity_taken="brushed_off")
    end_now(chat_model, clock, scheduler, seeded_settings)

    [asked] = tries_of(client.engine, user_id)
    assert asked.outcome == TryOutcome.BRUSHED_OFF
    assert [c.state for c in aimed_of(client.engine, user_id)] == [
        CuriosityState.RAISED
    ]

    clock.advance(timedelta(hours=5))
    saw = talk(client, chat_model, clock, "back again")
    assert "eh dunno" not in saw.split(AGENDA_HEADER)[0]
    assert "story follow-up: Go back to" in saw
    assert "(brushed off)" in saw
    end_now(chat_model, clock, scheduler, seeded_settings)

    _, next_try = tries_of(client.engine, user_id)
    assert (next_try.need, next_try.way) == (
        ExplorationNeed.UNCLEAR,
        ExplorationWay.OTHER_PERSON,
    )
    _, next_curiosity = aimed_of(client.engine, user_id)
    assert next_curiosity.question.startswith(MEI_STORY_POINTER)
    assert "would have gone differently with someone else" in next_curiosity.question
    first_asked_at = aimed_of(client.engine, user_id)[0].raised_at
    assert first_asked_at is not None
    assert next_curiosity.not_before == (
        users_today("Asia/Singapore", first_asked_at) + timedelta(days=3)
    )


def test_it_rests_after_the_tries_with_nothing_and_wakes_on_a_new_observation(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_exploring_on(client, auth_verifier)
    change_settings(
        client,
        auth_verifier,
        {"exploration_rest_after_tries": 1},
    )
    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)
    clock.advance(timedelta(days=1))
    talk(
        client,
        chat_model,
        clock,
        "hey",
        need="Think it through",
        bring_up=[{"curiosity": 1, "how": "weave"}],
    )
    talk(client, chat_model, clock, "eh", curiosity_taken="brushed_off")
    end_now(chat_model, clock, scheduler, seeded_settings)

    [resting] = explorations_of(client.engine, user_id)
    assert resting.state == ExplorationState.RESTING
    clock.advance(timedelta(days=1))
    assert AGENDA_HEADER not in talk(client, chat_model, clock, "hi")
    end_now(chat_model, clock, scheduler, seeded_settings)
    assert explorations_of(client.engine, user_id)[0].state == (
        ExplorationState.RESTING
    )

    clock.advance(timedelta(days=1))
    talk(client, chat_model, clock, TEXT)
    end_now(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        observations=[observation_entry(thread=None)],
    )

    [awake] = explorations_of(client.engine, user_id)
    assert awake.state == ExplorationState.ACTIVE
    assert awake.woke_at is not None


def test_with_pattern_exploring_off_nothing_is_made_offered_or_deleted(
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

    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)

    assert explorations_of(client.engine, user_id) == []
    assert aimed_of(client.engine, user_id) == []

    admin = owner_headers(client, auth_verifier)
    switch_for_user(client, admin, user_id, "pattern_exploring", "on")
    clock.advance(timedelta(days=1))
    talk(client, chat_model, clock, "hi")
    end_now(chat_model, clock, scheduler, seeded_settings)
    assert len(explorations_of(client.engine, user_id)) == 1
    [waiting] = aimed_of(client.engine, user_id)

    switch_for_user(client, admin, user_id, "pattern_exploring", "off")
    clock.advance(timedelta(days=1))
    saw = talk(client, chat_model, clock, "hello again")
    end_now(chat_model, clock, scheduler, seeded_settings)

    assert AGENDA_HEADER not in saw
    assert waiting.question not in saw
    assert len(explorations_of(client.engine, user_id)) == 1
    assert [c.state for c in aimed_of(client.engine, user_id)] == [
        CuriosityState.WAITING
    ]


def test_pattern_exploring_works_only_while_pattern_noticing_works(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_exploring_on(client, auth_verifier)
    admin = owner_headers(client, auth_verifier)

    switch_for_user(client, admin, user_id, "pattern_noticing", "off")

    exploring = user_features_by_key(client, admin, user_id)["pattern_exploring"]
    assert (exploring["works"], exploring["reason"]) == (
        False,
        "pattern_noticing_off",
    )


@pytest.mark.parametrize("route", ["/api/me/data", "/api/me"])
def test_delete_my_data_and_account_deletion_remove_explorations(
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
    turn_exploring_on(client, auth_verifier)
    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)

    response = client.delete(route, headers=auth_headers(auth_verifier, "user_maya"))

    assert response.status_code == 204
    with client.engine.connect() as connection:
        for table in ("explorations", "exploration_tries", "curiosities"):
            count = connection.execute(text(f"SELECT count(*) FROM {table}"))
            assert count.scalar_one() == 0, table


def test_every_agenda_number_is_a_setting_with_a_hint_and_an_eval_override(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
) -> None:
    admin = owner_headers(client, auth_verifier)

    settings = client.get("/api/admin/settings", headers=admin).json()["settings"]
    choices = client.get("/api/admin/setting-override-choices", headers=admin).json()

    assert {key: settings[key]["value"] for key in AGENDA_SETTINGS} == {
        "agenda_size": 3,
        "exploration_wait_days": 3,
        "exploration_rest_after_tries": 4,
    }
    assert all(settings[key]["hint"] for key in AGENDA_SETTINGS)
    assert set(AGENDA_SETTINGS) <= {setting["key"] for setting in choices["settings"]}


def test_the_migration_keeps_user_data_and_reloads_the_two_prompts(
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
    user_id = turn_exploring_on(client, auth_verifier)
    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)
    observations_before = observations_of(client.engine, user_id)
    with client.engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE platform_settings SET value = '\"edited\"' "
                "WHERE key IN ('pattern_tagging_prompt', 'reply_plan_prompt')"
            )
        )

    downgrade_to(database_url, "0086")
    try:
        with client.engine.connect() as connection:
            aims = connection.execute(text("SELECT aim FROM curiosities")).scalars()
            assert "exploration" not in list(aims)
    finally:
        migrate(database_url)

    assert observations_of(client.engine, user_id) == observations_before
    with client.engine.connect() as connection:
        stored = connection.execute(
            text(
                "SELECT count(*) FROM platform_settings "
                "WHERE key IN ('pattern_tagging_prompt', 'reply_plan_prompt')"
            )
        ).scalar_one()
    assert stored == 0


def test_no_agenda_is_kept_while_curiosities_is_off(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_exploring_on(client, auth_verifier)
    switch_for_user(
        client, owner_headers(client, auth_verifier), user_id, "curiosities", "off"
    )

    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)

    assert explorations_of(client.engine, user_id) == []
    assert aimed_of(client.engine, user_id) == []
