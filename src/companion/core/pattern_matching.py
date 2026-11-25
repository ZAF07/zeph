import json
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from itertools import groupby
from typing import Any
from uuid import UUID

from companion.core.errors import InvalidError
from companion.core.models import (
    ChatLine,
    ChatRole,
    ModelStep,
    Pattern,
    PatternMoveCause,
    PatternState,
    PatternType,
    TraceKind,
    UserSnapshot,
)
from companion.core.observations import (
    PatternTagger,
    describe_pattern_type,
    may_keep_observations,
)
from companion.core.pattern_catalog import PatternCatalogService
from companion.core.pattern_scoring import PatternScorer
from companion.core.patterns import describe_pattern
from companion.core.platform_settings import (
    PATTERN_MATCHING_MODEL,
    PATTERN_MATCHING_PROMPT,
    PATTERN_MATCHING_THINKING,
    thinking_to_use,
)
from companion.core.ports import Repositories
from companion.core.timing import day_span
from companion.core.usage import UsageRecordingChatModel
from companion.core.user_snapshot import UserSnapshotLoader

logger = logging.getLogger(__name__)

NOT_NOTICING = "Pattern noticing doesn't work for them, or they haven't pressed Got it"
FAILED = "it failed; see the backend log"


class UnknownPatternTypeError(InvalidError):
    """Raised when the matching pass is asked for a Pattern Type not in the catalog."""

    def __init__(self, pattern_type_id: str) -> None:
        """Remember which Pattern Type it was.

        Args:
            pattern_type_id: The ID asked for.
        """
        super().__init__(f"No Pattern Type {pattern_type_id} in the Pattern Catalog")


@dataclass(frozen=True)
class PatternMatch:
    """What the matching pass found for one Pattern. Holds no words of the User's.

    Attributes:
        pattern_id: The Pattern.
        state: The state it has, and keeps.
        pattern_type_id: The Pattern Type it fits; None when it fits none.
    """

    pattern_id: UUID
    state: PatternState
    pattern_type_id: str | None


@dataclass(frozen=True)
class UserMatchingReport:
    """What the matching pass did for one User. Holds no words of theirs.

    Attributes:
        user_id: The User.
        skipped_why: Why none of their Patterns was looked at; None when
            they were.
        matches: Each Pattern looked at, with the Pattern Type it fits.
        conversations_tagged: How many past Conversations were tagged again.
        observations_kept: How many new Observations that gave.
        days_without_messages: How many days of matched evidence had no
            messages left to tag, since Message Retention deleted them.
    """

    user_id: UUID
    skipped_why: str | None = None
    matches: tuple[PatternMatch, ...] = ()
    conversations_tagged: int = 0
    observations_kept: int = 0
    days_without_messages: int = 0

    @property
    def failed(self) -> bool:
        """Say whether matching this User's Patterns failed.

        Returns:
            True when it raised and was logged.
        """
        return self.skipped_why == FAILED


@dataclass(frozen=True)
class TaggedAgain:
    """How tagging a User's matched evidence again went.

    Attributes:
        conversations: How many past Conversations were tagged again.
        observations_kept: How many new Observations that gave.
        days_without_messages: How many evidence days had no messages left.
    """

    conversations: int = 0
    observations_kept: int = 0
    days_without_messages: int = 0


@dataclass(frozen=True)
class DayToTagAgain:
    """A day whose Conversations are tagged again, and against what.

    Attributes:
        day: The day, in the User's time zone.
        pattern_type_ids: The Pattern Types its evidence was found to fit.
        thread_ids: The Life Threads that evidence is in.
    """

    day: date
    pattern_type_ids: frozenset[str]
    thread_ids: frozenset[UUID]


def describe_pattern_to_match(
    pattern: Pattern, pattern_types: Sequence[PatternType], time_zone: str | None
) -> str:
    """Write what the matching model is given.

    Args:
        pattern: The Pattern to match.
        pattern_types: The Pattern Types it may fit.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        The Pattern Types, then the Pattern with its evidence.
    """
    catalog = "\n\n".join(
        describe_pattern_type(pattern_type) for pattern_type in pattern_types
    )
    return (
        f"The Pattern Types:\n{catalog}\n\n"
        f"The Pattern:\n{describe_pattern(pattern, time_zone)}"
    )


def read_matching_answer(answer: str) -> dict[str, Any] | None:
    """Read the matching model's JSON answer.

    Text around the JSON object, such as a code fence, is ignored.

    Args:
        answer: The model's answer.

    Returns:
        The answer, holding "pattern_type"; None if it can't be read.
    """
    start, end = answer.find("{"), answer.rfind("}")
    if start == -1 or end < start:
        return None
    try:
        parsed = json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or "pattern_type" not in parsed:
        return None
    return parsed


def read_fitting_pattern_type(
    parsed: dict[str, Any], pattern_types: Mapping[str, PatternType]
) -> str | None:
    """Read the Pattern Type a readable matching answer says the Pattern fits.

    Args:
        parsed: The answer, as the model wrote it.
        pattern_types: The Pattern Types it was given, by ID.

    Returns:
        The Pattern Type's ID; None when it names none, or one it wasn't
        given.
    """
    named = parsed["pattern_type"]
    return named if isinstance(named, str) and named in pattern_types else None


def plan_days_to_tag_again(
    matched: Sequence[tuple[Pattern, str]],
) -> list[DayToTagAgain]:
    """Work out which days' Conversations to tag again, and against what.

    Every day a matched Pattern has evidence on is tagged against the
    Pattern Type it fits. A closed Pattern's evidence is left alone: the
    User rejected it.

    Args:
        matched: Each matched Pattern with the ID of the Pattern Type it
            fits.

    Returns:
        The days, oldest first, each with every Pattern Type and Life Thread
        its evidence names.
    """
    pattern_type_ids: dict[date, set[str]] = {}
    thread_ids: dict[date, set[UUID]] = {}
    for pattern, pattern_type_id in matched:
        if pattern.state == PatternState.CLOSED:
            continue
        for item in pattern.evidence:
            pattern_type_ids.setdefault(item.day, set()).add(pattern_type_id)
            thread_ids.setdefault(item.day, set()).add(item.thread_id)
    return [
        DayToTagAgain(
            day=day,
            pattern_type_ids=frozenset(pattern_type_ids[day]),
            thread_ids=frozenset(thread_ids[day]),
        )
        for day in sorted(pattern_type_ids)
    ]


class PatternMatcher:
    """Matches Patterns with no Pattern Type to the Pattern Catalog, on demand.

    Run by an Admin command, never by a reply or a Conversation end: once to
    move the Patterns kept before the catalog across, and again whenever a
    Pattern Type is added. A match is only a link: the Pattern keeps its
    words, state and evidence. The Conversations behind a matched Pattern's
    evidence are then tagged again, so the evidence becomes Observations
    that code checks and scores like any other (ADR-0024).
    """

    def __init__(
        self,
        repositories: Repositories,
        pattern_catalog: PatternCatalogService,
        user_snapshots: UserSnapshotLoader,
        chat_model: UsageRecordingChatModel,
        pattern_tagger: PatternTagger,
        pattern_scorer: PatternScorer,
    ) -> None:
        """Set up the matcher.

        Args:
            repositories: Where Patterns, Conversations and Life Threads are
                stored.
            pattern_catalog: Reads the Pattern Types in the catalog now.
            user_snapshots: Reads each User's snapshot.
            chat_model: Says which Pattern Type a Pattern fits and records
                the tokens used.
            pattern_tagger: Tags past Conversations again.
            pattern_scorer: Scores a User's Patterns again after that.
        """
        self._repositories = repositories
        self._pattern_catalog = pattern_catalog
        self._user_snapshots = user_snapshots
        self._chat_model = chat_model
        self._pattern_tagger = pattern_tagger
        self._pattern_scorer = pattern_scorer

    def match(self, pattern_type_ids: Sequence[str] = ()) -> list[UserMatchingReport]:
        """Match every Pattern with no Pattern Type that wasn't matched yet.

        Only Users for whom Pattern noticing works and who have pressed "Got
        it" are looked at; the others are left for a later run. One User
        failing never stops the rest.

        Args:
            pattern_type_ids: The Pattern Types to match against, e.g. the
                ones just added; all of the catalog when empty.

        Returns:
            What was done for each User with such a Pattern.

        Raises:
            UnknownPatternTypeError: If an ID given isn't in the catalog.
        """
        pattern_types = self._pattern_types(pattern_type_ids)
        patterns = self._repositories.patterns.list_not_matched()
        if not pattern_types or not patterns:
            return []
        patterns_by_user = {
            user_id: list(theirs)
            for user_id, theirs in groupby(patterns, lambda pattern: pattern.user_id)
        }
        snapshots = self._user_snapshots.load_many(
            list(patterns_by_user),
            self._repositories.platform_settings.load(),
            TraceKind.PATTERN_MATCHING,
        )
        return [
            self._match_safely(
                snapshot, patterns_by_user[snapshot.user.id], pattern_types
            )
            for snapshot in snapshots
        ]

    def _pattern_types(self, pattern_type_ids: Sequence[str]) -> dict[str, PatternType]:
        """Read the Pattern Types to match against.

        Args:
            pattern_type_ids: The IDs asked for; empty for all.

        Returns:
            The Pattern Types, by ID.

        Raises:
            UnknownPatternTypeError: If an ID given isn't in the catalog.
        """
        catalog = {
            entry.pattern_type.id: entry.pattern_type
            for entry in self._pattern_catalog.catalog()
        }
        if not pattern_type_ids:
            return catalog
        for pattern_type_id in pattern_type_ids:
            if pattern_type_id not in catalog:
                raise UnknownPatternTypeError(pattern_type_id)
        return {
            pattern_type_id: catalog[pattern_type_id]
            for pattern_type_id in pattern_type_ids
        }

    def _match_safely(
        self,
        snapshot: UserSnapshot,
        patterns: Sequence[Pattern],
        pattern_types: Mapping[str, PatternType],
    ) -> UserMatchingReport:
        """Match one User's Patterns, logging a failure instead of raising.

        Args:
            snapshot: The User.
            patterns: Their Patterns not matched yet.
            pattern_types: The Pattern Types to match against, by ID.

        Returns:
            What was done for them; skipped, with why, if it failed.
        """
        try:
            return self._match_user(snapshot, patterns, pattern_types)
        except Exception:
            logger.exception("Could not match a User's Patterns")
            return UserMatchingReport(user_id=snapshot.user.id, skipped_why=FAILED)

    def _match_user(
        self,
        snapshot: UserSnapshot,
        patterns: Sequence[Pattern],
        pattern_types: Mapping[str, PatternType],
    ) -> UserMatchingReport:
        """Match one User's Patterns, then tag their evidence again and score.

        A match is saved only once its evidence was tagged again, so a run
        that fails part-way leaves the Pattern to be matched by the next.

        Args:
            snapshot: The User.
            patterns: Their Patterns not matched yet.
            pattern_types: The Pattern Types to match against, by ID.

        Returns:
            What was done for them.
        """
        user_id = snapshot.user.id
        if not may_keep_observations(snapshot):
            return UserMatchingReport(user_id=user_id, skipped_why=NOT_NOTICING)
        found = [
            (pattern, self._ask(snapshot, pattern, pattern_types))
            for pattern in patterns
        ]
        matched = [
            (pattern, pattern_type_id)
            for pattern, pattern_type_id in found
            if pattern_type_id is not None
        ]
        tagged = self._tag_again(
            snapshot, plan_days_to_tag_again(matched), pattern_types
        )
        if tagged.observations_kept:
            self._pattern_scorer.score(
                snapshot.user, snapshot.settings, PatternMoveCause.EVIDENCE_TAGGED_AGAIN
            )
        for pattern, pattern_type_id in matched:
            self._repositories.patterns.save_match(pattern.id, pattern_type_id)
        return UserMatchingReport(
            user_id=user_id,
            matches=tuple(
                PatternMatch(pattern.id, pattern.state, pattern_type_id)
                for pattern, pattern_type_id in found
            ),
            conversations_tagged=tagged.conversations,
            observations_kept=tagged.observations_kept,
            days_without_messages=tagged.days_without_messages,
        )

    def _tag_again(
        self,
        snapshot: UserSnapshot,
        days: Sequence[DayToTagAgain],
        pattern_types: Mapping[str, PatternType],
    ) -> TaggedAgain:
        """Tag again the Conversations of the days behind matched evidence.

        A Conversation whose messages Message Retention deleted can't be
        tagged: an Observation needs the User's exact words.

        Args:
            snapshot: The User.
            days: The days to tag again, each with its Pattern Types and
                Life Threads.
            pattern_types: The Pattern Types matched against, by ID.

        Returns:
            How many Conversations were tagged again, how many new
            Observations were kept and how many days had no messages left.
        """
        if not days:
            return TaggedAgain()
        user_id = snapshot.user.id
        conversations = self._repositories.conversations
        threads = self._repositories.life_threads.list_for_user(user_id)
        conversations_tagged = observations_kept = days_without_messages = 0
        for day in days:
            messages_by_conversation = {
                conversation.id: conversations.list_messages(conversation.id)
                for conversation in conversations.list_started_between(
                    user_id, *day_span(day.day, snapshot.user.time_zone)
                )
            }
            if not any(messages_by_conversation.values()):
                days_without_messages += 1
            for conversation_id, messages in messages_by_conversation.items():
                if not messages:
                    continue
                kept = self._pattern_tagger.tag_again(
                    snapshot,
                    conversation_id,
                    messages,
                    [thread for thread in threads if thread.id in day.thread_ids],
                    [pattern_types[key] for key in sorted(day.pattern_type_ids)],
                )
                conversations_tagged += 1
                observations_kept += len(kept)
        return TaggedAgain(
            conversations_tagged, observations_kept, days_without_messages
        )

    def _ask(
        self,
        snapshot: UserSnapshot,
        pattern: Pattern,
        pattern_types: Mapping[str, PatternType],
    ) -> str | None:
        """Ask the model which Pattern Type a Pattern fits, once more if unreadable.

        Args:
            snapshot: The User whose Pattern it is.
            pattern: The Pattern.
            pattern_types: The Pattern Types it may fit, by ID.

        Returns:
            The Pattern Type's ID; None when it fits none or both answers
            were unreadable.
        """
        settings = snapshot.settings
        description = describe_pattern_to_match(
            pattern, list(pattern_types.values()), snapshot.user.time_zone
        )
        for _ in range(2):
            answer = self._chat_model.generate(
                snapshot=snapshot,
                step=ModelStep.PATTERN_MATCHING,
                model=settings.get(PATTERN_MATCHING_MODEL),
                thinking=thinking_to_use(
                    settings, PATTERN_MATCHING_MODEL, PATTERN_MATCHING_THINKING
                ),
                instructions=settings.get(PATTERN_MATCHING_PROMPT),
                history=[ChatLine(role=ChatRole.USER, text=description)],
            )
            parsed = read_matching_answer(answer)
            if parsed is not None:
                return read_fitting_pattern_type(parsed, pattern_types)
        logger.warning("Pattern matching gave no readable answer")
        return None
