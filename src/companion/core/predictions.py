import json
import logging
import re
from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from companion.core.agenda import observations_of
from companion.core.models import (
    CatalogPattern,
    ChatLine,
    ChatRole,
    Curiosity,
    CuriosityAim,
    CuriosityChanges,
    CuriositySensitivity,
    CuriosityState,
    Feature,
    LifeThread,
    ModelStep,
    Observation,
    PatternMoveCause,
    PatternMoveReason,
    PatternReaction,
    PatternState,
    PatternType,
    PlatformSettings,
    Prediction,
    PredictionOutcome,
    ReactionToPattern,
    ThreadReaction,
    UserSnapshot,
)
from companion.core.pattern_catalog import PatternCatalogService
from companion.core.pattern_scoring import (
    PatternScore,
    logged_move,
    prediction_points,
    reaction_points,
    score_observations,
    scoring_numbers,
    sign_strengths_of,
    without_narrowing,
)
from companion.core.pattern_sharing import (
    FIRST_PREDICTION_WORDING,
    describe_where_it_shows,
)
from companion.core.platform_settings import (
    CHECK_IN_MODEL,
    PATTERN_CLOSED_UNDER_POINTS,
    PATTERN_CONFIRM_POINTS_AFTER_SHARING,
    PREDICTION_FOLLOW_UP_DROP,
    PREDICTION_FOLLOW_UP_WAIT,
    PREDICTIONS_TO_CLOSE,
    PREDICTIONS_TO_CONFIRM,
    PREDICTIONS_UNANSWERED_TO_STOP,
    thinking_for_model,
)
from companion.core.ports import Clock, Repositories
from companion.core.ready_gate import Weighing
from companion.core.timing import users_today
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

WORDS = re.compile(r"\w+")
OUTCOMES_THAT_COUNT = frozenset(
    {PredictionOutcome.CAME_TRUE, PredictionOutcome.DID_NOT}
)
REACTIONS_THAT_BRING_A_PATTERN_UP = frozenset(
    {PatternReaction.AGREED, PatternReaction.PUSHED_BACK}
)

WHY_FOLLOW_UP = (
    "What they noticed in their own life tests the Pattern you told them, "
    "whichever way it went."
)
WHY_A_NEW_PREDICTION = (
    "The Pattern you told them is still being tested and has nothing for "
    "them to watch for now."
)
GIVEN_CHECK_PROMPT = (
    "You check whether a message gave someone one thing to notice in their "
    "own life. You are given the Prediction the message was to give and the "
    "message as it will be sent. Answer with JSON only: "
    '{"given": true or false, "prediction": "..."}. "given" is true only if '
    "the message asks them to notice or watch for something in their own "
    "life from now on, and it is the thing that Prediction describes, in "
    "any words and with their own people; a question about what already "
    "happened, or something else to watch for, is not enough. "
    '"prediction" is that one thing, in the message\'s own words; "" if it '
    "gives none."
)


@dataclass(frozen=True)
class FollowUpNumbers:
    """The Admin-set times a Prediction is followed up within.

    Attributes:
        wait: How long after a Prediction is given, or after the User said
            it hasn't come up, before the Companion asks how it went.
        drop_after: How long after that same moment a Prediction with no
            answer is dropped.
        unanswered_to_stop: After this many Predictions in a row got no
            answer, no new one is offered until the User brings the
            Pattern up.
    """

    wait: timedelta
    drop_after: timedelta
    unanswered_to_stop: int


@dataclass(frozen=True)
class ConfirmBars:
    """The Admin-set bars a shared Pattern is confirmed or closed at.

    Attributes:
        predictions_to_confirm: How many Predictions that came true
            confirm it, when more came true than didn't.
        predictions_to_close: How many Predictions that didn't come true
            close it, when more didn't than did.
        confirmed_at_points_after_sharing: The score from Observations
            said after the day it was shared that confirms it.
        closed_under_points: A score under this closes it.
    """

    predictions_to_confirm: int
    predictions_to_close: int
    confirmed_at_points_after_sharing: int
    closed_under_points: int


@dataclass(frozen=True)
class SharedPatternFacts:
    """What code confirms or closes a Pattern the User was told from.

    Attributes:
        pattern: The Pattern.
        scored: Its score with its reactions and Prediction outcomes
            counted, and the situations it showed in.
        came_true: How many of its Prediction wordings came true, so the
            same test passed twice is one.
        did_not: How many of its Prediction wordings didn't come true,
            counted the same way.
        points_after_sharing: The score of its Observations said on a
            later day than it was shared, alone.
    """

    pattern: CatalogPattern
    scored: PatternScore
    came_true: int
    did_not: int
    points_after_sharing: float


@dataclass(frozen=True)
class FollowUpInput:
    """Everything the Curiosities about a User's Predictions are planned from.

    Attributes:
        user_id: The User.
        now: When they are planned.
        time_zone: The User's IANA time zone, for the days.
        patterns: Their Patterns of Pattern Types.
        pattern_types: The Pattern Types in the catalog now, by ID.
        predictions: Every Prediction given to them, oldest first.
        curiosities: Their Curiosities about Predictions, in any state.
        reactions: How they took the Patterns they were told, one per
            Pattern and Conversation.
    """

    user_id: UUID
    now: datetime
    time_zone: str | None
    patterns: Sequence[CatalogPattern]
    pattern_types: Mapping[str, PatternType]
    predictions: Sequence[Prediction]
    curiosities: Sequence[Curiosity]
    reactions: Sequence[ReactionToPattern] = ()


@dataclass(frozen=True)
class PlannedFollowUps:
    """What a Conversation's end changes in following up a User's Predictions.

    Attributes:
        curiosities: The new Curiosities and the waiting ones now closed.
        not_followed_up: The Predictions dropped for having no answer in
            time, each with that outcome.
    """

    curiosities: CuriosityChanges
    not_followed_up: list[Prediction]


@dataclass(frozen=True)
class FollowUpWindow:
    """When an open Prediction may be followed up.

    Attributes:
        counted_from: The moment the window counts from: when the
            Prediction was given, or when the User last said it hasn't
            come up.
        first_day: The first day, in the User's time zone, the Companion
            may ask how it went.
        last_day: The last day it may ask; after it the Prediction is
            dropped.
    """

    counted_from: datetime
    first_day: date
    last_day: date


@dataclass(frozen=True)
class PatternFollowUps:
    """What is planned for the Curiosities about one shared Pattern's Predictions.

    Attributes:
        added: The new Curiosities.
        kept_ids: The waiting Curiosities that stay; any other waiting one
            is closed.
        dropped: The Predictions dropped for having no answer, each with
            that outcome.
    """

    added: Sequence[Curiosity] = ()
    kept_ids: Set[UUID] = frozenset()
    dropped: Sequence[Prediction] = ()


@dataclass(frozen=True)
class GivenCheck:
    """What the check after a message that was to give a Prediction found.

    Attributes:
        given: Whether the message gave them something to notice.
        prediction: The Prediction as the message worded it; "" for none.
    """

    given: bool
    prediction: str


def counted_once(
    observations: Sequence[Observation], predictions: Sequence[Prediction]
) -> list[Observation]:
    """Leave out the Observations from a Conversation that settled a Prediction.

    A story that says how a Prediction went is often tagged as an
    Observation too. The Prediction's outcome is what counts, so one event
    never moves the Pattern twice.

    Args:
        observations: The Observations of a shared Pattern.
        predictions: The Predictions given for it.

    Returns:
        The Observations not said in a Conversation where the User said a
        Prediction came true or didn't.
    """
    settled_in = {
        prediction.outcome_conversation_id
        for prediction in predictions
        if prediction.outcome in OUTCOMES_THAT_COUNT
    }
    return [
        observation
        for observation in observations
        if observation.conversation_id not in settled_in
    ]


def wording_number_of(prediction: Prediction) -> int:
    """Say which of its Pattern Type's wordings a Prediction was given from.

    Args:
        prediction: The Prediction.

    Returns:
        Its number, counted from 1; the first for one given before the
        wordings were numbered, when a Pattern Type had only that one.
    """
    return prediction.wording_number or FIRST_PREDICTION_WORDING


def wordings_with(outcome: PredictionOutcome, predictions: Sequence[Prediction]) -> int:
    """Count the different Prediction wordings that went one way.

    Args:
        outcome: How a Prediction went.
        predictions: The Predictions given for one Pattern.

    Returns:
        How many wordings have a Prediction with that outcome, so the
        same test passed or failed twice counts once.
    """
    return len(
        {
            wording_number_of(prediction)
            for prediction in predictions
            if prediction.outcome == outcome
        }
    )


def shared_pattern_facts(
    pattern: CatalogPattern,
    observations: Sequence[Observation],
    reactions: Sequence[ReactionToPattern],
    predictions: Sequence[Prediction],
    weighing: Weighing,
    time_zone: str | None,
) -> SharedPatternFacts:
    """Work out what a Pattern the User was told is confirmed or closed from.

    Evidence against that only narrows the Pattern is left out, as scoring
    and the ready gate leave it out, and so is every Observation from a
    Conversation that settled one of its Predictions.

    Args:
        pattern: The Pattern.
        observations: The Observations of its Pattern Type.
        reactions: How the User took it, one per Conversation.
        predictions: The Predictions given for it.
        weighing: Each sign's strength, the Admin-set numbers and the
            User's day now.
        time_zone: The User's IANA time zone, for the day of each reaction
            and outcome.

    Returns:
        Its score with reactions and Prediction outcomes counted, how many
        Predictions came true and how many didn't, and the score of the
        Observations said on a later day than it was shared, so nothing
        from the Conversation it was shared in counts as new.
    """
    numbers, today = weighing.numbers, weighing.today
    counted = without_narrowing(counted_once(observations, predictions))
    scored = score_observations(counted, weighing.sign_strengths, numbers, today)
    said_after_sharing = [
        observation
        for observation in counted
        if pattern.shared_at is not None
        and observation.day > users_today(time_zone, pattern.shared_at)
    ]
    return SharedPatternFacts(
        pattern=pattern,
        scored=replace(
            scored,
            points=scored.points
            + reaction_points(reactions, numbers, today, time_zone)
            + prediction_points(predictions, numbers, today, time_zone),
        ),
        came_true=wordings_with(PredictionOutcome.CAME_TRUE, predictions),
        did_not=wordings_with(PredictionOutcome.DID_NOT, predictions),
        points_after_sharing=score_observations(
            said_after_sharing, weighing.sign_strengths, numbers, today
        ).points,
    )


def shared_move(
    facts: SharedPatternFacts, bars: ConfirmBars
) -> tuple[PatternState, PatternMoveReason] | None:
    """Say whether a shared Pattern is now confirmed or closed, and why.

    Args:
        facts: What it is judged from.
        bars: The Admin-set bars.

    Returns:
        Closed when its score is under the floor, or when enough of its
        Predictions didn't come true and more didn't than did; else
        confirmed when enough came true and more did than didn't, or the
        evidence since it was shared is strong enough; None when it stays
        shared, or isn't shared.
    """
    if facts.pattern.state != PatternState.SHARED:
        return None
    if facts.scored.points < bars.closed_under_points:
        return PatternState.CLOSED, PatternMoveReason.SCORE_UNDER_FLOOR
    if facts.did_not >= bars.predictions_to_close and facts.did_not > facts.came_true:
        return PatternState.CLOSED, PatternMoveReason.PREDICTIONS_DID_NOT
    if (
        facts.came_true >= bars.predictions_to_confirm
        and facts.came_true > facts.did_not
    ):
        return PatternState.CONFIRMED, PatternMoveReason.PREDICTIONS_CAME_TRUE
    if facts.points_after_sharing >= bars.confirmed_at_points_after_sharing:
        return PatternState.CONFIRMED, PatternMoveReason.STRONG_EVIDENCE_AFTER_SHARING
    return None


def follow_up_question(
    pattern: CatalogPattern, pattern_type: PatternType, prediction: Prediction
) -> str:
    """Write the instruction to ask how a Prediction went.

    It carries the Pattern and the Prediction, since the reply may no
    longer have the message that gave them.

    Args:
        pattern: The shared Pattern.
        pattern_type: Its Pattern Type, with the approved wording.
        prediction: The Prediction, as it was given.

    Returns:
        The instruction.
    """
    return (
        "A while ago you told them something you'd noticed about them: "
        f"{pattern_type.approved_wording}"
        f"{describe_where_it_shows(pattern.narrowings)} You asked them to "
        f"watch for this: “{prediction.wording}” Ask how that went: whether "
        "it happened, went differently, or hasn't come up yet. Take their "
        "answer as it comes and never argue for the Pattern."
    )


def next_prediction_wording(
    pattern_type: PatternType, given: Sequence[Prediction]
) -> tuple[int, str]:
    """Pick the Prediction wording a Pattern is given next.

    Args:
        pattern_type: The Pattern's Pattern Type, with its wordings.
        given: The Predictions already given for the Pattern, oldest first.

    Returns:
        The number, counted from 1, and the wording: the first the Pattern
        hasn't had, so each tests a different side of it; once it has had
        them all, the one given longest ago.
    """
    last_given = {
        wording_number_of(prediction): place for place, prediction in enumerate(given)
    }
    numbers = range(1, len(pattern_type.prediction_wordings) + 1)
    next_number = min(numbers, key=lambda candidate: last_given.get(candidate, -1))
    return next_number, pattern_type.prediction_wordings[next_number - 1]


def new_prediction_question(
    pattern: CatalogPattern, pattern_type: PatternType, wording: str
) -> str:
    """Write the instruction to give a shared Pattern a new Prediction.

    Args:
        pattern: The shared Pattern.
        pattern_type: Its Pattern Type, with the approved wording.
        wording: The Prediction wording to give.

    Returns:
        The instruction.
    """
    return (
        "A while ago you told them something you'd noticed about them: "
        f"{pattern_type.approved_wording}"
        f"{describe_where_it_shows(pattern.narrowings)} It is still only "
        "your view. Ask whether they'd try watching for one new thing in "
        "their own life that would test it, and say what it is: "
        f"{wording} Where it has a word in curly "
        "brackets, put their own person or thing. Offer it lightly, as an "
        "invitation and not a task."
    )


def waiting_curiosity(
    follow_up_input: FollowUpInput,
    pattern: CatalogPattern,
    question: str,
    why: str,
) -> Curiosity:
    """Write a waiting Curiosity about a shared Pattern's Prediction.

    Args:
        follow_up_input: The User and when it is written.
        pattern: The shared Pattern.
        question: The instruction the reply is given.
        why: Why the Companion wonders.

    Returns:
        The Curiosity, with no first or last day and no Prediction yet.
    """
    return Curiosity(
        id=uuid4(),
        user_id=follow_up_input.user_id,
        question=question,
        why=why,
        not_before=None,
        sensitivity=CuriositySensitivity.MEDIUM,
        state=CuriosityState.WAITING,
        created_at=follow_up_input.now,
        aim=CuriosityAim.PREDICTION,
        pattern_id=pattern.id,
    )


def counted_from(prediction: Prediction) -> datetime:
    """Say when an open Prediction's follow-up window counts from.

    Args:
        prediction: The Prediction, still open.

    Returns:
        When the User last said it hasn't come up; else when it was given.
    """
    if (
        prediction.outcome == PredictionOutcome.NOT_COME_UP
        and prediction.outcome_at is not None
    ):
        return prediction.outcome_at
    return prediction.made_at


def follow_up_window(
    prediction: Prediction, numbers: FollowUpNumbers, time_zone: str | None
) -> FollowUpWindow:
    """Work out when an open Prediction may be followed up.

    Args:
        prediction: The Prediction, still open.
        numbers: The Admin-set times.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        The window, counted from when the Prediction was given or from
        when the User last said it hasn't come up. Its last day is never
        before its first, whatever the Admin-set times.
    """
    window_start = counted_from(prediction)
    return FollowUpWindow(
        counted_from=window_start,
        first_day=users_today(time_zone, window_start + numbers.wait),
        last_day=users_today(
            time_zone, window_start + max(numbers.wait, numbers.drop_after)
        ),
    )


def is_in_mind(
    observations: Sequence[Observation], threads_in_mind: Sequence[LifeThread]
) -> bool:
    """Say whether the User is talking about where a Pattern showed.

    Args:
        observations: The Observations of the Pattern.
        threads_in_mind: The Life Threads this reply has in mind.

    Returns:
        True when one of those Threads is one the Pattern showed in, or
        has a person in it that one of its Observations is about.
    """
    thread_ids = {thread.id for thread in threads_in_mind}
    people = {
        person.casefold() for thread in threads_in_mind for person in thread.people
    }
    return any(
        observation.thread_id in thread_ids
        or people & set(WORDS.findall(observation.about.casefold()))
        for observation in observations
    )


def follow_ups_due_early(
    curiosities: Sequence[Curiosity],
    patterns: Sequence[CatalogPattern],
    observations: Sequence[Observation],
    predictions: Sequence[Prediction],
    threads_in_mind: Sequence[LifeThread],
    today: date,
    time_zone: str | None,
) -> frozenset[UUID]:
    """Find the follow-ups that may be asked before their wait is over.

    A fixed wait alone is too passive: when the User next talks about a
    person or part of their life the Pattern showed with, that is the
    moment to ask how the Prediction went.

    Args:
        curiosities: The User's Curiosities about Predictions.
        patterns: Their Patterns of Pattern Types.
        observations: Their Observations.
        predictions: The Predictions given to them.
        threads_in_mind: The Life Threads this reply has in mind.
        today: The User's day now.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        The waiting follow-ups whose Pattern showed in a Life Thread now
        in mind, or with a person in one, on a later day than their
        Prediction was given or the User last said it hasn't come up.
    """
    pattern_type_ids = {pattern.id: pattern.pattern_type_id for pattern in patterns}
    predictions_by_id = {prediction.id: prediction for prediction in predictions}
    due_early = set()
    for curiosity in curiosities:
        if curiosity.prediction_id is None or curiosity.pattern_id is None:
            continue
        prediction = predictions_by_id.get(curiosity.prediction_id)
        pattern_type_id = pattern_type_ids.get(curiosity.pattern_id)
        if (
            curiosity.state != CuriosityState.WAITING
            or prediction is None
            or pattern_type_id is None
            or today <= users_today(time_zone, counted_from(prediction))
        ):
            continue
        if is_in_mind(observations_of(pattern_type_id, observations), threads_in_mind):
            due_early.add(curiosity.id)
    return frozenset(due_early)


def not_followed_up(prediction: Prediction, now: datetime) -> Prediction:
    """Drop an open Prediction that got no answer.

    Args:
        prediction: The Prediction.
        now: When it is dropped.

    Returns:
        The Prediction with the outcome "not followed up", which counts
        nothing.
    """
    return replace(
        prediction, outcome=PredictionOutcome.NOT_FOLLOWED_UP, outcome_at=now
    )


def plan_new_prediction(
    follow_up_input: FollowUpInput,
    pattern: CatalogPattern,
    its_curiosities: Sequence[Curiosity],
    numbers: FollowUpNumbers,
) -> PatternFollowUps:
    """Plan the Curiosity that offers a shared Pattern a new Prediction.

    Args:
        follow_up_input: What the User's Curiosities are planned from.
        pattern: The shared Pattern, with no open Prediction.
        its_curiosities: The Curiosities about its Predictions, in any
            state.
        numbers: The Admin-set times.

    Returns:
        The waiting offer, kept; with none, a new one for a wording the
        Pattern hasn't had, asked not before the Admin-set wait after the
        last offer was made, so one the User let pass isn't offered again
        in every Conversation.
    """
    offers = [
        curiosity for curiosity in its_curiosities if curiosity.prediction_id is None
    ]
    waiting = [
        curiosity for curiosity in offers if curiosity.state == CuriosityState.WAITING
    ]
    if waiting:
        return PatternFollowUps(kept_ids={curiosity.id for curiosity in waiting})
    offered_at = [
        curiosity.raised_at for curiosity in offers if curiosity.raised_at is not None
    ]
    pattern_type = follow_up_input.pattern_types[pattern.pattern_type_id]
    _, wording = next_prediction_wording(
        pattern_type,
        [
            prediction
            for prediction in follow_up_input.predictions
            if prediction.pattern_id == pattern.id
        ],
    )
    offer = waiting_curiosity(
        follow_up_input,
        pattern,
        new_prediction_question(pattern, pattern_type, wording),
        WHY_A_NEW_PREDICTION,
    )
    first_day = (
        users_today(follow_up_input.time_zone, max(offered_at) + numbers.wait)
        if offered_at
        else None
    )
    return PatternFollowUps(added=[replace(offer, not_before=first_day)])


def plan_follow_up(
    follow_up_input: FollowUpInput,
    pattern: CatalogPattern,
    its_curiosities: Sequence[Curiosity],
    prediction: Prediction,
    window: FollowUpWindow,
) -> PatternFollowUps:
    """Plan the Curiosity that asks how a shared Pattern's open Prediction went.

    Args:
        follow_up_input: What the User's Curiosities are planned from.
        pattern: The shared Pattern.
        its_curiosities: The Curiosities about its Predictions, in any
            state.
        prediction: Its open Prediction, whose last day hasn't passed.
        window: When it may be followed up.

    Returns:
        The follow-up waiting for this window, kept; a new one when none
        waits and none was asked in this window; nothing once one was
        asked, so it is asked once per window.
    """
    its_follow_ups = [
        curiosity
        for curiosity in its_curiosities
        if curiosity.prediction_id == prediction.id
    ]
    waiting = [
        curiosity
        for curiosity in its_follow_ups
        if curiosity.state == CuriosityState.WAITING
        and curiosity.not_before == window.first_day
    ]
    asked_in_this_window = any(
        curiosity.raised_at is not None and curiosity.raised_at > window.counted_from
        for curiosity in its_follow_ups
    )
    if waiting or asked_in_this_window:
        return PatternFollowUps(kept_ids={curiosity.id for curiosity in waiting})
    pattern_type = follow_up_input.pattern_types[pattern.pattern_type_id]
    follow_up = waiting_curiosity(
        follow_up_input,
        pattern,
        follow_up_question(pattern, pattern_type, prediction),
        WHY_FOLLOW_UP,
    )
    return PatternFollowUps(
        added=[
            replace(
                follow_up,
                not_before=window.first_day,
                not_after=window.last_day,
                prediction_id=prediction.id,
            )
        ]
    )


def stopped_for_no_answers(
    follow_up_input: FollowUpInput,
    pattern: CatalogPattern,
    dropped_now: Sequence[Prediction],
    numbers: FollowUpNumbers,
) -> bool:
    """Say whether a shared Pattern gets no new Prediction for now.

    Args:
        follow_up_input: What the User's Curiosities are planned from.
        pattern: The shared Pattern, with no open Prediction left.
        dropped_now: Its Predictions being dropped now for having no answer.
        numbers: The Admin-set times and numbers.

    Returns:
        True when its newest Predictions in a row, as many as Admins set,
        all got no answer, and the User hasn't agreed with the Pattern or
        pushed back on it since the last of them was dropped.
    """
    dropped_by_id = {prediction.id: prediction for prediction in dropped_now}
    newest_first = [
        dropped_by_id.get(prediction.id, prediction)
        for prediction in reversed(follow_up_input.predictions)
        if prediction.pattern_id == pattern.id
    ]
    unanswered = []
    for prediction in newest_first:
        if prediction.outcome != PredictionOutcome.NOT_FOLLOWED_UP:
            break
        unanswered.append(prediction)
    if len(unanswered) < numbers.unanswered_to_stop:
        return False
    stopped_at = unanswered[0].outcome_at
    return not any(
        reaction.pattern_id == pattern.id
        and reaction.reaction in REACTIONS_THAT_BRING_A_PATTERN_UP
        and stopped_at is not None
        and reaction.reacted_at > stopped_at
        for reaction in follow_up_input.reactions
    )


def plan_pattern_follow_ups(
    follow_up_input: FollowUpInput, pattern: CatalogPattern, numbers: FollowUpNumbers
) -> PatternFollowUps:
    """Decide which Curiosities about one shared Pattern's Predictions wait.

    Args:
        follow_up_input: What the User's Curiosities are planned from.
        pattern: The shared Pattern, whose Pattern Type is in the catalog.
        numbers: The Admin-set times.

    Returns:
        The new Curiosities, the waiting ones to keep and the Predictions
        dropped. Only its newest open Prediction is followed up; an older
        open one, one whose last day passed, and every open one once the
        User asked the Companion to drop a Curiosity about this Pattern,
        are dropped. After that ask nothing new is written. Nor is a new
        Prediction offered once enough in a row got no answer, until the
        User brings the Pattern up.
    """
    now = follow_up_input.now
    its_curiosities = [
        curiosity
        for curiosity in follow_up_input.curiosities
        if curiosity.pattern_id == pattern.id
    ]
    still_open = [
        prediction
        for prediction in follow_up_input.predictions
        if prediction.pattern_id == pattern.id and prediction.is_open
    ]
    if any(
        curiosity.reaction == ThreadReaction.ASKED_TO_DROP
        for curiosity in its_curiosities
    ):
        return PatternFollowUps(
            dropped=[not_followed_up(prediction, now) for prediction in still_open]
        )
    dropped = [not_followed_up(prediction, now) for prediction in still_open[:-1]]
    newest = still_open[-1] if still_open else None
    window = (
        follow_up_window(newest, numbers, follow_up_input.time_zone)
        if newest is not None
        else None
    )
    today = users_today(follow_up_input.time_zone, now)
    if newest is not None and window is not None and today <= window.last_day:
        planned = plan_follow_up(
            follow_up_input, pattern, its_curiosities, newest, window
        )
    else:
        dropped += [not_followed_up(newest, now)] if newest is not None else []
        if stopped_for_no_answers(follow_up_input, pattern, dropped, numbers):
            return PatternFollowUps(dropped=dropped)
        planned = plan_new_prediction(
            follow_up_input, pattern, its_curiosities, numbers
        )
    return replace(planned, dropped=dropped)


def plan_follow_ups(
    follow_up_input: FollowUpInput, numbers: FollowUpNumbers
) -> PlannedFollowUps:
    """Decide which Curiosities about Predictions wait for a User.

    Only a shared Pattern whose Pattern Type is in the catalog has any;
    the waiting ones of any other Pattern are closed. Its newest open
    Prediction gets one follow-up, asked not before the wait and not after
    the drop time, each counted from when it was given or from when the
    User last said it hasn't come up. One with no answer by the last day
    is dropped: it counts nothing. A shared Pattern with no open
    Prediction gets a Curiosity that offers it a new one, unless its last
    Predictions in a row, as many as Admins set, got no answer and the
    User hasn't brought the Pattern up since. Once the User asked the
    Companion to drop one of a Pattern's, nothing more is written for
    that Pattern.

    Args:
        follow_up_input: What they are planned from.
        numbers: The Admin-set times.

    Returns:
        The new Curiosities, the waiting ones now closed and the
        Predictions dropped.
    """
    per_pattern = [
        plan_pattern_follow_ups(follow_up_input, pattern, numbers)
        for pattern in follow_up_input.patterns
        if pattern.state == PatternState.SHARED
        and pattern.pattern_type_id in follow_up_input.pattern_types
    ]
    kept_ids = {
        curiosity_id for planned in per_pattern for curiosity_id in planned.kept_ids
    }
    return PlannedFollowUps(
        curiosities=CuriosityChanges(
            added=[curiosity for planned in per_pattern for curiosity in planned.added],
            updated=[
                replace(curiosity, state=CuriosityState.CLOSED)
                for curiosity in follow_up_input.curiosities
                if curiosity.state == CuriosityState.WAITING
                and curiosity.id not in kept_ids
            ],
            reactions={},
        ),
        not_followed_up=[
            prediction for planned in per_pattern for prediction in planned.dropped
        ],
    )


def describe_message_for_given_check(wording: str, texts: Sequence[str]) -> str:
    """Write what the check after a message that was to give a Prediction is given.

    Args:
        wording: The Prediction wording the message was to give.
        texts: The message's texts, in order.

    Returns:
        The Prediction it was to give and the message.
    """
    message = "\n".join(texts)
    return f"The Prediction it was to give: {wording}\n\nThe message:\n{message}"


def read_given_check(answer: str) -> GivenCheck | None:
    """Read the check's JSON answer.

    Text around the JSON object, such as a code fence, is ignored.

    Args:
        answer: The model's answer.

    Returns:
        Whether a Prediction was given and how it was worded; None if
        "given" can't be read.
    """
    start, end = answer.find("{"), answer.rfind("}")
    if start == -1 or end < start:
        return None
    try:
        parsed = json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or not isinstance(parsed.get("given"), bool):
        return None
    prediction = parsed.get("prediction")
    return GivenCheck(
        given=parsed["given"],
        prediction=prediction.strip() if isinstance(prediction, str) else "",
    )


def follow_up_numbers(settings: PlatformSettings) -> FollowUpNumbers:
    """Read the Admin-set times a Prediction is followed up within.

    Args:
        settings: The platform settings.

    Returns:
        The times.
    """
    return FollowUpNumbers(
        wait=settings.get(PREDICTION_FOLLOW_UP_WAIT),
        drop_after=settings.get(PREDICTION_FOLLOW_UP_DROP),
        unanswered_to_stop=settings.get(PREDICTIONS_UNANSWERED_TO_STOP),
    )


def confirm_bars(settings: PlatformSettings) -> ConfirmBars:
    """Read the Admin-set bars a shared Pattern is confirmed or closed at.

    Args:
        settings: The platform settings.

    Returns:
        The bars.
    """
    return ConfirmBars(
        predictions_to_confirm=settings.get(PREDICTIONS_TO_CONFIRM),
        predictions_to_close=settings.get(PREDICTIONS_TO_CLOSE),
        confirmed_at_points_after_sharing=settings.get(
            PATTERN_CONFIRM_POINTS_AFTER_SHARING
        ),
        closed_under_points=settings.get(PATTERN_CLOSED_UNDER_POINTS),
    )


class PredictionKeeper:
    """Follows up a shared Pattern's Predictions, and confirms or closes it.

    The model reads how a Prediction went and words the questions; code
    decides when to ask, what an answer counts for and when a shared
    Pattern is confirmed or closed.
    """

    def __init__(
        self,
        repositories: Repositories,
        pattern_catalog: PatternCatalogService,
        chat_model: UsageRecordingChatModel,
        clock: Clock,
    ) -> None:
        """Set up the keeper.

        Args:
            repositories: Where Patterns, their log, Predictions, reactions
                and Curiosities are stored.
            pattern_catalog: Reads the Pattern Types in the catalog now.
            chat_model: Makes the check after a message that was to give a
                Prediction, and records the tokens used.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._pattern_catalog = pattern_catalog
        self._chat_model = chat_model
        self._clock = clock

    def settle_shared(self, snapshot: UserSnapshot, conversation_id: UUID) -> None:
        """Confirm or close each shared Pattern its evidence now calls for.

        Runs when a Conversation ends, after the tagging step saved how the
        User took their Patterns and how their Predictions went. The User
        is locked, like scoring, and each move is logged with its reason
        and the Pattern's score, which counts its reactions and Prediction
        outcomes.

        Args:
            snapshot: The User whose Conversation it was.
            conversation_id: The ended Conversation.
        """
        user, settings = snapshot.user, snapshot.settings
        with self._repositories.transaction() as transaction:
            transaction.lock_user(user.id)
            repositories = transaction.repositories
            shared = [
                pattern
                for pattern in repositories.patterns.list_of_pattern_types(user.id)
                if pattern.state == PatternState.SHARED
            ]
            if not shared:
                return
            now = self._clock.now()
            weighing = Weighing(
                sign_strengths=sign_strengths_of(
                    entry.pattern_type for entry in self._pattern_catalog.catalog()
                ),
                numbers=scoring_numbers(settings),
                today=users_today(user.time_zone, now),
            )
            bars = confirm_bars(settings)
            observations = repositories.observations.list_for_user(user.id)
            reactions = repositories.patterns.list_reactions(user.id)
            predictions = repositories.patterns.list_predictions(user.id)
            changed, moves = [], []
            for pattern in shared:
                facts = shared_pattern_facts(
                    pattern,
                    observations_of(pattern.pattern_type_id, observations),
                    [item for item in reactions if item.pattern_id == pattern.id],
                    [item for item in predictions if item.pattern_id == pattern.id],
                    weighing,
                    user.time_zone,
                )
                move = shared_move(facts, bars)
                if move is None:
                    continue
                state, reason = move
                moves.append(
                    logged_move(
                        pattern,
                        pattern.state,
                        state,
                        facts.scored,
                        PatternMoveCause.CONVERSATION_TAGGED,
                        conversation_id,
                        now,
                        reason=reason,
                    )
                )
                changed.append(replace(pattern, state=state, updated_at=now))
            repositories.patterns.save_moves([], changed, [], moves)

    def keep_follow_ups(self, snapshot: UserSnapshot) -> None:
        """Plan the Curiosities about the User's Predictions and save what changed.

        Runs when a Conversation ends, only while Pattern sharing and
        Curiosities work for them, since one can be asked only then. No
        model call. The User is locked while it reads and saves, so two
        Conversation ends never write the same one.

        Args:
            snapshot: The User whose Conversation ended.
        """
        if not (
            snapshot.works(Feature.PATTERN_SHARING)
            and snapshot.works(Feature.CURIOSITIES)
        ):
            return
        user = snapshot.user
        with self._repositories.transaction() as transaction:
            transaction.lock_user(user.id)
            repositories = transaction.repositories
            patterns = repositories.patterns.list_of_pattern_types(user.id)
            curiosities = repositories.curiosities.list_about_predictions(user.id)
            if not curiosities and not any(
                pattern.state == PatternState.SHARED for pattern in patterns
            ):
                return
            planned = plan_follow_ups(
                FollowUpInput(
                    user_id=user.id,
                    now=self._clock.now(),
                    time_zone=user.time_zone,
                    patterns=patterns,
                    pattern_types={
                        entry.pattern_type.id: entry.pattern_type
                        for entry in self._pattern_catalog.catalog()
                    },
                    predictions=repositories.patterns.list_predictions(user.id),
                    curiosities=curiosities,
                    reactions=repositories.patterns.list_reactions(user.id),
                ),
                follow_up_numbers(snapshot.settings),
            )
            repositories.patterns.save_prediction_outcomes(planned.not_followed_up)
            repositories.curiosities.save_changes(planned.curiosities)

    def follow_ups_due_early(
        self, snapshot: UserSnapshot, threads_in_mind: Sequence[LifeThread]
    ) -> frozenset[UUID]:
        """Find the follow-ups a reply may ask before their wait is over.

        Nothing is read unless Pattern sharing works for the User, a Life
        Thread is in mind and a follow-up is waiting.

        Args:
            snapshot: The User being answered.
            threads_in_mind: The Life Threads this reply has in mind.

        Returns:
            The waiting follow-ups whose Pattern showed in one of those
            Threads, or with a person in one, on a later day than their
            Prediction was given.
        """
        if not threads_in_mind or not snapshot.works(Feature.PATTERN_SHARING):
            return frozenset()
        user_id = snapshot.user.id
        waiting = [
            curiosity
            for curiosity in self._repositories.curiosities.list_about_predictions(
                user_id
            )
            if curiosity.state == CuriosityState.WAITING
            and curiosity.prediction_id is not None
        ]
        if not waiting:
            return frozenset()
        return follow_ups_due_early(
            waiting,
            self._repositories.patterns.list_of_pattern_types(user_id),
            self._repositories.observations.list_for_user(user_id),
            self._repositories.patterns.list_predictions(user_id),
            threads_in_mind,
            snapshot.today,
            snapshot.user.time_zone,
        )

    def record_given(
        self,
        snapshot: UserSnapshot,
        curiosity_ids: Sequence[UUID],
        texts: Sequence[str],
    ) -> None:
        """Keep the new Prediction a sent message gave, if it gave one.

        Nothing is read unless the message brought up a Curiosity. For one
        that was to give a shared Pattern a new Prediction, one small
        model call, on the Check-in model, without thinking where the
        model can do without, reads the message; only when it says a
        Prediction was given is it kept, as the message worded it. It
        never raises: a failed or unreadable check keeps nothing, and the
        next Conversation end writes the Curiosity again.

        Args:
            snapshot: The User the message went to.
            curiosity_ids: The Curiosities the message brought up.
            texts: The message's texts, in order.
        """
        if not curiosity_ids or not snapshot.works(Feature.PATTERN_SHARING):
            return
        try:
            giving = [
                curiosity
                for curiosity in self._repositories.curiosities.list_about_predictions(
                    snapshot.user.id
                )
                if curiosity.id in curiosity_ids
                and curiosity.prediction_id is None
                and curiosity.pattern_id is not None
            ]
            for curiosity in giving:
                self._check_and_record(snapshot, curiosity, texts)
        except Exception:
            logger.exception("Could not check or record a new Prediction")

    def _check_and_record(
        self, snapshot: UserSnapshot, curiosity: Curiosity, texts: Sequence[str]
    ) -> None:
        """Ask whether a message gave a Prediction, and keep it if so.

        Args:
            snapshot: The User the message went to.
            curiosity: The Curiosity that told the message to give one.
            texts: The message's texts, in order.
        """
        user_id = snapshot.user.id
        pattern = self._shared_pattern(self._repositories, user_id, curiosity)
        pattern_type = next(
            (
                entry.pattern_type
                for entry in self._pattern_catalog.catalog()
                if pattern is not None
                and entry.pattern_type.id == pattern.pattern_type_id
            ),
            None,
        )
        if pattern is None or pattern_type is None:
            return
        number, wording = next_prediction_wording(
            pattern_type,
            [
                prediction
                for prediction in self._repositories.patterns.list_predictions(user_id)
                if prediction.pattern_id == pattern.id
            ],
        )
        model = snapshot.settings.get(CHECK_IN_MODEL)
        answer = self._chat_model.generate(
            snapshot=snapshot,
            step=ModelStep.PREDICTION_GIVEN_CHECK,
            model=model,
            thinking=thinking_for_model(snapshot.settings, model, wanted=False),
            instructions=GIVEN_CHECK_PROMPT,
            history=[
                ChatLine(
                    role=ChatRole.USER,
                    text=describe_message_for_given_check(wording, texts),
                )
            ],
        )
        check = read_given_check(answer)
        if check is None or not check.given or not check.prediction:
            return
        with self._repositories.transaction() as transaction:
            transaction.lock_user(user_id)
            repositories = transaction.repositories
            if self._shared_pattern(repositories, user_id, curiosity) is None:
                return
            if any(
                prediction.pattern_id == pattern.id and prediction.is_open
                for prediction in repositories.patterns.list_predictions(user_id)
            ):
                return
            repositories.patterns.add_prediction(
                Prediction(
                    id=uuid4(),
                    user_id=user_id,
                    pattern_id=pattern.id,
                    wording=check.prediction,
                    made_at=self._clock.now(),
                    wording_number=number,
                )
            )

    def _shared_pattern(
        self, repositories: Repositories, user_id: UUID, curiosity: Curiosity
    ) -> CatalogPattern | None:
        """Find the Pattern a Curiosity is about, if it is still shared.

        Args:
            repositories: Where Patterns are read from.
            user_id: The User.
            curiosity: The Curiosity about one of its Predictions.

        Returns:
            The Pattern; None when it is gone or no longer shared.
        """
        return next(
            (
                pattern
                for pattern in repositories.patterns.list_of_pattern_types(user_id)
                if pattern.id == curiosity.pattern_id
                and pattern.state == PatternState.SHARED
            ),
            None,
        )
