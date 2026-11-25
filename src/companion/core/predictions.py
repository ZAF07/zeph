import json
import logging
from collections.abc import Mapping, Sequence
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
    ModelStep,
    Observation,
    PatternMoveCause,
    PatternMoveReason,
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
)
from companion.core.pattern_sharing import describe_where_it_shows
from companion.core.platform_settings import (
    CHECK_IN_MODEL,
    PATTERN_CLOSED_UNDER_POINTS,
    PATTERN_CONFIRM_POINTS_AFTER_SHARING,
    PREDICTION_FOLLOW_UP_DROP,
    PREDICTION_FOLLOW_UP_WAIT,
    PREDICTIONS_TO_CONFIRM,
    thinking_for_model,
)
from companion.core.ports import Clock, Repositories
from companion.core.ready_gate import Weighing
from companion.core.timing import users_today
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

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
    "life from now on; a question about what already happened is not "
    'enough. "prediction" is that one thing, in the message\'s own words; '
    '"" if it gives none.'
)


@dataclass(frozen=True)
class FollowUpNumbers:
    """The Admin-set times a Prediction is followed up within.

    Attributes:
        wait: How long after a Prediction is given, or after the User said
            it hasn't come up, before the Companion asks how it went.
        drop_after: How long after that same moment a Prediction with no
            answer is dropped.
    """

    wait: timedelta
    drop_after: timedelta


@dataclass(frozen=True)
class ConfirmBars:
    """The Admin-set bars a shared Pattern is confirmed or closed at.

    Attributes:
        predictions_to_confirm: How many Predictions that came true
            confirm it.
        points_after_sharing: The score from Observations tagged after it
            was shared that confirms it.
        closed_under_points: A score under this closes it.
    """

    predictions_to_confirm: int
    points_after_sharing: int
    closed_under_points: int


@dataclass(frozen=True)
class SharedPatternFacts:
    """What code confirms or closes a Pattern the User was told from.

    Attributes:
        pattern: The Pattern.
        scored: Its score with its reactions and Prediction outcomes
            counted, and the situations it showed in.
        came_true: How many of its Predictions came true.
        points_after_sharing: The score of its Observations tagged after
            it was shared, alone.
    """

    pattern: CatalogPattern
    scored: PatternScore
    came_true: int
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
    """

    user_id: UUID
    now: datetime
    time_zone: str | None
    patterns: Sequence[CatalogPattern]
    pattern_types: Mapping[str, PatternType]
    predictions: Sequence[Prediction]
    curiosities: Sequence[Curiosity]


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
class GivenCheck:
    """What the check after a message that was to give a Prediction found.

    Attributes:
        given: Whether the message gave them something to notice.
        prediction: The Prediction as the message worded it; "" for none.
    """

    given: bool
    prediction: str


def shared_pattern_facts(
    pattern: CatalogPattern,
    observations: Sequence[Observation],
    reactions: Sequence[ReactionToPattern],
    predictions: Sequence[Prediction],
    weighing: Weighing,
    time_zone: str | None,
) -> SharedPatternFacts:
    """Work out what a Pattern the User was told is confirmed or closed from.

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
        Predictions came true and the score of the Observations tagged
        after it was shared.
    """
    numbers, today = weighing.numbers, weighing.today
    scored = score_observations(observations, weighing.sign_strengths, numbers, today)
    tagged_after_sharing = [
        observation
        for observation in observations
        if pattern.shared_at is not None and observation.tagged_at > pattern.shared_at
    ]
    return SharedPatternFacts(
        pattern=pattern,
        scored=replace(
            scored,
            points=scored.points
            + reaction_points(reactions, numbers, today, time_zone)
            + prediction_points(predictions, numbers, today, time_zone),
        ),
        came_true=sum(
            prediction.outcome == PredictionOutcome.CAME_TRUE
            for prediction in predictions
        ),
        points_after_sharing=score_observations(
            tagged_after_sharing, weighing.sign_strengths, numbers, today
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
        Closed when its score is under the floor; else confirmed when
        enough of its Predictions came true or the evidence since it was
        shared is strong enough; None when it stays shared, or isn't
        shared.
    """
    if facts.pattern.state != PatternState.SHARED:
        return None
    if facts.scored.points < bars.closed_under_points:
        return PatternState.CLOSED, PatternMoveReason.SCORE_UNDER_FLOOR
    if facts.came_true >= bars.predictions_to_confirm:
        return PatternState.CONFIRMED, PatternMoveReason.PREDICTIONS_CAME_TRUE
    if facts.points_after_sharing >= bars.points_after_sharing:
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


def new_prediction_question(pattern: CatalogPattern, pattern_type: PatternType) -> str:
    """Write the instruction to give a shared Pattern a new Prediction.

    Args:
        pattern: The shared Pattern.
        pattern_type: Its Pattern Type, with the approved wording.

    Returns:
        The instruction.
    """
    return (
        "A while ago you told them something you'd noticed about them: "
        f"{pattern_type.approved_wording}"
        f"{describe_where_it_shows(pattern.narrowings)} It is still only "
        "your view. Don't ask a question here: give them one new thing to "
        f"notice in their own life that would test it: "
        f"{pattern_type.prediction_wording} Where it has a word in curly "
        "brackets, put their own person or thing. Say it lightly, as an "
        "invitation and not a task."
    )


def prediction_curiosity(
    follow_up_input: FollowUpInput,
    pattern: CatalogPattern,
    question: str,
    why: str,
    prediction: Prediction | None = None,
    first_day: date | None = None,
    last_day: date | None = None,
) -> Curiosity:
    """Write a waiting Curiosity about a shared Pattern's Prediction.

    Args:
        follow_up_input: The User and when it is written.
        pattern: The shared Pattern.
        question: The instruction the reply is given.
        why: Why the Companion wonders.
        prediction: The Prediction it asks about; None when it gives a
            new one.
        first_day: The first day it may be asked; None for any day.
        last_day: The last day it may be asked; None for no last day.

    Returns:
        The Curiosity.
    """
    return Curiosity(
        id=uuid4(),
        user_id=follow_up_input.user_id,
        question=question,
        why=why,
        not_before=first_day,
        sensitivity=CuriositySensitivity.MEDIUM,
        state=CuriosityState.WAITING,
        created_at=follow_up_input.now,
        aim=CuriosityAim.PREDICTION,
        not_after=last_day,
        pattern_id=pattern.id,
        prediction_id=prediction.id if prediction is not None else None,
    )


def follow_up_window(
    prediction: Prediction, numbers: FollowUpNumbers, time_zone: str | None
) -> tuple[datetime, date, date]:
    """Work out when an open Prediction may be followed up.

    Args:
        prediction: The Prediction, still open.
        numbers: The Admin-set times.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        The moment the window counts from (when it was given, or when the
        User last said it hasn't come up), the first day the Companion
        may ask and the last.
    """
    counted_from = (
        prediction.outcome_at
        if prediction.outcome == PredictionOutcome.NOT_COME_UP
        and prediction.outcome_at is not None
        else prediction.made_at
    )
    return (
        counted_from,
        users_today(time_zone, counted_from + numbers.wait),
        users_today(time_zone, counted_from + numbers.drop_after),
    )


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
    Prediction gets a Curiosity that gives it a new one. Once the User
    asked the Companion to drop one of a Pattern's, nothing more is
    written for that Pattern.

    Args:
        follow_up_input: What they are planned from.
        numbers: The Admin-set times.

    Returns:
        The new Curiosities, the waiting ones now closed and the
        Predictions dropped.
    """
    today = users_today(follow_up_input.time_zone, follow_up_input.now)
    shared = {
        pattern.id: pattern
        for pattern in follow_up_input.patterns
        if pattern.state == PatternState.SHARED
        and pattern.pattern_type_id in follow_up_input.pattern_types
    }
    added: list[Curiosity] = []
    not_followed_up: list[Prediction] = []
    kept_ids: set[UUID] = set()
    for pattern in shared.values():
        pattern_type = follow_up_input.pattern_types[pattern.pattern_type_id]
        its_curiosities = [
            curiosity
            for curiosity in follow_up_input.curiosities
            if curiosity.pattern_id == pattern.id
        ]
        if any(
            curiosity.reaction == ThreadReaction.ASKED_TO_DROP
            for curiosity in its_curiosities
        ):
            continue
        waiting = [
            curiosity
            for curiosity in its_curiosities
            if curiosity.state == CuriosityState.WAITING
        ]
        still_open = [
            prediction
            for prediction in follow_up_input.predictions
            if prediction.pattern_id == pattern.id and prediction.is_open
        ]
        prediction = still_open[-1] if still_open else None
        if prediction is not None:
            counted_from, first_day, last_day = follow_up_window(
                prediction, numbers, follow_up_input.time_zone
            )
            if today > last_day:
                not_followed_up.append(
                    replace(
                        prediction,
                        outcome=PredictionOutcome.NOT_FOLLOWED_UP,
                        outcome_at=follow_up_input.now,
                    )
                )
                prediction = None
        if prediction is None:
            giving = [
                curiosity for curiosity in waiting if curiosity.prediction_id is None
            ]
            kept_ids.update(curiosity.id for curiosity in giving)
            if not giving:
                added.append(
                    prediction_curiosity(
                        follow_up_input,
                        pattern,
                        new_prediction_question(pattern, pattern_type),
                        WHY_A_NEW_PREDICTION,
                    )
                )
            continue
        its_follow_ups = [
            curiosity
            for curiosity in its_curiosities
            if curiosity.prediction_id == prediction.id
        ]
        waiting_for_this_window = [
            curiosity
            for curiosity in its_follow_ups
            if curiosity.state == CuriosityState.WAITING
            and curiosity.not_before == first_day
        ]
        asked_in_this_window = any(
            curiosity.raised_at is not None and curiosity.raised_at > counted_from
            for curiosity in its_follow_ups
        )
        kept_ids.update(curiosity.id for curiosity in waiting_for_this_window)
        if not waiting_for_this_window and not asked_in_this_window:
            added.append(
                prediction_curiosity(
                    follow_up_input,
                    pattern,
                    follow_up_question(pattern, pattern_type, prediction),
                    WHY_FOLLOW_UP,
                    prediction,
                    first_day,
                    last_day,
                )
            )
    return PlannedFollowUps(
        curiosities=CuriosityChanges(
            added=added,
            updated=[
                replace(curiosity, state=CuriosityState.CLOSED)
                for curiosity in follow_up_input.curiosities
                if curiosity.state == CuriosityState.WAITING
                and curiosity.id not in kept_ids
            ],
            reactions={},
        ),
        not_followed_up=not_followed_up,
    )


def describe_message_for_given_check(
    pattern_type: PatternType, texts: Sequence[str]
) -> str:
    """Write what the check after a message that was to give a Prediction is given.

    Args:
        pattern_type: The Pattern Type of the Pattern the Prediction tests.
        texts: The message's texts, in order.

    Returns:
        The Prediction it was to give and the message.
    """
    message = "\n".join(texts)
    return (
        f"The Prediction it was to give: {pattern_type.prediction_wording}"
        f"\n\nThe message:\n{message}"
    )


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
        points_after_sharing=settings.get(PATTERN_CONFIRM_POINTS_AFTER_SHARING),
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
                ),
                follow_up_numbers(snapshot.settings),
            )
            repositories.patterns.save_prediction_outcomes(planned.not_followed_up)
            repositories.curiosities.save_changes(planned.curiosities)

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
                    text=describe_message_for_given_check(pattern_type, texts),
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
