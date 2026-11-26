from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

import yaml
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate, seed_thought_experiments
from companion.core.models import (
    CuriosityState,
    EvidenceKind,
    ExplorationApproach,
    TryOutcome,
)
from companion.core.thought_experiments import leading_flags
from tests.conftest import THOUGHT_EXPERIMENTS_SEED_FILE
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import auth_headers, connect_telegram, owner_headers
from tests.test_curiosity_check_in import (
    WONDERING_OFFERED,
    wondering_answer,
)
from tests.test_explorations import (
    BELONG,
    WORTH,
    aimed_of,
    end_now,
    suspect_belonging,
    talk,
    tries_of,
    turn_exploring_on,
)
from tests.test_moves_migration import downgrade_to
from tests.test_onboarding import onboarding_answers
from tests.test_pattern_tagging import observation_entry, observations_of
from tests.test_recent_messages import change_settings

ROUTE = "/api/admin/thought-experiments"
FIRST_SEEDED = "belong-worth-team-plan"
TEAM_PLAN = "Your team lead, who you get on well with, shares a plan in a meeting"
ANSWER = "I'd keep quiet, I'd worry they'd think I was being difficult"
AREAS = ("CONF", "APPR", "CTRL", "ACH", "REL")


def seeded() -> list[dict[str, Any]]:
    """Read the seed file's Thought Experiments."""
    entries: list[dict[str, Any]] = yaml.safe_load(
        THOUGHT_EXPERIMENTS_SEED_FILE.read_text()
    )
    return entries


def listed(client: TestClient, admin: dict[str, str]) -> dict[str, Any]:
    """Fetch every Thought Experiment and the Pattern Types to pick from."""
    response = client.get(ROUTE, headers=admin)
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


def first_seeded(client: TestClient, admin: dict[str, str]) -> dict[str, Any]:
    """Find the first seeded Thought Experiment."""
    first: dict[str, Any] = listed(client, admin)["thought_experiments"][0]
    assert first["wording"].startswith(TEAM_PLAN)
    return first


def body_of(thought_experiment: dict[str, Any], **changes: Any) -> dict[str, Any]:
    """Build a save request from a Thought Experiment, with some fields changed."""
    return {
        key: thought_experiment[key]
        for key in (
            "wording",
            "pattern_type_id",
            "other_pattern_type_id",
            "sensitivity",
            "starter",
            "on",
        )
    } | changes


NEW_ONE = {
    "wording": "A friend asks you to read their speech two days before the "
    "wedding, and it isn't good. What do you tell them?",
    "pattern_type_id": BELONG,
    "other_pattern_type_id": WORTH,
    "sensitivity": "low",
    "starter": False,
    "on": True,
}


def test_the_first_set_comes_from_the_seed_with_every_detail(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    body = listed(client, admin)

    entries = seeded()
    assert [
        (
            listed_one["wording"],
            [listed_one["pattern_type_id"], listed_one["other_pattern_type_id"]],
            listed_one["sensitivity"],
            listed_one["starter"],
            listed_one["on"],
            listed_one["archived_at"],
            listed_one["asked_count"],
        )
        for listed_one in body["thought_experiments"]
    ] == [
        (
            entry["wording"],
            entry["pattern_types"],
            entry["sensitivity"],
            entry.get("starter", False),
            True,
            None,
            0,
        )
        for entry in entries
    ]
    assert {choice["id"] for choice in body["pattern_types"]} >= {BELONG, WORTH}
    assert all(choice["name"] for choice in body["pattern_types"])


def test_the_first_set_has_a_starter_per_area_and_no_leading_wording() -> None:
    entries = seeded()

    assert len(entries) >= 30
    assert len({entry["key"] for entry in entries}) == len(entries)
    assert all(
        len(set(entry["pattern_types"])) == 2 and entry["wording"].endswith("?")
        for entry in entries
    )
    starters = [entry["pattern_types"][0] for entry in entries if entry.get("starter")]
    assert sorted(starter.split(".")[0] for starter in starters) == sorted(AREAS)
    assert [entry["key"] for entry in entries if leading_flags(entry["wording"])] == []


def test_a_seed_never_overwrites_an_edit_or_brings_back_an_archived_one(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    engine: Engine,
    tmp_path: Path,
) -> None:
    admin = owner_headers(client, auth_verifier)
    first, second = listed(client, admin)["thought_experiments"][:2]
    client.put(
        f"{ROUTE}/{first['id']}",
        json=body_of(first, wording="Edited: what do you do?"),
        headers=admin,
    ).raise_for_status()
    client.post(f"{ROUTE}/{second['id']}/archive", headers=admin).raise_for_status()
    with_a_new_one = tmp_path / "thought_experiments.yaml"
    with_a_new_one.write_text(
        yaml.safe_dump(
            [
                *seeded(),
                {
                    "key": "brand-new",
                    "pattern_types": [BELONG, WORTH],
                    "sensitivity": "high",
                    "wording": "A new one. What do you do?",
                },
            ]
        )
    )

    seed_thought_experiments(engine, THOUGHT_EXPERIMENTS_SEED_FILE)
    seed_thought_experiments(engine, with_a_new_one)

    after = listed(client, admin)["thought_experiments"]
    assert len(after) == len(seeded()) + 1
    assert after[0]["wording"] == "Edited: what do you do?"
    assert after[1]["archived_at"] is not None
    assert (after[-1]["wording"], after[-1]["sensitivity"]) == (
        "A new one. What do you do?",
        "high",
    )


def test_admins_add_edit_switch_off_and_archive_but_never_delete(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    added = client.post(ROUTE, json=NEW_ONE, headers=admin)
    assert added.status_code == 201, added.text
    one = added.json()
    edited = client.put(
        f"{ROUTE}/{one['id']}",
        json=body_of(one, sensitivity="medium", starter=True, on=False),
        headers=admin,
    ).json()
    archived = client.post(f"{ROUTE}/{one['id']}/archive", headers=admin).json()

    assert (edited["sensitivity"], edited["starter"], edited["on"]) == (
        "medium",
        True,
        False,
    )
    assert archived["archived_at"] is not None
    assert archived in listed(client, admin)["thought_experiments"]
    after_archive = client.put(f"{ROUTE}/{one['id']}", json=NEW_ONE, headers=admin)
    assert after_archive.status_code == 409
    assert client.delete(f"{ROUTE}/{one['id']}", headers=admin).status_code == 405


def test_leading_wording_is_refused_until_saved_anyway(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    leading = NEW_ONE | {"wording": "Surely you'd tell them, wouldn't you?"}

    refused = client.post(ROUTE, json=leading, headers=admin)
    saved = client.post(ROUTE, json=leading | {"save_anyway": True}, headers=admin)

    assert refused.status_code == 422
    flags = refused.json()["fields"]["leading"].split("\n")
    assert [flag.split("”")[0] for flag in flags] == ["“Surely", "“wouldn't you"]
    assert "lead them to an answer" in refused.json()["detail"]
    assert saved.status_code == 201
    assert saved.json()["wording"] == leading["wording"]


def test_a_thought_experiment_needs_wording_and_two_pattern_types_from_the_catalog(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    blank = client.post(ROUTE, json=NEW_ONE | {"wording": "  "}, headers=admin)
    same = client.post(
        ROUTE, json=NEW_ONE | {"other_pattern_type_id": BELONG}, headers=admin
    )
    unknown = client.post(
        ROUTE, json=NEW_ONE | {"other_pattern_type_id": "NOT.A.TYPE"}, headers=admin
    )

    assert [blank.status_code, same.status_code, unknown.status_code] == [422] * 3
    assert "two different Pattern Types" in same.json()["detail"]
    assert "NOT.A.TYPE isn't a Pattern Type" in unknown.json()["detail"]


def test_only_admins_can_manage_thought_experiments(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    owner_headers(client, auth_verifier)
    maya = auth_headers(auth_verifier, "user_maya")

    assert client.get(ROUTE, headers=maya).status_code == 403
    assert client.post(ROUTE, json=NEW_ONE, headers=maya).status_code == 403


def try_twice_with_nothing(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> str:
    """Make CONF.AVOID.BELONG suspected with Mei unclear; two tries get nothing.

    With no wait after a try with nothing and one reply needed between two
    Curiosities, the story follow-up and the "with
    someone else" tries are each asked and come back vague (taken up, with
    nothing new), so the third try, written at the last Conversation's end,
    is the Thought Experiment way.

    Returns:
        The User's ID.
    """
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_exploring_on(client, auth_verifier)
    change_settings(
        client,
        auth_verifier,
        {"exploration_wait_days": 0, "curiosity_replies_between": 1},
    )
    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)
    for _ in range(2):
        clock.advance(timedelta(days=1))
        talk(
            client,
            chat_model,
            clock,
            "hey",
            need="Think it through",
            bring_up=[{"curiosity": 1, "how": "weave"}],
        )
        talk(client, chat_model, clock, "eh not sure", curiosity_taken="engaged")
        end_now(chat_model, clock, scheduler, seeded_settings)
        clock.advance(timedelta(hours=5))
        talk(client, chat_model, clock, "back again")
        end_now(chat_model, clock, scheduler, seeded_settings)
    return user_id


def test_the_thought_experiment_for_the_unclear_pair_is_asked_and_tagged_what_if(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = try_twice_with_nothing(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    admin = owner_headers(client, auth_verifier)
    team_plan = first_seeded(client, admin)

    *_, third = tries_of(client.engine, user_id)
    assert (third.approach, str(third.thought_experiment_id)) == (
        ExplorationApproach.THOUGHT_EXPERIMENT,
        team_plan["id"],
    )
    *_, curiosity = aimed_of(client.engine, user_id)
    assert curiosity.state == CuriosityState.WAITING
    assert curiosity.sensitivity.value == team_plan["sensitivity"]

    clock.advance(timedelta(days=1))
    saw = talk(
        client,
        chat_model,
        clock,
        "hey there",
        need="Think it through",
        bring_up=[{"curiosity": 1, "how": "weave"}],
    )
    assert (
        f'[1] Put this made-up situation to them, keeping its words: "{TEAM_PLAN}'
    ) in saw
    talk(client, chat_model, clock, ANSWER, curiosity_taken="engaged")
    end_now(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [
            observation_entry(
                quote=ANSWER,
                about="their team lead",
                relationship="colleague",
                power="above",
                setting="work",
                evidence="real_story",
                thought_experiment=1,
            )
        ],
    )

    tagging_input = chat_model.pattern_tagging_calls[-1].history[0].text
    assert (
        "Thought Experiments Zeph put to them in this Conversation:\n[1] Put this "
        f'made-up situation to them, keeping its words: "{TEAM_PLAN}'
    ) in tagging_input
    answered = next(
        o for o in observations_of(client.engine, user_id) if o.quote == ANSWER
    )
    assert answered.evidence_kind == EvidenceKind.WHAT_IF_ANSWER
    *_, judged = tries_of(client.engine, user_id)
    assert judged.outcome == TryOutcome.USEFUL
    assert first_seeded(client, admin)["asked_count"] == 1


def test_switching_one_off_or_archiving_it_closes_its_waiting_curiosity_at_once(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = try_twice_with_nothing(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    admin = owner_headers(client, auth_verifier)
    team_plan = first_seeded(client, admin)

    client.post(f"{ROUTE}/{team_plan['id']}/archive", headers=admin).raise_for_status()

    *_, closed = aimed_of(client.engine, user_id)
    assert closed.state == CuriosityState.CLOSED
    saw = talk(client, chat_model, clock, "hey there")
    assert TEAM_PLAN not in saw
    end_now(chat_model, clock, scheduler, seeded_settings)
    *_, next_try = tries_of(client.engine, user_id)
    assert next_try.thought_experiment_id != UUID(team_plan["id"])
    assert listed(client, admin)["thought_experiments"][0]["archived_at"] is not None


def test_the_weekly_number_is_a_setting_with_a_hint_and_an_eval_override(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    key = "thought_experiments_per_pattern_per_week"

    settings = client.get("/api/admin/settings", headers=admin).json()["settings"]
    choices = client.get("/api/admin/setting-override-choices", headers=admin).json()

    assert settings[key]["value"] == 1
    assert settings[key]["hint"]
    assert key in {setting["key"] for setting in choices["settings"]}


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
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_exploring_on(client, auth_verifier)
    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)
    observations_before = observations_of(client.engine, user_id)
    tries_before = tries_of(client.engine, user_id)
    with client.engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE platform_settings SET value = '\"edited\"' "
                "WHERE key = 'pattern_tagging_prompt'"
            )
        )

    downgrade_to(database_url, "0093")
    try:
        with client.engine.connect() as connection:
            tables = connection.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            ).scalars()
            assert "thought_experiments" not in list(tables)
    finally:
        migrate(database_url)

    assert observations_of(client.engine, user_id) == observations_before
    assert tries_of(client.engine, user_id) == tries_before
    with client.engine.connect() as connection:
        stored = connection.execute(
            text(
                "SELECT count(*) FROM platform_settings "
                "WHERE key = 'pattern_tagging_prompt'"
            )
        ).scalar_one()
    assert stored == 0


def test_a_waiting_thought_experiment_can_be_sent_by_the_wondering_check_in(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = try_twice_with_nothing(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    answers = onboarding_answers(check_ins_enabled=True, check_in_frequency="most_days")
    maya = auth_headers(auth_verifier, "user_maya")
    client.put("/api/onboarding", json=answers, headers=maya).raise_for_status()
    clock.advance(timedelta(days=1, hours=13))
    chat_channel.sent.clear()
    chat_model.script(wondering_answer("random thought experiment for you...", 1))

    scheduler.tick()

    [saw] = [
        call.history[0].text
        for call in chat_model.calls
        if WONDERING_OFFERED in call.history[0].text
    ]
    assert (
        '1. Put this made-up situation to them, keeping its words: "' + TEAM_PLAN
    ) in saw
    assert [sent.text for sent in chat_channel.sent] == [
        "random thought experiment for you..."
    ]
    *_, asked = aimed_of(client.engine, user_id)
    assert asked.state == CuriosityState.RAISED
