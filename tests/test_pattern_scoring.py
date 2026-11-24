from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from companion.core.models import (
    CatalogPattern,
    EvidenceKind,
    Observation,
    ObservationDirection,
    PatternMoveCause,
    PatternState,
    SignStrength,
    SituationSetting,
    SituationTags,
)
from companion.core.pattern_scoring import (
    PatternScore,
    PlannedPatternMoves,
    ScoringNumbers,
    StateBars,
    observation_points,
    observations_by_pattern_type,
    plan_pattern_moves,
    score_observations,
    state_for,
)

TODAY = date(2026, 11, 24)
NOW = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
USER_ID = uuid4()
CONVERSATION_ID = uuid4()
BELONG = "CONF.AVOID.BELONG"
WORTH = "ACH.WORTH.PERF"
NUMBERS = ScoringNumbers(
    sign_points={
        SignStrength.WEAK: 30,
        SignStrength.MODERATE: 70,
        SignStrength.STRONG: 140,
    },
    evidence_percents={
        EvidenceKind.REAL_STORY: 100,
        EvidenceKind.REPORTED_HABIT: 70,
        EvidenceKind.WHAT_IF_ANSWER: 40,
        EvidenceKind.OWN_OPINION: 30,
    },
    unclear_percent=25,
    half_life_days=75,
    people_per_situation=3,
)
BARS = StateBars(suspected_situations=2, suspected_points=100, closed_under_points=-150)
SIGN_STRENGTHS = {
    (BELONG, "I1"): SignStrength.WEAK,
    (BELONG, "I2"): SignStrength.STRONG,
    (BELONG, "C1"): SignStrength.MODERATE,
    (BELONG, "C2"): SignStrength.STRONG,
}
MUM_THREAD = uuid4()
WORK_THREAD = uuid4()


def observation(
    sign: str = "I2",
    thread: UUID | None = MUM_THREAD,
    about: str = "their mum",
    direction: ObservationDirection = ObservationDirection.FOR,
    kind: EvidenceKind = EvidenceKind.REAL_STORY,
    days_ago: int = 0,
    second: str | None = None,
    situational: bool = False,
    setting: SituationSetting | None = SituationSetting.HOME,
    pattern_type: str = BELONG,
) -> Observation:
    """A fresh strong real story for CONF.AVOID.BELONG, unless changed."""
    return Observation(
        id=uuid4(),
        user_id=USER_ID,
        conversation_id=CONVERSATION_ID,
        pattern_type_id=pattern_type,
        pattern_type_version="0.2.0",
        sign_id=sign,
        direction=direction,
        quote="I said yes again",
        context="Agreed to help again.",
        day=TODAY - timedelta(days=days_ago),
        thread_id=thread,
        about=about,
        tags=SituationTags(relationship=None, power=None, setting=setting, stance=None),
        evidence_kind=kind,
        second_pattern_type_id=second,
        second_pattern_type_version="0.1.0" if second else None,
        situational=situational,
        tagged_at=NOW,
    )


def points_of(item: Observation) -> float:
    """The points one Observation is worth today."""
    return observation_points(item, SIGN_STRENGTHS, NUMBERS, TODAY)


def score_of(*items: Observation) -> PatternScore:
    """The score of CONF.AVOID.BELONG from some Observations, today."""
    return score_observations(list(items), SIGN_STRENGTHS, NUMBERS, TODAY)


def pattern(state: PatternState, pattern_type: str = BELONG) -> CatalogPattern:
    """A User's Pattern of a Pattern Type, in a state."""
    return CatalogPattern(
        id=uuid4(),
        user_id=USER_ID,
        pattern_type_id=pattern_type,
        state=state,
        started_at=NOW - timedelta(days=10),
        updated_at=NOW - timedelta(days=10),
    )


@pytest.mark.parametrize(
    ("item", "points"),
    [
        (observation(sign="I2"), 140),
        (observation(sign="I1"), 30),
        (observation(kind=EvidenceKind.REPORTED_HABIT), 98),
        (observation(kind=EvidenceKind.WHAT_IF_ANSWER), 56),
        (observation(kind=EvidenceKind.OWN_OPINION), 42),
        (observation(second=WORTH), 35),
        (observation(situational=True), 0),
        (
            observation(sign="C1", direction=ObservationDirection.AGAINST),
            -70,
        ),
        (observation(sign="X9"), 0),
    ],
)
def test_an_observation_is_worth_its_sign_times_its_kind_of_evidence(
    item: Observation, points: float
) -> None:
    assert points_of(item) == pytest.approx(points)


def test_older_observations_count_for_less_by_the_half_life() -> None:
    assert points_of(observation(days_ago=75)) == pytest.approx(70)
    assert points_of(observation(days_ago=150)) == pytest.approx(35)


def test_ten_observations_about_one_person_in_one_thread_count_as_one() -> None:
    items = [observation(sign="I1") for _ in range(9)] + [observation(sign="I2")]

    assert score_of(*items) == PatternScore(points=140, situations=1)


def test_different_people_in_one_thread_add_weight_up_to_the_cap_in_one_situation() -> (
    None
):
    people = ["their mum", "their dad", "their sister", "their aunt"]
    items = [observation(about=person) for person in people]

    assert score_of(*items[:2]) == PatternScore(points=280, situations=1)
    assert score_of(*items) == PatternScore(points=420, situations=1)


def test_the_cap_keeps_the_strongest_people() -> None:
    items = [
        observation(sign="I1", about="their aunt"),
        observation(about="their mum"),
        observation(about="their dad"),
        observation(about="their sister"),
    ]

    assert score_of(*items).points == pytest.approx(420)


def test_each_thread_is_its_own_situation() -> None:
    score = score_of(observation(thread=MUM_THREAD), observation(thread=WORK_THREAD))

    assert score == PatternScore(points=280, situations=2)


def test_with_no_thread_a_situation_is_the_same_person_and_setting() -> None:
    same = [observation(thread=None), observation(thread=None, about=" Their Mum ")]
    other_setting = observation(thread=None, setting=SituationSetting.WORK)
    other_person = observation(thread=None, about="their boss")

    assert score_of(*same) == PatternScore(points=140, situations=1)
    assert score_of(*same, other_setting, other_person).situations == 3


def test_one_against_lowers_the_score_even_about_the_same_person() -> None:
    against = observation(sign="C1", direction=ObservationDirection.AGAINST)

    assert score_of(observation(), against).points == pytest.approx(70)


def test_situations_count_only_where_the_pattern_showed() -> None:
    against_elsewhere = observation(
        sign="C1", direction=ObservationDirection.AGAINST, thread=WORK_THREAD
    )
    situational_elsewhere = observation(situational=True, thread=uuid4())

    score = score_of(observation(), against_elsewhere, situational_elsewhere)

    assert score.situations == 1


def test_what_if_answers_alone_never_make_a_situation() -> None:
    answers = [
        observation(kind=EvidenceKind.WHAT_IF_ANSWER, thread=None, about=about)
        for about in ("their team lead", "a friend", "their mum")
    ]

    made_up_only = score_of(*answers)
    with_a_real_story = score_of(*answers, observation(thread=None, about="a friend"))

    assert made_up_only == PatternScore(points=pytest.approx(168), situations=0)
    assert state_for(PatternState.NOTICED, made_up_only, BARS) == PatternState.NOTICED
    assert with_a_real_story.situations == 1


def test_an_unclear_observation_counts_toward_each_of_its_pattern_types() -> None:
    grouped = observations_by_pattern_type([observation(second=WORTH)])

    assert {
        pattern_type: score_of(*items).points for pattern_type, items in grouped.items()
    } == {BELONG: pytest.approx(35), WORTH: pytest.approx(35)}


@pytest.mark.parametrize(
    ("current", "score", "expected"),
    [
        (PatternState.NOTICED, PatternScore(points=99, situations=5), "noticed"),
        (PatternState.NOTICED, PatternScore(points=500, situations=1), "noticed"),
        (PatternState.NOTICED, PatternScore(points=100, situations=2), "suspected"),
        (PatternState.SUSPECTED, PatternScore(points=99, situations=2), "noticed"),
        (PatternState.SUSPECTED, PatternScore(points=-151, situations=0), "closed"),
        (PatternState.NOTICED, PatternScore(points=-150, situations=0), "noticed"),
        (PatternState.CLOSED, PatternScore(points=-151, situations=3), "closed"),
        (PatternState.CLOSED, PatternScore(points=-149, situations=0), "noticed"),
        (PatternState.CLOSED, PatternScore(points=200, situations=3), "suspected"),
        (PatternState.READY, PatternScore(points=-500, situations=0), "ready"),
        (PatternState.SHARED, PatternScore(points=0, situations=0), "shared"),
        (PatternState.CONFIRMED, PatternScore(points=0, situations=0), "confirmed"),
        (PatternState.CONTESTED, PatternScore(points=900, situations=9), "contested"),
    ],
)
def test_a_pattern_moves_by_its_score_and_situations(
    current: PatternState, score: PatternScore, expected: str
) -> None:
    assert state_for(current, score, BARS) == PatternState(expected)


def plan(
    patterns: list[CatalogPattern],
    items: list[Observation],
    cause: PatternMoveCause = PatternMoveCause.CONVERSATION_TAGGED,
) -> PlannedPatternMoves:
    """Plan the moves for USER_ID's Patterns, today."""
    return plan_pattern_moves(
        USER_ID,
        patterns,
        items,
        SIGN_STRENGTHS,
        NUMBERS,
        BARS,
        TODAY,
        NOW,
        cause,
        CONVERSATION_ID if cause == PatternMoveCause.CONVERSATION_TAGGED else None,
    )


def test_a_first_observation_starts_a_noticed_pattern_and_logs_it() -> None:
    planned = plan([], [observation(sign="I1")])

    [started] = planned.added
    assert (started.pattern_type_id, started.state) == (BELONG, PatternState.NOTICED)
    assert (started.started_at, started.updated_at) == (NOW, NOW)
    [move] = planned.moves
    assert move.pattern_id == started.id
    assert (move.from_state, move.to_state) == (None, PatternState.NOTICED)
    assert move.cause == PatternMoveCause.CONVERSATION_TAGGED
    assert move.conversation_id == CONVERSATION_ID
    assert (move.points, move.situations) == (pytest.approx(30), 1)
    assert not planned.changed and not planned.deleted_ids


def test_a_first_batch_past_the_bar_is_noticed_then_suspected() -> None:
    planned = plan(
        [], [observation(thread=MUM_THREAD), observation(thread=WORK_THREAD)]
    )

    assert [started.state for started in planned.added] == [PatternState.SUSPECTED]
    assert [(move.from_state, move.to_state) for move in planned.moves] == [
        (None, PatternState.NOTICED),
        (PatternState.NOTICED, PatternState.SUSPECTED),
    ]


def test_an_unclear_observation_notices_both_pattern_types() -> None:
    planned = plan([], [observation(second=WORTH)])

    assert sorted(started.pattern_type_id for started in planned.added) == [
        WORTH,
        BELONG,
    ]


def test_a_pattern_that_does_not_move_is_left_alone() -> None:
    noticed = pattern(PatternState.NOTICED)

    planned = plan([noticed], [observation()])

    assert not planned.added and not planned.changed and not planned.moves


def test_deleted_evidence_moves_a_pattern_back_with_its_cause() -> None:
    suspected = pattern(PatternState.SUSPECTED)

    planned = plan([suspected], [observation()], PatternMoveCause.OBSERVATIONS_DELETED)

    [moved] = planned.changed
    assert (moved.id, moved.state, moved.updated_at) == (
        suspected.id,
        PatternState.NOTICED,
        NOW,
    )
    assert moved.started_at == suspected.started_at
    [move] = planned.moves
    assert (move.from_state, move.to_state) == (
        PatternState.SUSPECTED,
        PatternState.NOTICED,
    )
    assert (move.cause, move.conversation_id) == (
        PatternMoveCause.OBSERVATIONS_DELETED,
        None,
    )


def test_a_pattern_with_no_observations_left_is_deleted_without_a_move() -> None:
    noticed = pattern(PatternState.NOTICED)

    planned = plan([noticed], [], PatternMoveCause.OBSERVATIONS_DELETED)

    assert planned.deleted_ids == [noticed.id]
    assert not planned.moves


@pytest.mark.parametrize(
    "state",
    [
        PatternState.READY,
        PatternState.SHARED,
        PatternState.CONFIRMED,
        PatternState.CONTESTED,
    ],
)
def test_a_pattern_past_suspected_is_never_deleted_by_scoring(
    state: PatternState,
) -> None:
    planned = plan([pattern(state)], [], PatternMoveCause.OBSERVATIONS_DELETED)

    assert not planned.deleted_ids and not planned.moves
