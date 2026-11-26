from datetime import timedelta
from typing import Any
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import (
    Curiosity,
    CuriosityAim,
    CuriosityState,
    EvidenceKind,
    PatternState,
)
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import auth_headers, connect_telegram, owner_headers
from tests.test_explorations import (
    BELONG,
    aimed_of,
    end_now,
    suspect_belonging,
    talk,
    turn_exploring_on,
)
from tests.test_moves_migration import downgrade_to
from tests.test_pattern_states import patterns_of
from tests.test_pattern_tagging import (
    observation_entry,
    observations_of,
    turn_noticing_on,
)
from tests.test_post_conversation import quiet_gap
from tests.test_recent_messages import change_settings
from tests.test_thought_experiments import ROUTE, TEAM_PLAN, listed

FAMILIARITY_SETTINGS = (
    "familiarity_conversations",
    "familiarity_life_threads",
    "familiarity_real_stories",
    "starter_thought_experiments",
    "starter_thought_experiment_days",
    "starter_thought_experiments_per_conversation",
)
NEW_LINE = "How well you know them (Familiarity): new\n"
GETTING_TO_KNOW_LINE = "How well you know them (Familiarity): getting to know\n"
PUT_A_STARTER = "Put this made-up situation to them, keeping its words:"
NO_ONE_MINDS = "A colleague asks if you could take on a small extra task this week."
TEAM_PLAN_ANSWER = "I'd keep quiet, I'd worry they'd think I was being difficult"
EXTRA_TASK_ANSWER = "I'd still say yes, I couldn't bear to let them down"


def starters_of(engine: Engine, user_id: str) -> list[Curiosity]:
    """List a User's starter Thought Experiment Curiosities, oldest first."""
    return build_postgres_repositories(engine).curiosities.list_starters(UUID(user_id))


def familiarity_of_maya(client: TestClient, auth_verifier: FakeAuthVerifier) -> str:
    """Read Maya's Familiarity as Admins see it on the Users page."""
    response = client.get(
        "/api/admin/users", headers=owner_headers(client, auth_verifier)
    )
    [maya] = [row for row in response.json()["users"] if row["role"] == "user"]
    familiarity: str = maya["familiarity"]
    return familiarity


def start_exploring_as_a_new_user(
    client: TestClient, auth_verifier: FakeAuthVerifier, chat_channel: FakeChatChannel
) -> str:
    """Connect Maya with Pattern exploring on and one reply between Curiosities."""
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_exploring_on(client, auth_verifier)
    change_settings(client, auth_verifier, {"curiosity_replies_between": 1})
    return user_id


def answer_the_starter(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    answer: str,
    about: str,
) -> list[str]:
    """Have the next day's Conversation ask the waiting starter and tag its answer.

    Returns:
        What the Reply Plan was given on each of the two replies.
    """
    clock.advance(timedelta(days=1))
    asked = talk(
        client,
        chat_model,
        clock,
        "hey",
        need="Think it through",
        bring_up=[{"curiosity": 1, "how": "weave"}],
    )
    answered = talk(client, chat_model, clock, answer, curiosity_taken="engaged")
    end_now(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [
            observation_entry(
                quote=answer,
                about=about,
                thread=None,
                relationship="colleague",
                power="above",
                setting="work",
                thought_experiment=1,
            )
        ],
    )
    return [asked, answered]


def test_a_new_user_is_put_one_starter_a_conversation_and_answers_are_weak_evidence(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = start_exploring_as_a_new_user(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    team_plan, *_ = listed(client, admin)["thought_experiments"]

    first_reply = talk(client, chat_model, clock, "hi there")
    end_now(chat_model, clock, scheduler, seeded_settings)

    assert NEW_LINE in first_reply
    assert PUT_A_STARTER not in first_reply
    [waiting] = starters_of(client.engine, user_id)
    assert (waiting.aim, waiting.state) == (
        CuriosityAim.STARTER,
        CuriosityState.WAITING,
    )
    assert str(waiting.thought_experiment_id) == team_plan["id"]
    assert waiting.sensitivity.value == team_plan["sensitivity"]

    asked, answered = answer_the_starter(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        TEAM_PLAN_ANSWER,
        "their team lead",
    )

    assert f'[1] {PUT_A_STARTER} "{TEAM_PLAN}' in asked
    assert "a starter Thought Experiment" in asked
    assert f"[1] {PUT_A_STARTER}" not in answered
    tagging_input = chat_model.pattern_tagging_calls[-1].history[0].text
    assert (
        "Thought Experiments Zeph put to them in this Conversation:\n"
        f'[1] {PUT_A_STARTER} "{TEAM_PLAN}'
    ) in tagging_input
    first, second = starters_of(client.engine, user_id)
    assert (first.state, second.state) == (
        CuriosityState.RAISED,
        CuriosityState.WAITING,
    )
    assert NO_ONE_MINDS in second.question
    assert listed(client, admin)["thought_experiments"][0]["asked_count"] == 1

    answer_the_starter(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        EXTRA_TASK_ANSWER,
        "a colleague",
    )

    answers = observations_of(client.engine, user_id)
    assert [answer.evidence_kind for answer in answers] == [
        EvidenceKind.WHAT_IF_ANSWER,
        EvidenceKind.WHAT_IF_ANSWER,
    ]
    [pattern] = patterns_of(client.engine, user_id)
    assert (pattern.pattern_type_id, pattern.state) == (BELONG, PatternState.NOTICED)
    assert familiarity_of_maya(client, auth_verifier) == "new"
    assert aimed_of(client.engine, user_id) == []


def test_starters_stop_and_the_agenda_takes_over_once_zeph_is_getting_to_know_them(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = start_exploring_as_a_new_user(client, auth_verifier, chat_channel)
    talk(client, chat_model, clock, "hi there")
    end_now(chat_model, clock, scheduler, seeded_settings)
    assert familiarity_of_maya(client, auth_verifier) == "new"
    clock.advance(timedelta(hours=5))

    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)

    assert familiarity_of_maya(client, auth_verifier) == "getting_to_know"
    [starter] = starters_of(client.engine, user_id)
    assert starter.state == CuriosityState.CLOSED
    [aimed] = aimed_of(client.engine, user_id)
    assert aimed.state == CuriosityState.WAITING
    clock.advance(timedelta(days=1))
    saw = talk(client, chat_model, clock, "hey")
    assert GETTING_TO_KNOW_LINE in saw
    assert PUT_A_STARTER not in saw
    end_now(chat_model, clock, scheduler, seeded_settings)
    assert len(starters_of(client.engine, user_id)) == 1


def test_the_admin_set_bars_decide_when_a_user_is_no_longer_new(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = start_exploring_as_a_new_user(client, auth_verifier, chat_channel)
    change_settings(
        client,
        auth_verifier,
        {"familiarity_conversations": 2, "familiarity_life_threads": 0},
    )

    talk(client, chat_model, clock, "hi there")
    end_now(chat_model, clock, scheduler, seeded_settings)
    after_one = familiarity_of_maya(client, auth_verifier)
    clock.advance(timedelta(hours=5))
    talk(client, chat_model, clock, "back again")
    end_now(chat_model, clock, scheduler, seeded_settings)

    assert after_one == "new"
    assert familiarity_of_maya(client, auth_verifier) == "getting_to_know"
    [starter] = starters_of(client.engine, user_id)
    assert starter.state == CuriosityState.CLOSED


def test_starters_stay_within_the_admin_set_number_and_days(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = start_exploring_as_a_new_user(client, auth_verifier, chat_channel)
    change_settings(
        client,
        auth_verifier,
        {
            "starter_thought_experiments": 2,
            "starter_thought_experiment_days": 3,
            "starter_thought_experiments_per_conversation": 2,
        },
    )

    talk(client, chat_model, clock, "hi there")
    end_now(chat_model, clock, scheduler, seeded_settings)
    after_one = starters_of(client.engine, user_id)
    clock.advance(timedelta(hours=5))
    talk(client, chat_model, clock, "back again")
    end_now(chat_model, clock, scheduler, seeded_settings)
    after_two = starters_of(client.engine, user_id)
    clock.advance(timedelta(days=3))
    too_late = talk(client, chat_model, clock, "hello after a while")
    end_now(chat_model, clock, scheduler, seeded_settings)

    assert [starter.state for starter in after_one] == [CuriosityState.WAITING] * 2
    assert after_two == after_one
    assert PUT_A_STARTER not in too_late
    assert [starter.state for starter in starters_of(client.engine, user_id)] == [
        CuriosityState.CLOSED
    ] * 2


def test_no_starter_is_written_without_pattern_exploring(
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

    saw = talk(client, chat_model, clock, "hi there")
    end_now(chat_model, clock, scheduler, seeded_settings)

    assert NEW_LINE in saw
    assert starters_of(client.engine, user_id) == []
    assert familiarity_of_maya(client, auth_verifier) == "new"


def test_familiarity_is_worked_out_even_while_user_memory_is_off(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    change_settings(
        client,
        auth_verifier,
        {"familiarity_conversations": 1, "familiarity_life_threads": 0},
    )
    maya = auth_headers(auth_verifier, "user_maya")
    client.patch(
        "/api/me", json={"user_memory_enabled": False}, headers=maya
    ).raise_for_status()

    talk(client, chat_model, clock, "hi there")
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    scheduler.tick()

    assert familiarity_of_maya(client, auth_verifier) == "getting_to_know"


def test_switching_a_starter_off_closes_its_waiting_curiosity_at_once(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = start_exploring_as_a_new_user(client, auth_verifier, chat_channel)
    talk(client, chat_model, clock, "hi there")
    end_now(chat_model, clock, scheduler, seeded_settings)
    admin = owner_headers(client, auth_verifier)
    team_plan, *_ = listed(client, admin)["thought_experiments"]

    client.post(f"{ROUTE}/{team_plan['id']}/archive", headers=admin).raise_for_status()

    [closed] = starters_of(client.engine, user_id)
    assert closed.state == CuriosityState.CLOSED
    clock.advance(timedelta(hours=5))
    talk(client, chat_model, clock, "back again")
    end_now(chat_model, clock, scheduler, seeded_settings)
    *_, next_one = starters_of(client.engine, user_id)
    assert next_one.state == CuriosityState.WAITING
    assert NO_ONE_MINDS in next_one.question


def test_delete_my_data_makes_zeph_new_to_them_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = start_exploring_as_a_new_user(client, auth_verifier, chat_channel)
    talk(client, chat_model, clock, "hi there")
    end_now(chat_model, clock, scheduler, seeded_settings)
    clock.advance(timedelta(hours=5))
    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)
    assert familiarity_of_maya(client, auth_verifier) == "getting_to_know"

    response = client.delete(
        "/api/me/data", headers=auth_headers(auth_verifier, "user_maya")
    )

    assert response.status_code == 204
    assert familiarity_of_maya(client, auth_verifier) == "new"
    assert starters_of(client.engine, user_id) == []


def test_every_bar_and_limit_is_a_setting_with_a_hint_and_an_eval_override(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    settings = client.get("/api/admin/settings", headers=admin).json()["settings"]
    choices = client.get("/api/admin/setting-override-choices", headers=admin).json()

    assert {key: settings[key]["value"] for key in FAMILIARITY_SETTINGS} == {
        "familiarity_conversations": 5,
        "familiarity_life_threads": 3,
        "familiarity_real_stories": 0,
        "starter_thought_experiments": 4,
        "starter_thought_experiment_days": 14,
        "starter_thought_experiments_per_conversation": 1,
    }
    assert all(settings[key]["hint"] for key in FAMILIARITY_SETTINGS)
    assert set(FAMILIARITY_SETTINGS) <= {
        setting["key"] for setting in choices["settings"]
    }


def test_the_migration_keeps_user_data_and_reloads_the_reply_plan_prompt(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    database_url: str,
) -> None:
    user_id = start_exploring_as_a_new_user(client, auth_verifier, chat_channel)
    talk(client, chat_model, clock, "hi there")
    end_now(chat_model, clock, scheduler, seeded_settings)
    clock.advance(timedelta(hours=5))
    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)
    observations_before = observations_of(client.engine, user_id)
    aimed_before = aimed_of(client.engine, user_id)
    with client.engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE platform_settings SET value = '\"edited\"' "
                "WHERE key = 'reply_plan_prompt'"
            )
        )

    downgrade_to(database_url, "0094")
    try:
        with client.engine.connect() as connection:
            columns = connection.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'users'"
                )
            ).scalars()
            assert "familiarity" not in list(columns)
    finally:
        migrate(database_url)

    assert observations_of(client.engine, user_id) == observations_before
    assert aimed_of(client.engine, user_id) == aimed_before
    assert familiarity_of_maya(client, auth_verifier) == "new"
    with client.engine.connect() as connection:
        stored = connection.execute(
            text(
                "SELECT count(*) FROM platform_settings WHERE key = 'reply_plan_prompt'"
            )
        ).scalar_one()
    assert stored == 0
