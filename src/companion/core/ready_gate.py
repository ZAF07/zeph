import json
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime
from uuid import UUID

from companion.core.agenda import counter_tested, newest_first, observations_of
from companion.core.memory_retrieval import format_day
from companion.core.models import (
    CatalogPattern,
    ChatLine,
    ChatRole,
    ExplorationTry,
    ModelStep,
    NarrowingTag,
    Observation,
    ObservationDirection,
    PatternMove,
    PatternMoveCause,
    PatternNarrowing,
    PatternState,
    PatternType,
    PatternTypeStatus,
    PlatformSettings,
    ReadyCheck,
    SignStrength,
    User,
    UserSnapshot,
)
from companion.core.observations import (
    UserText,
    find_quoted_text,
    is_situational,
    users_own_texts,
)
from companion.core.pattern_catalog import PatternCatalogService
from companion.core.pattern_scoring import (
    PatternScore,
    ScoringNumbers,
    StateBars,
    logged_move,
    observation_points,
    score_observations,
    scoring_numbers,
    sign_strengths_of,
    state_bars,
    state_for,
)
from companion.core.platform_settings import (
    PATTERN_OTHER_SIDE_MODEL,
    PATTERN_OTHER_SIDE_PROMPT,
    PATTERN_OTHER_SIDE_THINKING,
    PATTERN_READY_AGAINST_UNDER_POINTS,
    PATTERN_READY_CONVERSATIONS,
    PATTERN_READY_POINTS,
    PATTERN_READY_SITUATIONS,
    PATTERN_RULED_OUT_TOPICS,
    PATTERN_SAFEGUARD_QUIET,
    thinking_to_use,
)
from companion.core.ports import Clock, Repositories
from companion.core.timing import users_today
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

STATES_THE_GATE_LOOKS_AT = frozenset({PatternState.SUSPECTED, PatternState.READY})


@dataclass(frozen=True)
class ReadyBars:
    """The Admin-set bars a Pattern must pass to be ready.

    Attributes:
        situations: The fewest situations it must show in.
        conversations: The fewest Conversations its evidence must come from.
        points: The lowest score.
        against_under_points: The evidence against must stay under this.
    """

    situations: int
    conversations: int
    points: int
    against_under_points: int


@dataclass(frozen=True)
class Weighing:
    """What an Observation's weight is worked out with, as scoring does.

    Attributes:
        sign_strengths: Each sign's strength, by Pattern Type ID and sign ID.
        numbers: The Admin-set scoring numbers.
        today: The User's day now, for fading.
    """

    sign_strengths: Mapping[tuple[str, str], SignStrength]
    numbers: ScoringNumbers
    today: date

    def score(self, observations: Sequence[Observation]) -> PatternScore:
        """Score some Observations as one Pattern's, as scoring does.

        Args:
            observations: The Observations.

        Returns:
            Their score and the situations they show in.
        """
        return score_observations(
            observations, self.sign_strengths, self.numbers, self.today
        )

    def points(self, observation: Observation) -> float:
        """Work out what one Observation is worth today.

        Args:
            observation: The Observation.

        Returns:
            Its points; negative when against.
        """
        return observation_points(
            observation, self.sign_strengths, self.numbers, self.today
        )


@dataclass(frozen=True)
class GateFacts:
    """What code found out about one Pattern, for the ready gate to judge.

    Attributes:
        score: Its score and situations, without the evidence against that
            only narrows it.
        clear_score: The same from its clear Observations alone.
        score_without_situational: The same without any Observation where
            anyone would act the same, by the Pattern Catalog now.
        conversations: How many Conversations its evidence for comes from.
        counter_tested: Whether a counter-test was asked and answered.
        points_against: How much evidence against it there is, as points
            above 0.
        exclusion_applies: Whether an exclusion of its Pattern Type applies
            to the User now.
        recent_safeguard_event: Whether a Safeguard Event happened within
            the Admin-set time.
        ruled_out_topic: Whether it rests on a ruled-out topic the User
            didn't raise.
        pattern_type_approved: Whether its Pattern Type is approved.
        narrowings: Where counter-tests showed it doesn't happen.
        unchecked_quotes: How many of its quotes are not word for word in
            the User's texts still kept; None while not looked at, which
            blocks.
        better_explanation: Whether the model arguing the other side found
            a better explanation; None while not asked or when the call
            failed, which blocks.
    """

    score: PatternScore
    clear_score: PatternScore
    score_without_situational: PatternScore
    conversations: int
    counter_tested: bool
    points_against: float
    exclusion_applies: bool
    recent_safeguard_event: bool
    ruled_out_topic: bool
    pattern_type_approved: bool
    narrowings: tuple[PatternNarrowing, ...] = ()
    unchecked_quotes: int | None = None
    better_explanation: bool | None = None


@dataclass(frozen=True)
class UserSafety:
    """What the "safe" check knows about a User now.

    Attributes:
        excluded_pattern_type_ids: The Pattern Types with an exclusion that
            applies to them now.
        recent_safeguard_event: Whether a Safeguard Event happened within
            the Admin-set time.
        ruled_out_topics: The Admin-set ruled-out topics, in lower case.
    """

    excluded_pattern_type_ids: frozenset[str]
    recent_safeguard_event: bool
    ruled_out_topics: frozenset[str]


def meets_bars(score: PatternScore, bars: ReadyBars) -> bool:
    """Say whether a score is in enough situations and past the score bar.

    Args:
        score: The score.
        bars: The Admin-set bars.

    Returns:
        True when both are met.
    """
    return score.situations >= bars.situations and score.points >= bars.points


def ready_check(facts: GateFacts, bars: ReadyBars) -> ReadyCheck | None:
    """Find the first of the ten ready checks a Pattern fails.

    The eight checks code can make from what is stored come first, the
    plainest reason first: too much evidence against is named before the
    low score it causes. The two that cost more (reading the kept texts
    again, and the model call that argues the other side) come last, so
    they are looked at only when every other check passes; while not
    looked at, they block.

    Args:
        facts: What code found out about the Pattern.
        bars: The Admin-set bars.

    Returns:
        The check that blocks it; None when it is ready.
    """
    if facts.score.situations < bars.situations:
        return ReadyCheck.SITUATIONS
    if facts.conversations < bars.conversations:
        return ReadyCheck.CONVERSATIONS
    if not facts.counter_tested or facts.points_against >= bars.against_under_points:
        return ReadyCheck.COUNTER_TEST
    if facts.score.points < bars.points:
        return ReadyCheck.SCORE
    if not meets_bars(facts.clear_score, bars):
        return ReadyCheck.CLEAR
    if not meets_bars(facts.score_without_situational, bars):
        return ReadyCheck.SITUATIONAL
    if facts.exclusion_applies or facts.recent_safeguard_event or facts.ruled_out_topic:
        return ReadyCheck.SAFE
    if not facts.pattern_type_approved:
        return ReadyCheck.ALLOWED
    if facts.unchecked_quotes is None or facts.unchecked_quotes > 0:
        return ReadyCheck.QUOTES
    if facts.better_explanation is None or facts.better_explanation:
        return ReadyCheck.OTHER_SIDE
    return None


def tag_value(observation: Observation, tag: NarrowingTag) -> str | None:
    """Read one of an Observation's situation tags.

    Args:
        observation: The Observation.
        tag: Which tag.

    Returns:
        Its value; None when the tag is empty.
    """
    value = (
        observation.tags.relationship
        if tag == NarrowingTag.RELATIONSHIP
        else observation.tags.power
    )
    return value.value if value else None


def narrowings_of(observations: Sequence[Observation]) -> tuple[PatternNarrowing, ...]:
    """Work out where a Pattern holds and where it was shown not to happen.

    A Pattern is narrowed by a tag (who the other person is, or where they
    stand) when its clear evidence against is all with other kinds of
    people than any of its clear evidence for: "with seniors, not with
    friends". Observations that carry no weight are left out.

    Args:
        observations: The Observations of the Pattern.

    Returns:
        One narrowing per tag that tells the two apart; none when the
        evidence against is with the same kinds of people, or there is none.
    """
    clear = [
        observation
        for observation in observations
        if not observation.unclear
        and not observation.situational
        and not observation.excluded
    ]
    narrowings = []
    for tag in NarrowingTag:
        holds_with = {
            tag_value(observation, tag)
            for observation in clear
            if observation.direction == ObservationDirection.FOR
        } - {None}
        against = [
            tag_value(observation, tag)
            for observation in clear
            if observation.direction == ObservationDirection.AGAINST
        ]
        not_with = set(against) - {None}
        if not holds_with or not not_with or None in against:
            continue
        if holds_with & not_with:
            continue
        narrowings.append(
            PatternNarrowing(
                tag=tag,
                holds_with=tuple(sorted(value for value in holds_with if value)),
                not_with=tuple(sorted(value for value in not_with if value)),
            )
        )
    return tuple(narrowings)


def narrows(observation: Observation, narrowings: Sequence[PatternNarrowing]) -> bool:
    """Say whether an Observation against only narrows its Pattern.

    Args:
        observation: The Observation.
        narrowings: The Pattern's narrowings.

    Returns:
        True when it is evidence against from a kind of situation the
        Pattern is narrowed away from.
    """
    return observation.direction == ObservationDirection.AGAINST and any(
        tag_value(observation, narrowing.tag) in narrowing.not_with
        for narrowing in narrowings
    )


def gate_facts(
    pattern_type: PatternType,
    observations: Sequence[Observation],
    tries: Sequence[ExplorationTry],
    safety: UserSafety,
    weighing: Weighing,
) -> GateFacts:
    """Find out what the ready gate needs to know about one Pattern.

    Args:
        pattern_type: Its Pattern Type, in the catalog now.
        observations: The Observations of the Pattern.
        tries: The tries of its Exploration.
        safety: What the "safe" check knows about the User now.
        weighing: What an Observation's weight is worked out with.

    Returns:
        The facts, with the quotes not looked at and the other side not
        asked yet.
    """
    narrowings = narrowings_of(observations)
    counted = [
        observation
        for observation in observations
        if not narrows(observation, narrowings)
    ]

    return GateFacts(
        score=weighing.score(counted),
        clear_score=weighing.score(
            [observation for observation in counted if not observation.unclear]
        ),
        score_without_situational=weighing.score(
            [
                observation
                for observation in counted
                if not is_situational(observation.tags, pattern_type.anyone_would_when)
            ]
        ),
        conversations=len(
            {
                observation.conversation_id
                for observation in counted
                if weighing.points(observation) > 0
            }
        ),
        counter_tested=counter_tested(observations, tries),
        points_against=-weighing.score(
            [
                observation
                for observation in counted
                if observation.direction == ObservationDirection.AGAINST
            ]
        ).points,
        exclusion_applies=pattern_type.id in safety.excluded_pattern_type_ids,
        recent_safeguard_event=safety.recent_safeguard_event,
        ruled_out_topic=any(
            observation.ruled_out_topic is not None
            and observation.ruled_out_topic.casefold() in safety.ruled_out_topics
            and not observation.raised_by_user
            for observation in observations
        ),
        pattern_type_approved=pattern_type.status == PatternTypeStatus.APPROVED,
        narrowings=narrowings,
    )


def count_unchecked_quotes(
    observations: Sequence[Observation],
    kept_texts: Mapping[UUID, Sequence[UserText]],
) -> int:
    """Count the quotes that are not word for word in the User's texts.

    Each quote was checked when it was tagged. It is checked again against
    the texts of its Conversation still kept; one whose Conversation has no
    texts left (Message Retention) can't be, and counts as checked.

    Args:
        observations: The Observations of the Pattern.
        kept_texts: What the User wrote in each Conversation, by its ID.

    Returns:
        How many quotes are not in their Conversation's texts.
    """
    return sum(
        1
        for observation in observations
        if kept_texts.get(observation.conversation_id)
        and find_quoted_text(observation.quote, kept_texts[observation.conversation_id])
        is None
    )


def read_other_side_answer(answer: str) -> bool | None:
    """Read whether the model arguing the other side found a better explanation.

    Text around the JSON object, such as a code fence, is ignored.

    Args:
        answer: The model's answer.

    Returns:
        True or False as it says in "better_explanation"; None if it can't
        be read.
    """
    start, end = answer.find("{"), answer.rfind("}")
    if start == -1 or end < start:
        return None
    try:
        parsed = json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    better = parsed.get("better_explanation")
    return better if isinstance(better, bool) else None


def describe_narrowing(narrowing: PatternNarrowing) -> str:
    """Write one narrowing in plain words.

    Args:
        narrowing: The narrowing.

    Returns:
        E.g. "power: shows with above, not with equal".
    """
    return (
        f"{narrowing.tag.value}: shows with {', '.join(narrowing.holds_with)}, "
        f"not with {', '.join(narrowing.not_with)}"
    )


def describe_pattern_to_argue(
    pattern_type: PatternType,
    observations: Sequence[Observation],
    narrowings: Sequence[PatternNarrowing],
    time_zone: str | None,
    now: datetime,
) -> str:
    """Write what the model arguing the other side is given.

    Args:
        pattern_type: The Pattern's Pattern Type.
        observations: The Observations of the Pattern.
        narrowings: Where it was shown not to happen.
        time_zone: The User's IANA time zone, for the days.
        now: The current time.

    Returns:
        Today's date, the Pattern Type with its look-alikes and what anyone
        would do, the narrowings and every Observation, newest first.
    """
    look_alikes = "\n".join(
        f"- {look_alike.name or look_alike.pattern_type_id}: {look_alike.tells_apart}"
        for look_alike in pattern_type.look_alikes
    )
    evidence = "\n".join(
        f"- {observation.day.isoformat()}, {observation.direction.value}"
        f"{', unclear' if observation.unclear else ''}, "
        f"{observation.evidence_kind.value}, about {observation.about}. "
        f"{observation.context} They said: “{observation.quote}”"
        for observation in newest_first(observations)
    )
    narrowed = "\n".join(describe_narrowing(narrowing) for narrowing in narrowings)
    return (
        f"Today: {format_day(now, time_zone)}\n\n"
        f"The Pattern Zeph is about to tell them:\n"
        f"{pattern_type.name}\n"
        f"What it is: {pattern_type.definition}\n"
        f"If: {pattern_type.if_situation}. Then: {pattern_type.then_behaviour}. "
        f"Function: {pattern_type.function}.\n\n"
        f"Look-alikes:\n{look_alikes or 'None.'}\n\n"
        f"What anyone would do: {pattern_type.anyone_would}\n\n"
        f"Where it was shown not to happen:\n{narrowed or 'Nowhere.'}\n\n"
        f"The evidence:\n{evidence}"
    )


def ready_bars(settings: PlatformSettings, pattern_type: PatternType) -> ReadyBars:
    """Read the bars one Pattern must pass to be ready.

    Args:
        settings: The platform settings.
        pattern_type: Its Pattern Type, which may ask for more situations
            than the Admin-set number.

    Returns:
        The bars.
    """
    return ReadyBars(
        situations=max(
            settings.get(PATTERN_READY_SITUATIONS),
            pattern_type.numbers.situations_needed,
        ),
        conversations=settings.get(PATTERN_READY_CONVERSATIONS),
        points=settings.get(PATTERN_READY_POINTS),
        against_under_points=settings.get(PATTERN_READY_AGAINST_UNDER_POINTS),
    )


@dataclass(frozen=True)
class JudgedPattern:
    """One Pattern as the gate judged it from what is stored.

    Attributes:
        pattern: The Pattern, as stored.
        pattern_type: Its Pattern Type.
        observations: Its Observations.
        facts: What code found out about it.
        bars: The bars it must pass.
        scored: Its score as scoring counts it, for the log.
    """

    pattern: CatalogPattern
    pattern_type: PatternType
    observations: list[Observation]
    facts: GateFacts
    bars: ReadyBars
    scored: PatternScore


@dataclass(frozen=True)
class LastChecks:
    """What the gate's last two checks found for one Pattern.

    Attributes:
        pattern_id: The Pattern.
        observation_ids: The Observations that were looked at.
        unchecked_quotes: How many of their quotes failed the check.
        better_explanation: What the other side found; None when it wasn't
            asked or the call failed.
        asked_now: Whether a model was asked just now, and not its earlier
            answer on the same evidence used.
    """

    pattern_id: UUID
    observation_ids: frozenset[UUID]
    unchecked_quotes: int
    better_explanation: bool | None
    asked_now: bool


@dataclass(frozen=True)
class Looked:
    """What one look at a User's suspected and ready Patterns found.

    Attributes:
        waiting: The suspected Patterns only the last two checks still
            block.
        ready: The ready Patterns that still pass every stored check.
    """

    waiting: list[JudgedPattern]
    ready: list[JudgedPattern]


def has_new_evidence(judged: JudgedPattern) -> bool:
    """Say whether a Pattern has evidence the other side hasn't argued yet.

    Args:
        judged: The Pattern.

    Returns:
        True when it was never argued, or an Observation of the Pattern
        was tagged since, so the same evidence is never argued twice.
    """
    asked_at = judged.pattern.other_side_asked_at
    return asked_at is None or any(
        observation.tagged_at > asked_at for observation in judged.observations
    )


def taken_back(
    pattern: CatalogPattern,
    blocked_by: ReadyCheck,
    scored: PatternScore,
    bars: StateBars,
    cause: PatternMoveCause,
    conversation_id: UUID | None,
    now: datetime,
) -> tuple[CatalogPattern, PatternMove]:
    """Move a ready Pattern that fails a check back to where its score puts it.

    Args:
        pattern: The ready Pattern.
        blocked_by: The check it now fails.
        scored: Its score as scoring counts it.
        bars: The Admin-set state bars.
        cause: What made the gate look.
        conversation_id: The Conversation tagged, when that is the cause.
        now: When it is moved.

    Returns:
        The Pattern, suspected, noticed or closed, and the move for the log
        with the check it failed.
    """
    state = state_for(PatternState.SUSPECTED, scored, bars)
    move = logged_move(
        pattern, pattern.state, state, scored, cause, conversation_id, now, blocked_by
    )
    return replace(pattern, state=state, updated_at=now, blocked_by=blocked_by), move


class ReadyKeeper:
    """Judges a User's suspected and ready Patterns from what is stored.

    No model call. It takes back a ready Pattern that no longer passes, at
    a Conversation end and at once when Observations are deleted or tagged
    again, and moves a Pattern to ready once the gate's last two checks
    are known.
    """

    def __init__(
        self,
        repositories: Repositories,
        pattern_catalog: PatternCatalogService,
        clock: Clock,
    ) -> None:
        """Set up the keeper.

        Args:
            repositories: Where Patterns, Observations and what the checks
                read are stored.
            pattern_catalog: Reads the Pattern Types in the catalog now.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._pattern_catalog = pattern_catalog
        self._clock = clock

    def look(
        self,
        user: User,
        settings: PlatformSettings,
        cause: PatternMoveCause,
        conversation_id: UUID | None = None,
    ) -> list[JudgedPattern]:
        """Judge the User's suspected and ready Patterns from what is stored.

        The User is locked, like scoring. A ready Pattern that fails a
        check, or whose Pattern Type left the catalog, is moved back to
        where its score puts it. Each Pattern's blocking check and
        narrowings are saved.

        Args:
            user: The User.
            settings: The platform settings.
            cause: What made their Patterns be scored again.
            conversation_id: The Conversation tagged, when that is the cause.

        Returns:
            The suspected Patterns only the last two checks still block,
            left out when the other side already found a better
            explanation of the same evidence.
        """
        return self._look(user, settings, cause, conversation_id).waiting

    def still_ready(
        self, user: User, settings: PlatformSettings
    ) -> list[JudgedPattern]:
        """Look again at a User's Patterns, and list those still ready.

        Used before a Pattern is shared, since a ready one is otherwise
        judged only when a Conversation ends. No model call.

        Args:
            user: The User.
            settings: The platform settings.

        Returns:
            Their ready Patterns that still pass every stored check, as
            judged now; one that no longer does was moved back.
        """
        return self._look(
            user, settings, PatternMoveCause.LOOKED_BEFORE_SHARING, None
        ).ready

    def _look(
        self,
        user: User,
        settings: PlatformSettings,
        cause: PatternMoveCause,
        conversation_id: UUID | None,
    ) -> Looked:
        """Judge the User's suspected and ready Patterns, and save what changed.

        Args:
            user: The User.
            settings: The platform settings.
            cause: What made their Patterns be looked at.
            conversation_id: The Conversation tagged, when that is the cause.

        Returns:
            The suspected Patterns waiting for the last two checks, and the
            Patterns still ready.
        """
        with self._repositories.transaction() as transaction:
            transaction.lock_user(user.id)
            repositories = transaction.repositories
            patterns = self._patterns_to_judge(repositories, user)
            all_judged = self._judge(repositories, user, settings, patterns)
            now = self._clock.now()
            bars = state_bars(settings)
            judged_ids = {judged.pattern.id for judged in all_judged}
            taken = [
                taken_back(
                    pattern,
                    ReadyCheck.ALLOWED,
                    PatternScore(points=0.0, situations=0),
                    bars,
                    cause,
                    conversation_id,
                    now,
                )
                for pattern in patterns
                if pattern.id not in judged_ids and pattern.state == PatternState.READY
            ]
            changed = [pattern for pattern, _ in taken]
            moves = [move for _, move in taken]
            waiting = []
            ready = []
            for judged in all_judged:
                pattern = replace(judged.pattern, narrowings=judged.facts.narrowings)
                if pattern.state == PatternState.READY:
                    blocked = ready_check(
                        replace(
                            judged.facts, unchecked_quotes=0, better_explanation=False
                        ),
                        judged.bars,
                    )
                    if blocked is not None:
                        pattern, move = taken_back(
                            pattern,
                            blocked,
                            judged.scored,
                            bars,
                            cause,
                            conversation_id,
                            now,
                        )
                        moves.append(move)
                    else:
                        ready.append(replace(judged, pattern=pattern))
                else:
                    blocked = ready_check(judged.facts, judged.bars)
                    if blocked == ReadyCheck.QUOTES:
                        if has_new_evidence(judged) or not (
                            pattern.other_side_found_better
                        ):
                            waiting.append(judged)
                            continue
                        blocked = ReadyCheck.OTHER_SIDE
                    pattern = replace(pattern, blocked_by=blocked)
                if pattern != judged.pattern:
                    changed.append(pattern)
            repositories.patterns.save_moves([], changed, [], moves)
            return Looked(waiting=waiting, ready=ready)

    def settle(
        self,
        user: User,
        settings: PlatformSettings,
        conversation_id: UUID,
        last_checks: LastChecks,
    ) -> None:
        """Judge one Pattern again with the last two checks, and move it.

        The User is locked and everything read again, so evidence deleted
        while the model was asked is never counted. If its Observations are
        no longer the ones looked at, the last two checks count as not
        made, and it waits for the next Conversation end.

        Args:
            user: The User.
            settings: The platform settings.
            conversation_id: The ended Conversation.
            last_checks: What the last two checks found.
        """
        with self._repositories.transaction() as transaction:
            transaction.lock_user(user.id)
            repositories = transaction.repositories
            patterns = [
                pattern
                for pattern in self._patterns_to_judge(repositories, user)
                if pattern.id == last_checks.pattern_id
                and pattern.state == PatternState.SUSPECTED
            ]
            all_judged = self._judge(repositories, user, settings, patterns)
            if not all_judged:
                return
            [judged] = all_judged
            same_evidence = last_checks.observation_ids == frozenset(
                observation.id for observation in judged.observations
            )
            better = last_checks.better_explanation if same_evidence else None
            now = self._clock.now()
            blocked = ready_check(
                replace(
                    judged.facts,
                    unchecked_quotes=(
                        last_checks.unchecked_quotes if same_evidence else None
                    ),
                    better_explanation=better,
                ),
                judged.bars,
            )
            pattern = replace(
                judged.pattern, blocked_by=blocked, narrowings=judged.facts.narrowings
            )
            if last_checks.asked_now and better is not None:
                pattern = replace(
                    pattern, other_side_asked_at=now, other_side_found_better=better
                )
            if blocked is not None:
                repositories.patterns.save_moves([], [pattern], [], [])
                return
            move = logged_move(
                pattern,
                pattern.state,
                PatternState.READY,
                judged.scored,
                PatternMoveCause.CONVERSATION_TAGGED,
                conversation_id,
                now,
                judged.pattern.blocked_by,
            )
            repositories.patterns.save_moves(
                [],
                [replace(pattern, state=PatternState.READY, updated_at=now)],
                [],
                [move],
            )

    def _patterns_to_judge(
        self, repositories: Repositories, user: User
    ) -> list[CatalogPattern]:
        """List the User's Patterns the gate looks at.

        Args:
            repositories: The repositories, inside the locking transaction.
            user: The User.

        Returns:
            Their suspected and ready Patterns of Pattern Types.
        """
        return [
            pattern
            for pattern in repositories.patterns.list_of_pattern_types(user.id)
            if pattern.state in STATES_THE_GATE_LOOKS_AT
        ]

    def _judge(
        self,
        repositories: Repositories,
        user: User,
        settings: PlatformSettings,
        patterns: Sequence[CatalogPattern],
    ) -> list[JudgedPattern]:
        """Find out the facts about some of a User's Patterns.

        Args:
            repositories: The repositories, inside the locking transaction.
            user: The User.
            settings: The platform settings.
            patterns: Their Patterns to judge.

        Returns:
            Each of those whose Pattern Type is in the catalog now, judged;
            with no Patterns, nothing more is read.
        """
        if not patterns:
            return []
        catalog = self._pattern_catalog.catalog()
        pattern_types = {entry.pattern_type.id: entry.pattern_type for entry in catalog}
        now = self._clock.now()
        weighing = Weighing(
            sign_strengths=sign_strengths_of(pattern_types.values()),
            numbers=scoring_numbers(settings),
            today=users_today(user.time_zone, now),
        )
        safety = UserSafety(
            excluded_pattern_type_ids=frozenset(
                flag.pattern_type_id
                for flag in repositories.observations.list_exclusion_flags(user.id)
            ),
            recent_safeguard_event=repositories.safeguard_events.happened_since(
                user.id, now - settings.get(PATTERN_SAFEGUARD_QUIET)
            ),
            ruled_out_topics=frozenset(
                topic.casefold() for topic in settings.get(PATTERN_RULED_OUT_TOPICS)
            ),
        )
        observations = repositories.observations.list_for_user(user.id)
        tries = repositories.explorations.list_tries(user.id)
        exploration_ids = {
            exploration.pattern_id: exploration.id
            for exploration in repositories.explorations.list_for_user(user.id)
        }
        all_judged = []
        for pattern in patterns:
            pattern_type = pattern_types.get(pattern.pattern_type_id)
            if pattern_type is None:
                continue
            its_observations = observations_of(pattern_type.id, observations)
            its_tries = [
                attempt
                for attempt in tries
                if attempt.exploration_id == exploration_ids.get(pattern.id)
            ]
            all_judged.append(
                JudgedPattern(
                    pattern=pattern,
                    pattern_type=pattern_type,
                    observations=its_observations,
                    facts=gate_facts(
                        pattern_type, its_observations, its_tries, safety, weighing
                    ),
                    bars=ready_bars(settings, pattern_type),
                    scored=weighing.score(its_observations),
                )
            )
        return all_judged


class ReadyGate:
    """Decides when a User's Pattern may be shared.

    Code makes every check. One model call argues the other side for a
    Pattern that passed all the others, and can only block. Nothing is
    shared here: a ready Pattern waits.
    """

    def __init__(
        self,
        repositories: Repositories,
        ready_keeper: ReadyKeeper,
        chat_model: UsageRecordingChatModel,
        clock: Clock,
    ) -> None:
        """Set up the gate.

        Args:
            repositories: Where the Conversations' messages are stored.
            ready_keeper: Judges the Patterns from what is stored and moves
                them.
            chat_model: Argues the other side and records the tokens used.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._ready_keeper = ready_keeper
        self._chat_model = chat_model
        self._clock = clock

    def check(self, snapshot: UserSnapshot, conversation_id: UUID) -> None:
        """Run the gate when a Conversation ends, after scoring.

        A ready Pattern that now fails a check goes back. A suspected one
        that passes every stored check has its quotes read again and the
        other side argued, outside the lock, and is then judged once more
        under it before it becomes ready. The other side is asked only
        about evidence it hasn't argued yet; its earlier answer stands for
        the same evidence.

        Args:
            snapshot: The User whose Conversation it was.
            conversation_id: The ended Conversation.
        """
        user, settings = snapshot.user, snapshot.settings
        cause = PatternMoveCause.CONVERSATION_TAGGED
        for judged in self._ready_keeper.look(user, settings, cause, conversation_id):
            unchecked = self._count_unchecked_quotes(judged.observations)
            ask_now = not unchecked and has_new_evidence(judged)
            better = (
                self._argue_other_side(snapshot, judged)
                if ask_now
                else judged.pattern.other_side_found_better
            )
            self._ready_keeper.settle(
                user,
                settings,
                conversation_id,
                LastChecks(
                    pattern_id=judged.pattern.id,
                    observation_ids=frozenset(
                        observation.id for observation in judged.observations
                    ),
                    unchecked_quotes=unchecked,
                    better_explanation=None if unchecked else better,
                    asked_now=ask_now,
                ),
            )

    def _count_unchecked_quotes(self, observations: Sequence[Observation]) -> int:
        """Read a Pattern's quotes again against the texts still kept.

        Args:
            observations: The Observations of the Pattern.

        Returns:
            How many quotes are not word for word in their Conversation's
            texts.
        """
        kept_texts = {
            conversation_id: users_own_texts(
                self._repositories.conversations.list_messages(conversation_id)
            )
            for conversation_id in {
                observation.conversation_id for observation in observations
            }
        }
        return count_unchecked_quotes(observations, kept_texts)

    def _argue_other_side(
        self, snapshot: UserSnapshot, judged: JudgedPattern
    ) -> bool | None:
        """Ask a model for a better explanation of a Pattern's evidence.

        An unreadable answer is asked once more. A failed call is logged
        and blocks, so the rest of the Conversation end goes on.

        Args:
            snapshot: The User whose Pattern it is.
            judged: The Pattern, which passed every other check.

        Returns:
            Whether it found a better explanation; None when the call
            failed or both answers were unreadable.
        """
        settings = snapshot.settings
        description = describe_pattern_to_argue(
            judged.pattern_type,
            judged.observations,
            judged.facts.narrowings,
            snapshot.user.time_zone,
            self._clock.now(),
        )
        try:
            for _ in range(2):
                better = read_other_side_answer(
                    self._chat_model.generate(
                        snapshot=snapshot,
                        step=ModelStep.PATTERN_OTHER_SIDE,
                        model=settings.get(PATTERN_OTHER_SIDE_MODEL),
                        thinking=thinking_to_use(
                            settings,
                            PATTERN_OTHER_SIDE_MODEL,
                            PATTERN_OTHER_SIDE_THINKING,
                        ),
                        instructions=settings.get(PATTERN_OTHER_SIDE_PROMPT),
                        history=[ChatLine(role=ChatRole.USER, text=description)],
                    )
                )
                if better is not None:
                    return better
        except Exception:
            logger.exception("Could not argue the other side of a Pattern")
            return None
        logger.warning("Arguing the other side gave no readable answer")
        return None
