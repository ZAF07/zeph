from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from companion.core.memory_retrieval import format_day
from companion.core.models import (
    AgendaChanges,
    CatalogPattern,
    Curiosity,
    CuriosityAim,
    CuriositySensitivity,
    CuriosityState,
    Exploration,
    ExplorationNeed,
    ExplorationState,
    ExplorationTry,
    ExplorationWay,
    Feature,
    Observation,
    ObservationDirection,
    PatternState,
    PatternType,
    PlatformSettings,
    Relationship,
    SituationSetting,
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
)
from companion.core.platform_settings import (
    AGENDA_SIZE,
    EXPLORATION_REST_AFTER_TRIES,
    EXPLORATION_WAIT,
)
from companion.core.ports import Clock, Repositories
from companion.core.timing import users_today

PARTS_OF_LIFE = (SituationSetting.HOME, SituationSetting.WORK, SituationSetting.SOCIAL)
WAYS = (
    ExplorationWay.STORY_FOLLOW_UP,
    ExplorationWay.OTHER_PERSON,
    ExplorationWay.NOTICE_THIS_WEEK,
)
NEED_ORDER = (
    ExplorationNeed.UNCLEAR,
    ExplorationNeed.MISSING_PART,
    ExplorationNeed.COUNTER_TEST,
)
NOTHING_USEFUL = frozenset({TryOutcome.VAGUE, TryOutcome.BRUSHED_OFF})
PART_WORDS = {
    SituationSetting.HOME: "at home",
    SituationSetting.WORK: "at work",
    SituationSetting.SOCIAL: "with friends",
}
PERSON_FOR_PART = {
    SituationSetting.HOME: "family",
    SituationSetting.WORK: "a colleague",
    SituationSetting.SOCIAL: "a friend",
}
OTHER_PEOPLE = (
    (Relationship.FRIEND, "a friend"),
    (Relationship.COLLEAGUE, "a colleague"),
    (Relationship.FAMILY, "family"),
    (Relationship.PARTNER, "a partner"),
)
WAY_WORDS = {
    ExplorationWay.STORY_FOLLOW_UP: "story follow-up",
    ExplorationWay.OTHER_PERSON: "would it differ with someone else",
    ExplorationWay.NOTICE_THIS_WEEK: "notice this week",
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
            story a counter-test starts from; None otherwise.
        part_of_life: The part of life not seen yet; None otherwise.
    """

    need: ExplorationNeed
    observation: Observation | None = None
    part_of_life: SituationSetting | None = None


@dataclass(frozen=True)
class AgendaNumbers:
    """The Admin-set numbers the Agenda is kept with.

    Attributes:
        size: The most Explorations active at once.
        wait: How long to wait after a try with nothing.
        rest_after_tries: Tries with nothing in a row before resting.
    """

    size: int
    wait: timedelta
    rest_after_tries: int


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


def open_needs(
    observations: Sequence[Observation],
    tries: Sequence[ExplorationTry],
) -> list[OpenNeed]:
    """Work out what an Exploration still needs to learn from its Observations.

    Unclear stories come first, newest first; then a part of life (home,
    work, with friends) not seen yet while another is; then a counter-test,
    open until an Observation against comes or a counter-test try was
    useful.

    Args:
        observations: The Observations of its Pattern.
        tries: Its tries.

    Returns:
        The open needs, in the order they are worked on.
    """
    needs = [
        OpenNeed(ExplorationNeed.UNCLEAR, observation=observation)
        for observation in newest_first(observations)
        if observation.unclear
    ]
    seen = {observation.tags.setting for observation in observations}
    missing = [part for part in PARTS_OF_LIFE if part not in seen]
    if missing and len(missing) < len(PARTS_OF_LIFE):
        needs.append(OpenNeed(ExplorationNeed.MISSING_PART, part_of_life=missing[0]))
    tested = any(
        observation.direction == ObservationDirection.AGAINST
        for observation in observations
    ) or any(
        attempt.need == ExplorationNeed.COUNTER_TEST
        and attempt.outcome == TryOutcome.USEFUL
        for attempt in tries
    )
    if not tested:
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
    return needs


def aims_at(attempt: ExplorationTry, need: OpenNeed) -> bool:
    """Say whether a try aimed at this very need.

    A counter-test is one need whichever story it starts from.

    Args:
        attempt: The try.
        need: The open need.

    Returns:
        True when it has the same kind and, except for a counter-test, the
        same Observation or part of life.
    """
    if attempt.need != need.need:
        return False
    if need.need == ExplorationNeed.COUNTER_TEST:
        return True
    return (
        attempt.observation_id == (need.observation.id if need.observation else None)
        and attempt.part_of_life == need.part_of_life
    )


def next_way(
    need: OpenNeed,
    tries: Sequence[ExplorationTry],
    asked_at: Mapping[UUID, datetime],
) -> ExplorationWay:
    """Pick how to ask about a need next, least pushy first.

    Each try at the same need moves on to the next way, round again after
    the last, so the next try is always a different way.

    Args:
        need: The open need.
        tries: The Exploration's tries.
        asked_at: When each asked try's Curiosity was asked, by Curiosity ID.

    Returns:
        The way after the one tried last at this need; the first if none was.
    """
    asked = sorted(
        (
            attempt
            for attempt in tries
            if attempt.curiosity_id in asked_at and aims_at(attempt, need)
        ),
        key=lambda attempt: asked_at[attempt.curiosity_id],
    )
    if not asked:
        return WAYS[0]
    return WAYS[(WAYS.index(asked[-1].way) + 1) % len(WAYS)]


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
        Brushed off when brushed off or asked to drop; useful when engaged
        and it settled something or brought new evidence; vague otherwise.
    """
    if reaction in (ThreadReaction.BRUSHED_OFF, ThreadReaction.ASKED_TO_DROP):
        return TryOutcome.BRUSHED_OFF
    if reaction == ThreadReaction.ENGAGED and (settled or new_evidence):
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
    judged = sorted(
        (
            attempt
            for attempt in tries
            if attempt.outcome is not None
            and attempt.curiosity_id in asked_at
            and (
                exploration.woke_at is None
                or asked_at[attempt.curiosity_id] > exploration.woke_at
            )
        ),
        key=lambda attempt: asked_at[attempt.curiosity_id],
        reverse=True,
    )
    count = 0
    for attempt in judged:
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


def aimed_question(
    need: OpenNeed, way: ExplorationWay, pattern_type: PatternType
) -> tuple[str, str]:
    """Write an aimed Curiosity's question and why, for the model to word.

    Args:
        need: The need it aims at.
        way: How it asks.
        pattern_type: The Pattern's Pattern Type, for its situation.

    Returns:
        The question, as a plain instruction, and why Zeph wonders. Neither
        names the Pattern.
    """
    moment = f"a moment like this: {lowered(pattern_type.if_situation)}"
    story = describe_story(need.observation) if need.observation else ""
    if need.need == ExplorationNeed.UNCLEAR and need.observation is not None:
        why = "What drove it isn't clear yet, and how they answer would tell."
        if way == ExplorationWay.STORY_FOLLOW_UP:
            return (
                f"Go back to {story}. Ask what they did next, and what they "
                "were most hoping would or wouldn't happen then.",
                why,
            )
        if way == ExplorationWay.OTHER_PERSON:
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
    if need.need == ExplorationNeed.MISSING_PART and need.part_of_life is not None:
        part = PART_WORDS[need.part_of_life]
        why = f"Zeph hasn't heard how this goes for them {part} yet."
        if way == ExplorationWay.STORY_FOLLOW_UP:
            return (
                f"Ask about a recent time {part}, {moment}. What happened, and "
                "what did they do?",
                why,
            )
        if way == ExplorationWay.OTHER_PERSON:
            return (
                f"Ask whether it goes the same way {part}, say with "
                f"{PERSON_FOR_PART[need.part_of_life]}, in {moment}.",
                why,
            )
        return (
            f"Ask them, lightly, to notice this week {part} {moment}, and what "
            "they do then.",
            why,
        )
    why = "To learn when it doesn't happen, not only when it does."
    if way == ExplorationWay.STORY_FOLLOW_UP:
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
    if way == ExplorationWay.OTHER_PERSON:
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
    asked = sorted(
        (attempt for attempt in tries if attempt.curiosity_id in asked_at),
        key=lambda attempt: asked_at[attempt.curiosity_id],
    )
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
    way: ExplorationWay,
    pattern_type: PatternType,
    not_before: date | None,
    agenda: AgendaInput,
) -> tuple[Curiosity, ExplorationTry]:
    """Write the aimed Curiosity for an Exploration's top need, with its try.

    Args:
        exploration: The Exploration.
        need: Its top open need.
        way: How to ask.
        pattern_type: Its Pattern's Pattern Type.
        not_before: The first day it may be asked; None for any day.
        agenda: What the Agenda is kept from.

    Returns:
        The Curiosity, waiting, and its try, not yet asked.
    """
    question, why = aimed_question(need, way, pattern_type)
    curiosity = Curiosity(
        id=uuid4(),
        user_id=agenda.user_id,
        question=question,
        why=why,
        not_before=not_before,
        sensitivity=CuriositySensitivity.MEDIUM,
        state=CuriosityState.WAITING,
        created_at=agenda.now,
        aim=CuriosityAim.EXPLORATION,
        exploration_id=exploration.id,
        source_observation_id=need.observation.id if need.observation else None,
    )
    return curiosity, ExplorationTry(
        curiosity_id=curiosity.id,
        exploration_id=exploration.id,
        user_id=agenda.user_id,
        need=need.need,
        way=way,
        created_at=agenda.now,
        observation_id=need.observation.id if need.observation else None,
        part_of_life=need.part_of_life,
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
            [attempt for attempt in tries if attempt.exploration_id == exploration.id],
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
    planned = AgendaChanges(
        added=[exploration for exploration in placed if exploration.id not in before],
        changed=[
            exploration
            for exploration in placed
            if exploration.id in before and exploration != before[exploration.id]
        ],
        judged=judged,
        closed_curiosity_ids=[],
        new_curiosities=[],
        new_tries=[],
    )
    for exploration in placed:
        write_next_try(exploration, tries, asked_at, agenda, numbers, planned)
    return planned


def write_next_try(
    exploration: Exploration,
    tries: Sequence[ExplorationTry],
    asked_at: Mapping[UUID, datetime],
    agenda: AgendaInput,
    numbers: AgendaNumbers,
    planned: AgendaChanges,
) -> None:
    """Close an Exploration's waiting aimed Curiosity, or write its next one.

    A waiting one is closed when the Exploration isn't active or no longer
    aims at its top need. A new one is written only for an active
    Exploration with none waiting, not tried in this Conversation, so it is
    never worked on two Conversations in a row.

    Args:
        exploration: The Exploration, in its new state.
        tries: Every try, judged.
        asked_at: When each asked try's Curiosity was asked, by Curiosity ID.
        agenda: What the Agenda is kept from.
        numbers: The Admin-set numbers.
        planned: Where the changes are written.
    """
    its_tries = [
        attempt for attempt in tries if attempt.exploration_id == exploration.id
    ]
    waiting = [
        attempt
        for attempt in its_tries
        if any(
            curiosity.id == attempt.curiosity_id
            and curiosity.state == CuriosityState.WAITING
            for curiosity in agenda.aimed
        )
    ]
    pattern_type = agenda.pattern_types.get(exploration.pattern_type_id)
    needs = open_needs(
        observations_of(exploration.pattern_type_id, agenda.observations), its_tries
    )
    top = needs[0] if needs else None
    wanted = (
        exploration.state == ExplorationState.ACTIVE
        and top is not None
        and pattern_type is not None
    )
    still_waiting = [
        attempt for attempt in waiting if wanted and top and aims_at(attempt, top)
    ]
    planned.closed_curiosity_ids.extend(
        attempt.curiosity_id for attempt in waiting if attempt not in still_waiting
    )
    tried_here = any(
        curiosity.raised_conversation_id == agenda.conversation_id
        for curiosity in agenda.aimed
        if curiosity.exploration_id == exploration.id
    )
    if not wanted or still_waiting or tried_here or top is None or not pattern_type:
        return
    curiosity, attempt = aimed_curiosity(
        exploration,
        top,
        next_way(top, its_tries, asked_at),
        pattern_type,
        not_before_after(its_tries, asked_at, numbers.wait, agenda.time_zone),
        agenda,
    )
    planned.new_curiosities.append(curiosity)
    planned.new_tries.append(attempt)


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

        Runs only while Pattern exploring works for them. The User is locked
        while it reads and saves, like scoring, so an Observation deleted
        meanwhile is never aimed at.

        Args:
            snapshot: The User whose Conversation it was.
            conversation_id: The ended Conversation.
        """
        if not snapshot.works(Feature.PATTERN_EXPLORING):
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
        sign_strengths = {
            (entry.pattern_type.id, sign.id): sign.strength
            for entry in catalog
            for sign in (*entry.pattern_type.signs, *entry.pattern_type.signs_against)
        }
        now = self._clock.now()
        today = users_today(user.time_zone, now)
        numbers = scoring_numbers(snapshot.settings)
        scores = {
            pattern_type_id: score_observations(
                its_observations, sign_strengths, numbers, today
            )
            for pattern_type_id, its_observations in observations_by_pattern_type(
                observations
            ).items()
        }
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
        E.g. "how it goes for them at work, not heard yet".
    """
    if need.need == ExplorationNeed.UNCLEAR and need.observation is not None:
        return f"what drove {describe_story(need.observation)}, still unclear"
    if need.need == ExplorationNeed.MISSING_PART and need.part_of_life is not None:
        return f"how it goes for them {PART_WORDS[need.part_of_life]}, not heard yet"
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
            f"{WAY_WORDS[asked.attempt.way]}: {asked.curiosity.question} "
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
        "\n\nWhat you are exploring about them (the Agenda). These are only "
        "suspicions: never name them, never say you are exploring, and never "
        "claim any of them. Its aimed Curiosities are among the ones whose time "
        "has come:\n"
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
        self, repositories: Repositories, pattern_catalog: PatternCatalogService
    ) -> None:
        """Set up the reader.

        Args:
            repositories: Where Explorations, Observations and Curiosities
                are stored.
            pattern_catalog: Reads the Pattern Types in the catalog now.
        """
        self._repositories = repositories
        self._pattern_catalog = pattern_catalog

    def read(self, snapshot: UserSnapshot, struggling: bool) -> list[AgendaEntry]:
        """Read the User's active Explorations with their needs and tries.

        Args:
            snapshot: The User being answered.
            struggling: Whether the Understanding found them struggling.

        Returns:
            The active Explorations, oldest first; none while Pattern
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
        pattern_types = {
            entry.pattern_type.id: entry.pattern_type
            for entry in self._pattern_catalog.catalog()
        }
        observations = self._repositories.observations.list_for_user(user_id)
        tries = self._repositories.explorations.list_tries(user_id)
        aimed = {
            curiosity.id: curiosity
            for curiosity in self._repositories.curiosities.list_aimed(user_id)
        }
        entries = []
        for exploration in active:
            pattern_type = pattern_types.get(exploration.pattern_type_id)
            if pattern_type is None:
                continue
            its_tries = [
                attempt for attempt in tries if attempt.exploration_id == exploration.id
            ]
            asked = sorted(
                (
                    AskedTry(aimed[attempt.curiosity_id], attempt)
                    for attempt in its_tries
                    if attempt.curiosity_id in aimed
                    and aimed[attempt.curiosity_id].raised_at is not None
                ),
                key=lambda item: item.curiosity.raised_at or item.curiosity.created_at,
            )
            entries.append(
                AgendaEntry(
                    pattern_type=pattern_type,
                    open_needs=tuple(
                        open_needs(
                            observations_of(exploration.pattern_type_id, observations),
                            its_tries,
                        )
                    ),
                    earlier_tries=tuple(asked),
                )
            )
        return entries
