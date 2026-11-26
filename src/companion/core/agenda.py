from collections.abc import Iterable, Mapping, Sequence, Set
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from companion.core.condition_coverage import (
    VALUES_TO_LEARN,
    condition_value,
    coverage_of,
    is_clear,
    missing_condition,
)
from companion.core.memory_retrieval import format_day
from companion.core.models import (
    AgendaChanges,
    Audience,
    CatalogPattern,
    CatalogPatternType,
    Condition,
    Curiosity,
    CuriosityAim,
    CuriositySensitivity,
    CuriosityState,
    Exploration,
    ExplorationApproach,
    ExplorationNeed,
    ExplorationState,
    ExplorationTry,
    Feature,
    Observation,
    ObservationDirection,
    PatternState,
    PatternType,
    PlatformSettings,
    Power,
    Relationship,
    SituationSetting,
    Stakes,
    Stance,
    ThoughtExperiment,
    ThreadReaction,
    TryOutcome,
    UserSnapshot,
)
from companion.core.pattern_catalog import PatternCatalogService
from companion.core.pattern_scoring import (
    PatternScore,
    observations_by_pattern_type,
    score_observations,
    scoring_numbers,
    sign_strengths_of,
    without_narrowing,
)
from companion.core.platform_settings import (
    AGENDA_SIZE,
    CONDITION_ONE_SIDED_STORIES,
    EXPLORATION_REST_AFTER_TRIES,
    EXPLORATION_WAIT,
    THOUGHT_EXPERIMENTS_PER_PATTERN_PER_WEEK,
)
from companion.core.ports import Clock, Repositories
from companion.core.starter_thought_experiments import put_as_starters
from companion.core.thought_experiments import (
    pick_thought_experiment,
    put_to_user,
    thought_experiment_question,
    thought_experiments_this_week,
)
from companion.core.timing import users_today

APPROACHES = (
    ExplorationApproach.STORY_FOLLOW_UP,
    ExplorationApproach.WOULD_IT_DIFFER,
    ExplorationApproach.THOUGHT_EXPERIMENT,
    ExplorationApproach.NOTICE_THIS_WEEK,
)
CONDITION_APPROACHES = (
    ExplorationApproach.STORY_FOLLOW_UP,
    ExplorationApproach.WOULD_IT_DIFFER,
    ExplorationApproach.NOTICE_THIS_WEEK,
)
STATE_APPROACHES = (
    ExplorationApproach.STORY_FOLLOW_UP,
    ExplorationApproach.NOTICE_THIS_WEEK,
)
NOTHING_USEFUL = frozenset({TryOutcome.VAGUE, TryOutcome.BRUSHED_OFF})
CONDITION_WORDS: Mapping[tuple[Condition, str], tuple[str, str]] = {
    (Condition.AUDIENCE, Audience.ONE_TO_ONE.value): (
        "one-to-one, with just one other person",
        "it had been just the two of them",
    ),
    (Condition.AUDIENCE, Audience.GROUP.value): (
        "in a group",
        "it had been in a group",
    ),
    (Condition.AUDIENCE, Audience.IN_FRONT_OF_OTHERS.value): (
        "with other people watching",
        "other people had been watching",
    ),
    (Condition.STAKES, Stakes.LOW.value): (
        "with little riding on it",
        "less had been riding on it",
    ),
    (Condition.STAKES, Stakes.HIGH.value): (
        "with a lot riding on it",
        "more had been riding on it",
    ),
    (Condition.RELATIONSHIP, Relationship.FRIEND.value): (
        "with a friend",
        "it had been with a friend",
    ),
    (Condition.RELATIONSHIP, Relationship.COLLEAGUE.value): (
        "with a colleague",
        "it had been with a colleague",
    ),
    (Condition.RELATIONSHIP, Relationship.FAMILY.value): (
        "with family",
        "it had been with family",
    ),
    (Condition.RELATIONSHIP, Relationship.PARTNER.value): (
        "with a partner",
        "it had been with a partner",
    ),
    (Condition.POWER, Power.ABOVE.value): (
        "with someone above them",
        "it had been with someone above them",
    ),
    (Condition.POWER, Power.EQUAL.value): (
        "with someone on their own level",
        "it had been with someone on their own level",
    ),
    (Condition.POWER, Power.BELOW.value): (
        "with someone who looks up to them or answers to them",
        "it had been with someone who looks up to them or answers to them",
    ),
    (Condition.STANCE, Stance.SUPPORTIVE.value): (
        "with the other person on their side",
        "the other person had been on their side",
    ),
    (Condition.STANCE, Stance.NEUTRAL.value): (
        "with the other person neither for nor against them",
        "the other person had been neither for nor against them",
    ),
    (Condition.STANCE, Stance.HOSTILE.value): (
        "with the other person against them",
        "the other person had been against them",
    ),
    (Condition.SETTING, SituationSetting.HOME.value): (
        "at home",
        "it had happened at home",
    ),
    (Condition.SETTING, SituationSetting.WORK.value): (
        "at work",
        "it had happened at work",
    ),
    (Condition.SETTING, SituationSetting.SOCIAL.value): (
        "out with friends",
        "it had happened out with friends",
    ),
}
STATE_OPENLY = (
    "Ask openly, and name no mood or state yourself: let them say how they were."
)
OTHER_PEOPLE = (
    (Relationship.FRIEND, "a friend"),
    (Relationship.COLLEAGUE, "a colleague"),
    (Relationship.FAMILY, "family"),
    (Relationship.PARTNER, "a partner"),
)
APPROACH_WORDS = {
    ExplorationApproach.STORY_FOLLOW_UP: "story follow-up",
    ExplorationApproach.WOULD_IT_DIFFER: "would it have gone differently",
    ExplorationApproach.THOUGHT_EXPERIMENT: "a Thought Experiment",
    ExplorationApproach.NOTICE_THIS_WEEK: "notice this week",
}
OUTCOME_WORDS = {
    TryOutcome.USEFUL: "useful",
    TryOutcome.VAGUE: "vague",
    TryOutcome.BRUSHED_OFF: "brushed off",
}


@dataclass(frozen=True)
class OpenNeed:
    """Something an Exploration still needs to learn, and what it aims at.

    Attributes:
        need: The kind of need.
        observation: The Observation it is about: the unclear one, or the
            story a counter-test or a missing Condition starts from; None
            otherwise, and always None for the state going in.
        condition: The Condition whose stories are one-sided; None otherwise.
        value: The value of it not seen yet, which is what to learn; None
            otherwise.
    """

    need: ExplorationNeed
    observation: Observation | None = None
    condition: Condition | None = None
    value: str | None = None


@dataclass(frozen=True)
class AgendaNumbers:
    """The Admin-set numbers the Agenda is kept with.

    Attributes:
        size: The most Explorations active at once.
        wait: How long to wait after a try with nothing.
        rest_after_tries: Tries with nothing in a row before resting.
        thought_experiments_per_week: The most Thought Experiments asked for
            one Pattern in 7 days.
        one_sided_stories: Clear stories for a Pattern sharing one value of
            a Condition before another value is worth asking about.
    """

    size: int
    wait: timedelta
    rest_after_tries: int
    thought_experiments_per_week: int
    one_sided_stories: int


@dataclass(frozen=True)
class AgendaInput:
    """Everything the Agenda is kept from, for one User.

    Attributes:
        user_id: The User.
        patterns: Their Patterns of Pattern Types.
        observations: All their Observations.
        scores: Each Pattern's score now, by Pattern Type ID.
        pattern_types: The Pattern Types in the catalog now, by ID.
        explorations: Their Explorations.
        tries: Every try of theirs.
        aimed: Every aimed Curiosity of theirs, in any state.
        conversation_id: The Conversation that just ended.
        now: When the Agenda is kept.
        time_zone: The User's IANA time zone.
        thought_experiments: Every Thought Experiment, archived ones too.
        starters_put: The Thought Experiments already put to them as
            starters, or waiting to be.
    """

    user_id: UUID
    patterns: Sequence[CatalogPattern]
    observations: Sequence[Observation]
    scores: Mapping[str, PatternScore]
    pattern_types: Mapping[str, PatternType]
    explorations: Sequence[Exploration]
    tries: Sequence[ExplorationTry]
    aimed: Sequence[Curiosity]
    conversation_id: UUID
    now: datetime
    time_zone: str | None
    thought_experiments: Sequence[ThoughtExperiment] = ()
    starters_put: Set[UUID] = frozenset()


def observations_of(
    pattern_type_id: str, observations: Sequence[Observation]
) -> list[Observation]:
    """Keep the Observations that count toward one Pattern Type.

    Args:
        pattern_type_id: The Pattern Type's ID.
        observations: The User's Observations.

    Returns:
        Those naming it, first or second.
    """
    return [
        observation
        for observation in observations
        if pattern_type_id
        in (observation.pattern_type_id, observation.second_pattern_type_id)
    ]


def newest_first(observations: Sequence[Observation]) -> list[Observation]:
    """Order Observations by the day they were said, newest first.

    Args:
        observations: The Observations.

    Returns:
        Them, newest day first, then newest tagged.
    """
    return sorted(
        observations,
        key=lambda observation: (observation.day, observation.tagged_at),
        reverse=True,
    )


def counter_tested(
    observations: Sequence[Observation], tries: Sequence[ExplorationTry]
) -> bool:
    """Say whether a Pattern was tested against itself.

    Args:
        observations: The Observations of the Pattern.
        tries: The tries of its Exploration.

    Returns:
        True when an Observation against came, or a counter-test try came
        back useful.
    """
    return any(
        observation.direction == ObservationDirection.AGAINST
        for observation in observations
    ) or any(
        attempt.need == ExplorationNeed.COUNTER_TEST
        and attempt.outcome == TryOutcome.USEFUL
        for attempt in tries
    )


def closed_condition_values(
    tries: Sequence[ExplorationTry],
) -> set[tuple[Condition, str]]:
    """Name the Condition values an Exploration already learned about.

    Args:
        tries: Its tries.

    Returns:
        Each Condition and value a missing-Condition try came back useful
        for. Such a value is never asked about again. The state going in
        is asked about with one open question whatever the value, so a
        useful try closes every value of it.
    """
    closed: set[tuple[Condition, str]] = set()
    for attempt in tries:
        if (
            attempt.need != ExplorationNeed.MISSING_CONDITION
            or attempt.outcome != TryOutcome.USEFUL
            or attempt.condition is None
            or attempt.condition_value is None
        ):
            continue
        if attempt.condition == Condition.STATE_GOING_IN:
            closed.update(
                (attempt.condition, value)
                for value in VALUES_TO_LEARN[attempt.condition]
            )
        closed.add((attempt.condition, attempt.condition_value))
    return closed


def missing_condition_need(
    observations: Sequence[Observation],
    tries: Sequence[ExplorationTry],
    one_sided_stories: int,
) -> OpenNeed | None:
    """Work out the one Condition value an Exploration should ask about.

    Args:
        observations: The Observations of its Pattern.
        tries: Its tries.
        one_sided_stories: The Admin-set number of stories to be one-sided.

    Returns:
        The need, with the newest clear story for the Pattern that says the
        Condition to start from (none for the state going in, which is
        never asked about from a story that already says it); None when no
        Condition is one-sided with a value left to learn.
    """
    missing = missing_condition(
        coverage_of(observations), one_sided_stories, closed_condition_values(tries)
    )
    if missing is None:
        return None
    stories = [
        observation
        for observation in newest_first(observations)
        if is_clear(observation)
        and observation.direction == ObservationDirection.FOR
        and condition_value(observation, missing.condition) is not None
    ]
    return OpenNeed(
        ExplorationNeed.MISSING_CONDITION,
        observation=(
            None if missing.condition == Condition.STATE_GOING_IN else stories[0]
        ),
        condition=missing.condition,
        value=missing.value,
    )


def open_needs(
    observations: Sequence[Observation],
    tries: Sequence[ExplorationTry],
    one_sided_stories: int,
) -> list[OpenNeed]:
    """Work out what an Exploration still needs to learn from its Observations.

    Unclear stories come first, newest first; then a counter-test, open
    until an Observation against comes or a counter-test try was useful;
    then a missing Condition: one value not seen yet of the Condition the
    stories so far are most one-sided on.

    Args:
        observations: The Observations of its Pattern.
        tries: Its tries.
        one_sided_stories: The Admin-set number of stories to be one-sided.

    Returns:
        The open needs, in the order they are worked on.
    """
    needs = [
        OpenNeed(ExplorationNeed.UNCLEAR, observation=observation)
        for observation in newest_first(observations)
        if observation.unclear
    ]
    if not counter_tested(observations, tries):
        stories = [
            observation
            for observation in newest_first(observations)
            if not observation.unclear
        ]
        needs.append(
            OpenNeed(
                ExplorationNeed.COUNTER_TEST,
                observation=stories[0] if stories else None,
            )
        )
    missing = missing_condition_need(observations, tries, one_sided_stories)
    if missing is not None:
        needs.append(missing)
    return needs


def aims_at(attempt: ExplorationTry, need: OpenNeed) -> bool:
    """Say whether a try aimed at this very need.

    A counter-test is one need whichever story it starts from, and so is a
    missing Condition's value.

    Args:
        attempt: The try.
        need: The open need.

    Returns:
        True when it has the same kind and the same unclear Observation, or
        the same Condition and value.
    """
    if attempt.need != need.need:
        return False
    if need.need == ExplorationNeed.COUNTER_TEST:
        return True
    if need.need == ExplorationNeed.MISSING_CONDITION:
        return (attempt.condition, attempt.condition_value) == (
            need.condition,
            need.value,
        )
    return attempt.observation_id == (need.observation.id if need.observation else None)


def tries_of(
    exploration: Exploration, tries: Sequence[ExplorationTry]
) -> list[ExplorationTry]:
    """Keep one Exploration's tries.

    Args:
        exploration: The Exploration.
        tries: Every try.

    Returns:
        Its tries, in the order given.
    """
    return [attempt for attempt in tries if attempt.exploration_id == exploration.id]


def asked_in_order(
    tries: Iterable[ExplorationTry], asked_at: Mapping[UUID, datetime]
) -> list[ExplorationTry]:
    """Keep the tries that were asked, in the order they were asked.

    Args:
        tries: The tries.
        asked_at: When each asked try's Curiosity was asked, by Curiosity ID.

    Returns:
        The asked ones, first asked first.
    """
    return sorted(
        (attempt for attempt in tries if attempt.curiosity_id in asked_at),
        key=lambda attempt: asked_at[attempt.curiosity_id],
    )


def approaches_for(need: OpenNeed) -> tuple[ExplorationApproach, ...]:
    """Name the Approaches a need may be asked by, least pushy first.

    Args:
        need: The open need.

    Returns:
        All four for an unclear story or a counter-test. A missing Condition
        never gets a Thought Experiment, and the state going in never a
        "would it have gone differently if" either, since that would name a
        state before the User has.
    """
    if need.need != ExplorationNeed.MISSING_CONDITION:
        return APPROACHES
    if need.condition == Condition.STATE_GOING_IN:
        return STATE_APPROACHES
    return CONDITION_APPROACHES


def approach_after(
    approach: ExplorationApproach, need: OpenNeed
) -> ExplorationApproach:
    """Name the Approach that comes after another, round again after the last.

    Args:
        approach: The Approach.
        need: The need it asks about.

    Returns:
        The next, a little pushier, Approach the need may be asked by.
    """
    allowed = approaches_for(need)
    later = APPROACHES[APPROACHES.index(approach) + 1 :]
    return next((other for other in later if other in allowed), allowed[0])


def next_approach(
    need: OpenNeed,
    tries: Sequence[ExplorationTry],
    asked_at: Mapping[UUID, datetime],
) -> ExplorationApproach:
    """Pick how to ask about a need next, least pushy first.

    A try at the same need that came back with nothing moves on to the
    next Approach, round again after the last, so the next try is a
    different Approach; after a useful one the same Approach is used again.

    Args:
        need: The open need.
        tries: The Exploration's tries.
        asked_at: When each asked try's Curiosity was asked, by Curiosity ID.

    Returns:
        The Approach to use next; the first if none was tried at this need.
    """
    asked = [
        attempt for attempt in asked_in_order(tries, asked_at) if aims_at(attempt, need)
    ]
    if not asked:
        return approaches_for(need)[0]
    last = asked[-1]
    if last.outcome not in NOTHING_USEFUL:
        return last.approach
    return approach_after(last.approach, need)


def try_outcome(
    reaction: ThreadReaction | None, settled: bool, new_evidence: bool
) -> TryOutcome:
    """Decide how a try came back from how the User took it.

    Args:
        reaction: How the User took the aimed Curiosity; None if not known.
        settled: Whether the unclear Observation it aimed at is now clear.
        new_evidence: Whether the Conversation it was asked in brought a new
            Observation for its Pattern.

    Returns:
        Brushed off when brushed off or asked to drop; useful when it
        settled the unclear story, or when engaged and it brought new
        evidence; vague otherwise.
    """
    if reaction in (ThreadReaction.BRUSHED_OFF, ThreadReaction.ASKED_TO_DROP):
        return TryOutcome.BRUSHED_OFF
    if settled or (reaction == ThreadReaction.ENGAGED and new_evidence):
        return TryOutcome.USEFUL
    return TryOutcome.VAGUE


def tries_with_nothing(
    exploration: Exploration,
    tries: Sequence[ExplorationTry],
    asked_at: Mapping[UUID, datetime],
) -> int:
    """Count the tries in a row with nothing useful, newest back.

    Tries asked before the Exploration last woke don't count.

    Args:
        exploration: The Exploration.
        tries: Its judged tries.
        asked_at: When each asked try's Curiosity was asked, by Curiosity ID.

    Returns:
        How many of its newest tries in a row came back vague or brushed off.
    """
    judged = [
        attempt
        for attempt in asked_in_order(tries, asked_at)
        if attempt.outcome is not None
        and (
            exploration.woke_at is None
            or asked_at[attempt.curiosity_id] > exploration.woke_at
        )
    ]
    count = 0
    for attempt in reversed(judged):
        if attempt.outcome not in NOTHING_USEFUL:
            break
        count += 1
    return count


def rank_explorations(
    explorations: Sequence[Exploration], scores: Mapping[str, PatternScore]
) -> list[Exploration]:
    """Rank Explorations for a place on the Agenda.

    Args:
        explorations: The Explorations that may have a place.
        scores: Each Pattern's score, by Pattern Type ID.

    Returns:
        Them, highest score first, then oldest first.
    """
    return sorted(
        explorations,
        key=lambda exploration: (
            -scores[exploration.pattern_type_id].points
            if exploration.pattern_type_id in scores
            else 0.0,
            exploration.created_at,
        ),
    )


def lowered(text: str) -> str:
    """Start a phrase with a small letter, to sit inside a sentence.

    Args:
        text: The phrase, e.g. "Disagreement with a valued other".

    Returns:
        It with its first letter small.
    """
    return text[:1].lower() + text[1:]


def other_person(observation: Observation) -> str:
    """Pick someone else in their life to ask about, unlike the one in a story.

    Args:
        observation: The story.

    Returns:
        E.g. "a colleague", never who the story was with.
    """
    return next(
        words
        for relationship, words in OTHER_PEOPLE
        if relationship != observation.tags.relationship
    )


def describe_story(observation: Observation) -> str:
    """Point at a story the User told, without their words or a Pattern name.

    Args:
        observation: The Observation.

    Returns:
        E.g. "what they told you about their sister on 3 Nov 2026 (Mei asked
        for help moving; they said yes though worn out)".
    """
    day = f"{observation.day.day} {observation.day:%b %Y}"
    return (
        f"what they told you about {observation.about} on {day} ({observation.context})"
    )


def condition_question(
    need: OpenNeed, approach: ExplorationApproach, moment: str
) -> tuple[str, str]:
    """Write the question and why for a missing Condition's value.

    The state going in is asked about openly: no state is ever named.

    Args:
        need: The missing-Condition need.
        approach: Its Approach.
        moment: The Pattern Type's situation, as "a moment like this: …".

    Returns:
        The question, as a plain instruction, and why Zeph wonders.
    """
    if need.condition is None or need.value is None:
        raise ValueError("A missing-Condition need names a Condition and a value")
    if need.condition == Condition.STATE_GOING_IN:
        why = "Zeph doesn't know yet how they are doing going into these moments."
        if approach == ExplorationApproach.NOTICE_THIS_WEEK:
            return (
                f"Ask them, lightly, to notice this week, in {moment}, how they "
                f"were doing going into it. {STATE_OPENLY}",
                why,
            )
        return (
            f"Ask about a recent time, {moment}, and how they were doing going "
            f"into it. {STATE_OPENLY}",
            why,
        )
    where, if_it_had = CONDITION_WORDS[(need.condition, need.value)]
    why = f"Zeph hasn't heard how this goes for them {where} yet."
    if approach == ExplorationApproach.STORY_FOLLOW_UP:
        return (
            f"Ask about a recent time {where}, {moment}. What happened, and "
            "what did they do?",
            why,
        )
    if approach == ExplorationApproach.WOULD_IT_DIFFER and need.observation:
        return (
            f"Go back to {describe_story(need.observation)}. Ask whether it "
            f"would have gone differently if {if_it_had}.",
            why,
        )
    return (
        f"Ask them, lightly, to notice this week whether it's the same {where}, "
        f"in {moment}, and what they do then.",
        why,
    )


def aimed_question(
    need: OpenNeed, approach: ExplorationApproach, pattern_type: PatternType
) -> tuple[str, str]:
    """Write an aimed Curiosity's question and why, for the model to word.

    Args:
        need: The need it aims at.
        approach: Its Approach: how it asks.
        pattern_type: The Pattern's Pattern Type, for its situation.

    Returns:
        The question, as a plain instruction, and why Zeph wonders. Neither
        names the Pattern.
    """
    moment = f"a moment like this: {lowered(pattern_type.if_situation)}"
    story = describe_story(need.observation) if need.observation else ""
    if need.need == ExplorationNeed.UNCLEAR and need.observation is not None:
        why = "What drove it isn't clear yet, and how they answer would tell."
        if approach == ExplorationApproach.STORY_FOLLOW_UP:
            return (
                f"Go back to {story}. Ask what they did next, and what they "
                "were most hoping would or wouldn't happen then.",
                why,
            )
        if approach == ExplorationApproach.WOULD_IT_DIFFER:
            return (
                f"Go back to {story}. Ask whether it would have gone differently "
                f"with someone else, like {other_person(need.observation)}.",
                why,
            )
        return (
            f"Ask them, lightly, to notice this week {moment}: what goes "
            "through their mind first, and what they do.",
            why,
        )
    if need.need == ExplorationNeed.MISSING_CONDITION:
        return condition_question(need, approach, moment)
    why = "To learn when it doesn't happen, not only when it does."
    if approach == ExplorationApproach.STORY_FOLLOW_UP:
        if need.observation is not None:
            return (
                f"Go back to {story}. Ask whether there was a time in a similar "
                "spot when they did something different, and what was "
                "different then.",
                why,
            )
        return (
            f"Ask about a time, {moment}, when they did something different "
            "from usual.",
            why,
        )
    if approach == ExplorationApproach.WOULD_IT_DIFFER:
        if need.observation is not None:
            return (
                f"Go back to {story}. Ask whether they would have done the same "
                f"with someone else, like {other_person(need.observation)}.",
                why,
            )
        return (
            f"Ask whether there is someone in their life with whom, in {moment}, "
            "they act differently.",
            why,
        )
    return (
        f"Ask them, lightly, to notice this week a time, {moment}, when they "
        "don't do what they usually do.",
        why,
    )


def not_before_after(
    tries: Sequence[ExplorationTry],
    asked_at: Mapping[UUID, datetime],
    wait: timedelta,
    time_zone: str | None,
) -> date | None:
    """Work out the first day an Exploration may be tried again.

    Args:
        tries: Its tries.
        asked_at: When each asked try's Curiosity was asked, by Curiosity ID.
        wait: How long to wait after a try with nothing.
        time_zone: The User's IANA time zone.

    Returns:
        The day of its last try plus the wait, when that try came back with
        nothing; None otherwise.
    """
    asked = asked_in_order(tries, asked_at)
    if not asked or asked[-1].outcome not in NOTHING_USEFUL:
        return None
    return users_today(time_zone, asked_at[asked[-1].curiosity_id]) + wait


def new_exploration(pattern: CatalogPattern, now: datetime) -> Exploration:
    """Start an Exploration for a suspected Pattern.

    Args:
        pattern: The Pattern.
        now: When it starts.

    Returns:
        The Exploration, waiting for a place.
    """
    return Exploration(
        id=uuid4(),
        user_id=pattern.user_id,
        pattern_id=pattern.id,
        pattern_type_id=pattern.pattern_type_id,
        state=ExplorationState.WAITING,
        created_at=now,
        updated_at=now,
    )


def judge_tries(
    tries: Sequence[ExplorationTry],
    aimed: Mapping[UUID, Curiosity],
    pattern_type_ids: Mapping[UUID, str],
    observations: Sequence[Observation],
) -> list[ExplorationTry]:
    """Work out how each asked, not yet judged try came back.

    Args:
        tries: Every try.
        aimed: Every aimed Curiosity, by ID.
        pattern_type_ids: Each Exploration's Pattern Type ID, by its ID.
        observations: All the User's Observations now.

    Returns:
        The tries just judged, with their outcome.
    """
    by_id = {observation.id: observation for observation in observations}
    judged: list[ExplorationTry] = []
    for attempt in tries:
        curiosity = aimed.get(attempt.curiosity_id)
        pattern_type_id = pattern_type_ids.get(attempt.exploration_id)
        if (
            attempt.outcome is not None
            or curiosity is None
            or curiosity.raised_at is None
            or pattern_type_id is None
        ):
            continue
        aimed_at = by_id.get(attempt.observation_id) if attempt.observation_id else None
        settled = (
            attempt.need == ExplorationNeed.UNCLEAR
            and aimed_at is not None
            and not aimed_at.unclear
        )
        new_evidence = curiosity.raised_conversation_id is not None and any(
            observation.conversation_id == curiosity.raised_conversation_id
            and observation.id != attempt.observation_id
            for observation in observations_of(pattern_type_id, observations)
        )
        judged.append(
            replace(
                attempt,
                outcome=try_outcome(curiosity.reaction, settled, new_evidence),
            )
        )
    return judged


def next_state(
    exploration: Exploration,
    pattern: CatalogPattern | None,
    tries: Sequence[ExplorationTry],
    asked_at: Mapping[UUID, datetime],
    observations: Sequence[Observation],
    asked_to_drop: bool,
    numbers: AgendaNumbers,
    now: datetime,
) -> Exploration:
    """Rest or wake an Exploration, before places on the Agenda are given.

    A resting one wakes when a new Observation for its Pattern was tagged
    since it rested. One that isn't resting rests after the Admin-set
    tries with nothing in a row, or at once when the User asked to drop it.

    Args:
        exploration: The Exploration.
        pattern: Its Pattern; None if it is gone.
        tries: Its tries, judged.
        asked_at: When each asked try's Curiosity was asked, by Curiosity ID.
        observations: The Observations of its Pattern.
        asked_to_drop: Whether the User asked to drop its latest try.
        numbers: The Admin-set numbers.
        now: When the Agenda is kept.

    Returns:
        It resting, woken (waiting for a place) or as it was.
    """
    if exploration.state == ExplorationState.RESTING:
        woken = exploration.rested_at is not None and any(
            observation.tagged_at > exploration.rested_at
            for observation in observations
        )
        if not woken:
            return exploration
        return replace(
            exploration, state=ExplorationState.WAITING, woke_at=now, updated_at=now
        )
    if pattern is None:
        return exploration
    if asked_to_drop or (
        tries_with_nothing(exploration, tries, asked_at) >= numbers.rest_after_tries
    ):
        return replace(
            exploration, state=ExplorationState.RESTING, rested_at=now, updated_at=now
        )
    return exploration


def aimed_curiosity(
    exploration: Exploration,
    need: OpenNeed,
    approach: ExplorationApproach,
    pattern_type: PatternType,
    not_before: date | None,
    user_id: UUID,
    now: datetime,
    thought_experiment: ThoughtExperiment | None = None,
) -> tuple[Curiosity, ExplorationTry]:
    """Write the aimed Curiosity for an Exploration's top need, with its try.

    Args:
        exploration: The Exploration.
        need: Its top open need.
        approach: Its Approach: how to ask.
        pattern_type: Its Pattern's Pattern Type.
        not_before: The first day it may be asked; None for any day.
        user_id: The User.
        now: When it is written.
        thought_experiment: The Thought Experiment it puts to the User, for
            that Approach; None otherwise. Its wording and sensitivity are
            used.

    Returns:
        The Curiosity, waiting, and its try, not yet asked.
    """
    question, why = (
        thought_experiment_question(thought_experiment)
        if thought_experiment
        else aimed_question(need, approach, pattern_type)
    )
    curiosity = Curiosity(
        id=uuid4(),
        user_id=user_id,
        question=question,
        why=why,
        not_before=not_before,
        sensitivity=(
            thought_experiment.details.sensitivity
            if thought_experiment
            else CuriositySensitivity.MEDIUM
        ),
        state=CuriosityState.WAITING,
        created_at=now,
        aim=CuriosityAim.EXPLORATION,
        exploration_id=exploration.id,
        source_observation_id=need.observation.id if need.observation else None,
    )
    return curiosity, ExplorationTry(
        curiosity_id=curiosity.id,
        exploration_id=exploration.id,
        user_id=user_id,
        need=need.need,
        approach=approach,
        created_at=now,
        observation_id=need.observation.id if need.observation else None,
        condition=need.condition,
        condition_value=need.value,
        thought_experiment_id=thought_experiment.id if thought_experiment else None,
    )


def with_place(exploration: Exploration, on_agenda: bool, now: datetime) -> Exploration:
    """Give an Exploration its place on the Agenda, or take it away.

    Args:
        exploration: The Exploration, rested or woken already.
        on_agenda: Whether it ranked high enough for a place.
        now: When the Agenda is kept.

    Returns:
        It active or waiting; a resting one, or one already in the right
        state, as it was.
    """
    state = ExplorationState.ACTIVE if on_agenda else ExplorationState.WAITING
    if exploration.state in (ExplorationState.RESTING, state):
        return exploration
    return replace(exploration, state=state, updated_at=now)


def plan_agenda(agenda: AgendaInput, numbers: AgendaNumbers) -> AgendaChanges:
    """Keep a User's Agenda when a Conversation ends, and write what to ask next.

    Judges the tries asked, gives each suspected Pattern an Exploration,
    rests and wakes Explorations, gives the highest-ranked suspected ones a
    place on the Agenda, closes the waiting aimed Curiosities no longer
    wanted, and writes the next aimed Curiosity for each active Exploration
    with none waiting that wasn't tried in this Conversation.

    Args:
        agenda: What the Agenda is kept from.
        numbers: The Admin-set numbers.

    Returns:
        What changes.
    """
    now = agenda.now
    patterns = {pattern.id: pattern for pattern in agenda.patterns}
    aimed = {curiosity.id: curiosity for curiosity in agenda.aimed}
    asked_at = {
        curiosity.id: curiosity.raised_at
        for curiosity in agenda.aimed
        if curiosity.raised_at is not None
    }
    explored = {exploration.pattern_id for exploration in agenda.explorations}
    added = [
        new_exploration(pattern, now)
        for pattern in agenda.patterns
        if pattern.state == PatternState.SUSPECTED and pattern.id not in explored
    ]
    explorations = [*agenda.explorations, *added]
    judged = judge_tries(
        agenda.tries,
        aimed,
        {exploration.id: exploration.pattern_type_id for exploration in explorations},
        agenda.observations,
    )
    judged_by_id = {attempt.curiosity_id: attempt for attempt in judged}
    tries = [
        judged_by_id.get(attempt.curiosity_id, attempt) for attempt in agenda.tries
    ]
    dropped = {
        attempt.exploration_id
        for attempt in judged
        if aimed[attempt.curiosity_id].reaction == ThreadReaction.ASKED_TO_DROP
    }
    stepped = [
        next_state(
            exploration,
            patterns.get(exploration.pattern_id),
            tries_of(exploration, tries),
            asked_at,
            observations_of(exploration.pattern_type_id, agenda.observations),
            exploration.id in dropped,
            numbers,
            now,
        )
        for exploration in explorations
    ]
    may_have_a_place = [
        exploration
        for exploration in stepped
        if exploration.state != ExplorationState.RESTING
        and exploration.pattern_id in patterns
        and patterns[exploration.pattern_id].state == PatternState.SUSPECTED
    ]
    active_ids = {
        exploration.id
        for exploration in rank_explorations(may_have_a_place, agenda.scores)[
            : numbers.size
        ]
    }
    placed = [
        with_place(exploration, exploration.id in active_ids, now)
        for exploration in stepped
    ]
    before = {exploration.id: exploration for exploration in agenda.explorations}
    next_tries = [
        next_try_for(
            exploration, tries_of(exploration, tries), asked_at, agenda, numbers
        )
        for exploration in placed
    ]
    return AgendaChanges(
        added=[exploration for exploration in placed if exploration.id not in before],
        changed=[
            exploration
            for exploration in placed
            if exploration.id in before and exploration != before[exploration.id]
        ],
        judged=judged,
        closed_curiosity_ids=[
            curiosity_id for closed, _ in next_tries for curiosity_id in closed
        ],
        new_curiosities=[written[0] for _, written in next_tries if written],
        new_tries=[written[1] for _, written in next_tries if written],
    )


def next_try_for(
    exploration: Exploration,
    its_tries: Sequence[ExplorationTry],
    asked_at: Mapping[UUID, datetime],
    agenda: AgendaInput,
    numbers: AgendaNumbers,
) -> tuple[list[UUID], tuple[Curiosity, ExplorationTry] | None]:
    """Work out an Exploration's aimed Curiosities to close, and its next one.

    A waiting one is closed when the Exploration isn't active or no longer
    aims at its top need. A new one is written only for an active
    Exploration with none waiting, not tried in this Conversation, so it is
    never worked on two Conversations in a row.

    Args:
        exploration: The Exploration, in its new state.
        its_tries: Its tries, judged.
        asked_at: When each asked try's Curiosity was asked, by Curiosity ID.
        agenda: What the Agenda is kept from.
        numbers: The Admin-set numbers.

    Returns:
        The IDs of its waiting aimed Curiosities to close, and its new aimed
        Curiosity with its try; None when none is written.
    """
    waiting_ids = {
        curiosity.id
        for curiosity in agenda.aimed
        if curiosity.state == CuriosityState.WAITING
    }
    waiting = [attempt for attempt in its_tries if attempt.curiosity_id in waiting_ids]
    pattern_type = agenda.pattern_types.get(exploration.pattern_type_id)
    needs = open_needs(
        observations_of(exploration.pattern_type_id, agenda.observations),
        its_tries,
        numbers.one_sided_stories,
    )
    top = needs[0] if needs else None
    if (
        exploration.state != ExplorationState.ACTIVE
        or top is None
        or pattern_type is None
    ):
        return [attempt.curiosity_id for attempt in waiting], None
    askable = {
        thought_experiment.id
        for thought_experiment in agenda.thought_experiments
        if thought_experiment.askable
    }
    closed = [
        attempt.curiosity_id
        for attempt in waiting
        if not aims_at(attempt, top)
        or (
            attempt.thought_experiment_id is not None
            and attempt.thought_experiment_id not in askable
        )
    ]
    tried_here = any(
        curiosity.raised_conversation_id == agenda.conversation_id
        for curiosity in agenda.aimed
        if curiosity.exploration_id == exploration.id
    )
    if len(closed) < len(waiting) or tried_here:
        return closed, None
    approach = next_approach(top, its_tries, asked_at)
    thought_experiment = (
        thought_experiment_for(exploration, top, its_tries, agenda, numbers)
        if approach == ExplorationApproach.THOUGHT_EXPERIMENT
        else None
    )
    if (
        approach == ExplorationApproach.THOUGHT_EXPERIMENT
        and thought_experiment is None
    ):
        approach = approach_after(approach, top)
    return closed, aimed_curiosity(
        exploration,
        top,
        approach,
        pattern_type,
        not_before_after(its_tries, asked_at, numbers.wait, agenda.time_zone),
        agenda.user_id,
        agenda.now,
        thought_experiment,
    )


def thought_experiment_for(
    exploration: Exploration,
    need: OpenNeed,
    its_tries: Sequence[ExplorationTry],
    agenda: AgendaInput,
    numbers: AgendaNumbers,
) -> ThoughtExperiment | None:
    """Pick the Thought Experiment an Exploration's next try puts to the User.

    Only an unclear need is tried by this Approach, since a Thought Experiment tells
    two look-alike Pattern Types apart, and only while fewer than the
    Admin-set number were asked for its Pattern in the last 7 days.

    Args:
        exploration: The Exploration.
        need: Its top open need.
        its_tries: Its tries.
        agenda: What the Agenda is kept from.
        numbers: The Admin-set numbers.

    Returns:
        The Thought Experiment for the look-alike pair with the most unclear
        evidence, never one already put to them, as a starter either; None
        when the need isn't unclear, the week's are used up or none is left
        to ask.
    """
    aimed = {curiosity.id: curiosity for curiosity in agenda.aimed}
    if (
        need.need != ExplorationNeed.UNCLEAR
        or thought_experiments_this_week(its_tries, aimed, agenda.now)
        >= numbers.thought_experiments_per_week
    ):
        return None
    return pick_thought_experiment(
        exploration.pattern_type_id,
        observations_of(exploration.pattern_type_id, agenda.observations),
        agenda.thought_experiments,
        put_to_user(agenda.tries, aimed) | agenda.starters_put,
    )


def pattern_scores(
    observations: Sequence[Observation],
    catalog: Sequence[CatalogPatternType],
    settings: PlatformSettings,
    today: date,
) -> dict[str, PatternScore]:
    """Work out each of a User's Patterns' scores, as scoring does.

    Args:
        observations: All their Observations.
        catalog: The Pattern Catalog now.
        settings: The platform settings, for the scoring numbers.
        today: The User's day now, for fading.

    Returns:
        Each score, by Pattern Type ID.
    """
    sign_strengths = sign_strengths_of(entry.pattern_type for entry in catalog)
    numbers = scoring_numbers(settings)
    return {
        pattern_type_id: score_observations(
            without_narrowing(its_observations), sign_strengths, numbers, today
        )
        for pattern_type_id, its_observations in observations_by_pattern_type(
            observations
        ).items()
    }


def agenda_numbers(settings: PlatformSettings) -> AgendaNumbers:
    """Read the Admin-set numbers the Agenda is kept with.

    Args:
        settings: The platform settings.

    Returns:
        The numbers.
    """
    return AgendaNumbers(
        size=settings.get(AGENDA_SIZE),
        wait=settings.get(EXPLORATION_WAIT),
        rest_after_tries=settings.get(EXPLORATION_REST_AFTER_TRIES),
        thought_experiments_per_week=settings.get(
            THOUGHT_EXPERIMENTS_PER_PATTERN_PER_WEEK
        ),
        one_sided_stories=settings.get(CONDITION_ONE_SIDED_STORIES),
    )


class AgendaKeeper:
    """Keeps a User's Agenda when a Conversation ends, and writes what to ask next.

    No model call: code judges the tries, rests and wakes Explorations, ranks
    them and writes each active one's next aimed Curiosity.
    """

    def __init__(
        self,
        repositories: Repositories,
        pattern_catalog: PatternCatalogService,
        clock: Clock,
    ) -> None:
        """Set up the keeper.

        Args:
            repositories: Where Patterns, Observations, Explorations and
                Curiosities are stored.
            pattern_catalog: Reads the Pattern Types in the catalog now.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._pattern_catalog = pattern_catalog
        self._clock = clock

    def keep(self, snapshot: UserSnapshot, conversation_id: UUID) -> None:
        """Keep the User's Agenda after their Patterns were scored.

        Runs only while Pattern exploring and Curiosities work for them,
        since an aimed Curiosity can be asked only then. The User is locked
        while it reads and saves, like scoring, so an Observation deleted
        meanwhile is never aimed at.

        Args:
            snapshot: The User whose Conversation it was.
            conversation_id: The ended Conversation.
        """
        if not (
            snapshot.works(Feature.PATTERN_EXPLORING)
            and snapshot.works(Feature.CURIOSITIES)
        ):
            return
        with self._repositories.transaction() as transaction:
            transaction.lock_user(snapshot.user.id)
            self._keep_locked(transaction.repositories, snapshot, conversation_id)

    def _keep_locked(
        self,
        repositories: Repositories,
        snapshot: UserSnapshot,
        conversation_id: UUID,
    ) -> None:
        """Keep the User's Agenda while they are locked.

        Args:
            repositories: The repositories, inside the locking transaction.
            snapshot: The User whose Conversation it was.
            conversation_id: The ended Conversation.
        """
        user = snapshot.user
        patterns = repositories.patterns.list_of_pattern_types(user.id)
        explorations = repositories.explorations.list_for_user(user.id)
        if not patterns and not explorations:
            return
        observations = repositories.observations.list_for_user(user.id)
        catalog = self._pattern_catalog.catalog()
        now = self._clock.now()
        scores = pattern_scores(
            observations, catalog, snapshot.settings, users_today(user.time_zone, now)
        )
        repositories.explorations.save_agenda(
            plan_agenda(
                AgendaInput(
                    user_id=user.id,
                    patterns=patterns,
                    observations=observations,
                    scores=scores,
                    pattern_types={
                        entry.pattern_type.id: entry.pattern_type for entry in catalog
                    },
                    explorations=explorations,
                    tries=repositories.explorations.list_tries(user.id),
                    aimed=repositories.curiosities.list_aimed(user.id),
                    conversation_id=conversation_id,
                    now=now,
                    time_zone=user.time_zone,
                    thought_experiments=repositories.thought_experiments.list_all(),
                    starters_put=put_as_starters(
                        repositories.curiosities.list_starters(user.id)
                    ),
                ),
                agenda_numbers(snapshot.settings),
            )
        )


@dataclass(frozen=True)
class AskedTry:
    """A try that was asked, as the Reply Plan reads it.

    Attributes:
        curiosity: The aimed Curiosity.
        attempt: Its try.
    """

    curiosity: Curiosity
    attempt: ExplorationTry


@dataclass(frozen=True)
class AgendaEntry:
    """One active Exploration, as the Reply Plan is given it.

    Attributes:
        pattern_type: Its Pattern's Pattern Type.
        open_needs: What it still needs to learn, in order.
        earlier_tries: Its tries already asked, oldest first.
    """

    pattern_type: PatternType
    open_needs: tuple[OpenNeed, ...]
    earlier_tries: tuple[AskedTry, ...]


def describe_need(need: OpenNeed) -> str:
    """Write an open need in plain words, naming no Pattern.

    Args:
        need: The open need.

    Returns:
        E.g. "how it goes for them at work, not heard yet". The state going
        in is put openly, with no state named.
    """
    if need.need == ExplorationNeed.UNCLEAR and need.observation is not None:
        return f"what drove {describe_story(need.observation)}, still unclear"
    if need.condition == Condition.STATE_GOING_IN:
        return (
            "how they were doing going into it, asked openly and never naming "
            "a mood or state yourself"
        )
    if need.condition is not None and need.value is not None:
        where, _ = CONDITION_WORDS[(need.condition, need.value)]
        return f"how it goes for them {where}, not heard yet"
    return "a time it didn't happen, when it might have"


def outcome_words(outcome: TryOutcome | None) -> str:
    """Write how a try came back.

    Args:
        outcome: How it came back; None before its Conversation ends.

    Returns:
        E.g. "vague"; "not known yet" with none.
    """
    return OUTCOME_WORDS[outcome] if outcome else "not known yet"


def describe_agenda(entries: Sequence[AgendaEntry], time_zone: str | None) -> str:
    """Write the Agenda as the Reply Plan model reads it.

    Args:
        entries: The active Explorations.
        time_zone: The User's IANA time zone, for days.

    Returns:
        One numbered block per Exploration with its Pattern Type, what it
        still needs and its earlier tries, then a line on aiming Get curious;
        "" when the Agenda is empty.
    """
    if not entries:
        return ""
    blocks = []
    for number, entry in enumerate(entries, start=1):
        pattern_type = entry.pattern_type
        needs = (
            "; ".join(describe_need(need) for need in entry.open_needs)
            or "nothing open now"
        )
        tries = "\n".join(
            f"  - {format_day(asked.curiosity.raised_at, time_zone)}, "
            f"{APPROACH_WORDS[asked.attempt.approach]}: {asked.curiosity.question} "
            f"({outcome_words(asked.attempt.outcome)})"
            for asked in entry.earlier_tries
            if asked.curiosity.raised_at is not None
        )
        blocks.append(
            f"[{number}] {pattern_type.name}: if {lowered(pattern_type.if_situation)}, "
            f"then {lowered(pattern_type.then_behaviour)}.\n"
            f"  Still to learn: {needs}.\n"
            f"  Tried before:\n{tries or '  - Nothing yet.'}"
        )
    return (
        "\n\nWhat you are exploring about them (the Agenda), most worth "
        "learning first. These are only suspicions: never name them, never say "
        "you are exploring, and never claim any of them. When an aimed "
        "Curiosity's day has come, it is first among the Curiosities above:\n"
        + "\n".join(blocks)
        + "\nIf you pick a Move that asks a question, such as Get curious, aim it "
        "at something still to learn above when it fits what they just said."
    )


def describe_open_needs_for_reply(entries: Sequence[AgendaEntry]) -> str:
    """Write the Agenda's open needs for a reply whose Move asks a question.

    Args:
        entries: The active Explorations.

    Returns:
        A line naming what Zeph wants to learn, naming no Pattern; "" when
        nothing is open.
    """
    needs = [describe_need(need) for entry in entries for need in entry.open_needs]
    if not needs:
        return ""
    return (
        "If your question can aim at something you want to learn about them, "
        "and it fits what they just said, aim it at one of these: "
        + "; ".join(needs)
        + "."
    )


class AgendaReader:
    """Reads a User's Agenda for the Reply Plan, on every reply.

    No model call. Empty while Pattern exploring doesn't work for the User
    or they are struggling.
    """

    def __init__(
        self,
        repositories: Repositories,
        pattern_catalog: PatternCatalogService,
        clock: Clock,
    ) -> None:
        """Set up the reader.

        Args:
            repositories: Where Explorations, Observations and Curiosities
                are stored.
            pattern_catalog: Reads the Pattern Types in the catalog now.
            clock: Tells the current time, for the scores.
        """
        self._repositories = repositories
        self._pattern_catalog = pattern_catalog
        self._clock = clock

    def read(self, snapshot: UserSnapshot, struggling: bool) -> list[AgendaEntry]:
        """Read the User's active Explorations with their needs and tries.

        Args:
            snapshot: The User being answered.
            struggling: Whether the Understanding found them struggling.

        Returns:
            The active Explorations in rank order; none while Pattern
            exploring doesn't work for them or they are struggling.
        """
        if struggling or not snapshot.works(Feature.PATTERN_EXPLORING):
            return []
        user_id = snapshot.user.id
        active = [
            exploration
            for exploration in self._repositories.explorations.list_for_user(user_id)
            if exploration.state == ExplorationState.ACTIVE
        ]
        if not active:
            return []
        catalog = self._pattern_catalog.catalog()
        pattern_types = {entry.pattern_type.id: entry.pattern_type for entry in catalog}
        observations = self._repositories.observations.list_for_user(user_id)
        tries = self._repositories.explorations.list_tries(user_id)
        aimed = {
            curiosity.id: curiosity
            for curiosity in self._repositories.curiosities.list_aimed(user_id)
        }
        asked_at = {
            curiosity_id: curiosity.raised_at
            for curiosity_id, curiosity in aimed.items()
            if curiosity.raised_at is not None
        }
        scores = pattern_scores(
            observations,
            catalog,
            snapshot.settings,
            users_today(snapshot.user.time_zone, self._clock.now()),
        )
        return [
            AgendaEntry(
                pattern_type=pattern_types[exploration.pattern_type_id],
                open_needs=tuple(
                    open_needs(
                        observations_of(exploration.pattern_type_id, observations),
                        tries_of(exploration, tries),
                        snapshot.settings.get(CONDITION_ONE_SIDED_STORIES),
                    )
                ),
                earlier_tries=tuple(
                    AskedTry(aimed[attempt.curiosity_id], attempt)
                    for attempt in asked_in_order(
                        tries_of(exploration, tries), asked_at
                    )
                ),
            )
            for exploration in rank_explorations(active, scores)
            if exploration.pattern_type_id in pattern_types
        ]
