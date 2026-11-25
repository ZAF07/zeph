import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any
from uuid import UUID, uuid4

from companion.core.errors import InvalidError, NotFoundError
from companion.core.models import (
    CountedUnmatchedEntry,
    Pattern,
    PatternState,
    PlatformSettings,
    UnmatchedEntry,
    UnmatchedMark,
)
from companion.core.pattern_catalog import PatternCatalogService
from companion.core.platform_settings import UNMATCHED_GROUPING_CLOSENESS_PERCENT
from companion.core.ports import Clock, Embedder, Repositories

logger = logging.getLogger(__name__)

TELLING_CHARACTERS = re.compile(r"[\d\"“”«»]")


@dataclass(frozen=True)
class ReviewedEntry:
    """An unmatched entry as an Admin reads it.

    Attributes:
        id: The entry's ID.
        description: Its general description, with nothing about a User.
        user_count: How many Users it appears for now.
        mark: Its mark as it reads now: a dropped entry that has since
            appeared for more Users reads as to review.
        folded_into_pattern_type_id: The Pattern Type it was folded into;
            None unless its mark is folded.
        dropped_before: Whether it was dropped and came back by appearing
            for more Users.
    """

    id: UUID
    description: str
    user_count: int
    mark: UnmatchedMark
    folded_into_pattern_type_id: str | None
    dropped_before: bool


class UnmatchedEntryNotFoundError(NotFoundError):
    """Raised when no unmatched entry has the given ID."""

    shown_message = "No such entry"


class UnknownFoldedPatternTypeError(InvalidError):
    """Raised when an entry is folded into no Pattern Type in the catalog."""

    shown_message = "Pick the Pattern Type in the Pattern Catalog it is folded into."


def read_general_description(value: Any, user_name: str | None) -> str | None:
    """Read the general description the keeping model wrote for a Pattern.

    It is the only thing of an unmatched Pattern an Admin reads, so one
    that could tell who it is about is dropped: one with a digit (a date,
    an age, an amount), a quote mark, or the User's name as a word.

    Args:
        value: The description as the model wrote it.
        user_name: What the Companion calls the User; None if not known.

    Returns:
        The description, trimmed; None if there is none or it was dropped.
    """
    if not isinstance(value, str):
        return None
    description = value.strip()
    if not description or TELLING_CHARACTERS.search(description):
        return None
    name = (user_name or "").strip()
    if name and re.search(rf"\b{re.escape(name)}\b", description, re.IGNORECASE):
        return None
    return description


def needs_general_description(pattern: Pattern) -> bool:
    """Say whether an unmatched Pattern still has no general description.

    Args:
        pattern: The Pattern.

    Returns:
        True if it is unmatched and has none.
    """
    return (
        pattern.state == PatternState.UNMATCHED and pattern.general_description is None
    )


def shown_mark(entry: UnmatchedEntry, user_count: int) -> UnmatchedMark:
    """Work out the mark an entry reads as now.

    A dropped entry stays dropped unless it appears for more Users than
    when it was dropped; then it is to review again.

    Args:
        entry: The entry.
        user_count: How many Users it appears for now.

    Returns:
        The mark.
    """
    came_back = (
        entry.mark == UnmatchedMark.DROPPED
        and entry.users_when_marked is not None
        and user_count > entry.users_when_marked
    )
    return UnmatchedMark.TO_REVIEW if came_back else entry.mark


def to_reviewed_entry(counted: CountedUnmatchedEntry) -> ReviewedEntry:
    """Turn a counted entry into what an Admin reads.

    Args:
        counted: The entry and how many Users it appears for now.

    Returns:
        The entry as an Admin reads it.
    """
    entry = counted.entry
    mark = shown_mark(entry, counted.user_count)
    return ReviewedEntry(
        id=entry.id,
        description=entry.description,
        user_count=counted.user_count,
        mark=mark,
        folded_into_pattern_type_id=entry.folded_into_pattern_type_id,
        dropped_before=mark != entry.mark,
    )


class UnmatchedGrouper:
    """Groups unmatched Patterns under entries by their general descriptions.

    An entry is made only from a general description, never from a
    Pattern's own words or evidence, and holds no User.
    """

    def __init__(
        self, repositories: Repositories, embedder: Embedder, clock: Clock
    ) -> None:
        """Set up the grouper.

        Args:
            repositories: Where unmatched entries are stored.
            embedder: Embeds each general description.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._embedder = embedder
        self._clock = clock

    def link(
        self, settings: PlatformSettings, patterns: Sequence[Pattern]
    ) -> list[Pattern]:
        """Give each unmatched Pattern that has a description its entry.

        A Pattern joins the entry closest in meaning to its general
        description, if one is at least as close as the Admin-set bar;
        otherwise a new entry is started with that description. A Pattern
        that isn't unmatched, has no description or already has an entry is
        left as it is. If the descriptions can't be embedded none is
        linked, and they are tried again next time.

        Args:
            settings: The platform settings in force.
            patterns: The Patterns.

        Returns:
            The Patterns, in the same order, with their entries.
        """
        waiting = [
            pattern
            for pattern in patterns
            if pattern.state == PatternState.UNMATCHED
            and pattern.general_description is not None
            and pattern.unmatched_entry_id is None
        ]
        if not waiting:
            return list(patterns)
        try:
            embeddings = self._embedder.embed_passages(
                [pattern.general_description or "" for pattern in waiting]
            )
        except Exception:
            logger.exception("Could not embed general descriptions")
            return list(patterns)
        min_closeness = settings.get(UNMATCHED_GROUPING_CLOSENESS_PERCENT) / 100
        entry_ids = {
            pattern.id: self._entry_for(
                pattern.general_description or "", embedding, min_closeness
            )
            for pattern, embedding in zip(waiting, embeddings, strict=True)
        }
        return [
            replace(pattern, unmatched_entry_id=entry_ids[pattern.id])
            if pattern.id in entry_ids
            else pattern
            for pattern in patterns
        ]

    def _entry_for(
        self, description: str, embedding: list[float], min_closeness: float
    ) -> UUID:
        """Find the entry a general description belongs under, or start one.

        Args:
            description: The general description.
            embedding: It embedded.
            min_closeness: How close in meaning an entry must be, from 0 to 1.

        Returns:
            The entry's ID.
        """
        entries = self._repositories.unmatched_entries
        closest_id = entries.find_closest_id(embedding, min_closeness)
        if closest_id is not None:
            return closest_id
        entry = UnmatchedEntry(
            id=uuid4(),
            description=description,
            mark=UnmatchedMark.TO_REVIEW,
            folded_into_pattern_type_id=None,
            users_when_marked=None,
        )
        entries.add(entry, embedding, self._clock.now())
        return entry.id


class UnmatchedReviewService:
    """Lets Admins review what keeps turning up that fits no Pattern Type.

    Admins read only general descriptions and how many Users each appears
    for, never a User's Pattern, words or name. Marking an entry changes
    nothing else: writing a Pattern Type stays manual.
    """

    def __init__(
        self,
        repositories: Repositories,
        pattern_catalog: PatternCatalogService,
        clock: Clock,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where unmatched entries are stored.
            pattern_catalog: Reads the Pattern Types in the catalog now.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._pattern_catalog = pattern_catalog
        self._clock = clock

    def list_entries(self, mark: UnmatchedMark | None) -> list[ReviewedEntry]:
        """List the entries that appear for at least one User.

        Args:
            mark: Only entries that read as this mark now; None for all.

        Returns:
            The entries, most Users first, then oldest first.
        """
        entries = [
            to_reviewed_entry(counted)
            for counted in self._repositories.unmatched_entries.list_counted()
        ]
        return [entry for entry in entries if mark is None or entry.mark == mark]

    def mark(
        self, entry_id: UUID, mark: UnmatchedMark, pattern_type_id: str | None
    ) -> ReviewedEntry:
        """Mark an entry, remembering how many Users it appeared for.

        Args:
            entry_id: The entry's ID.
            mark: The Admin's decision; to review takes a decision back.
            pattern_type_id: The Pattern Type it is folded into; used only
                when the mark is folded.

        Returns:
            The entry as it reads now.

        Raises:
            UnmatchedEntryNotFoundError: If there is no such entry.
            UnknownFoldedPatternTypeError: If it is folded into no Pattern
                Type in the catalog.
        """
        entries = self._repositories.unmatched_entries
        counted = entries.get_counted(entry_id)
        if counted is None:
            raise UnmatchedEntryNotFoundError
        folded_into = pattern_type_id if mark == UnmatchedMark.FOLDED else None
        if mark == UnmatchedMark.FOLDED and folded_into not in {
            entry.pattern_type.id for entry in self._pattern_catalog.catalog()
        }:
            raise UnknownFoldedPatternTypeError
        marked = replace(
            counted.entry,
            mark=mark,
            folded_into_pattern_type_id=folded_into,
            users_when_marked=counted.user_count,
            marked_at=self._clock.now(),
        )
        entries.save_mark(marked)
        return to_reviewed_entry(replace(counted, entry=marked))
