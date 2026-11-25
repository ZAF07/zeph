import json
from dataclasses import replace
from datetime import date, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from companion.core.models import (
    CatalogPattern,
    Curiosity,
    CuriosityAim,
    CuriosityState,
    ObservationDirection,
    PatternMoveCause,
    PatternMoveReason,
    PatternReaction,
    PatternState,
    Prediction,
    PredictionOutcome,
    ReactionToPattern,
    Relationship,
    ThreadReaction,
)
from companion.core.observations import (
    describe_predictions_given,
    plan_prediction_outcomes,
)
from companion.core.pattern_scoring import (
    PatternScore,
    StateBars,
    plan_pattern_moves,
    prediction_points,
)
from companion.core.predictions import (
    ConfirmBars,
    FollowUpInput,
    FollowUpNumbers,
    GivenCheck,
    PlannedFollowUps,
    SharedPatternFacts,
    counted_once,
    follow_up_window,
    follow_ups_due_early,
    next_prediction_wording,
    plan_follow_ups,
    read_given_check,
    shared_move,
    shared_pattern_facts,
)
from tests.test_ready_gate_rules import (
    BELONG,
    NOW,
    PATTERN_TYPES,
    TODAY,
    WEIGHING,
    story,
)

NUMBERS = FollowUpNumbers(
    wait=timedelta(days=7), drop_after=timedelta(days=21), unanswered_to_stop=2
)
BARS = ConfirmBars(
    predictions_to_confirm=2,
    predictions_to_close=2,
    confirmed_at_points_after_sharing=300,
    closed_under_points=-150,
)
USER = uuid4()
SHARED_AT = NOW - timedelta(days=30)
WORDING = "Next time Mei asks, notice whether you say yes first."


def shared_pattern(state: PatternState = PatternState.SHARED) -> CatalogPattern:
    """A User's Pattern of CONF.AVOID.BELONG, told to them 30 days ago."""
    return CatalogPattern(
        id=uuid4(),
        user_id=USER,
        pattern_type_id=BELONG,
        state=state,
        started_at=SHARED_AT,
        updated_at=SHARED_AT,
        shared_at=SHARED_AT,
    )


def prediction(
    pattern: CatalogPattern,
    made_days_ago: int = 0,
    outcome: PredictionOutcome | None = None,
    outcome_days_ago: int = 0,
) -> Prediction:
    """A Prediction given for a Pattern some days ago."""
    return Prediction(
        id=uuid4(),
        user_id=USER,
        pattern_id=pattern.id,
        wording=WORDING,
        made_at=NOW - timedelta(days=made_days_ago),
        outcome=outcome,
        outcome_at=NOW - timedelta(days=outcome_days_ago) if outcome else None,
    )


def planned(
    patterns: list[CatalogPattern],
    predictions: list[Prediction],
    curiosities: list[Curiosity] | None = None,
    now: datetime = NOW,
    reactions: list[ReactionToPattern] | None = None,
) -> PlannedFollowUps:
    """Plan the Curiosities about a User's Predictions."""
    return plan_follow_ups(
        FollowUpInput(
            user_id=USER,
            now=now,
            time_zone="UTC",
            patterns=patterns,
            pattern_types=PATTERN_TYPES,
            predictions=predictions,
            curiosities=curiosities or [],
            reactions=reactions or [],
        ),
        NUMBERS,
    )


def asked(curiosity: Curiosity, days_ago: int = 0) -> Curiosity:
    """The Curiosity, asked some days ago."""
    return replace(
        curiosity,
        state=CuriosityState.RAISED,
        raised_at=NOW - timedelta(days=days_ago),
    )


def facts(
    pattern: CatalogPattern,
    points: float = 300,
    came_true: int = 0,
    points_after_sharing: float = 0,
    did_not: int = 0,
) -> SharedPatternFacts:
    """What a shared Pattern is confirmed or closed from."""
    return SharedPatternFacts(
        pattern=pattern,
        scored=PatternScore(points=points, situations=3),
        came_true=came_true,
        did_not=did_not,
        points_after_sharing=points_after_sharing,
    )


def test_a_prediction_gets_a_follow_up_not_before_the_wait_and_not_after_the_drop() -> (
    None
):
    pattern = shared_pattern()
    given = prediction(pattern)

    plan = planned([pattern], [given])

    [follow_up] = plan.curiosities.added
    assert follow_up.aim == CuriosityAim.PREDICTION
    assert (follow_up.pattern_id, follow_up.prediction_id) == (pattern.id, given.id)
    assert follow_up.not_before == TODAY + timedelta(days=7)
    assert follow_up.not_after == TODAY + timedelta(days=21)
    assert follow_up.state == CuriosityState.WAITING
    assert WORDING in follow_up.question
    assert PATTERN_TYPES[BELONG].approved_wording in follow_up.question
    assert plan.not_followed_up == []


def test_a_waiting_follow_up_is_not_written_twice() -> None:
    pattern = shared_pattern()
    given = prediction(pattern)
    [follow_up] = planned([pattern], [given]).curiosities.added

    plan = planned([pattern], [given], [follow_up])

    assert plan.curiosities.added == []
    assert plan.curiosities.updated == []


def test_a_follow_up_not_asked_in_time_is_closed_and_its_prediction_dropped() -> None:
    pattern = shared_pattern()
    given = prediction(pattern)
    [follow_up] = planned([pattern], [given]).curiosities.added
    later = NOW + timedelta(days=22)

    plan = planned([pattern], [given], [follow_up], now=later)

    assert [
        (curiosity.id, curiosity.state) for curiosity in plan.curiosities.updated
    ] == [(follow_up.id, CuriosityState.CLOSED)]
    [dropped] = plan.not_followed_up
    assert (dropped.id, dropped.outcome, dropped.outcome_at) == (
        given.id,
        PredictionOutcome.NOT_FOLLOWED_UP,
        later,
    )


def test_one_asked_and_never_answered_is_not_asked_again_and_dropped_in_time() -> None:
    pattern = shared_pattern()
    given = prediction(pattern, made_days_ago=10)
    [follow_up] = planned([pattern], [given]).curiosities.added
    was_asked = asked(follow_up, days_ago=2)

    waiting = planned([pattern], [given], [was_asked])
    late = planned([pattern], [given], [was_asked], now=NOW + timedelta(days=12))

    assert waiting.curiosities.added == []
    assert waiting.not_followed_up == []
    assert [dropped.id for dropped in late.not_followed_up] == [given.id]


def test_hasnt_come_up_starts_a_new_wait_from_the_day_they_said_so() -> None:
    pattern = shared_pattern()
    given = prediction(pattern, made_days_ago=10, outcome=PredictionOutcome.NOT_COME_UP)
    [first] = planned([pattern], [replace(given, outcome=None)]).curiosities.added
    was_asked = asked(first, days_ago=1)

    plan = planned([pattern], [given], [was_asked])

    [again] = plan.curiosities.added
    assert again.prediction_id == given.id
    assert again.not_before == TODAY + timedelta(days=7)
    assert again.not_after == TODAY + timedelta(days=21)
    assert plan.not_followed_up == []


def test_a_waiting_follow_up_from_before_they_said_not_yet_is_replaced() -> None:
    pattern = shared_pattern()
    before = prediction(pattern, made_days_ago=3)
    [first] = planned([pattern], [before]).curiosities.added
    said_not_yet = replace(
        before, outcome=PredictionOutcome.NOT_COME_UP, outcome_at=NOW
    )

    plan = planned([pattern], [said_not_yet], [first])

    assert [curiosity.id for curiosity in plan.curiosities.updated] == [first.id]
    [again] = plan.curiosities.added
    assert again.not_before == TODAY + timedelta(days=7)


@pytest.mark.parametrize(
    "outcome",
    [
        PredictionOutcome.CAME_TRUE,
        PredictionOutcome.DID_NOT,
        PredictionOutcome.NOT_FOLLOWED_UP,
    ],
)
def test_a_shared_pattern_gets_a_new_prediction_once_the_last_is_settled(
    outcome: PredictionOutcome,
) -> None:
    pattern = shared_pattern()
    settled = prediction(pattern, made_days_ago=8, outcome=outcome)
    [follow_up] = planned([pattern], [replace(settled, outcome=None)]).curiosities.added

    plan = planned([pattern], [settled], [follow_up])

    assert [curiosity.id for curiosity in plan.curiosities.updated] == [follow_up.id]
    [give] = plan.curiosities.added
    assert (give.aim, give.pattern_id, give.prediction_id) == (
        CuriosityAim.PREDICTION,
        pattern.id,
        None,
    )
    assert give.not_before is None
    assert PATTERN_TYPES[BELONG].prediction_wordings[0] in give.question
    assert planned([pattern], [settled], [give]).curiosities.added == []


def test_a_pattern_shared_with_no_prediction_gets_one() -> None:
    pattern = shared_pattern()

    [give] = planned([pattern], []).curiosities.added

    assert (give.pattern_id, give.prediction_id) == (pattern.id, None)


def test_nothing_more_is_asked_about_a_pattern_once_they_asked_zeph_to_drop_it() -> (
    None
):
    pattern = shared_pattern()
    given = prediction(pattern, made_days_ago=10)
    [follow_up] = planned([pattern], [given]).curiosities.added
    dropped = replace(asked(follow_up), reaction=ThreadReaction.ASKED_TO_DROP)
    [give] = planned([pattern], []).curiosities.added

    plan = planned([pattern], [given], [dropped, give])

    assert plan.curiosities.added == []
    assert [curiosity.id for curiosity in plan.curiosities.updated] == [give.id]


def test_dropping_one_drops_the_open_prediction_too() -> None:
    pattern = shared_pattern()
    given = prediction(pattern, made_days_ago=10)
    [follow_up] = planned([pattern], [given]).curiosities.added
    dropped = replace(asked(follow_up), reaction=ThreadReaction.ASKED_TO_DROP)

    plan = planned([pattern], [given], [dropped])

    assert [(item.id, item.outcome) for item in plan.not_followed_up] == [
        (given.id, PredictionOutcome.NOT_FOLLOWED_UP)
    ]


def test_only_the_newest_open_prediction_is_followed_up() -> None:
    pattern = shared_pattern()
    older = prediction(pattern, made_days_ago=5)
    newest = prediction(pattern, made_days_ago=1)

    plan = planned([pattern], [older, newest])

    assert [item.id for item in plan.not_followed_up] == [older.id]
    assert [item.prediction_id for item in plan.curiosities.added] == [newest.id]


def test_a_new_prediction_they_let_pass_is_not_offered_again_before_the_wait() -> None:
    pattern = shared_pattern()
    [offer] = planned([pattern], []).curiosities.added
    let_pass = asked(offer, days_ago=2)

    [again] = planned([pattern], [], [let_pass]).curiosities.added

    assert again.prediction_id is None
    assert again.not_before == TODAY + timedelta(days=5)


def test_a_drop_time_shorter_than_the_wait_never_ends_before_the_first_day() -> None:
    pattern = shared_pattern()
    numbers = replace(NUMBERS, drop_after=timedelta(days=3))

    window = follow_up_window(prediction(pattern), numbers, "UTC")

    assert window.first_day == window.last_day == TODAY + timedelta(days=7)


@pytest.mark.parametrize(
    "state",
    [PatternState.CONFIRMED, PatternState.CONTESTED, PatternState.CLOSED],
)
def test_only_a_shared_pattern_has_curiosities_about_predictions(
    state: PatternState,
) -> None:
    shared = shared_pattern()
    given = prediction(shared)
    [follow_up] = planned([shared], [given]).curiosities.added
    no_longer_shared = replace(shared, state=state)

    plan = planned([no_longer_shared], [given], [follow_up])

    assert plan.curiosities.added == []
    assert [
        (curiosity.id, curiosity.state) for curiosity in plan.curiosities.updated
    ] == [(follow_up.id, CuriosityState.CLOSED)]
    assert plan.not_followed_up == []


def test_came_true_is_a_strong_sign_for_and_didnt_a_strong_sign_against() -> None:
    pattern = shared_pattern()
    came_true = prediction(pattern, outcome=PredictionOutcome.CAME_TRUE)
    did_not = prediction(pattern, outcome=PredictionOutcome.DID_NOT)
    not_yet = prediction(pattern, outcome=PredictionOutcome.NOT_COME_UP)
    dropped = prediction(pattern, outcome=PredictionOutcome.NOT_FOLLOWED_UP)
    still_open = prediction(pattern)
    numbers = WEIGHING.numbers

    assert prediction_points([came_true], numbers, TODAY, "UTC") == 140
    assert prediction_points([did_not], numbers, TODAY, "UTC") == -140
    assert prediction_points([not_yet, dropped, still_open], numbers, TODAY, "UTC") == 0
    assert prediction_points([came_true, came_true], numbers, TODAY, "UTC") == 280


def test_a_prediction_outcome_fades_like_any_evidence() -> None:
    pattern = shared_pattern()
    old = prediction(
        pattern, 90, outcome=PredictionOutcome.CAME_TRUE, outcome_days_ago=75
    )

    assert prediction_points([old], WEIGHING.numbers, TODAY, "UTC") == pytest.approx(70)


def test_enough_predictions_that_came_true_confirm_a_shared_pattern() -> None:
    pattern = shared_pattern()

    assert shared_move(facts(pattern, came_true=1), BARS) is None
    assert shared_move(facts(pattern, came_true=2), BARS) == (
        PatternState.CONFIRMED,
        PatternMoveReason.PREDICTIONS_CAME_TRUE,
    )


def test_predictions_confirm_only_when_more_came_true_than_did_not() -> None:
    pattern = shared_pattern()

    assert shared_move(facts(pattern, came_true=2, did_not=2), BARS) is None
    assert shared_move(facts(pattern, came_true=3, did_not=2), BARS) == (
        PatternState.CONFIRMED,
        PatternMoveReason.PREDICTIONS_CAME_TRUE,
    )


def test_enough_predictions_that_did_not_come_true_close_a_shared_pattern() -> None:
    pattern = shared_pattern()

    assert shared_move(facts(pattern, did_not=1), BARS) is None
    assert shared_move(facts(pattern, did_not=2), BARS) == (
        PatternState.CLOSED,
        PatternMoveReason.PREDICTIONS_DID_NOT,
    )
    assert shared_move(facts(pattern, did_not=2, came_true=1), BARS) == (
        PatternState.CLOSED,
        PatternMoveReason.PREDICTIONS_DID_NOT,
    )
    assert shared_move(facts(pattern, did_not=3, came_true=3), BARS) is None


def test_a_story_that_settles_a_prediction_moves_the_score_once() -> None:
    pattern = shared_pattern()
    said_in = uuid4()
    same_story = story(
        about="Dana", direction=ObservationDirection.AGAINST, conversation=said_in
    )
    another_day = story(about="Priya")
    did_not = replace(
        prediction(pattern, outcome=PredictionOutcome.DID_NOT),
        outcome_conversation_id=said_in,
    )
    not_yet = replace(
        prediction(pattern, outcome=PredictionOutcome.NOT_COME_UP),
        outcome_conversation_id=another_day.conversation_id,
    )

    found = shared_pattern_facts(
        pattern, [same_story, another_day], [], [did_not, not_yet], WEIGHING, "UTC"
    )

    assert counted_once([same_story, another_day], [did_not, not_yet]) == [another_day]
    assert found.scored.points == pytest.approx(140 - 140)
    assert found.points_after_sharing == pytest.approx(140)
    assert (found.came_true, found.did_not) == (0, 1)


def test_evidence_that_only_narrows_a_shared_pattern_does_not_count_against_it() -> (
    None
):
    pattern = shared_pattern()
    not_with_friends = story(
        about="Jun, a friend",
        direction=ObservationDirection.AGAINST,
        relationship=Relationship.FRIEND,
    )

    found = shared_pattern_facts(
        pattern, [story(), not_with_friends], [], [], WEIGHING, "UTC"
    )

    assert found.scored.points == pytest.approx(140)
    assert found.points_after_sharing == pytest.approx(140)


def reaction(
    pattern: CatalogPattern, kind: PatternReaction, days_ago: int = 0
) -> ReactionToPattern:
    """How the User took a Pattern some days ago."""
    return ReactionToPattern(
        id=uuid4(),
        user_id=USER,
        pattern_id=pattern.id,
        reaction=kind,
        conversation_id=uuid4(),
        reacted_at=NOW - timedelta(days=days_ago),
    )


def test_no_new_prediction_is_offered_after_two_in_a_row_got_no_answer() -> None:
    pattern = shared_pattern()
    answered = prediction(pattern, 80, outcome=PredictionOutcome.CAME_TRUE)
    first = prediction(pattern, 60, PredictionOutcome.NOT_FOLLOWED_UP, 39)
    second = prediction(pattern, 22)
    [offer] = planned([pattern], [answered, first]).curiosities.added
    [follow_up] = planned(
        [pattern], [answered, first, second], now=NOW - timedelta(days=10)
    ).curiosities.added

    plan = planned([pattern], [answered, first, second], [follow_up])
    one_unanswered = planned([pattern], [answered, second], [follow_up])

    assert offer.prediction_id is None
    assert [item.id for item in plan.not_followed_up] == [second.id]
    assert plan.curiosities.added == []
    assert [item.id for item in plan.curiosities.updated] == [follow_up.id]
    assert [item.prediction_id for item in one_unanswered.curiosities.added] == [None]


@pytest.mark.parametrize(
    ("kind", "days_ago", "offered"),
    [
        (PatternReaction.AGREED, 1, True),
        (PatternReaction.PUSHED_BACK, 1, True),
        (PatternReaction.BRUSHED_OFF, 1, False),
        (PatternReaction.AGREED, 20, False),
    ],
)
def test_predictions_are_offered_again_once_the_user_brings_the_pattern_up(
    kind: PatternReaction, days_ago: int, offered: bool
) -> None:
    pattern = shared_pattern()
    unanswered = [
        prediction(pattern, 60, PredictionOutcome.NOT_FOLLOWED_UP, 39),
        prediction(pattern, 31, PredictionOutcome.NOT_FOLLOWED_UP, 10),
    ]

    plan = planned([pattern], unanswered, reactions=[reaction(pattern, kind, days_ago)])

    assert [item.prediction_id for item in plan.curiosities.added] == (
        [None] if offered else []
    )


def test_strong_evidence_after_sharing_confirms_a_shared_pattern() -> None:
    pattern = shared_pattern()

    assert shared_move(facts(pattern, points_after_sharing=299), BARS) is None
    assert shared_move(facts(pattern, points_after_sharing=300), BARS) == (
        PatternState.CONFIRMED,
        PatternMoveReason.STRONG_EVIDENCE_AFTER_SHARING,
    )


def test_a_shared_pattern_under_the_floor_is_closed_whatever_came_true() -> None:
    pattern = shared_pattern()

    assert shared_move(facts(pattern, points=-150), BARS) is None
    assert shared_move(facts(pattern, points=-151, came_true=2), BARS) == (
        PatternState.CLOSED,
        PatternMoveReason.SCORE_UNDER_FLOOR,
    )


def test_only_a_shared_pattern_is_confirmed_or_closed_this_way() -> None:
    confirmed = shared_pattern(PatternState.CONFIRMED)

    assert shared_move(facts(confirmed, points=-500), BARS) is None


def test_a_shared_patterns_score_counts_reactions_and_prediction_outcomes() -> None:
    pattern = shared_pattern()
    shared_on = TODAY - timedelta(days=30)
    earlier = [replace(story(about=name), day=shared_on) for name in ("Mei", "Jun")]
    later = [story(about="Priya")]
    predictions = [
        prediction(pattern, outcome=PredictionOutcome.CAME_TRUE),
        prediction(pattern, outcome=PredictionOutcome.DID_NOT),
        prediction(pattern, outcome=PredictionOutcome.CAME_TRUE),
    ]
    faded = 140 * 0.5 ** (30 / 75)

    found = shared_pattern_facts(
        pattern, [*earlier, *later], [], predictions, WEIGHING, "UTC"
    )

    assert found.came_true == 2
    assert found.scored.points == pytest.approx(2 * faded + 140 + 140)
    assert found.scored.situations == 3
    assert found.points_after_sharing == pytest.approx(140)


def test_what_was_said_on_the_day_it_was_shared_is_not_new_evidence() -> None:
    pattern = replace(shared_pattern(), shared_at=NOW)

    found = shared_pattern_facts(pattern, [story()], [], [], WEIGHING, "UTC")

    assert found.points_after_sharing == 0


def test_evidence_against_after_sharing_counts_against_the_new_evidence() -> None:
    pattern = shared_pattern()
    against = story(about="Jun", direction=ObservationDirection.AGAINST)

    found = shared_pattern_facts(pattern, [story(), against], [], [], WEIGHING, "UTC")

    assert found.points_after_sharing < 140


def test_a_pattern_closed_after_it_was_shared_is_never_moved_again_by_scoring() -> None:
    closed = shared_pattern(PatternState.CLOSED)
    never_shared = replace(
        shared_pattern(PatternState.CLOSED),
        pattern_type_id="ACH.WORTH.PERF",
        shared_at=None,
    )
    observations = [story(about="Mei"), story(about="Jun")]
    bars = StateBars(
        suspected_situations=2, suspected_points=100, closed_under_points=-150
    )

    with_evidence = plan_pattern_moves(
        USER,
        [closed],
        observations,
        WEIGHING.sign_strengths,
        WEIGHING.numbers,
        bars,
        TODAY,
        NOW,
        PatternMoveCause.CONVERSATION_TAGGED,
        None,
    )
    with_none = plan_pattern_moves(
        USER,
        [closed, never_shared],
        [],
        WEIGHING.sign_strengths,
        WEIGHING.numbers,
        bars,
        TODAY,
        NOW,
        PatternMoveCause.OBSERVATIONS_DELETED,
        None,
    )

    assert (with_evidence.changed, with_evidence.moves) == ([], [])
    assert with_none.deleted_ids == [never_shared.id]


def test_an_outcome_is_kept_once_per_prediction_shown() -> None:
    pattern = shared_pattern()
    shown = {1: prediction(pattern), 2: prediction(pattern), 3: prediction(pattern)}
    entries = [
        {"prediction": 1, "outcome": "came_true"},
        {"prediction": 1, "outcome": "did_not"},
        {"prediction": 2, "outcome": "not_come_up"},
        {"prediction": 3, "outcome": "not_followed_up"},
        {"prediction": 3, "outcome": "probably"},
        {"prediction": 9, "outcome": "came_true"},
        {"prediction": True, "outcome": "came_true"},
        "came_true",
    ]

    said_in = uuid4()

    kept = plan_prediction_outcomes(entries, shown, said_in, NOW)

    assert [(item.id, item.outcome, item.outcome_at) for item in kept] == [
        (shown[1].id, PredictionOutcome.CAME_TRUE, NOW),
        (shown[2].id, PredictionOutcome.NOT_COME_UP, NOW),
    ]
    assert {item.outcome_conversation_id for item in kept} == {said_in}


def test_the_tagging_model_reads_each_open_prediction_with_its_day() -> None:
    pattern = shared_pattern()

    described = describe_predictions_given({1: prediction(pattern, 5)}, "UTC")

    assert described.startswith("[1] (given ")
    assert "20 Nov" in described
    assert described.endswith(WORDING)
    assert describe_predictions_given({}, "UTC") == "None."


def test_the_given_check_reads_whether_a_prediction_was_given() -> None:
    answer = json.dumps({"given": True, "prediction": f" {WORDING} "})

    assert read_given_check(f"```json\n{answer}\n```") == GivenCheck(True, WORDING)
    assert read_given_check('{"given": false}') == GivenCheck(False, "")
    assert read_given_check('{"given": "yes"}') is None
    assert read_given_check("no idea") is None


def numbered(pattern: CatalogPattern, number: int | None, **changes: Any) -> Prediction:
    """A Prediction given from one of its Pattern Type's wordings."""
    return replace(prediction(pattern, **changes), wording_number=number)


def test_a_new_prediction_uses_a_wording_the_pattern_has_not_had() -> None:
    pattern = shared_pattern()
    belonging = PATTERN_TYPES[BELONG]
    wordings = belonging.prediction_wordings

    first = next_prediction_wording(belonging, [])
    second = next_prediction_wording(belonging, [numbered(pattern, 1)])
    third = next_prediction_wording(
        belonging, [numbered(pattern, 1), numbered(pattern, 2)]
    )
    before_they_were_numbered = next_prediction_wording(
        belonging, [numbered(pattern, None)]
    )

    assert first == (1, wordings[0])
    assert second == (2, wordings[1])
    assert third == (3, wordings[2])
    assert before_they_were_numbered == (1, wordings[0])


def test_once_every_wording_was_given_the_one_given_longest_ago_comes_again() -> None:
    pattern = shared_pattern()
    belonging = PATTERN_TYPES[BELONG]
    given = [numbered(pattern, number) for number in (1, 2, 3, 1)]

    assert next_prediction_wording(belonging, given)[0] == 2


def test_the_offer_of_a_new_prediction_carries_the_next_wording() -> None:
    pattern = shared_pattern()
    settled = numbered(pattern, 1, made_days_ago=8, outcome=PredictionOutcome.CAME_TRUE)

    [give] = planned([pattern], [settled]).curiosities.added

    wordings = PATTERN_TYPES[BELONG].prediction_wordings
    assert wordings[1] in give.question
    assert wordings[0] not in give.question


def test_the_same_wording_coming_true_twice_is_one_test_passed() -> None:
    pattern = shared_pattern()
    came_true = PredictionOutcome.CAME_TRUE
    same_twice = [numbered(pattern, 1, outcome=came_true) for _ in range(2)]
    two_sides = [numbered(pattern, number, outcome=came_true) for number in (1, 2)]
    not_numbered = [numbered(pattern, None, outcome=came_true) for _ in range(2)]

    def came_true_of(predictions: list[Prediction]) -> int:
        return shared_pattern_facts(
            pattern, [], [], predictions, WEIGHING, "UTC"
        ).came_true

    assert came_true_of(same_twice) == 1
    assert came_true_of(two_sides) == 2
    assert came_true_of(not_numbered) == 2


def test_a_follow_up_is_due_early_when_a_thread_of_the_pattern_is_in_mind() -> None:
    pattern = shared_pattern()
    with_mei = story(about="Mei")
    given = prediction(pattern, made_days_ago=2)
    [follow_up] = planned([pattern], [given]).curiosities.added
    other_thread = uuid4()

    def due_early(
        thread_ids: set[Any], today: date = TODAY, asked: Prediction = given
    ) -> frozenset[Any]:
        return follow_ups_due_early(
            [follow_up], [pattern], [with_mei], [asked], thread_ids, today, "UTC"
        )

    said_not_yet_today = replace(
        given, outcome=PredictionOutcome.NOT_COME_UP, outcome_at=NOW
    )
    assert follow_up.not_before is not None
    assert follow_up.not_before > TODAY
    assert due_early({with_mei.thread_id}) == frozenset({follow_up.id})
    assert due_early({other_thread}) == frozenset()
    assert due_early(set()) == frozenset()
    assert due_early({with_mei.thread_id}, TODAY - timedelta(days=2)) == frozenset()
    assert due_early({with_mei.thread_id}, asked=said_not_yet_today) == frozenset()
