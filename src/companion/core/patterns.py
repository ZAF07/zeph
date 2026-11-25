import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from companion.core.life_threads import (
    RemindedThread,
    describe_thread,
    incoming_texts,
    read_text,
    recent_texts_to_search,
)
from companion.core.memory_retrieval import format_calendar_day, format_day
from companion.core.models import (
    ChatLine,
    ChatRole,
    ConversationMessage,
    DaySummary,
    LifeThread,
    ModelStep,
    Pattern,
    PatternEvidence,
    PatternReaction,
    PatternState,
    PatternToSave,
    PatternType,
    UserSnapshot,
)
from companion.core.observations import may_keep_observations
from companion.core.pattern_catalog import PatternCatalogService
from companion.core.platform_settings import (
    LIFE_THREADS_TEXTS_TO_SEARCH,
    PATTERN_CLOSENESS_PERCENT,
    PATTERN_KEEPING_DAYS,
    PATTERN_KEEPING_MODEL,
    PATTERN_KEEPING_PROMPT,
    PATTERN_KEEPING_THINKING,
    PATTERN_KEEPING_THREADS,
    PATTERN_PUSHED_BACK_WAIT,
    thinking_to_use,
)
from companion.core.ports import Clock, Embedder, Repositories
from companion.core.timing import day_span, users_today
from companion.core.transcripts import to_transcript_lines
from companion.core.unmatched_review import (
    UnmatchedGrouper,
    needs_general_description,
    read_general_description,
)
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

FEWEST_THREADS_TO_START_A_PATTERN = 2
MOST_PATTERNS_IN_MIND = 10
NEEDS_GENERAL_DESCRIPTION = "(needs a general description) "
STATE_WORDS = {
    PatternState.UNMATCHED: "unmatched",
    PatternState.CONFIRMED: "confirmed",
    PatternState.CLOSED: "closed",
}
REACTION_WORDS = {
    PatternReaction.AGREED: "they agreed",
    PatternReaction.PUSHED_BACK: "they pushed back",
    PatternReaction.BRUSHED_OFF: "they brushed it off",
}


@dataclass(frozen=True)
class PlannedPatterns:
    """The unmatched Patterns a keeping answer starts and adds evidence to.

    Attributes:
        added: The new Patterns, each with its evidence.
        changed: The changed Patterns, each with all its evidence.
    """

    added: list[Pattern]
    changed: list[Pattern]


@dataclass(frozen=True)
class DayBehindEvidence:
    """A day some evidence happened on, as the keeping model reads it again.

    Attributes:
        day: The day, in the User's time zone.
        messages: That day's messages, oldest first; empty once Message
            Retention deleted them.
        summary: That day's Day Summary, read when there are no messages;
            None if it has none.
    """

    day: date
    messages: list[ConversationMessage]
    summary: DaySummary | None


@dataclass(frozen=True)
class RemindedPattern:
    """A Pattern that came to mind for a reply, numbered for the Reply Plan.

    Attributes:
        number: Its number in the list the model is shown, from 1.
        pattern: The Pattern.
    """

    number: int
    pattern: Pattern


def describe_pattern(pattern: Pattern, time_zone: str | None) -> str:
    """Write a Pattern, its state, when it was last offered and its evidence.

    Args:
        pattern: The Pattern.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        E.g. "(confirmed; last offered 3 Nov 2026, they agreed) When
        something grabs them... Evidence:" then one "- " line per piece.
    """
    notes = [STATE_WORDS[pattern.state]]
    if pattern.last_offered_at is not None:
        reaction = (
            REACTION_WORDS[pattern.last_reaction]
            if pattern.last_reaction
            else "not known how they took it"
        )
        notes.append(
            f"last offered {format_day(pattern.last_offered_at, time_zone)}, {reaction}"
        )
    evidence_lines = "\n".join(
        f"  - {format_calendar_day(item.day)}, {item.thread_title}: {item.line}"
        for item in pattern.evidence
    )
    return f"({'; '.join(notes)}) {pattern.pattern} Evidence:\n{evidence_lines}"


def may_come_to_mind(
    pattern: Pattern, now: datetime, pushed_back_wait: timedelta
) -> bool:
    """Say whether a Pattern may come to mind for a reply.

    A closed Pattern never does. One the User pushed back on waits the
    Admin-set time after it was offered.

    Args:
        pattern: The Pattern.
        now: The current time.
        pushed_back_wait: How long to wait after they pushed back.

    Returns:
        True if it may come to mind.
    """
    if pattern.state == PatternState.CLOSED:
        return False
    return not (
        pattern.last_reaction == PatternReaction.PUSHED_BACK
        and pattern.last_offered_at is not None
        and now < pattern.last_offered_at + pushed_back_wait
    )


def describe_patterns_in_mind(
    reminded: Sequence[RemindedPattern], time_zone: str | None
) -> str:
    """Write the Patterns in mind as the Reply Plan model reads them.

    Args:
        reminded: The Patterns, numbered.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        One block per Pattern, with its state, when it was last offered and
        how they took it, and its evidence; "None." if there are none.
    """
    return (
        "\n".join(
            f"[{item.number}] {describe_pattern(item.pattern, time_zone)}"
            for item in reminded
        )
        or "None."
    )


def describe_numbered_threads(
    threads: dict[int, LifeThread], time_zone: str | None
) -> str:
    """Write some Life Threads, one per line under its number.

    Args:
        threads: The Threads, by number.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        One line per Thread; "None." if there are none.
    """
    return (
        "\n".join(
            f"[{number}] {describe_thread(thread, time_zone)}"
            for number, thread in threads.items()
        )
        or "None."
    )


def describe_days_behind_evidence(
    days: Sequence[DayBehindEvidence], time_zone: str | None
) -> str:
    """Write the days behind the evidence, each as messages or its Day Summary.

    Args:
        days: The days, newest first.
        time_zone: The User's IANA time zone, for when a Replied-to Text was
            sent.

    Returns:
        One block per day; "None." if there are none.
    """
    blocks = []
    for day in days:
        heading = format_calendar_day(day.day)
        if day.messages:
            transcript = to_transcript_lines(day.messages, time_zone)
            blocks.append(f"{heading}, the messages:\n{transcript}")
        elif day.summary is not None:
            blocks.append(f"{heading}, the Day Summary:\n{day.summary.summary}")
    return "\n\n".join(blocks) or "None."


def describe_pattern_types_looked_for(pattern_types: Sequence[PatternType]) -> str:
    """Write the Pattern Types, so the keeping model leaves them to tagging.

    Args:
        pattern_types: Every Pattern Type in the catalog now.

    Returns:
        One line per Pattern Type: its name, its if / then / function and
        what it is; "None." if there are none.
    """
    return (
        "\n".join(
            f"- {pattern_type.name}. If: {pattern_type.if_situation}. "
            f"Then: {pattern_type.then_behaviour}. "
            f"Function: {pattern_type.function}. {pattern_type.definition}"
            for pattern_type in pattern_types
        )
        or "None."
    )


def describe_patterns_to_keep(
    touched: dict[int, LifeThread],
    closest: dict[int, LifeThread],
    pattern_types: Sequence[PatternType],
    known: dict[int, Pattern],
    days: Sequence[DayBehindEvidence],
    messages: list[ConversationMessage],
    conversation_day: date,
    now: datetime,
    time_zone: str | None,
) -> str:
    """Write what the Pattern keeping model is given.

    Args:
        touched: The Threads the Conversation touched, by number.
        closest: The User's other Threads closest in meaning, by number.
        pattern_types: The Pattern Types tagging looks for, for this User;
            none while Pattern noticing doesn't work for them.
        known: The User's Patterns with no Pattern Type, by number.
        days: The days behind the evidence in play, newest first.
        messages: The Conversation's messages, oldest first.
        conversation_day: The day the Conversation started.
        now: The current time.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        Today's date, the Threads, the Pattern Types, the Patterns, the
        days behind their evidence and the Conversation under the day it
        started. An unmatched Pattern with no general description yet is
        marked as needing one.
    """
    pattern_lines = "\n".join(
        f"[{number}] "
        f"{NEEDS_GENERAL_DESCRIPTION if needs_general_description(pattern) else ''}"
        f"{describe_pattern(pattern, time_zone)}"
        for number, pattern in known.items()
    )
    touched_lines = describe_numbered_threads(touched, time_zone)
    closest_lines = describe_numbered_threads(closest, time_zone)
    evidence_days = describe_days_behind_evidence(days, time_zone)
    return (
        f"Today: {format_day(now, time_zone)}\n\n"
        f"Life Threads this Conversation touched:\n{touched_lines}\n\n"
        f"Their other Life Threads closest in meaning:\n{closest_lines}\n\n"
        f"Pattern Types Zeph already looks for:\n"
        f"{describe_pattern_types_looked_for(pattern_types)}\n\n"
        f"Patterns kept so far:\n{pattern_lines or 'None yet.'}\n\n"
        f"The days behind that evidence:\n{evidence_days}\n\n"
        f"The Conversation, on {format_calendar_day(conversation_day)}:\n"
        f"{to_transcript_lines(messages, time_zone)}"
    )


def read_pattern_keeping_answer(answer: str) -> list[Any] | None:
    """Read the Patterns the keeping model wrote from its JSON answer.

    Text around the JSON object, such as a code fence, is ignored.

    Args:
        answer: The model's answer.

    Returns:
        The Patterns, as the model wrote them; None if it can't be read.
    """
    start, end = answer.find("{"), answer.rfind("}")
    if start == -1 or end < start:
        return None
    try:
        parsed = json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or not isinstance(parsed.get("patterns"), list):
        return None
    patterns: list[Any] = parsed["patterns"]
    return patterns


def read_day(value: Any, conversation_day: date) -> date:
    """Read the day a piece of evidence happened on.

    Args:
        value: The day as the model wrote it, e.g. "2026-11-20".
        conversation_day: The day the Conversation started, used when the
            day is missing, unreadable or after it.

    Returns:
        The day.
    """
    if not isinstance(value, str):
        return conversation_day
    try:
        day = date.fromisoformat(value.strip())
    except ValueError:
        return conversation_day
    return min(day, conversation_day)


def read_evidence(
    entry: dict[str, Any], threads: dict[int, LifeThread], conversation_day: date
) -> list[PatternEvidence]:
    """Read the evidence of one Pattern the model wrote.

    Evidence naming a Thread it wasn't shown, or with no line, is skipped.

    Args:
        entry: The Pattern, as the model wrote it.
        threads: The Threads it was shown, by number.
        conversation_day: The day the Conversation started, for evidence
            with no readable day.

    Returns:
        The evidence, in the order written.
    """
    value = entry.get("evidence")
    if not isinstance(value, list):
        return []
    evidence = []
    for item in value:
        if not isinstance(item, dict):
            continue
        number, line = item.get("thread"), read_text(item, "line")
        if not isinstance(number, int) or isinstance(number, bool) or line is None:
            continue
        thread = threads.get(number)
        if thread is None:
            continue
        evidence.append(
            PatternEvidence(
                id=uuid4(),
                day=read_day(item.get("day"), conversation_day),
                thread_id=thread.id,
                thread_title=thread.title,
                line=line,
            )
        )
    return evidence


def add_new_evidence(
    entry: dict[str, Any],
    existing: Pattern,
    threads: dict[int, LifeThread],
    user_name: str | None,
    conversation_day: date,
    now: datetime,
) -> Pattern:
    """Add what the model wrote to an unmatched Pattern already kept.

    Only an unmatched Pattern changes, and only by gaining evidence or, if
    it has none yet, its general description: its state never does, and a
    general description once kept is never rewritten.

    Args:
        entry: The Pattern, as the model wrote it.
        existing: The Pattern kept so far.
        threads: The Threads it was shown, by number.
        user_name: What the Companion calls the User, which a general
            description may not hold.
        conversation_day: The day the Conversation started, for evidence
            with no readable day.
        now: When the change is made.

    Returns:
        The Pattern, with what is new or as it was.
    """
    if existing.state != PatternState.UNMATCHED:
        return existing
    new_evidence = read_evidence(entry, threads, conversation_day)
    general_description = existing.general_description or read_general_description(
        entry.get("general"), user_name
    )
    if not new_evidence and general_description == existing.general_description:
        return existing
    return replace(
        existing,
        evidence=(*existing.evidence, *new_evidence),
        general_description=general_description,
        updated_at=now,
    )


def plan_pattern_changes(
    entries: list[Any],
    threads: dict[int, LifeThread],
    known: dict[int, Pattern],
    user_id: UUID,
    user_name: str | None,
    conversation_day: date,
    now: datetime,
) -> PlannedPatterns:
    """Turn the Patterns the model wrote into unmatched Patterns to save.

    An entry whose "pattern" is a known Pattern's number adds evidence to
    it, if it is unmatched, and its general description if it has none; one
    whose "pattern" is text starts an unmatched Pattern, only if its
    evidence comes from two or more different Threads. An unknown number or
    one already used is skipped. Whatever state or reaction the model
    writes is ignored: no Pattern's state ever changes here. A general
    description that could tell who it is about is dropped, and the Pattern
    is kept without one.

    Args:
        entries: The Patterns, as the model wrote them.
        threads: The Threads it was shown, by number.
        known: The Patterns it was shown, by number.
        user_id: The User whose Patterns they are.
        user_name: What the Companion calls the User, which a general
            description may not hold.
        conversation_day: The day the Conversation started, for evidence
            with no readable day.
        now: When the changes are made.

    Returns:
        The new and changed Patterns.
    """
    added: list[Pattern] = []
    changed: list[Pattern] = []
    used_numbers: set[int] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        value = entry.get("pattern")
        if isinstance(value, str):
            text = value.strip()
            evidence = read_evidence(entry, threads, conversation_day)
            thread_ids = {item.thread_id for item in evidence}
            if not text or len(thread_ids) < FEWEST_THREADS_TO_START_A_PATTERN:
                continue
            added.append(
                Pattern(
                    id=uuid4(),
                    user_id=user_id,
                    pattern=text,
                    state=PatternState.UNMATCHED,
                    evidence=tuple(evidence),
                    started_at=now,
                    updated_at=now,
                    general_description=read_general_description(
                        entry.get("general"), user_name
                    ),
                )
            )
            continue
        if not isinstance(value, int) or isinstance(value, bool):
            continue
        existing = known.get(value)
        if existing is None or value in used_numbers:
            continue
        used_numbers.add(value)
        pattern = add_new_evidence(
            entry, existing, threads, user_name, conversation_day, now
        )
        if pattern != existing:
            changed.append(pattern)
    return PlannedPatterns(added=added, changed=changed)


class PatternReminder:
    """Brings the User's Patterns to mind before each reply.

    No model call. A Pattern comes to mind through its linked Life Threads,
    when one of them is in mind, and directly when what the User means and
    their latest texts are close to it in meaning, so one can surface in a
    brand-new situation. Patterns that came to mind earlier in the
    Conversation stay in mind until it ends.
    """

    def __init__(
        self, repositories: Repositories, embedder: Embedder, clock: Clock
    ) -> None:
        """Set up the reminder.

        Args:
            repositories: Where Conversations and Patterns are stored.
            embedder: Embeds what the User means and their latest texts.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._embedder = embedder
        self._clock = clock

    def remind(
        self,
        snapshot: UserSnapshot,
        conversation_id: UUID,
        meaning: str,
        threads: Sequence[RemindedThread],
    ) -> list[RemindedPattern]:
        """Find the User's Patterns that come to mind for the Message.

        Those close in meaning come first, then those linked to a Thread in
        mind, then those that came to mind earlier in the Conversation, at
        most `MOST_PATTERNS_IN_MIND`. The search uses what the User means
        and their latest texts, as many as Life Threads are searched on,
        with the Life Thread closeness bar. A closed Pattern never comes to
        mind, and one they pushed back on waits the Admin-set time. Each one
        found is kept in mind for the rest of the Conversation. If the
        search can't be embedded, Patterns come only through their Threads.

        Args:
            snapshot: The User being answered.
            conversation_id: The Conversation the Message is in.
            meaning: What the Understanding says the User means; "" if it
                failed.
            threads: The Life Threads in mind for the Message.

        Returns:
            The Patterns, numbered from 1.
        """
        now = self._clock.now()
        wait = snapshot.settings.get(PATTERN_PUSHED_BACK_WAIT)
        pattern_repository = self._repositories.patterns
        allowed = {
            pattern.id: pattern
            for pattern in pattern_repository.list_for_user(snapshot.user.id)
            if may_come_to_mind(pattern, now, wait)
        }
        if not allowed:
            return []
        thread_ids = {item.thread.id for item in threads}
        linked_ids = [
            pattern.id
            for pattern in allowed.values()
            if pattern.thread_ids & thread_ids
        ]
        close_ids = [
            pattern_id
            for pattern_id in self._find_close_ids(snapshot, conversation_id, meaning)
            if pattern_id in allowed
        ]
        found_ids = list(dict.fromkeys([*close_ids, *linked_ids]))
        pattern_repository.keep_in_mind(conversation_id, found_ids, now)
        in_mind_ids = dict.fromkeys(
            [*found_ids, *pattern_repository.list_in_mind_ids(conversation_id)]
        )
        in_mind = [
            allowed[pattern_id] for pattern_id in in_mind_ids if pattern_id in allowed
        ]
        return [
            RemindedPattern(number=number, pattern=pattern)
            for number, pattern in enumerate(in_mind[:MOST_PATTERNS_IN_MIND], start=1)
        ]

    def _find_close_ids(
        self, snapshot: UserSnapshot, conversation_id: UUID, meaning: str
    ) -> list[UUID]:
        """Find the User's Patterns close in meaning to the Message.

        Args:
            snapshot: The User being answered.
            conversation_id: The Conversation the Message is in.
            meaning: What the Understanding says the User means.

        Returns:
            The Patterns' IDs, closest first; none if there is nothing to
            search on or it can't be embedded.
        """
        settings = snapshot.settings
        texts = recent_texts_to_search(
            self._repositories.conversations.list_messages(conversation_id),
            settings.get(LIFE_THREADS_TEXTS_TO_SEARCH),
        )
        search = "\n".join(part for part in [meaning, *texts] if part)
        if not search:
            return []
        try:
            embedding = self._embedder.embed_query(search)
        except Exception:
            logger.exception("Could not embed the texts to find Patterns by")
            return []
        return self._repositories.patterns.find_close_ids(
            snapshot.user.id,
            embedding,
            settings.get(PATTERN_CLOSENESS_PERCENT) / 100,
        )


class PatternKeeper:
    """Notes a User's unmatched Patterns when a Conversation ends.

    It runs after the Life Threads are kept, and only notes what recurs
    across two or more Threads and fits no Pattern Type. It never starts,
    confirms or closes a Pattern of a Pattern Type: code does, from
    Observations (ADR-0024). New Patterns are embedded, so they can be
    found by meaning. Each unmatched Pattern also gets a general
    description with nothing about the User, grouped with like ones from
    other Users for Admins to review.
    """

    def __init__(
        self,
        repositories: Repositories,
        pattern_catalog: PatternCatalogService,
        unmatched_grouper: UnmatchedGrouper,
        chat_model: UsageRecordingChatModel,
        embedder: Embedder,
        clock: Clock,
    ) -> None:
        """Set up the keeper.

        Args:
            repositories: Where Life Threads, Patterns, Conversations and
                Day Summaries are stored.
            pattern_catalog: Reads the Pattern Types in the catalog now.
            unmatched_grouper: Groups unmatched Patterns by their general
                descriptions.
            chat_model: Writes the Patterns and records the tokens used.
            embedder: Embeds the touched Threads and each new Pattern.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._pattern_catalog = pattern_catalog
        self._unmatched_grouper = unmatched_grouper
        self._chat_model = chat_model
        self._embedder = embedder
        self._clock = clock

    def keep_from(
        self,
        snapshot: UserSnapshot,
        conversation_id: UUID,
        messages: list[ConversationMessage],
        touched: Sequence[LifeThread],
    ) -> None:
        """Note the User's unmatched Patterns from an ended Conversation.

        Runs whenever the User wrote something. The model sees the Threads
        the Conversation touched, the User's other Threads closest in
        meaning to those and to their texts, however old (up to the
        Admin-set number), the Pattern Types in the catalog (only while
        tagging notes the evidence for those, so nothing that recurs is
        left unkept for a User without Pattern noticing), all their
        Patterns with no Pattern Type, and the days behind the evidence of
        the Patterns linked to those Threads (up to the Admin-set number).
        An unreadable answer is asked again once; if it is still unreadable
        nothing changes. Every unmatched Pattern with a general description
        and no unmatched entry yet, new or kept earlier, is grouped under
        one.

        Args:
            snapshot: The User whose Conversation it was; User Memory works
                for them.
            conversation_id: The ended Conversation.
            messages: Its messages, oldest first.
            touched: The Life Threads the Conversation started, changed or
                brought up.
        """
        texts = incoming_texts(messages)
        if not texts:
            return
        settings = snapshot.settings
        user_id = snapshot.user.id
        time_zone = snapshot.user.time_zone
        closest = self._find_closest_threads(
            user_id, touched, texts, settings.get(PATTERN_KEEPING_THREADS)
        )
        touched_by_number = dict(enumerate(touched, start=1))
        closest_by_number = dict(enumerate(closest, start=len(touched) + 1))
        threads = touched_by_number | closest_by_number
        known = dict(
            enumerate(self._repositories.patterns.list_for_user(user_id), start=1)
        )
        now = self._clock.now()
        conversation_day = users_today(time_zone, messages[0].sent_at)
        days = self._read_days_behind_evidence(
            snapshot,
            conversation_id,
            list(known.values()),
            {thread.id for thread in threads.values()},
            settings.get(PATTERN_KEEPING_DAYS),
        )
        pattern_types = (
            [entry.pattern_type for entry in self._pattern_catalog.catalog()]
            if may_keep_observations(snapshot)
            else []
        )
        entries = self._ask(
            snapshot,
            describe_patterns_to_keep(
                touched_by_number,
                closest_by_number,
                pattern_types,
                known,
                days,
                messages,
                conversation_day,
                now,
                time_zone,
            ),
        )
        if entries is None:
            logger.warning("Pattern keeping gave no readable answer")
            return
        planned = plan_pattern_changes(
            entries,
            threads,
            known,
            user_id,
            snapshot.user.name,
            conversation_day,
            now,
        )
        kept = {pattern.id: pattern for pattern in known.values()}
        latest = kept | {pattern.id: pattern for pattern in planned.changed}
        self._repositories.patterns.save_many(
            added=[
                self._to_save(pattern)
                for pattern in self._unmatched_grouper.link(settings, planned.added)
            ],
            changed=[
                PatternToSave(pattern=pattern, embedding=None)
                for pattern in self._unmatched_grouper.link(
                    settings, list(latest.values())
                )
                if pattern != kept[pattern.id]
            ],
        )

    def _find_closest_threads(
        self,
        user_id: UUID,
        touched: Sequence[LifeThread],
        texts: Sequence[str],
        limit: int,
    ) -> list[LifeThread]:
        """Find the User's other Threads closest in meaning to the Conversation.

        Args:
            user_id: The User's ID.
            touched: The Threads the Conversation touched.
            texts: The texts the User sent in it.
            limit: The most to find.

        Returns:
            The closest Threads, closest first; none if they can't be
            embedded.
        """
        if limit < 1:
            return []
        try:
            embedding = self._embedder.embed_query(
                "\n".join(
                    [*(f"{thread.title}. {thread.story}" for thread in touched), *texts]
                )
            )
        except Exception:
            logger.exception("Could not embed the Conversation's Threads and texts")
            return []
        return self._repositories.life_threads.find_closest(
            user_id, embedding, [thread.id for thread in touched], limit
        )

    def _read_days_behind_evidence(
        self,
        snapshot: UserSnapshot,
        conversation_id: UUID,
        known: Sequence[Pattern],
        thread_ids: set[UUID],
        limit: int,
    ) -> list[DayBehindEvidence]:
        """Read again the days behind the evidence in play.

        The evidence in play is that of the Patterns linked to the Threads
        given. A day is read as its messages while Message Retention keeps
        them, leaving out the ended Conversation, and as its Day Summary
        after.

        Args:
            snapshot: The User whose Conversation it was.
            conversation_id: The ended Conversation, given on its own.
            known: The User's Patterns.
            thread_ids: The IDs of the Threads given.
            limit: The most days to read.

        Returns:
            The days, newest first.
        """
        days = sorted(
            {
                item.day
                for pattern in known
                if pattern.thread_ids & thread_ids
                for item in pattern.evidence
            },
            reverse=True,
        )[: max(limit, 0)]
        conversations = self._repositories.conversations
        time_zone = snapshot.user.time_zone
        messages_by_day = {
            day: [
                message
                for conversation in conversations.list_started_between(
                    snapshot.user.id, *day_span(day, time_zone)
                )
                if conversation.id != conversation_id
                for message in conversations.list_messages(conversation.id)
            ]
            for day in days
        }
        summaries = {
            summary.day: summary
            for summary in self._repositories.user_memory.list_summaries_for_days(
                snapshot.user.id,
                [day for day, messages in messages_by_day.items() if not messages],
            )
        }
        return [
            DayBehindEvidence(
                day=day, messages=messages_by_day[day], summary=summaries.get(day)
            )
            for day in days
        ]

    def _to_save(self, pattern: Pattern) -> PatternToSave:
        """Add a new Pattern's embedding, so it can be found by meaning.

        Args:
            pattern: The new Pattern.

        Returns:
            It with its embedding; no embedding if that failed.
        """
        try:
            [embedding] = self._embedder.embed_passages([pattern.pattern])
        except Exception:
            logger.exception("Could not embed a Pattern")
            embedding = None
        return PatternToSave(pattern=pattern, embedding=embedding)

    def _ask(self, snapshot: UserSnapshot, description: str) -> list[Any] | None:
        """Ask the model about the Patterns, once more if it can't be read.

        Args:
            snapshot: The User whose Conversation it was.
            description: The Threads, Patterns, days and Conversation.

        Returns:
            The Patterns it wrote, or None if both answers were unreadable.
        """
        settings = snapshot.settings
        for _ in range(2):
            answer = self._chat_model.generate(
                snapshot=snapshot,
                step=ModelStep.PATTERNS,
                model=settings.get(PATTERN_KEEPING_MODEL),
                thinking=thinking_to_use(
                    settings, PATTERN_KEEPING_MODEL, PATTERN_KEEPING_THINKING
                ),
                instructions=settings.get(PATTERN_KEEPING_PROMPT),
                history=[ChatLine(role=ChatRole.USER, text=description)],
            )
            entries = read_pattern_keeping_answer(answer)
            if entries is not None:
                return entries
        return None
