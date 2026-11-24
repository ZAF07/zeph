import re
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from companion.core.errors import ConflictError, InvalidError, NotFoundError
from companion.core.models import (
    Curiosity,
    CuriosityState,
    ExplorationTry,
    Observation,
    ThoughtExperiment,
    ThoughtExperimentDetails,
)
from companion.core.pattern_catalog import PatternCatalogService
from companion.core.ports import Clock, Repositories

WEEK = timedelta(days=7)
MAX_WORDING_LENGTH = 1000
SUGGESTS_THE_ANSWER = (
    "suggests the answer. Ask what they would do, and leave both choices open."
)
MAKES_A_CHOICE_SOUND_BAD = (
    "makes one choice sound bad. Ask what they would do, in words that judge "
    "neither choice."
)
LEADING_PHRASES = (
    ("surely", SUGGESTS_THE_ANSWER),
    ("obviously", SUGGESTS_THE_ANSWER),
    ("of course", SUGGESTS_THE_ANSWER),
    ("clearly", SUGGESTS_THE_ANSWER),
    ("naturally", SUGGESTS_THE_ANSWER),
    ("wouldn't you", SUGGESTS_THE_ANSWER),
    ("don't you", SUGGESTS_THE_ANSWER),
    ("isn't it", SUGGESTS_THE_ANSWER),
    ("aren't you", SUGGESTS_THE_ANSWER),
    ("shouldn't you", SUGGESTS_THE_ANSWER),
    ("be honest", SUGGESTS_THE_ANSWER),
    ("admit it", SUGGESTS_THE_ANSWER),
    ("most people would", SUGGESTS_THE_ANSWER),
    ("anyone would", SUGGESTS_THE_ANSWER),
    ("everyone would", SUGGESTS_THE_ANSWER),
    ("the right thing", SUGGESTS_THE_ANSWER),
    ("you'd probably", SUGGESTS_THE_ANSWER),
    ("you probably", SUGGESTS_THE_ANSWER),
    ("selfish", MAKES_A_CHOICE_SOUND_BAD),
    ("weak", MAKES_A_CHOICE_SOUND_BAD),
    ("lazy", MAKES_A_CHOICE_SOUND_BAD),
    ("needy", MAKES_A_CHOICE_SOUND_BAD),
    ("clingy", MAKES_A_CHOICE_SOUND_BAD),
    ("controlling", MAKES_A_CHOICE_SOUND_BAD),
    ("overreact", MAKES_A_CHOICE_SOUND_BAD),
    ("cowardly", MAKES_A_CHOICE_SOUND_BAD),
)


def leading_flags(wording: str) -> list[str]:
    """Flag the words in a Thought Experiment that lead the User to an answer.

    A plain check by code, no model: phrases that suggest the answer
    ("wouldn't you", "most people would") and words that make one choice
    sound bad ("selfish", "needy"). Curly apostrophes count as straight.

    Args:
        wording: The Thought Experiment's wording.

    Returns:
        One line per phrase found, in the order they first appear, each
        naming the phrase and what to change; empty when none is found.
    """
    evened = wording.replace("’", "'")
    found = []
    for phrase, why in LEADING_PHRASES:
        match = re.search(rf"\b{re.escape(phrase)}\w*", evened, re.IGNORECASE)
        if match:
            found.append((match.start(), f"“{match.group(0)}” {why}"))
    return [flag for _, flag in sorted(found)]


def unclear_pairs(
    pattern_type_id: str, observations: Sequence[Observation]
) -> list[frozenset[str]]:
    """Rank a Pattern's look-alike pairs by how much unclear evidence they have.

    Args:
        pattern_type_id: The Pattern's Pattern Type.
        observations: The User's Observations.

    Returns:
        Each pair of the Pattern Type and a look-alike that an unclear
        Observation named, most unclear Observations first, then the pair
        with the newest one.
    """
    counts: dict[frozenset[str], int] = {}
    newest: dict[frozenset[str], tuple[date, datetime]] = {}
    for observation in observations:
        if observation.second_pattern_type_id is None:
            continue
        pair = frozenset(
            (observation.pattern_type_id, observation.second_pattern_type_id)
        )
        if pattern_type_id not in pair:
            continue
        counts[pair] = counts.get(pair, 0) + 1
        said = (observation.day, observation.tagged_at)
        newest[pair] = max(newest[pair], said) if pair in newest else said
    return sorted(counts, key=lambda pair: (counts[pair], newest[pair]), reverse=True)


def pick_thought_experiment(
    pattern_type_id: str,
    observations: Sequence[Observation],
    thought_experiments: Sequence[ThoughtExperiment],
    put_to: set[UUID],
) -> ThoughtExperiment | None:
    """Pick the Thought Experiment to put to a User for one of their Patterns.

    It is for the look-alike pair with the most unclear evidence that still
    has one to ask: on, not archived and never put to this User. The oldest
    such one comes first.

    Args:
        pattern_type_id: The Pattern's Pattern Type.
        observations: The User's Observations.
        thought_experiments: Every Thought Experiment.
        put_to: The Thought Experiments already put to this User.

    Returns:
        The one to ask; None when no pair with unclear evidence has one left.
    """
    for pair in unclear_pairs(pattern_type_id, observations):
        left = sorted(
            (
                thought_experiment
                for thought_experiment in thought_experiments
                if thought_experiment.askable
                and thought_experiment.pair == pair
                and thought_experiment.id not in put_to
            ),
            key=lambda thought_experiment: thought_experiment.created_at,
        )
        if left:
            return left[0]
    return None


def put_to_user(
    tries: Sequence[ExplorationTry], curiosities: Mapping[UUID, Curiosity]
) -> set[UUID]:
    """Find the Thought Experiments already put to a User, or waiting to be.

    Args:
        tries: Every try of theirs.
        curiosities: Their aimed Curiosities, by ID.

    Returns:
        The IDs of those whose Curiosity was asked or is waiting; one whose
        Curiosity was closed unasked may be put again.
    """
    return {
        attempt.thought_experiment_id
        for attempt in tries
        if attempt.thought_experiment_id is not None
        and attempt.curiosity_id in curiosities
        and curiosities[attempt.curiosity_id].state != CuriosityState.CLOSED
    }


def thought_experiments_this_week(
    tries: Sequence[ExplorationTry],
    curiosities: Mapping[UUID, Curiosity],
    now: datetime,
) -> int:
    """Count one Pattern's Thought Experiments asked in the last 7 days.

    Args:
        tries: Its Exploration's tries.
        curiosities: The User's aimed Curiosities, by ID.
        now: The time now.

    Returns:
        How many were asked in the last 7 days, or are waiting to be.
    """
    count = 0
    for attempt in tries:
        curiosity = curiosities.get(attempt.curiosity_id)
        if attempt.thought_experiment_id is None or curiosity is None:
            continue
        waiting = curiosity.state == CuriosityState.WAITING
        recent = curiosity.raised_at is not None and curiosity.raised_at > now - WEEK
        count += waiting or recent
    return count


def thought_experiment_question(
    thought_experiment: ThoughtExperiment,
) -> tuple[str, str]:
    """Write the aimed Curiosity that puts a Thought Experiment to the User.

    Args:
        thought_experiment: The Thought Experiment.

    Returns:
        The question, telling the Reply to keep its words, and why Zeph
        wonders. Neither names a Pattern.
    """
    return (
        "Put this made-up situation to them, keeping its words: "
        f'"{thought_experiment.details.wording}" Then hear how they would '
        "choose, and why.",
        "How someone would choose in a made-up situation can tell apart two "
        "things that look alike in their stories.",
    )


class ThoughtExperimentNotFoundError(NotFoundError):
    """Raised when no Thought Experiment has the given ID."""

    shown_message = "No such Thought Experiment"


class InvalidThoughtExperimentError(InvalidError):
    """Raised when a Thought Experiment's details are not valid."""


class ArchivedThoughtExperimentError(ConflictError):
    """Raised when changing a Thought Experiment that is archived."""

    shown_message = "This Thought Experiment is archived and can't be changed."


class LeadingWordingError(InvalidError):
    """Raised when a Thought Experiment's wording leads the User to an answer.

    The Admin can change the wording, or save it anyway.

    Attributes:
        flags: One line per leading phrase found.
    """

    shown_message = (
        "This wording may lead them to an answer. Change it, or save it anyway."
    )

    def __init__(self, flags: Sequence[str]) -> None:
        """Set up the error.

        Args:
            flags: One line per leading phrase found.
        """
        super().__init__(self.shown_message)
        self.flags = list(flags)

    def field_errors(self) -> dict[str, str]:
        """Give the leading phrases, to show under the wording.

        Returns:
            The flags, one per line, under `leading`.
        """
        return {"leading": "\n".join(self.flags)}


class ThoughtExperimentService:
    """Lets Admins add, edit, switch off and archive Thought Experiments.

    None is ever deleted, so the tries that asked one still name it. The
    Agenda reads them fresh at every Conversation end. Switching one off or
    archiving it closes the aimed Curiosities waiting to ask it, so it is
    never asked after.
    """

    def __init__(
        self,
        repositories: Repositories,
        pattern_catalog: PatternCatalogService,
        clock: Clock,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where Thought Experiments are stored.
            pattern_catalog: Reads the Pattern Types in the catalog now.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._pattern_catalog = pattern_catalog
        self._clock = clock

    def list_all(self) -> list[ThoughtExperiment]:
        """List every Thought Experiment, archived ones too, oldest first.

        Returns:
            The Thought Experiments.
        """
        return self._repositories.thought_experiments.list_all()

    def asked_counts(self) -> dict[UUID, int]:
        """Count how many times each Thought Experiment was put to a User.

        Returns:
            How many times each was asked, by its ID; one never asked is
            left out.
        """
        return self._repositories.thought_experiments.asked_counts()

    def add(
        self, details: ThoughtExperimentDetails, save_anyway: bool
    ) -> ThoughtExperiment:
        """Add a Thought Experiment.

        Args:
            details: What the Admin set.
            save_anyway: Whether to save it even with leading wording.

        Returns:
            The saved Thought Experiment.

        Raises:
            InvalidThoughtExperimentError: If its wording is blank or too long,
                or its two Pattern Types aren't two different ones in the
                catalog.
            LeadingWordingError: If its wording leads to an answer and the
                Admin didn't choose to save it anyway.
        """
        checked = self._checked(details, None, save_anyway)
        now = self._clock.now()
        thought_experiment = ThoughtExperiment(
            id=uuid4(), details=checked, created_at=now, updated_at=now
        )
        self._repositories.thought_experiments.add(thought_experiment)
        return thought_experiment

    def update(
        self,
        thought_experiment_id: UUID,
        details: ThoughtExperimentDetails,
        save_anyway: bool,
    ) -> ThoughtExperiment:
        """Change a Thought Experiment, or switch it on or off.

        Past tries keep the words they were asked with.

        Args:
            thought_experiment_id: Its ID.
            details: Its new values.
            save_anyway: Whether to save it even with leading wording.

        Returns:
            The saved Thought Experiment.

        Raises:
            ThoughtExperimentNotFoundError: If there is no such one.
            ArchivedThoughtExperimentError: If it is archived.
            InvalidThoughtExperimentError: If its wording is blank or too long,
                or its two Pattern Types aren't two different ones in the
                catalog.
            LeadingWordingError: If its wording leads to an answer and the
                Admin didn't choose to save it anyway.
        """
        saved = self.get(thought_experiment_id)
        if saved.archived_at is not None:
            raise ArchivedThoughtExperimentError
        checked = self._checked(details, saved, save_anyway)
        updated = self._repositories.thought_experiments.update(
            thought_experiment_id, checked, self._clock.now()
        )
        if not updated.details.on:
            self._repositories.thought_experiments.close_waiting(thought_experiment_id)
        return updated

    def archive(self, thought_experiment_id: UUID) -> ThoughtExperiment:
        """Archive a Thought Experiment, so it is never asked again.

        Archiving one already archived changes nothing.

        Args:
            thought_experiment_id: Its ID.

        Returns:
            The archived Thought Experiment.

        Raises:
            ThoughtExperimentNotFoundError: If there is no such one.
        """
        saved = self.get(thought_experiment_id)
        if saved.archived_at is not None:
            return saved
        archived = self._repositories.thought_experiments.archive(
            thought_experiment_id, self._clock.now()
        )
        self._repositories.thought_experiments.close_waiting(thought_experiment_id)
        return archived

    def get(self, thought_experiment_id: UUID) -> ThoughtExperiment:
        """Find a Thought Experiment.

        Args:
            thought_experiment_id: Its ID.

        Returns:
            It.

        Raises:
            ThoughtExperimentNotFoundError: If there is no such one.
        """
        found = self._repositories.thought_experiments.get(thought_experiment_id)
        if found is None:
            raise ThoughtExperimentNotFoundError(thought_experiment_id)
        return found

    def _checked(
        self,
        details: ThoughtExperimentDetails,
        saved: ThoughtExperiment | None,
        save_anyway: bool,
    ) -> ThoughtExperimentDetails:
        """Check a Thought Experiment's details and tidy their spacing.

        A Pattern Type it already names may stay, even if the catalog no
        longer has it; a new one must be in the catalog.

        Args:
            details: The details to check.
            saved: The Thought Experiment being edited; None when adding.
            save_anyway: Whether to allow leading wording.

        Returns:
            The details, with the wording's spacing evened out.

        Raises:
            InvalidThoughtExperimentError: If a detail isn't valid.
            LeadingWordingError: If the wording leads, unless saved anyway.
        """
        checked = replace(
            details,
            wording=" ".join(details.wording.split()),
            pattern_type_id=details.pattern_type_id.strip(),
            other_pattern_type_id=details.other_pattern_type_id.strip(),
        )
        if not checked.wording:
            raise InvalidThoughtExperimentError("Write what to ask.")
        if len(checked.wording) > MAX_WORDING_LENGTH:
            raise InvalidThoughtExperimentError(
                f"Keep the wording to {MAX_WORDING_LENGTH} characters."
            )
        named = (checked.pattern_type_id, checked.other_pattern_type_id)
        if named[0] == named[1]:
            raise InvalidThoughtExperimentError(
                "Choose two different Pattern Types for it to tell apart."
            )
        in_catalog = {
            entry.pattern_type.id for entry in self._pattern_catalog.catalog()
        }
        kept = saved.pair if saved else frozenset()
        unknown = [
            pattern_type_id
            for pattern_type_id in named
            if pattern_type_id not in in_catalog and pattern_type_id not in kept
        ]
        if unknown:
            raise InvalidThoughtExperimentError(
                f"{unknown[0]} isn't a Pattern Type in the catalog."
            )
        flags = leading_flags(checked.wording)
        if flags and not save_anyway:
            raise LeadingWordingError(flags)
        return checked
