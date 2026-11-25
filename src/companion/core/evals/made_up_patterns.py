from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from companion.core.agenda import (
    aimed_curiosity,
    describe_need,
    new_exploration,
    observations_of,
    open_needs,
)
from companion.core.evals.cases import (
    EvalMemory,
    EvalObservation,
    EvalPattern,
    EvalThoughtExperiment,
    EvalTry,
)
from companion.core.evals.made_up_memory import add_ended_conversation
from companion.core.evals.ports import EvalCompanion, EvalSetupError
from companion.core.models import (
    AgendaChanges,
    CatalogPattern,
    ConversationMessage,
    Curiosity,
    CuriosityState,
    EvidenceKind,
    Exploration,
    ExplorationTry,
    MemoryChanges,
    MessageDirection,
    MessageKind,
    Observation,
    ObservationDirection,
    PatternState,
    PatternType,
    ReplyPlan,
    ReplyPlanForm,
    SituationTags,
    ThoughtExperiment,
    ThoughtExperimentDetails,
    ThreadReaction,
    TryOutcome,
)
from companion.core.observations import is_situational
from companion.core.pattern_catalog import PatternCatalogService
from companion.core.platform_settings import CURIOSITY_REPLIES_BETWEEN
from companion.core.ports import Repositories
from companion.core.timing import users_today

THOUGHT_EXPERIMENTS_DAYS_AGO = 30
REPLY_GAP = timedelta(minutes=1)
MADE_UP_NEED = "Just chatting"
REACTIONS = {
    TryOutcome.USEFUL: ThreadReaction.ENGAGED,
    TryOutcome.VAGUE: None,
    TryOutcome.BRUSHED_OFF: ThreadReaction.BRUSHED_OFF,
}


@dataclass(frozen=True)
class AimedAt:
    """What an aimed Curiosity is for, as the checks read it.

    Attributes:
        pattern_type_id: Its Exploration's Pattern Type.
        attempt: Its try: the need it aims at and the way it asks.
    """

    pattern_type_id: str
    attempt: ExplorationTry


@dataclass(frozen=True)
class MadeUpAgenda:
    """The made-up User's Agenda when the case's first Message is sent.

    Attributes:
        open_needs: What each active Exploration still needs to learn, as
            the Reply Plan is told it.
        aimed: What each aimed Curiosity is for, by Curiosity ID.
    """

    open_needs: tuple[str, ...] = ()
    aimed: Mapping[UUID, AimedAt] = field(default_factory=dict)


class MadeUpConversations:
    """The made-up ended Conversations a case's history happened in, one per day."""

    def __init__(
        self, repositories: Repositories, user_id: UUID, now: datetime
    ) -> None:
        """Set up with none yet.

        Args:
            repositories: Where Conversations are stored.
            user_id: The made-up User's ID.
            now: The case's time.
        """
        self._repositories = repositories
        self._user_id = user_id
        self._now = now
        self._by_days_ago: dict[int, UUID] = {}

    def moment(self, days_ago: int) -> datetime:
        """Tell when the Conversation of a day happened.

        Args:
            days_ago: How many days before the case's time.

        Returns:
            That moment.
        """
        return self._now - timedelta(days=days_ago)

    def on(self, days_ago: int) -> UUID:
        """Find the ended Conversation of a day, adding it, processed, the first time.

        Args:
            days_ago: How many days before the case's time.

        Returns:
            Its ID.
        """
        if days_ago not in self._by_days_ago:
            ended_at = self.moment(days_ago)
            conversation_id = add_ended_conversation(
                self._repositories, self._user_id, ended_at
            )
            self._repositories.user_memory.save_processed_conversation(
                conversation_id,
                ended_at,
                None,
                MemoryChanges(added=[], updated=[], removed_ids=[]),
            )
            self._by_days_ago[days_ago] = conversation_id
        return self._by_days_ago[days_ago]

    def newest(self) -> UUID | None:
        """Find the Conversation that ended last.

        Returns:
            Its ID; None when there is none.
        """
        if not self._by_days_ago:
            return None
        return self._by_days_ago[min(self._by_days_ago)]


def pattern_type_in_catalog(
    pattern_types: Mapping[str, PatternType], pattern_type_id: str
) -> PatternType:
    """Find a Pattern Type a case names.

    Args:
        pattern_types: The Pattern Types in the catalog now, by ID.
        pattern_type_id: The ID the case names.

    Returns:
        The Pattern Type.

    Raises:
        EvalSetupError: If the catalog has no such Pattern Type.
    """
    pattern_type = pattern_types.get(pattern_type_id)
    if pattern_type is None:
        raise EvalSetupError(f"No such Pattern Type in the catalog: {pattern_type_id}")
    return pattern_type


def to_observation(
    user_id: UUID,
    pattern_type: PatternType,
    made_up: EvalObservation,
    pattern_types: Mapping[str, PatternType],
    thread_ids: Mapping[str, UUID],
    conversation_id: UUID,
    said_at: datetime,
) -> Observation:
    """Make an Observation to save, as the tagging step would have kept it.

    Args:
        user_id: The made-up User's ID.
        pattern_type: Its Pattern Type.
        made_up: The made-up Observation.
        pattern_types: The Pattern Types in the catalog now, by ID.
        thread_ids: The made-up Life Threads' IDs, by title.
        conversation_id: The ended Conversation it was said in.
        said_at: When it was said.

    Returns:
        The Observation, a real story, situational when anyone would act
        the same in its situation.

    Raises:
        EvalSetupError: If its sign or second Pattern Type isn't in the
            catalog.
    """
    signs = (
        pattern_type.signs
        if made_up.direction == ObservationDirection.FOR
        else pattern_type.signs_against
    )
    if made_up.sign not in {sign.id for sign in signs}:
        raise EvalSetupError(
            f"{pattern_type.id} has no sign {made_up.sign} {made_up.direction.value} it"
        )
    second = (
        pattern_type_in_catalog(pattern_types, made_up.second_pattern_type)
        if made_up.second_pattern_type
        else None
    )
    tags = SituationTags(
        relationship=made_up.relationship,
        power=None,
        setting=made_up.setting,
        stance=None,
    )
    return Observation(
        id=uuid4(),
        user_id=user_id,
        conversation_id=conversation_id,
        pattern_type_id=pattern_type.id,
        pattern_type_version=pattern_type.version,
        sign_id=made_up.sign,
        direction=made_up.direction,
        quote=made_up.quote,
        context=made_up.context,
        day=users_today(None, said_at),
        thread_id=thread_ids[made_up.thread] if made_up.thread else None,
        about=made_up.about,
        tags=tags,
        evidence_kind=EvidenceKind.REAL_STORY,
        second_pattern_type_id=second.id if second else None,
        second_pattern_type_version=second.version if second else None,
        situational=is_situational(tags, pattern_type.anyone_would_when),
        tagged_at=said_at,
    )


def catalog_pattern_types(repositories: Repositories) -> dict[str, PatternType]:
    """Read the Pattern Types in the Eval database's catalog.

    Args:
        repositories: Where the Pattern Catalog is stored.

    Returns:
        The Pattern Types at their current versions, by ID.
    """
    catalog = PatternCatalogService(repositories.pattern_catalog).catalog()
    return {entry.pattern_type.id: entry.pattern_type for entry in catalog}


def thread_ids_by_title(repositories: Repositories, user_id: UUID) -> dict[str, UUID]:
    """Read the made-up User's Life Threads' IDs.

    Args:
        repositories: Where Life Threads are stored.
        user_id: The made-up User's ID.

    Returns:
        Each Thread's ID, by its title.
    """
    return {
        thread.title: thread.id
        for thread in repositories.life_threads.list_for_user(user_id)
    }


def replace_thought_experiments(
    repositories: Repositories,
    thought_experiments: Sequence[EvalThoughtExperiment],
    now: datetime,
) -> None:
    """Make a case's Thought Experiments the only ones Zeph may ask.

    Args:
        repositories: Where Thought Experiments are stored.
        thought_experiments: The case's; with none, nothing changes.
        now: The case's time.
    """
    if not thought_experiments:
        return
    store = repositories.thought_experiments
    for seeded in store.list_all():
        if seeded.archived_at is None:
            store.archive(seeded.id, now)
    added_at = now - timedelta(days=THOUGHT_EXPERIMENTS_DAYS_AGO)
    for number, made_up in enumerate(thought_experiments):
        store.add(
            ThoughtExperiment(
                id=uuid4(),
                details=ThoughtExperimentDetails(
                    wording=made_up.wording,
                    pattern_type_id=made_up.pattern_type,
                    other_pattern_type_id=made_up.other_pattern_type,
                    sensitivity=made_up.sensitivity,
                    starter=False,
                    on=True,
                ),
                created_at=added_at + REPLY_GAP * number,
                updated_at=added_at + REPLY_GAP * number,
            )
        )


def add_replies_after(
    repositories: Repositories,
    user_id: UUID,
    conversation_id: UUID,
    asked_at: datetime,
    count: int,
) -> None:
    """Let a made-up Conversation go on for some replies after a try was asked.

    A real Conversation goes on after a Curiosity is asked. Without these
    replies the pace between Curiosities would hold the next one back from
    the case's first Message.

    Args:
        repositories: Where Conversations and Reply Plans are stored.
        user_id: The made-up User's ID.
        conversation_id: The Conversation the try was asked in.
        asked_at: When it was asked.
        count: How many replies followed.
    """
    for number in range(1, count + 1):
        sent_at = asked_at + REPLY_GAP * number
        message = ConversationMessage(
            id=uuid4(),
            conversation_id=conversation_id,
            direction=MessageDirection.INCOMING,
            kind=MessageKind.TEXT,
            content="mm",
            sent_at=sent_at,
        )
        repositories.conversations.add_message(message)
        repositories.reply_plans.add(
            ReplyPlan(
                id=uuid4(),
                user_id=user_id,
                conversation_id=conversation_id,
                message_id=message.id,
                form=ReplyPlanForm(need=MADE_UP_NEED),
                need=MADE_UP_NEED,
                asked_why=False,
                made_at=sent_at,
            )
        )


def asked_try(
    exploration: Exploration,
    made_up: EvalTry,
    pattern_type: PatternType,
    observations: Sequence[Observation],
    earlier: Sequence[ExplorationTry],
    conversation_id: UUID,
    asked_at: datetime,
) -> tuple[Curiosity, ExplorationTry]:
    """Write a try already made, with the aimed Curiosity that asked it.

    The Agenda's own code picks what it aimed at and words it, so it reads
    as a try that code wrote back then.

    Args:
        exploration: Its Exploration.
        made_up: The made-up try.
        pattern_type: The Exploration's Pattern Type.
        observations: The Observations of its Pattern.
        earlier: The Exploration's tries before this one.
        conversation_id: The ended Conversation it was asked in.
        asked_at: When it was asked.

    Returns:
        The Curiosity, raised, and its try. A try they asked to drop isn't
        judged yet, so the real Agenda code judges it and rests the
        Exploration.

    Raises:
        EvalSetupError: If the Pattern has no open need of the try's kind.
    """
    need = next(
        (
            open_need
            for open_need in open_needs(observations, earlier)
            if open_need.need == made_up.need
        ),
        None,
    )
    if need is None:
        raise EvalSetupError(
            f"{pattern_type.id} has no open need to try: {made_up.need.value}"
        )
    curiosity, attempt = aimed_curiosity(
        exploration,
        need,
        made_up.way,
        pattern_type,
        None,
        exploration.user_id,
        asked_at,
    )
    reaction = (
        ThreadReaction.ASKED_TO_DROP
        if made_up.asked_to_drop
        else REACTIONS[made_up.outcome]
    )
    return (
        replace(
            curiosity,
            state=CuriosityState.RAISED,
            raised_at=asked_at,
            raised_conversation_id=conversation_id,
            reaction=reaction,
        ),
        replace(attempt, outcome=None if made_up.asked_to_drop else made_up.outcome),
    )


def save_tries_made(
    repositories: Repositories,
    pattern: CatalogPattern,
    made_up: EvalPattern,
    pattern_type: PatternType,
    conversations: MadeUpConversations,
) -> None:
    """Save a suspected Pattern's Exploration with the tries already made at it.

    Args:
        repositories: Where Explorations and Curiosities are stored.
        pattern: The suspected Pattern.
        made_up: The made-up Pattern, with its tries.
        pattern_type: Its Pattern Type.
        conversations: The made-up ended Conversations.

    Raises:
        EvalSetupError: If the Pattern has no open need of a try's kind.
    """
    oldest_first = sorted(
        made_up.tries, key=lambda attempt: attempt.days_ago, reverse=True
    )
    exploration = new_exploration(
        pattern, conversations.moment(oldest_first[0].days_ago)
    )
    observations = observations_of(
        pattern.pattern_type_id,
        repositories.observations.list_for_user(pattern.user_id),
    )
    replies = repositories.platform_settings.load().get(CURIOSITY_REPLIES_BETWEEN) * 2
    curiosities: list[Curiosity] = []
    tries: list[ExplorationTry] = []
    for made_up_try in oldest_first:
        conversation_id = conversations.on(made_up_try.days_ago)
        asked_at = conversations.moment(made_up_try.days_ago)
        curiosity, attempt = asked_try(
            exploration,
            made_up_try,
            pattern_type,
            observations,
            tries,
            conversation_id,
            asked_at,
        )
        curiosities.append(curiosity)
        tries.append(attempt)
        add_replies_after(
            repositories, pattern.user_id, conversation_id, asked_at, replies
        )
    repositories.explorations.save_agenda(
        AgendaChanges(
            added=[exploration],
            changed=[],
            judged=[],
            closed_curiosity_ids=[],
            new_curiosities=curiosities,
            new_tries=tries,
        )
    )


def give_made_up_patterns(
    companion: EvalCompanion, user_id: UUID, memory: EvalMemory, now: datetime
) -> MadeUpAgenda:
    """Give the made-up User suspected Patterns, and let real code build the Agenda.

    Pattern noticing and exploring are turned on. Each Observation is saved
    in an ended Conversation of its day, the real scoring step makes the
    Patterns, the tries already made are saved with their Explorations, and
    the real Agenda step then runs as if the newest of those Conversations
    just ended. It writes the Explorations and the aimed Curiosities.

    Args:
        companion: The app on the Eval database.
        user_id: The made-up User's ID.
        memory: The made-up memory; its Life Threads are already saved.
        now: When the case's first Message is sent.

    Returns:
        The Agenda the case starts with; empty when the memory has no
        suspected Pattern, and then nothing is turned on or saved.

    Raises:
        EvalSetupError: If a Pattern Type or sign isn't in the catalog, a
            Pattern isn't suspected from its Observations, or it has no
            open need of a try's kind.
    """
    if not memory.patterns:
        return MadeUpAgenda()
    repositories = companion.repositories
    companion.turn_pattern_exploring_on()
    replace_thought_experiments(repositories, memory.thought_experiments, now)
    pattern_types = catalog_pattern_types(repositories)
    thread_ids = thread_ids_by_title(repositories, user_id)
    conversations = MadeUpConversations(repositories, user_id, now)
    repositories.observations.add_many(
        [
            to_observation(
                user_id,
                pattern_type_in_catalog(pattern_types, pattern.pattern_type),
                observation,
                pattern_types,
                thread_ids,
                conversations.on(observation.days_ago),
                conversations.moment(observation.days_ago),
            )
            for pattern in memory.patterns
            for observation in pattern.observations
        ]
    )
    companion.score_patterns()
    scored = {
        pattern.pattern_type_id: pattern
        for pattern in repositories.patterns.list_of_pattern_types(user_id)
    }
    for made_up in memory.patterns:
        pattern = scored.get(made_up.pattern_type)
        if pattern is None or pattern.state != PatternState.SUSPECTED:
            raise EvalSetupError(
                f"{made_up.pattern_type} isn't suspected from its Observations"
            )
        if made_up.tries:
            save_tries_made(
                repositories,
                pattern,
                made_up,
                pattern_types[made_up.pattern_type],
                conversations,
            )
    newest = conversations.newest()
    if newest is not None:
        companion.keep_agenda(newest)
    return read_made_up_agenda(companion, user_id)


def read_made_up_agenda(companion: EvalCompanion, user_id: UUID) -> MadeUpAgenda:
    """Read the Agenda the real code built for the made-up User.

    Args:
        companion: The app on the Eval database.
        user_id: The made-up User's ID.

    Returns:
        What each active Exploration still needs to learn, and what each
        aimed Curiosity is for.
    """
    explorations = companion.repositories.explorations
    pattern_type_ids = {
        exploration.id: exploration.pattern_type_id
        for exploration in explorations.list_for_user(user_id)
    }
    return MadeUpAgenda(
        open_needs=tuple(
            describe_need(need)
            for entry in companion.read_agenda()
            for need in entry.open_needs
        ),
        aimed={
            attempt.curiosity_id: AimedAt(
                pattern_type_ids[attempt.exploration_id], attempt
            )
            for attempt in explorations.list_tries(user_id)
        },
    )
