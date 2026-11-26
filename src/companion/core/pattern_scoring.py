from collections.abc import Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime
from uuid import UUID, uuid4

from companion.core.condition_coverage import (
    CONDITION_ORDER,
    condition_value,
    coverage_of,
)
from companion.core.models import (
    CatalogPattern,
    EvidenceKind,
    Observation,
    ObservationDirection,
    PatternMove,
    PatternMoveCause,
    PatternMoveReason,
    PatternNarrowing,
    PatternReaction,
    PatternState,
    PatternType,
    PlatformSettings,
    Prediction,
    PredictionOutcome,
    ReactionToPattern,
    ReadyCheck,
    SignStrength,
    User,
)
from companion.core.pattern_catalog import PatternCatalogService
from companion.core.platform_settings import (
    NARROWING_STORIES_NEEDED,
    NARROWINGS_PER_PATTERN,
    PATTERN_CLOSED_UNDER_POINTS,
    PATTERN_HALF_LIFE_DAYS,
    PATTERN_MODERATE_SIGN_POINTS,
    PATTERN_OWN_OPINION_PERCENT,
    PATTERN_PEOPLE_PER_SITUATION,
    PATTERN_REAL_STORY_PERCENT,
    PATTERN_REPORTED_HABIT_PERCENT,
    PATTERN_STRONG_SIGN_POINTS,
    PATTERN_SUSPECTED_POINTS,
    PATTERN_SUSPECTED_SITUATIONS,
    PATTERN_UNCLEAR_PERCENT,
    PATTERN_WEAK_SIGN_POINTS,
    PATTERN_WHAT_IF_PERCENT,
)
from companion.core.ports import Clock, Repositories
from companion.core.timing import users_today

STATES_MOVED_BY_SCORE = frozenset(
    {PatternState.NOTICED, PatternState.SUSPECTED, PatternState.CLOSED}
)


@dataclass(frozen=True)
class ScoringNumbers:
    """The Admin-set numbers a Pattern's Observations are counted with.

    Attributes:
        sign_points: The points each strength of sign is worth.
        evidence_percents: How much of that each kind of evidence keeps.
        unclear_percent: How much an unclear Observation keeps, toward each
            of its two Pattern Types.
        half_life_days: After how many days an Observation counts half.
        people_per_situation: The most people whose Observations count in
            one situation.
        narrowing_stories_needed: The fewest clear stories for a Pattern
            that must say a Condition before it can narrow the Pattern.
        narrowings_per_pattern: The most Conditions that narrow one Pattern.
    """

    sign_points: Mapping[SignStrength, int]
    evidence_percents: Mapping[EvidenceKind, int]
    unclear_percent: int
    half_life_days: int
    people_per_situation: int
    narrowing_stories_needed: int
    narrowings_per_pattern: int


@dataclass(frozen=True)
class StateBars:
    """The Admin-set bars a Pattern moves between states at.

    Attributes:
        suspected_situations: The fewest situations to be suspected.
        suspected_points: The lowest score to be suspected.
        closed_under_points: A score under this closes it.
    """

    suspected_situations: int
    suspected_points: int
    closed_under_points: int


@dataclass(frozen=True)
class PatternScore:
    """A Pattern's score, worked out from its Observations when it is read.

    Attributes:
        points: The score.
        situations: How many situations it showed in.
    """

    points: float
    situations: int


@dataclass(frozen=True)
class ObservationPoints:
    """What one Observation counts for in its situation.

    Attributes:
        person: Who it is about.
        points: Its points today; negative when against.
        made_up: Whether it answers a made-up situation (a "what if"
            answer) and not something from their life.
    """

    person: str
    points: float
    made_up: bool


@dataclass(frozen=True)
class PlannedPatternMoves:
    """What scoring a User's Patterns again changes.

    Attributes:
        added: Patterns noticed for the first time, in their state now.
        changed: Patterns that moved, in their new state.
        deleted_ids: Patterns with no Observations left.
        moves: Every move, in order, for the log.
    """

    added: list[CatalogPattern]
    changed: list[CatalogPattern]
    deleted_ids: list[UUID]
    moves: list[PatternMove]


def observation_points(
    observation: Observation,
    sign_strengths: Mapping[tuple[str, str], SignStrength],
    numbers: ScoringNumbers,
    today: date,
) -> float:
    """Work out what one Observation is worth today.

    Its sign's points times its kind of evidence, cut when unclear, nothing
    when situational or said while an exclusion applied whose evidence is
    ignored, negative when against, and halved every half-life since the
    day it was said.

    Args:
        observation: The Observation.
        sign_strengths: Each sign's strength, by Pattern Type ID and sign ID.
        numbers: The Admin-set numbers.
        today: The User's day now.

    Returns:
        The points; 0 when its sign isn't in the catalog now.
    """
    strength = sign_strengths.get((observation.pattern_type_id, observation.sign_id))
    if strength is None or observation.situational or observation.excluded:
        return 0.0
    points = (
        numbers.sign_points[strength]
        * numbers.evidence_percents[observation.evidence_kind]
        / 100
    )
    if observation.unclear:
        points = points * numbers.unclear_percent / 100
    if observation.direction == ObservationDirection.AGAINST:
        points = -points
    age_in_days = max((today - observation.day).days, 0)
    fading: float = 0.5 ** (age_in_days / numbers.half_life_days)
    return points * fading


def sign_strengths_of(
    pattern_types: Iterable[PatternType],
) -> dict[tuple[str, str], SignStrength]:
    """Read each sign's strength from some Pattern Types.

    Args:
        pattern_types: The Pattern Types, as the Pattern Catalog holds them now.

    Returns:
        The strength of every sign for and against, by Pattern Type ID and
        sign ID.
    """
    return {
        (pattern_type.id, sign.id): sign.strength
        for pattern_type in pattern_types
        for sign in (*pattern_type.signs, *pattern_type.signs_against)
    }


def reaction_points(
    reactions: Sequence[ReactionToPattern],
    numbers: ScoringNumbers,
    today: date,
    time_zone: str | None,
) -> float:
    """Work out what a User's reactions to one Pattern are worth today.

    Agreeing counts as one weak sign for it and pushing back as one weak
    sign against it, each halved every half-life since its day; brushing
    it off counts nothing. So agreeing adds up and never settles it alone.

    Args:
        reactions: How they took the Pattern, one per Conversation.
        numbers: The Admin-set numbers.
        today: The User's day now.
        time_zone: The User's IANA time zone, for the day of each reaction.

    Returns:
        The points; negative when they pushed back more than they agreed.
    """
    weak = numbers.sign_points[SignStrength.WEAK]
    worth = {
        PatternReaction.AGREED: weak,
        PatternReaction.PUSHED_BACK: -weak,
        PatternReaction.BRUSHED_OFF: 0,
    }
    points = 0.0
    for reaction in reactions:
        day = users_today(time_zone, reaction.reacted_at)
        age_in_days = max((today - day).days, 0)
        points += worth[reaction.reaction] * 0.5 ** (
            age_in_days / numbers.half_life_days
        )
    return points


def prediction_points(
    predictions: Sequence[Prediction],
    numbers: ScoringNumbers,
    today: date,
    time_zone: str | None,
) -> float:
    """Work out what the Predictions given for one Pattern are worth today.

    One that came true counts as one strong sign for the Pattern and one
    that didn't as one strong sign against it, each halved every half-life
    since the day the User said so; any other counts nothing.

    Args:
        predictions: The Predictions given for the Pattern.
        numbers: The Admin-set numbers.
        today: The User's day now.
        time_zone: The User's IANA time zone, for the day of each outcome.

    Returns:
        The points; negative when more didn't come true than did.
    """
    strong = numbers.sign_points[SignStrength.STRONG]
    worth = {PredictionOutcome.CAME_TRUE: strong, PredictionOutcome.DID_NOT: -strong}
    points = 0.0
    for prediction in predictions:
        if prediction.outcome not in worth or prediction.outcome_at is None:
            continue
        day = users_today(time_zone, prediction.outcome_at)
        age_in_days = max((today - day).days, 0)
        points += worth[prediction.outcome] * 0.5 ** (
            age_in_days / numbers.half_life_days
        )
    return points


def situation_of(observation: Observation) -> Hashable:
    """Say which situation an Observation belongs to.

    Args:
        observation: The Observation.

    Returns:
        Its Life Thread; with none, the person it is about and the setting.
    """
    if observation.thread_id is not None:
        return observation.thread_id
    return (person_of(observation), observation.tags.setting)


def person_of(observation: Observation) -> str:
    """Say who an Observation is about, so two mentions of one person match.

    Args:
        observation: The Observation.

    Returns:
        Who it is about, trimmed and in lower case.
    """
    return observation.about.strip().casefold()


def strongest_people_sum(points_by_person: Mapping[str, float], cap: int) -> float:
    """Add up the strongest people's points, up to the cap of people.

    Args:
        points_by_person: Each person's strongest points, all for or all
            against.
        cap: The most people who count.

    Returns:
        The sum of the strongest `cap` of them.
    """
    strongest = sorted(points_by_person.values(), key=abs, reverse=True)
    return sum(strongest[:cap])


def score_situation(points: Sequence[ObservationPoints], cap: int) -> PatternScore:
    """Score one situation from the points of its Observations.

    For it and against it are counted apart: on each side only the strongest
    Observation per person counts, up to the cap of people. The Pattern
    showed in the situation only when something from their life counts for
    it there: "what if" answers add points, but alone they never make a
    situation.

    Args:
        points: What each of its Observations counts for.
        cap: The most people who count on each side.

    Returns:
        Its points, and 1 situation if the Pattern showed in it, else 0.
    """
    strongest_for: dict[str, float] = {}
    strongest_against: dict[str, float] = {}
    for counted in points:
        side = strongest_for if counted.points > 0 else strongest_against
        if abs(counted.points) > abs(side.get(counted.person, 0.0)):
            side[counted.person] = counted.points
    points_for = strongest_people_sum(strongest_for, cap)
    points_against = strongest_people_sum(strongest_against, cap)
    showed = any(counted.points > 0 and not counted.made_up for counted in points)
    return PatternScore(
        points=points_for + points_against, situations=1 if showed else 0
    )


def score_observations(
    observations: Sequence[Observation],
    sign_strengths: Mapping[tuple[str, str], SignStrength],
    numbers: ScoringNumbers,
    today: date,
) -> PatternScore:
    """Work out a Pattern's score from its Observations, as of today.

    Args:
        observations: The Observations naming its Pattern Type.
        sign_strengths: Each sign's strength, by Pattern Type ID and sign ID.
        numbers: The Admin-set numbers.
        today: The User's day now.

    Returns:
        The sum over its situations, and how many it showed in.
    """
    by_situation: dict[Hashable, list[ObservationPoints]] = {}
    for observation in observations:
        by_situation.setdefault(situation_of(observation), []).append(
            ObservationPoints(
                person=person_of(observation),
                points=observation_points(observation, sign_strengths, numbers, today),
                made_up=observation.evidence_kind == EvidenceKind.WHAT_IF_ANSWER,
            )
        )
    scores = [
        score_situation(points, numbers.people_per_situation)
        for points in by_situation.values()
    ]
    return PatternScore(
        points=sum(score.points for score in scores),
        situations=sum(score.situations for score in scores),
    )


def narrowings_of(
    observations: Sequence[Observation], numbers: ScoringNumbers
) -> tuple[PatternNarrowing, ...]:
    """Work out where a Pattern holds and where it was shown not to happen.

    Each Condition is looked at alone, from the Pattern's coverage table.
    One narrows the Pattern when enough clear stories for it say that
    Condition, and its clear evidence against is all under other values
    than any clear story for: "in a group, not one-to-one". Only the
    Conditions with the most stories for behind them are kept, up to the
    Admin-set number, ties going by `CONDITION_ORDER`. Observations that
    carry no weight are left out, and so is evidence against that doesn't
    say the Condition: it neither narrows the Pattern nor stops it being
    narrowed.

    Args:
        observations: The Observations of the Pattern.
        numbers: The Admin-set numbers, for the stories needed and the
            most narrowings.

    Returns:
        The kept narrowings, the one with the most stories first; none
        when no Condition tells the evidence for and against apart.
    """
    table = coverage_of(observations)
    found: list[tuple[int, PatternNarrowing]] = []
    for condition in CONDITION_ORDER:
        holds_with = {
            value for value, seen in table[condition].items() if seen.stories_for
        }
        not_with = {
            value for value, seen in table[condition].items() if seen.stories_against
        }
        stories = sum(seen.stories_for for seen in table[condition].values())
        if stories < numbers.narrowing_stories_needed or not not_with:
            continue
        if holds_with & not_with:
            continue
        found.append(
            (
                stories,
                PatternNarrowing(
                    tag=condition,
                    holds_with=tuple(sorted(holds_with)),
                    not_with=tuple(sorted(not_with)),
                ),
            )
        )
    most_stories_first = sorted(found, key=lambda kept: kept[0], reverse=True)
    return tuple(
        narrowing
        for _, narrowing in most_stories_first[: numbers.narrowings_per_pattern]
    )


def narrows(observation: Observation, narrowings: Sequence[PatternNarrowing]) -> bool:
    """Say whether an Observation against only narrows its Pattern.

    Args:
        observation: The Observation.
        narrowings: The Pattern's kept narrowings.

    Returns:
        True when it is evidence against from a kind of situation the
        Pattern is narrowed away from.
    """
    return observation.direction == ObservationDirection.AGAINST and any(
        condition_value(observation, narrowing.tag) in narrowing.not_with
        for narrowing in narrowings
    )


def without_narrowing(
    observations: Sequence[Observation], numbers: ScoringNumbers
) -> list[Observation]:
    """Leave out the evidence against that only narrows a Pattern.

    Scoring and the ready gate both count a Pattern's Observations this
    way, so "not with my partner" marks where the Pattern stops and never
    counts against it. Evidence against that no kept narrowing explains
    stays, and counts against the Pattern in full.

    Args:
        observations: The Observations of the Pattern.
        numbers: The Admin-set numbers, for the stories needed and the
            most narrowings.

    Returns:
        The Observations that count toward its score, in the order given.
    """
    narrowings = narrowings_of(observations, numbers)
    return [
        observation
        for observation in observations
        if not narrows(observation, narrowings)
    ]


def is_moved_by_score(pattern: CatalogPattern) -> bool:
    """Say whether a Pattern's state follows the score of its Observations.

    Args:
        pattern: The Pattern.

    Returns:
        True for a noticed, suspected or closed Pattern the User was never
        told; one closed after it was shared stays closed.
    """
    return pattern.state in STATES_MOVED_BY_SCORE and pattern.shared_at is None


def state_for(
    current: PatternState, score: PatternScore, bars: StateBars
) -> PatternState:
    """Say which state a Pattern should be in for its score.

    Only noticed, suspected and closed are moved by the score; a Pattern in
    any other state stays there. The state follows the evidence, so a
    Pattern moves back as well as on.

    Args:
        current: The state it is in.
        score: Its score now.
        bars: The Admin-set bars.

    Returns:
        Closed under the floor; suspected in enough situations with a high
        enough score; otherwise noticed.
    """
    if current not in STATES_MOVED_BY_SCORE:
        return current
    if score.points < bars.closed_under_points:
        return PatternState.CLOSED
    if (
        score.situations >= bars.suspected_situations
        and score.points >= bars.suspected_points
    ):
        return PatternState.SUSPECTED
    return PatternState.NOTICED


def observations_by_pattern_type(
    observations: Sequence[Observation],
) -> dict[str, list[Observation]]:
    """Group Observations by the Pattern Types they count toward.

    An unclear one counts toward both of its Pattern Types.

    Args:
        observations: The User's Observations.

    Returns:
        Each Pattern Type's Observations, by its ID, in the order given.
    """
    grouped: dict[str, list[Observation]] = {}
    for observation in observations:
        grouped.setdefault(observation.pattern_type_id, []).append(observation)
        if observation.second_pattern_type_id is not None:
            grouped.setdefault(observation.second_pattern_type_id, []).append(
                observation
            )
    return grouped


def logged_move(
    pattern: CatalogPattern,
    from_state: PatternState | None,
    to_state: PatternState,
    score: PatternScore,
    cause: PatternMoveCause,
    conversation_id: UUID | None,
    now: datetime,
    blocked_by: ReadyCheck | None = None,
    reason: PatternMoveReason | None = None,
) -> PatternMove:
    """Write one move of a Pattern as its log keeps it.

    Args:
        pattern: The Pattern that moved.
        from_state: The state it left; None when it was first noticed.
        to_state: The state it moved to.
        score: Its score at the move.
        cause: What made it be scored again.
        conversation_id: The Conversation tagged, when that is the cause.
        now: When it moved.
        blocked_by: The ready check to record, for a move to or from ready.
        reason: Why a shared Pattern was confirmed or closed.

    Returns:
        The move.
    """
    return PatternMove(
        id=uuid4(),
        user_id=pattern.user_id,
        pattern_id=pattern.id,
        pattern_type_id=pattern.pattern_type_id,
        from_state=from_state,
        to_state=to_state,
        cause=cause,
        conversation_id=conversation_id,
        points=score.points,
        situations=score.situations,
        moved_at=now,
        blocked_by=blocked_by,
        reason=reason,
    )


def moved(
    pattern: CatalogPattern,
    score: PatternScore,
    bars: StateBars,
    cause: PatternMoveCause,
    conversation_id: UUID | None,
    now: datetime,
    planned: PlannedPatternMoves,
) -> CatalogPattern:
    """Move a Pattern to the state its score calls for, logging the move.

    Args:
        pattern: The Pattern, in its state now.
        score: Its score now.
        bars: The Admin-set bars.
        cause: What made it be scored again.
        conversation_id: The Conversation tagged, when that is the cause.
        now: When it is scored.
        planned: Where the move is logged.

    Returns:
        The Pattern in its new state; the same Pattern if it doesn't move.
    """
    state = state_for(pattern.state, score, bars)
    if state == pattern.state:
        return pattern
    planned.moves.append(
        logged_move(pattern, pattern.state, state, score, cause, conversation_id, now)
    )
    return replace(pattern, state=state, updated_at=now)


def plan_pattern_moves(
    user_id: UUID,
    patterns: Sequence[CatalogPattern],
    observations: Sequence[Observation],
    sign_strengths: Mapping[tuple[str, str], SignStrength],
    numbers: ScoringNumbers,
    bars: StateBars,
    today: date,
    now: datetime,
    cause: PatternMoveCause,
    conversation_id: UUID | None,
    never_again: frozenset[str] = frozenset(),
) -> PlannedPatternMoves:
    """Score a User's Patterns again from their Observations, and move them.

    Evidence against that only narrows a Pattern is left out of its score,
    as the ready gate leaves it out. A Pattern Type with Observations and
    no Pattern gets one, noticed, which may move on at once. A noticed,
    suspected or closed Pattern with no Observations left is deleted; one
    in any other state is kept, and so is one closed after it was shared,
    which never moves again.

    Args:
        user_id: The User.
        patterns: Their Patterns of Pattern Types now.
        observations: All their Observations.
        sign_strengths: Each sign's strength, by Pattern Type ID and sign ID.
        numbers: The Admin-set scoring numbers.
        bars: The Admin-set state bars.
        today: The User's day now, for fading.
        now: When it is scored.
        cause: What made it be scored again.
        conversation_id: The Conversation tagged, when that is the cause.
        never_again: The Pattern Types of the Patterns the User deleted
            after disagreeing or after they didn't hold up; none gets a
            Pattern again.

    Returns:
        The Patterns added, moved and deleted, and every move for the log.
    """
    by_type = observations_by_pattern_type(observations)
    existing = {pattern.pattern_type_id: pattern for pattern in patterns}
    planned = PlannedPatternMoves(
        added=[],
        changed=[],
        deleted_ids=[
            pattern.id
            for pattern in patterns
            if pattern.pattern_type_id not in by_type and is_moved_by_score(pattern)
        ],
        moves=[],
    )
    for pattern_type_id, its_observations in by_type.items():
        score = score_observations(
            without_narrowing(its_observations, numbers),
            sign_strengths,
            numbers,
            today,
        )
        pattern = existing.get(pattern_type_id)
        if pattern is None and pattern_type_id in never_again:
            continue
        if pattern is None:
            noticed = CatalogPattern(
                id=uuid4(),
                user_id=user_id,
                pattern_type_id=pattern_type_id,
                state=PatternState.NOTICED,
                started_at=now,
                updated_at=now,
            )
            planned.moves.append(
                logged_move(
                    noticed, None, noticed.state, score, cause, conversation_id, now
                )
            )
            planned.added.append(
                moved(noticed, score, bars, cause, conversation_id, now, planned)
            )
            continue
        if not is_moved_by_score(pattern):
            continue
        after = moved(pattern, score, bars, cause, conversation_id, now, planned)
        if after is not pattern:
            planned.changed.append(after)
    return planned


def scoring_numbers(settings: PlatformSettings) -> ScoringNumbers:
    """Read the Admin-set scoring numbers.

    Args:
        settings: The platform settings.

    Returns:
        The numbers a Pattern's Observations are counted with.
    """
    return ScoringNumbers(
        sign_points={
            SignStrength.WEAK: settings.get(PATTERN_WEAK_SIGN_POINTS),
            SignStrength.MODERATE: settings.get(PATTERN_MODERATE_SIGN_POINTS),
            SignStrength.STRONG: settings.get(PATTERN_STRONG_SIGN_POINTS),
        },
        evidence_percents={
            EvidenceKind.REAL_STORY: settings.get(PATTERN_REAL_STORY_PERCENT),
            EvidenceKind.REPORTED_HABIT: settings.get(PATTERN_REPORTED_HABIT_PERCENT),
            EvidenceKind.WHAT_IF_ANSWER: settings.get(PATTERN_WHAT_IF_PERCENT),
            EvidenceKind.OWN_OPINION: settings.get(PATTERN_OWN_OPINION_PERCENT),
        },
        unclear_percent=settings.get(PATTERN_UNCLEAR_PERCENT),
        half_life_days=settings.get(PATTERN_HALF_LIFE_DAYS),
        people_per_situation=settings.get(PATTERN_PEOPLE_PER_SITUATION),
        narrowing_stories_needed=settings.get(NARROWING_STORIES_NEEDED),
        narrowings_per_pattern=settings.get(NARROWINGS_PER_PATTERN),
    )


def state_bars(settings: PlatformSettings) -> StateBars:
    """Read the Admin-set bars a Pattern moves between states at.

    Args:
        settings: The platform settings.

    Returns:
        The bars.
    """
    return StateBars(
        suspected_situations=settings.get(PATTERN_SUSPECTED_SITUATIONS),
        suspected_points=settings.get(PATTERN_SUSPECTED_POINTS),
        closed_under_points=settings.get(PATTERN_CLOSED_UNDER_POINTS),
    )


class PatternScorer:
    """Scores a User's Patterns of Pattern Types again and moves them, with a log.

    Runs when a Conversation's Observations were tagged and when
    Observations are deleted. Nothing reaches a reply.
    """

    def __init__(
        self,
        repositories: Repositories,
        pattern_catalog: PatternCatalogService,
        clock: Clock,
    ) -> None:
        """Set up the scorer.

        Args:
            repositories: Where Observations, Patterns and their log are
                stored.
            pattern_catalog: Reads each sign's strength in the catalog now.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._pattern_catalog = pattern_catalog
        self._clock = clock

    def score(
        self,
        user: User,
        settings: PlatformSettings,
        cause: PatternMoveCause,
        conversation_id: UUID | None = None,
    ) -> None:
        """Score the User's Patterns again from all their Observations.

        The User is locked while their Observations and Patterns are read and
        the moves saved, so an Observation deleted meanwhile is never counted
        in a state saved after its deletion.

        Args:
            user: The User.
            settings: The platform settings, which may hold an Eval
                Variant's overrides.
            cause: What made them be scored again.
            conversation_id: The Conversation tagged, when that is the cause.
        """
        with self._repositories.transaction() as transaction:
            transaction.lock_user(user.id)
            self._score_locked(
                transaction.repositories, user, settings, cause, conversation_id
            )

    def _score_locked(
        self,
        repositories: Repositories,
        user: User,
        settings: PlatformSettings,
        cause: PatternMoveCause,
        conversation_id: UUID | None,
    ) -> None:
        """Score the User's Patterns again while they are locked.

        Args:
            repositories: The repositories, inside the locking transaction.
            user: The User.
            settings: The platform settings.
            cause: What made them be scored again.
            conversation_id: The Conversation tagged, when that is the cause.
        """
        observations = repositories.observations.list_for_user(user.id)
        patterns = repositories.patterns.list_of_pattern_types(user.id)
        if not observations and not patterns:
            return
        sign_strengths = sign_strengths_of(
            entry.pattern_type for entry in self._pattern_catalog.catalog()
        )
        now = self._clock.now()
        planned = plan_pattern_moves(
            user.id,
            patterns,
            observations,
            sign_strengths,
            scoring_numbers(settings),
            state_bars(settings),
            users_today(user.time_zone, now),
            now,
            cause,
            conversation_id,
            repositories.patterns.list_never_again(user.id),
        )
        repositories.patterns.save_moves(
            planned.added, planned.changed, planned.deleted_ids, planned.moves
        )
