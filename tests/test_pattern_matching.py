import json
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import (
    Pattern,
    PatternEvidence,
    PatternMoveCause,
    PatternState,
)
from companion.core.pattern_matching import (
    DayToTagAgain,
    PatternMatch,
    PatternMatcher,
    UnknownPatternTypeError,
    UserMatchingReport,
    plan_days_to_tag_again,
    read_fitting_pattern_type,
    read_matching_answer,
)
from companion.pattern_matching_terminal import (
    build_pattern_matcher,
    match_and_report,
    read_pattern_type_ids,
    report_lines,
)
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakePhotoViewer,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import connect_telegram, owner_headers
from tests.test_features import maya_id
from tests.test_message_retention import retention
from tests.test_model_call_log import list_traces
from tests.test_pattern_states import moves_of
from tests.test_pattern_states import patterns_of as catalog_patterns_of
from tests.test_pattern_tagging import (
    observation_entry,
    observations_of,
    tagging_answer,
    turn_noticing_on,
)
from tests.test_patterns import (
    GOES_QUIET,
    patterns_of,
    set_pattern_state,
    start_goes_quiet_pattern,
)
from tests.test_patterns_dashboard import keep_pattern, threads_by_title

ABSORBED = "ACH.ABSORB.PULL"
BELONG = "CONF.AVOID.BELONG"
FORGOT_TO_EAT = observation_entry(
    pattern_types=[ABSORBED],
    sign="I2",
    quote="I forgot to eat",
    context="Skipped meals while building the app.",
    about="themselves",
    relationship=None,
    power=None,
    stance=None,
)


def matching_answer(pattern_type_id: str | None) -> str:
    """Build the JSON the matching model answers with."""
    return json.dumps({"pattern_type": pattern_type_id})


def matcher_of(
    client: TestClient, chat_model: ScriptedChatModel, clock: FakeClock
) -> PatternMatcher:
    """Build the Pattern matcher on the test database and fakes, as the Admin
    command builds it."""
    return build_pattern_matcher(
        build_postgres_repositories(client.engine),
        chat_model,
        FakePhotoViewer(),
        clock,
    )


def have_unmatched_pattern(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> str:
    """Connect Maya with Pattern noticing on and told, and keep the unmatched
    Pattern linking the side project and mum's visit; return her User ID."""
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_noticing_on(client, auth_verifier)
    start_goes_quiet_pattern(client, chat_model, clock, scheduler, seeded_settings)
    return user_id


def test_a_pattern_is_linked_to_the_pattern_type_it_fits_and_stays_as_it_was(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = have_unmatched_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    [before] = patterns_of(client.engine, user_id)
    chat_model.script_pattern_matching(matching_answer(ABSORBED))

    [report] = matcher_of(client, chat_model, clock).match()

    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.matched_pattern_type_id == ABSORBED
    assert (pattern.pattern, pattern.state, pattern.evidence) == (
        before.pattern,
        PatternState.UNMATCHED,
        before.evidence,
    )
    assert report.matches == (
        PatternMatch(pattern.id, PatternState.UNMATCHED, ABSORBED),
    )
    seen = chat_model.pattern_matching_calls[-1].history[0].text
    assert f"{ABSORBED}: Everything else goes quiet when something grabs them" in seen
    assert f"The Pattern:\n(unmatched) {GOES_QUIET} Evidence:" in seen
    assert "Snapped at mum because the app had them." in seen


@pytest.mark.parametrize(
    "answer",
    [
        matching_answer(None),
        matching_answer("ACH.MADE.UP"),
        "It could be several of them.",
    ],
)
def test_a_pattern_that_fits_no_pattern_type_in_the_catalog_stays_not_matched(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    answer: str,
) -> None:
    user_id = have_unmatched_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    chat_model.script_pattern_matching(answer, answer)
    tagging_calls = len(chat_model.pattern_tagging_calls)

    [report] = matcher_of(client, chat_model, clock).match()

    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.matched_pattern_type_id is None
    assert report.matches == (PatternMatch(pattern.id, PatternState.UNMATCHED, None),)
    assert (report.conversations_tagged, report.observations_kept) == (0, 0)
    assert len(chat_model.pattern_tagging_calls) == tagging_calls


def test_matched_evidence_is_tagged_again_into_observations_checked_like_any_other(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = have_unmatched_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    told_on = clock.now().date()
    clock.advance(timedelta(days=5))
    chat_model.script_pattern_matching(matching_answer(ABSORBED))
    chat_model.script_pattern_tagging(
        tagging_answer(
            FORGOT_TO_EAT,
            {**FORGOT_TO_EAT, "quote": "I never eat when the app has me"},
            {**FORGOT_TO_EAT, "pattern_types": [BELONG], "quote": "snapped at mum"},
        )
    )

    [report] = matcher_of(client, chat_model, clock).match()

    [observation] = observations_of(client.engine, user_id)
    assert (observation.pattern_type_id, observation.quote) == (
        ABSORBED,
        "I forgot to eat",
    )
    assert observation.day == told_on
    assert (report.conversations_tagged, report.observations_kept) == (1, 1)
    seen = chat_model.pattern_tagging_calls[-1].history[0].text
    assert f"The Pattern Catalog:\n{ABSORBED}: " in seen
    assert BELONG not in seen
    threads = threads_by_title(client.engine, user_id)
    first_thread = next(title for title in threads if f"[1] {title}" in seen)
    assert observation.thread_id == threads[first_thread]
    assert all(f"] {title}" in seen for title in threads)
    [noticed] = catalog_patterns_of(client.engine, user_id)
    assert (noticed.pattern_type_id, noticed.state) == (ABSORBED, PatternState.NOTICED)
    [move] = moves_of(client.engine, user_id)
    assert move.cause == PatternMoveCause.EVIDENCE_TAGGED_AGAIN
    [unmatched] = patterns_of(client.engine, user_id)
    assert unmatched.state == PatternState.UNMATCHED
    admin = owner_headers(client, auth_verifier)
    assert len(list_traces(client, admin, step="pattern_matching")) == 1


def test_users_not_told_about_pattern_noticing_are_left_for_a_later_run(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    start_goes_quiet_pattern(client, chat_model, clock, scheduler, seeded_settings)

    [report] = matcher_of(client, chat_model, clock).match()

    assert report.user_id == UUID(user_id)
    assert report.skipped_why is not None
    assert chat_model.pattern_matching_calls == []
    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.matched_pattern_type_id is None


def test_only_the_pattern_types_asked_for_are_matched_against(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = have_unmatched_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    chat_model.script_pattern_matching(matching_answer(ABSORBED))

    [first] = matcher_of(client, chat_model, clock).match([BELONG])
    seen = chat_model.pattern_matching_calls[-1].history[0].text
    [pattern] = patterns_of(client.engine, user_id)
    with pytest.raises(UnknownPatternTypeError):
        matcher_of(client, chat_model, clock).match(["ACH.MADE.UP"])

    assert f"{BELONG}: " in seen
    assert ABSORBED not in seen
    assert first.matches == (PatternMatch(pattern.id, PatternState.UNMATCHED, None),)
    assert pattern.matched_pattern_type_id is None


def test_a_matched_pattern_is_not_asked_about_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    have_unmatched_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    chat_model.script_pattern_matching(matching_answer(ABSORBED))
    matcher_of(client, chat_model, clock).match()

    assert matcher_of(client, chat_model, clock).match() == []
    assert len(chat_model.pattern_matching_calls) == 1


def test_a_conversation_tagged_again_twice_keeps_each_quote_once(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = have_unmatched_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    chat_model.script_pattern_matching(matching_answer(ABSORBED))
    chat_model.script_pattern_tagging(tagging_answer(FORGOT_TO_EAT))
    matcher_of(client, chat_model, clock).match()
    [first] = patterns_of(client.engine, user_id)
    keep_pattern(
        client.engine,
        user_id,
        "Loses whole days to whatever is new.",
        PatternState.UNMATCHED,
        [(item.day, item.thread_id, "Again.") for item in first.evidence],
    )
    chat_model.script_pattern_matching(matching_answer(ABSORBED))
    chat_model.script_pattern_tagging(tagging_answer(FORGOT_TO_EAT))

    [report] = matcher_of(client, chat_model, clock).match()

    assert (report.conversations_tagged, report.observations_kept) == (1, 0)
    assert len(observations_of(client.engine, user_id)) == 1


def test_evidence_whose_messages_message_retention_deleted_is_not_tagged(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = have_unmatched_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    clock.advance(retention(seeded_settings) + timedelta(days=1))
    scheduler.tick()
    tagging_calls = len(chat_model.pattern_tagging_calls)
    chat_model.script_pattern_matching(matching_answer(ABSORBED))

    [report] = matcher_of(client, chat_model, clock).match()

    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.matched_pattern_type_id == ABSORBED
    assert (report.conversations_tagged, report.observations_kept) == (0, 0)
    assert report.days_without_messages == 1
    assert len(chat_model.pattern_tagging_calls) == tagging_calls


def test_a_matching_run_that_fails_leaves_the_pattern_for_the_next_run(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = have_unmatched_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    chat_model.script_pattern_matching(matching_answer(ABSORBED))
    chat_model.script_pattern_tagging(RuntimeError("model down"))
    printed: list[str] = []

    every_user_done = match_and_report(
        matcher_of(client, chat_model, clock), [], printed.append
    )

    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.matched_pattern_type_id is None
    assert every_user_done is False
    assert printed == [f"User {user_id}: skipped (it failed; see the backend log)"]


def test_a_closed_pattern_is_linked_but_its_evidence_is_left_alone(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = have_unmatched_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    set_pattern_state(client.engine, PatternState.CLOSED)
    tagging_calls = len(chat_model.pattern_tagging_calls)
    chat_model.script_pattern_matching(matching_answer(ABSORBED))

    [report] = matcher_of(client, chat_model, clock).match()

    [pattern] = patterns_of(client.engine, user_id)
    assert (pattern.state, pattern.matched_pattern_type_id) == (
        PatternState.CLOSED,
        ABSORBED,
    )
    assert report.conversations_tagged == 0
    assert len(chat_model.pattern_tagging_calls) == tagging_calls


def test_the_admin_command_prints_ids_and_counts_and_never_a_users_words(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = have_unmatched_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    [pattern] = patterns_of(client.engine, user_id)
    chat_model.script_pattern_matching(matching_answer(ABSORBED))
    chat_model.script_pattern_tagging(tagging_answer(FORGOT_TO_EAT))
    printed: list[str] = []

    match_and_report(
        matcher_of(client, chat_model, clock), read_pattern_type_ids(""), printed.append
    )

    assert printed == [
        f"User {user_id}: 1 Patterns looked at, 1 matched, 1 Conversations tagged "
        "again, 1 Observations kept, 0 evidence days with no messages left",
        f"  Pattern {pattern.id} (unmatched): {ABSORBED}",
    ]


def test_pattern_matching_is_a_core_service_admins_can_tune(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    services = client.get("/api/admin/core-services", headers=admin).json()
    settings = client.get("/api/admin/settings", headers=admin).json()["settings"]

    [matching] = [
        service
        for service in services["services"]
        if service["name"] == "Pattern matching"
    ]
    assert matching["prompt_key"] == "pattern_matching_prompt"
    assert matching["runs_when"] == "Only when an Admin runs the matching command"
    assert "matching command" in settings["pattern_matching_prompt"]["hint"]
    assert (
        '{"pattern_type": "<ID>" | null}'
        in (settings["pattern_matching_prompt"]["value"])
    )


def test_pattern_type_ids_are_read_from_the_command_line() -> None:
    assert read_pattern_type_ids("") == []
    assert read_pattern_type_ids(" A.B.C, D.E.F ,") == ["A.B.C", "D.E.F"]


def test_the_report_says_when_there_was_nothing_to_match_or_a_user_was_skipped() -> (
    None
):
    user_id, pattern_id = uuid4(), uuid4()

    assert report_lines([]) == ["No Pattern to match."]
    assert report_lines(
        [
            UserMatchingReport(user_id=user_id, skipped_why="not told yet"),
            UserMatchingReport(
                user_id=user_id,
                matches=(PatternMatch(pattern_id, PatternState.CONFIRMED, None),),
            ),
        ]
    ) == [
        f"User {user_id}: skipped (not told yet)",
        f"User {user_id}: 1 Patterns looked at, 0 matched, 0 Conversations tagged "
        "again, 0 Observations kept, 0 evidence days with no messages left",
        f"  Pattern {pattern_id} (confirmed): fits no Pattern Type",
    ]


@pytest.mark.parametrize(
    ("answer", "read"),
    [
        ('{"pattern_type": "A.B.C"}', {"pattern_type": "A.B.C"}),
        ('```json\n{"pattern_type": null}\n```', {"pattern_type": None}),
        ('{"type": "A.B.C"}', None),
        ("A.B.C", None),
        ("{not json}", None),
        ('["A.B.C"]', None),
    ],
)
def test_a_matching_answer_is_read_only_when_it_is_the_json_asked_for(
    answer: str, read: dict[str, Any] | None
) -> None:
    assert read_matching_answer(answer) == read


@pytest.mark.parametrize(
    ("named", "fits"),
    [("A.B.C", "A.B.C"), ("X.Y.Z", None), (None, None), (7, None), (["A.B.C"], None)],
)
def test_only_a_pattern_type_it_was_given_counts_as_a_fit(
    named: Any, fits: str | None
) -> None:
    given: dict[str, Any] = {"A.B.C": object()}

    assert read_fitting_pattern_type({"pattern_type": named}, given) == fits


def written_pattern(state: PatternState, evidence: list[tuple[date, UUID]]) -> Pattern:
    """A Pattern with no Pattern Type, with evidence on the given days and Threads."""
    now = datetime(2026, 11, 20, 12, 0)
    return Pattern(
        id=uuid4(),
        user_id=uuid4(),
        pattern="Keeps busy so they never have to sit with a hard feeling.",
        state=state,
        evidence=tuple(
            PatternEvidence(
                id=uuid4(), day=day, thread_id=thread_id, thread_title="", line="x"
            )
            for day, thread_id in evidence
        ),
        started_at=now,
        updated_at=now,
    )


def test_each_evidence_day_is_tagged_against_every_pattern_type_its_patterns_fit() -> (
    None
):
    work, home = uuid4(), uuid4()
    first, second = date(2026, 11, 1), date(2026, 11, 2)
    unmatched = written_pattern(PatternState.UNMATCHED, [(second, work), (first, home)])
    confirmed = written_pattern(PatternState.CONFIRMED, [(second, home)])
    closed = written_pattern(PatternState.CLOSED, [(date(2026, 11, 3), home)])

    days = plan_days_to_tag_again(
        [(unmatched, "A.B.C"), (confirmed, "D.E.F"), (closed, "A.B.C")]
    )

    assert days == [
        DayToTagAgain(first, frozenset({"A.B.C"}), frozenset({home})),
        DayToTagAgain(second, frozenset({"A.B.C", "D.E.F"}), frozenset({work, home})),
    ]
