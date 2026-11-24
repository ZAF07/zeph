from collections.abc import Sequence, Set
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from companion.core.models import (
    Curiosity,
    CuriosityAim,
    CuriosityChanges,
    CuriosityState,
    Familiarity,
    Feature,
    PlatformSettings,
    ThoughtExperiment,
    ThreadReaction,
    UserSnapshot,
)
from companion.core.platform_settings import (
    STARTER_THOUGHT_EXPERIMENT_DAYS,
    STARTER_THOUGHT_EXPERIMENTS,
    STARTER_THOUGHT_EXPERIMENTS_PER_CONVERSATION,
)
from companion.core.ports import Clock, Repositories
from companion.core.thought_experiments import put_to_user, thought_experiment_question

WHY_A_STARTER = (
    "Zeph is new to them, and how someone would choose in a made-up situation "
    "is a light way to start getting to know them."
)


@dataclass(frozen=True)
class StarterNumbers:
    """The Admin-set limits starter Thought Experiments are offered within.

    Attributes:
        most: The most put to one User, counting one still waiting.
        days: How long after they sign up they are offered.
        per_conversation: The most in one Conversation, so the most waiting
            at once.
    """

    most: int
    days: timedelta
    per_conversation: int


@dataclass(frozen=True)
class StarterInput:
    """Everything a User's starter Thought Experiments are planned from.

    Attributes:
        user_id: The User.
        signed_up_at: When they signed up.
        familiarity: How well the Companion knows them now.
        now: When they are planned.
        thought_experiments: Every Thought Experiment, archived ones too.
        starters: Their Curiosities that put a starter one, in any state.
        put_by_agenda: The Thought Experiments an Exploration already put to
            them, or waits to.
    """

    user_id: UUID
    signed_up_at: datetime
    familiarity: Familiarity
    now: datetime
    thought_experiments: Sequence[ThoughtExperiment]
    starters: Sequence[Curiosity]
    put_by_agenda: Set[UUID] = frozenset()


def put_as_starters(starters: Sequence[Curiosity]) -> set[UUID]:
    """Find the Thought Experiments already put to a User as starters.

    Args:
        starters: Their Curiosities that put a starter one, in any state.

    Returns:
        The IDs of those asked or waiting to be; one closed unasked may be
        put again.
    """
    return {
        curiosity.thought_experiment_id
        for curiosity in starters
        if curiosity.thought_experiment_id is not None
        and (
            curiosity.raised_at is not None or curiosity.state == CuriosityState.WAITING
        )
    }


def starters_offered(
    familiarity: Familiarity, signed_up_at: datetime, now: datetime, days: timedelta
) -> bool:
    """Say whether starter Thought Experiments are still offered to a User.

    Args:
        familiarity: How well the Companion knows them.
        signed_up_at: When they signed up.
        now: The time now.
        days: How long after they sign up starters are offered.

    Returns:
        True while the Companion is new to them and the days haven't passed.
    """
    return familiarity == Familiarity.NEW and now < signed_up_at + days


def starter_curiosity(
    thought_experiment: ThoughtExperiment, user_id: UUID, now: datetime
) -> Curiosity:
    """Write the Curiosity that puts a starter Thought Experiment to a new User.

    Args:
        thought_experiment: The starter Thought Experiment.
        user_id: The User.
        now: When it is written.

    Returns:
        The Curiosity, waiting, with the Thought Experiment's wording and
        sensitivity.
    """
    question, _ = thought_experiment_question(thought_experiment)
    return Curiosity(
        id=uuid4(),
        user_id=user_id,
        question=question,
        why=WHY_A_STARTER,
        not_before=None,
        sensitivity=thought_experiment.details.sensitivity,
        state=CuriosityState.WAITING,
        created_at=now,
        aim=CuriosityAim.STARTER,
        thought_experiment_id=thought_experiment.id,
    )


def plan_starters(starters: StarterInput, numbers: StarterNumbers) -> CuriosityChanges:
    """Decide which starter Thought Experiments wait for a User's next Conversation.

    They are offered only while the Companion is new to the User, within the
    Admin-set days after they signed up, and until they ask Zeph to drop
    one; otherwise the waiting ones are closed. While offered, the oldest
    starters that are on and were never put to them are written, until the
    Admin-set number were put in all and never more waiting than one
    Conversation may ask.

    Args:
        starters: What they are planned from.
        numbers: The Admin-set limits.

    Returns:
        The new waiting Curiosities, and the waiting ones now closed.
    """
    waiting = [
        curiosity
        for curiosity in starters.starters
        if curiosity.state == CuriosityState.WAITING
    ]
    asked = [
        curiosity for curiosity in starters.starters if curiosity.raised_at is not None
    ]
    offered = starters_offered(
        starters.familiarity, starters.signed_up_at, starters.now, numbers.days
    ) and not any(
        curiosity.reaction == ThreadReaction.ASKED_TO_DROP for curiosity in asked
    )
    if not offered:
        return CuriosityChanges(
            added=[],
            updated=[
                replace(curiosity, state=CuriosityState.CLOSED) for curiosity in waiting
            ],
            reactions={},
        )
    room = min(
        numbers.most - len(asked) - len(waiting),
        numbers.per_conversation - len(waiting),
    )
    already_put = put_as_starters(starters.starters) | starters.put_by_agenda
    left = sorted(
        (
            thought_experiment
            for thought_experiment in starters.thought_experiments
            if thought_experiment.askable
            and thought_experiment.details.starter
            and thought_experiment.id not in already_put
        ),
        key=lambda thought_experiment: thought_experiment.created_at,
    )
    return CuriosityChanges(
        added=[
            starter_curiosity(thought_experiment, starters.user_id, starters.now)
            for thought_experiment in left[: max(room, 0)]
        ],
        updated=[],
        reactions={},
    )


def starter_numbers(settings: PlatformSettings) -> StarterNumbers:
    """Read the Admin-set limits starter Thought Experiments are offered within.

    Args:
        settings: The platform settings.

    Returns:
        The limits.
    """
    return StarterNumbers(
        most=settings.get(STARTER_THOUGHT_EXPERIMENTS),
        days=settings.get(STARTER_THOUGHT_EXPERIMENT_DAYS),
        per_conversation=settings.get(STARTER_THOUGHT_EXPERIMENTS_PER_CONVERSATION),
    )


class StarterThoughtExperimentKeeper:
    """Writes a new User's next starter Thought Experiment when a Conversation ends.

    No model call: code picks the starter and writes its Curiosity, which is
    then asked under the usual Need rules, like any Curiosity. It stops, and
    closes the waiting ones, once the Companion is getting to know the User.
    """

    def __init__(self, repositories: Repositories, clock: Clock) -> None:
        """Set up the keeper.

        Args:
            repositories: Where Thought Experiments and Curiosities are stored.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._clock = clock

    def keep(self, snapshot: UserSnapshot, familiarity: Familiarity) -> None:
        """Plan the User's starter Thought Experiments and save what changed.

        Runs only while Pattern exploring and Curiosities work for them,
        since a starter can be asked only then. The User is locked while it
        reads and saves, so two Conversation ends never write the same one.

        Args:
            snapshot: The User whose Conversation ended.
            familiarity: How well the Companion knows them now.
        """
        if not (
            snapshot.works(Feature.PATTERN_EXPLORING)
            and snapshot.works(Feature.CURIOSITIES)
        ):
            return
        user = snapshot.user
        with self._repositories.transaction() as transaction:
            transaction.lock_user(user.id)
            repositories = transaction.repositories
            starters = repositories.curiosities.list_starters(user.id)
            if familiarity != Familiarity.NEW and not starters:
                return
            aimed = {
                curiosity.id: curiosity
                for curiosity in repositories.curiosities.list_aimed(user.id)
            }
            repositories.curiosities.save_changes(
                plan_starters(
                    StarterInput(
                        user_id=user.id,
                        signed_up_at=user.created_at,
                        familiarity=familiarity,
                        now=self._clock.now(),
                        thought_experiments=(
                            repositories.thought_experiments.list_all()
                        ),
                        starters=starters,
                        put_by_agenda=put_to_user(
                            repositories.explorations.list_tries(user.id), aimed
                        ),
                    ),
                    starter_numbers(snapshot.settings),
                )
            )
