import json
import shutil
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import load_pattern_catalog, migrate
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import (
    ExcludedEvidence,
    NarrowingTag,
    PatternNarrowing,
    PatternState,
    ReadyCheck,
    RiskType,
    SafeguardEvent,
)
from companion.core.pattern_catalog import PatternCatalogService
from companion.core.ready_gate import LastChecks, ReadyKeeper
from tests.conftest import PATTERN_CATALOG_DIR
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import auth_headers, connect_telegram, owner_headers
from tests.test_life_threads import end_conversation
from tests.test_moves_migration import downgrade_to
from tests.test_pattern_catalog import load_catalog
from tests.test_pattern_catalog_reader import VALID
from tests.test_pattern_states import (
    BELONG,
    MEI_STORY,
    WORK,
    WORK_STORY,
    moves_of,
    patterns_of,
    states_and_causes,
)
from tests.test_pattern_tagging import (
    MEI,
    TEXT,
    observation_entry,
    observations_of,
    turn_noticing_on,
)
from tests.test_recent_messages import change_settings

LATER_TEXT = (
    "Jun asked me to cover for him and I just went along with it. "
    "With Sam I say what I think, no problem"
)
JUN_STORY = observation_entry(
    quote="I just went along with it",
    about="Jun, a friend",
    thread=None,
    relationship="friend",
    setting="social",
)
NOT_WITH_SAM = observation_entry(
    sign="D1",
    direction="against",
    quote="With Sam I say what I think",
    about="Sam, their partner",
    thread=None,
    relationship="partner",
    setting="home",
)
GATE_SETTINGS = (
    "pattern_ready_situations",
    "pattern_ready_conversations",
    "pattern_ready_points",
    "pattern_ready_against_under_points",
    "pattern_safeguard_quiet_days",
    "pattern_exclusion_summary_days",
    "pattern_ruled_out_topics",
)
OTHER_SIDE_SETTINGS = (
    "pattern_other_side_prompt",
    "pattern_other_side_model",
    "pattern_other_side_thinking",
)
BETTER = json.dumps({"better_explanation": True, "why": "A look-alike fits."})


def end_tagged(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    entries: list[dict[str, Any]],
    message: str = TEXT,
    exclusions: list[dict[str, str]] | None = None,
    threads: list[dict[str, Any]] | None = None,
) -> None:
    """End a Conversation hours later, tagged as given, keeping the given Threads."""
    clock.advance(timedelta(hours=5))
    chat_model.script_pattern_tagging(
        json.dumps({"observations": entries, "exclusions": exclusions or []})
    )
    end_conversation(
        client, chat_model, clock, scheduler, seeded_settings, message, threads or []
    )


def suspect_belonging(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    **changes: Any,
) -> None:
    """End a first Conversation with two strong stories, in two Life Threads."""
    end_tagged(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [{**MEI_STORY, **changes}, {**WORK_STORY, **changes}],
        threads=[MEI, WORK],
    )


def pass_the_stored_checks(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    **changes: Any,
) -> None:
    """End a second Conversation with a third story and an answered counter-test."""
    end_tagged(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [{**JUN_STORY, **changes}, NOT_WITH_SAM],
        LATER_TEXT,
    )


def make_belonging_ready(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    """Have the two Conversations after which CONF.AVOID.BELONG passes every check."""
    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)
    pass_the_stored_checks(client, chat_model, clock, scheduler, seeded_settings)


def belonging(engine: Engine, user_id: str) -> Any:
    """The User's Pattern of CONF.AVOID.BELONG."""
    [pattern] = [
        pattern
        for pattern in patterns_of(engine, user_id)
        if pattern.pattern_type_id == BELONG
    ]
    return pattern


def test_a_pattern_becomes_ready_once_all_ten_checks_pass_and_the_log_says_what_blocked(
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

    pattern = belonging(client.engine, user_id)
    assert pattern.state == PatternState.SUSPECTED
    assert pattern.blocked_by == ReadyCheck.SITUATIONS
    assert chat_model.other_side_calls == []

    pass_the_stored_checks(client, chat_model, clock, scheduler, seeded_settings)

    pattern = belonging(client.engine, user_id)
    assert pattern.state == PatternState.READY
    assert pattern.blocked_by is None
    assert pattern.other_side_asked_at is not None
    move = moves_of(client.engine, user_id)[-1]
    assert states_and_causes([move]) == [("suspected", "ready", "conversation_tagged")]
    assert move.blocked_by == ReadyCheck.SITUATIONS
    assert (move.points, move.situations) == (pytest.approx(420, abs=5), 3)
    [call] = chat_model.other_side_calls
    described = call.history[0].text
    assert "Softening disagreement to protect belonging" in described
    assert "I just went along with it" in described
    assert "relationship: shows with family, friend, not with partner" in described
    assert chat_model.call_order.index(
        "pattern_other_side"
    ) > chat_model.call_order.index("pattern_tagging")


def test_a_counter_test_showing_it_doesnt_happen_with_a_partner_narrows_it_and_is_saved(
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

    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)

    pattern = belonging(client.engine, user_id)
    assert pattern.state == PatternState.READY
    assert pattern.narrowings == (
        PatternNarrowing(
            tag=NarrowingTag.RELATIONSHIP,
            holds_with=("family", "friend"),
            not_with=("partner",),
        ),
    )


def test_a_pattern_with_no_answered_counter_test_never_becomes_ready(
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

    end_tagged(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [JUN_STORY],
        LATER_TEXT,
    )

    pattern = belonging(client.engine, user_id)
    assert pattern.state == PatternState.SUSPECTED
    assert pattern.blocked_by == ReadyCheck.COUNTER_TEST
    assert chat_model.other_side_calls == []


def test_a_better_explanation_blocks_and_is_argued_again_only_on_new_evidence(
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
    chat_model.script_other_side(BETTER)

    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)

    pattern = belonging(client.engine, user_id)
    assert pattern.state == PatternState.SUSPECTED
    assert pattern.blocked_by == ReadyCheck.OTHER_SIDE
    assert len(chat_model.other_side_calls) == 1

    end_tagged(client, chat_model, clock, scheduler, seeded_settings, [], "hello again")

    assert belonging(client.engine, user_id).blocked_by == ReadyCheck.OTHER_SIDE
    assert len(chat_model.other_side_calls) == 1

    end_tagged(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [observation_entry(quote="it's fine honestly", about="their mother")],
    )

    assert len(chat_model.other_side_calls) == 2
    assert belonging(client.engine, user_id).state == PatternState.READY
    assert moves_of(client.engine, user_id)[-1].blocked_by == ReadyCheck.OTHER_SIDE


@pytest.mark.parametrize(
    "answers",
    [
        [RuntimeError("model down")],
        ["I think it holds.", "Still no JSON."],
    ],
)
def test_a_failed_or_unreadable_other_side_call_blocks_and_the_rest_goes_on(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    answers: list[str | Exception],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_noticing_on(client, auth_verifier)
    chat_model.script_other_side(*answers)

    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)

    pattern = belonging(client.engine, user_id)
    assert pattern.state == PatternState.SUSPECTED
    assert pattern.blocked_by == ReadyCheck.OTHER_SIDE
    assert pattern.other_side_asked_at is None
    assert chat_model.call_order[-1] != "pattern_other_side"

    end_tagged(client, chat_model, clock, scheduler, seeded_settings, [], "hello again")

    assert belonging(client.engine, user_id).state == PatternState.READY


def test_a_pattern_of_a_draft_pattern_type_never_becomes_ready(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    tmp_path: Path,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_noticing_on(client, auth_verifier)
    folder = tmp_path / "catalog"
    shutil.copytree(PATTERN_CATALOG_DIR, folder)
    belong_file = folder / "conf-avoid-belong.yaml"
    draft = yaml.safe_load(belong_file.read_text())
    draft.update(version="9.0.0", status="draft")
    draft.pop("approved_by")
    draft.pop("approved_on")
    belong_file.write_text(yaml.safe_dump(draft))
    load_pattern_catalog(client.engine, folder)

    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)

    pattern = belonging(client.engine, user_id)
    assert pattern.state == PatternState.SUSPECTED
    assert pattern.blocked_by == ReadyCheck.ALLOWED
    assert chat_model.other_side_calls == []


def test_an_exclusion_whose_evidence_is_ignored_stops_scoring_and_ready(
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
    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)
    grief = [
        {"pattern_type": BELONG, "exclusion": "grief"},
        {"pattern_type": BELONG, "exclusion": "Made up"},
        {"pattern_type": "NOT.IN.CATALOG", "exclusion": "Grief"},
    ]

    end_tagged(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [observation_entry(quote="it's fine honestly", about="their mother")],
        exclusions=grief,
    )

    repositories = build_postgres_repositories(client.engine)
    [flag] = repositories.observations.list_exclusion_flags(UUID(user_id))
    assert (flag.pattern_type_id, flag.exclusion, flag.evidence) == (
        BELONG,
        "Grief",
        ExcludedEvidence.IGNORED,
    )
    assert [
        observation.excluded for observation in observations_of(client.engine, user_id)
    ] == [False, False, False, False, True]
    pattern = belonging(client.engine, user_id)
    assert pattern.state == PatternState.SUSPECTED
    assert pattern.blocked_by == ReadyCheck.SAFE
    move = moves_of(client.engine, user_id)[-1]
    assert states_and_causes([move]) == [("ready", "suspected", "conversation_tagged")]
    assert move.blocked_by == ReadyCheck.SAFE
    assert move.points == pytest.approx(416, abs=5)

    end_tagged(client, chat_model, clock, scheduler, seeded_settings, [], "hello again")

    assert repositories.observations.list_exclusion_flags(UUID(user_id)) == []
    assert belonging(client.engine, user_id).state == PatternState.READY


def test_an_exclusion_whose_evidence_is_counted_scores_but_is_never_ready(
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
    mood_fix = "REL.MOOD.FIX"
    catalog = {
        entry.pattern_type.id: entry.pattern_type
        for entry in PatternCatalogService(
            build_postgres_repositories(client.engine).pattern_catalog
        ).catalog()
    }
    counted = next(
        exclusion
        for exclusion in catalog[mood_fix].exclusions
        if exclusion.evidence == ExcludedEvidence.COUNTED_NOT_SHARED
    )
    sign = catalog[mood_fix].signs[0].id

    end_tagged(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [observation_entry(pattern_types=[mood_fix], sign=sign)],
        exclusions=[{"pattern_type": mood_fix, "exclusion": counted.text}],
    )

    [observation] = observations_of(client.engine, user_id)
    assert not observation.excluded
    [flag] = build_postgres_repositories(
        client.engine
    ).observations.list_exclusion_flags(UUID(user_id))
    assert flag.evidence == ExcludedEvidence.COUNTED_NOT_SHARED
    assert moves_of(client.engine, user_id)[0].points > 0


def test_a_safeguard_event_within_the_admin_set_days_blocks_ready(
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
    build_postgres_repositories(client.engine).safeguard_events.add(
        SafeguardEvent(
            id=uuid4(),
            user_id=UUID(user_id),
            risk_type=RiskType.SUICIDE_OR_SELF_HARM,
            created_at=clock.now(),
            helplines_country=None,
        )
    )

    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)

    pattern = belonging(client.engine, user_id)
    assert pattern.state == PatternState.SUSPECTED
    assert pattern.blocked_by == ReadyCheck.SAFE
    assert chat_model.other_side_calls == []

    change_settings(client, auth_verifier, {"pattern_safeguard_quiet_days": 0})
    end_tagged(client, chat_model, clock, scheduler, seeded_settings, [], "hello again")

    assert belonging(client.engine, user_id).state == PatternState.READY


def test_a_ruled_out_topic_blocks_unless_the_user_raised_it_and_admins_edit_the_list(
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
        client, auth_verifier, {"pattern_ruled_out_topics": ["Money", "abuse"]}
    )
    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)

    pass_the_stored_checks(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        ruled_out_topic="money",
        raised_by_user=False,
    )

    assert "Ruled-out topics: money, abuse" in (
        chat_model.pattern_tagging_calls[-1].history[0].text
    )
    jun = observations_of(client.engine, user_id)[2]
    assert (jun.ruled_out_topic, jun.raised_by_user) == ("money", False)
    pattern = belonging(client.engine, user_id)
    assert pattern.state == PatternState.SUSPECTED
    assert pattern.blocked_by == ReadyCheck.SAFE

    change_settings(client, auth_verifier, {"pattern_ruled_out_topics": ["abuse"]})
    end_tagged(client, chat_model, clock, scheduler, seeded_settings, [], "hello again")

    assert belonging(client.engine, user_id).state == PatternState.READY


def test_a_ruled_out_topic_the_user_raised_does_not_block(
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

    pass_the_stored_checks(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        ruled_out_topic="Abuse",
        raised_by_user=True,
    )

    jun = observations_of(client.engine, user_id)[2]
    assert (jun.ruled_out_topic, jun.raised_by_user) == ("abuse", True)
    assert belonging(client.engine, user_id).state == PatternState.READY


def test_a_ready_pattern_returns_to_suspected_when_evidence_against_arrives(
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
    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)
    against_with_family = observation_entry(
        sign="D1",
        direction="against",
        quote="it's fine honestly",
        about="Wei, their brother",
        thread=None,
    )

    end_tagged(
        client, chat_model, clock, scheduler, seeded_settings, [against_with_family]
    )

    pattern = belonging(client.engine, user_id)
    assert pattern.state == PatternState.SUSPECTED
    assert pattern.blocked_by == ReadyCheck.COUNTER_TEST
    move = moves_of(client.engine, user_id)[-1]
    assert states_and_causes([move]) == [("ready", "suspected", "conversation_tagged")]
    assert move.blocked_by == ReadyCheck.COUNTER_TEST


def test_a_ready_pattern_goes_back_at_once_when_its_evidence_is_deleted(
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
    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)
    headers = auth_headers(auth_verifier, "user_maya")
    threads = client.get("/api/life-threads", headers=headers).json()["threads"]
    [work] = [thread for thread in threads if thread["title"] == WORK["title"]]

    client.delete(f"/api/life-threads/{work['id']}", headers=headers)

    pattern = belonging(client.engine, user_id)
    assert pattern.state == PatternState.SUSPECTED
    assert pattern.blocked_by == ReadyCheck.SITUATIONS
    move = moves_of(client.engine, user_id)[-1]
    assert states_and_causes([move]) == [("ready", "suspected", "observations_deleted")]
    assert move.blocked_by == ReadyCheck.SITUATIONS


def test_the_admin_set_bars_decide_when_a_pattern_is_ready(
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
    change_settings(client, auth_verifier, {"pattern_ready_points": 500})

    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)

    assert belonging(client.engine, user_id).blocked_by == ReadyCheck.SCORE

    change_settings(
        client,
        auth_verifier,
        {"pattern_ready_points": 300, "pattern_ready_conversations": 3},
    )
    end_tagged(client, chat_model, clock, scheduler, seeded_settings, [], "hello again")

    assert belonging(client.engine, user_id).blocked_by == ReadyCheck.CONVERSATIONS


def test_the_tagging_step_is_shown_exclusions_open_threads_and_day_summaries(
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
    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)

    end_tagged(client, chat_model, clock, scheduler, seeded_settings, [], "hello again")

    shown = chat_model.pattern_tagging_calls[-1].history[0].text
    assert "Exclusions: Active relationship crisis; Grief" in shown
    assert "Their open Life Threads:\n- Falling-out with Mei (open;" in shown
    assert "Their latest Day Summaries, newest first:\n- " in shown
    assert "Talked about family." in shown
    assert "Ruled-out topics: abuse, sexual trauma" in shown


def test_admins_see_how_many_patterns_a_user_has_ready_never_their_content(
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
    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)

    response = client.get(
        "/api/admin/users", headers=owner_headers(client, auth_verifier)
    )

    [maya] = [row for row in response.json()["users"] if row["role"] == "user"]
    assert maya["pattern_counts"]["ready"] == 1
    assert sum(maya["pattern_counts"].values()) == 1
    assert BELONG not in response.text
    assert "Jun" not in response.text


def test_the_gate_numbers_and_the_other_side_call_are_settings_with_hints(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    settings = client.get("/api/admin/settings", headers=admin).json()["settings"]
    choices = client.get("/api/admin/setting-override-choices", headers=admin).json()
    services = client.get("/api/admin/core-services", headers=admin).json()

    assert {key: settings[key]["value"] for key in GATE_SETTINGS} == {
        "pattern_ready_situations": 3,
        "pattern_ready_conversations": 2,
        "pattern_ready_points": 300,
        "pattern_ready_against_under_points": 100,
        "pattern_safeguard_quiet_days": 14,
        "pattern_exclusion_summary_days": 7,
        "pattern_ruled_out_topics": [
            "abuse",
            "sexual trauma",
            "self-harm or suicide",
            "eating and body image",
        ],
    }
    assert all(settings[key]["hint"] for key in (*GATE_SETTINGS, *OTHER_SIDE_SETTINGS))
    assert {*GATE_SETTINGS, *OTHER_SIDE_SETTINGS} <= {
        setting["key"] for setting in choices["settings"]
    }
    [service] = [
        service for service in services["services"] if service["name"] == "Other side"
    ]
    assert (
        service["prompt_key"],
        service["model_key"],
        service["thinking_key"],
    ) == OTHER_SIDE_SETTINGS


def test_the_other_side_call_uses_its_own_prompt_model_and_thinking(
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
    change_settings(client, auth_verifier, {"pattern_other_side_thinking": False})

    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)

    [call] = chat_model.other_side_calls
    assert call.instructions == seeded_settings["pattern_other_side_prompt"]
    assert call.model == seeded_settings["pattern_other_side_model"]
    assert call.thinking is False


def test_delete_my_data_removes_exclusion_flags(
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
    end_tagged(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [MEI_STORY],
        exclusions=[{"pattern_type": BELONG, "exclusion": "Grief"}],
        threads=[MEI],
    )
    repositories = build_postgres_repositories(client.engine)
    assert len(repositories.observations.list_exclusion_flags(UUID(user_id))) == 1

    client.delete("/api/me/data", headers=auth_headers(auth_verifier, "user_maya"))

    assert repositories.observations.list_exclusion_flags(UUID(user_id)) == []


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
    user_id = turn_noticing_on(client, auth_verifier)
    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)
    observations_before = observations_of(client.engine, user_id)
    with client.engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE platform_settings SET value = '\"edited\"' "
                "WHERE key = 'pattern_tagging_prompt'"
            )
        )

    downgrade_to(database_url, "0097")
    try:
        with client.engine.connect() as connection:
            states = connection.execute(text("SELECT state FROM patterns")).scalars()
            assert list(states) == ["suspected"]
    finally:
        migrate(database_url)

    assert observations_of(client.engine, user_id) == observations_before
    assert len(moves_of(client.engine, user_id)) == 3
    with client.engine.connect() as connection:
        stored = connection.execute(
            text(
                "SELECT count(*) FROM platform_settings "
                "WHERE key = 'pattern_tagging_prompt'"
            )
        ).scalar_one()
    assert stored == 0


def add_safeguard_event(engine: Engine, user_id: str, clock: FakeClock) -> None:
    """Record a Safeguard Event for the User, now."""
    build_postgres_repositories(engine).safeguard_events.add(
        SafeguardEvent(
            id=uuid4(),
            user_id=UUID(user_id),
            risk_type=RiskType.SUICIDE_OR_SELF_HARM,
            created_at=clock.now(),
            helplines_country=None,
        )
    )


def test_a_pattern_taken_back_for_safety_is_ready_again_without_asking_the_model(
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
    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)
    add_safeguard_event(client.engine, user_id, clock)

    end_tagged(client, chat_model, clock, scheduler, seeded_settings, [], "hello again")

    pattern = belonging(client.engine, user_id)
    assert (pattern.state, pattern.blocked_by) == (
        PatternState.SUSPECTED,
        ReadyCheck.SAFE,
    )
    assert pattern.narrowings != ()

    change_settings(client, auth_verifier, {"pattern_safeguard_quiet_days": 0})
    end_tagged(client, chat_model, clock, scheduler, seeded_settings, [], "and again")

    assert belonging(client.engine, user_id).state == PatternState.READY
    assert moves_of(client.engine, user_id)[-1].blocked_by == ReadyCheck.SAFE
    assert len(chat_model.other_side_calls) == 1


def test_a_ready_pattern_whose_pattern_type_left_the_catalog_goes_back(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    tmp_path: Path,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_noticing_on(client, auth_verifier)
    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)
    load_catalog(client.engine, tmp_path / "catalog", VALID)

    end_tagged(client, chat_model, clock, scheduler, seeded_settings, [], "hello again")

    pattern = belonging(client.engine, user_id)
    assert pattern.state != PatternState.READY
    assert pattern.blocked_by == ReadyCheck.ALLOWED
    assert moves_of(client.engine, user_id)[-1].blocked_by == ReadyCheck.ALLOWED


def test_checks_made_on_other_evidence_than_is_stored_now_never_make_it_ready(
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
    chat_model.script_other_side(RuntimeError("model down"))
    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)
    repositories = build_postgres_repositories(client.engine)
    keeper = ReadyKeeper(
        repositories, PatternCatalogService(repositories.pattern_catalog), clock
    )
    user = repositories.users.get(UUID(user_id))
    assert user is not None
    settings = repositories.platform_settings.load()
    pattern = belonging(client.engine, user_id)
    observations = observations_of(client.engine, user_id)
    seen_before_one_was_tagged = frozenset(
        observation.id for observation in observations[:-1]
    )

    keeper.settle(
        user,
        settings,
        observations[0].conversation_id,
        LastChecks(pattern.id, seen_before_one_was_tagged, 0, False, True),
    )

    after = belonging(client.engine, user_id)
    assert after.state == PatternState.SUSPECTED
    assert after.blocked_by == ReadyCheck.QUOTES
    assert after.other_side_asked_at is None

    keeper.settle(
        user,
        settings,
        observations[0].conversation_id,
        LastChecks(
            pattern.id,
            frozenset(observation.id for observation in observations),
            0,
            False,
            True,
        ),
    )

    assert belonging(client.engine, user_id).state == PatternState.READY
