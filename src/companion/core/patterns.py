import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from companion.core.life_threads import describe_thread, incoming_texts, read_text
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
    UserSnapshot,
)
from companion.core.platform_settings import (
    PATTERN_KEEPING_DAYS,
    PATTERN_KEEPING_MODEL,
    PATTERN_KEEPING_PROMPT,
    PATTERN_KEEPING_THINKING,
    PATTERN_KEEPING_THREADS,
)
from companion.core.ports import Clock, Embedder, Repositories
from companion.core.timing import day_span, users_today
from companion.core.transcripts import to_transcript_lines
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

FEWEST_THREADS_TO_START_A_PATTERN = 2
STATE_WORDS = {
    PatternState.SUSPECTED: "suspected",
    PatternState.CONFIRMED: "confirmed",
    PatternState.CLOSED: "closed: never change it or start it again",
}
REACTION_WORDS = {
    PatternReaction.AGREED: "they agreed",
    PatternReaction.PUSHED_BACK: "they pushed back",
    PatternReaction.BRUSHED_OFF: "they brushed it off",
}


@dataclass(frozen=True)
class PlannedPatterns:
    """The Patterns a keeping answer starts and changes.

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


def describe_pattern(pattern: Pattern, time_zone: str | None) -> str:
    """Write a Pattern, its state, when it was last offered and its evidence.

    Args:
        pattern: The Pattern.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        E.g. "(suspected; last offered 3 Nov 2026, they pushed back) When
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


def describe_days_behind_evidence(days: Sequence[DayBehindEvidence]) -> str:
    """Write the days behind the evidence, each as messages or its Day Summary.

    Args:
        days: The days, newest first.

    Returns:
        One block per day; "None." if there are none.
    """
    blocks = []
    for day in days:
        heading = format_calendar_day(day.day)
        if day.messages:
            blocks.append(
                f"{heading}, the messages:\n{to_transcript_lines(day.messages)}"
            )
        elif day.summary is not None:
            blocks.append(f"{heading}, the Day Summary:\n{day.summary.summary}")
    return "\n\n".join(blocks) or "None."


def describe_patterns_to_keep(
    touched: dict[int, LifeThread],
    closest: dict[int, LifeThread],
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
        known: The User's Patterns, by number.
        days: The days behind the evidence in play, newest first.
        messages: The Conversation's messages, oldest first.
        conversation_day: The day the Conversation started.
        now: The current time.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        Today's date, the Threads, the Patterns, the days behind their
        evidence and the Conversation under the day it started.
    """
    pattern_lines = "\n".join(
        f"[{number}] {describe_pattern(pattern, time_zone)}"
        for number, pattern in known.items()
    )
    touched_lines = describe_numbered_threads(touched, time_zone)
    closest_lines = describe_numbered_threads(closest, time_zone)
    return (
        f"Today: {format_day(now, time_zone)}\n\n"
        f"Life Threads this Conversation touched:\n{touched_lines}\n\n"
        f"Their other Life Threads closest in meaning:\n{closest_lines}\n\n"
        f"Patterns kept so far:\n{pattern_lines or 'None yet.'}\n\n"
        f"The days behind that evidence:\n{describe_days_behind_evidence(days)}\n\n"
        f"The Conversation, on {format_calendar_day(conversation_day)}:\n"
        f"{to_transcript_lines(messages)}"
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


def apply_reaction(entry: dict[str, Any], pattern: Pattern, now: datetime) -> Pattern:
    """Record how the User took a view offered from a Pattern in this Conversation.

    It is confirmed only when they agreed, and closed only when they pushed
    back; brushing it off changes neither.

    Args:
        entry: The Pattern, as the model wrote it.
        pattern: The Pattern so far.
        now: When the view was judged.

    Returns:
        The Pattern with when it was offered, how they took it and its new
        state (and when it was first confirmed); unchanged if the model gave
        no reaction.
    """
    reaction = entry.get("reaction")
    if reaction not in {value.value for value in PatternReaction}:
        return pattern
    reacted = replace(
        pattern, last_offered_at=now, last_reaction=PatternReaction(reaction)
    )
    state_allowed_by_reaction = {
        PatternReaction.AGREED: PatternState.CONFIRMED,
        PatternReaction.PUSHED_BACK: PatternState.CLOSED,
    }
    allowed_state = state_allowed_by_reaction.get(PatternReaction(reaction))
    if allowed_state is None or entry.get("state") != allowed_state.value:
        return reacted
    if allowed_state == PatternState.CONFIRMED and pattern.confirmed_at is None:
        return replace(reacted, state=allowed_state, confirmed_at=now)
    return replace(reacted, state=allowed_state)


def change_known_pattern(
    entry: dict[str, Any],
    existing: Pattern,
    threads: dict[int, LifeThread],
    conversation_day: date,
    now: datetime,
) -> Pattern:
    """Apply what the model wrote about a Pattern already kept.

    Its new evidence is added, and how the User took a view offered from it
    is recorded (see `apply_reaction`). A closed Pattern never changes.

    Args:
        entry: The Pattern, as the model wrote it.
        existing: The Pattern kept so far.
        threads: The Threads it was shown, by number.
        conversation_day: The day the Conversation started, for evidence
            with no readable day.
        now: When the change is made.

    Returns:
        The Pattern, changed or not.
    """
    if existing.state == PatternState.CLOSED:
        return existing
    changed = existing
    new_evidence = read_evidence(entry, threads, conversation_day)
    if new_evidence:
        changed = replace(changed, evidence=(*changed.evidence, *new_evidence))
    changed = apply_reaction(entry, changed, now)
    return replace(changed, updated_at=now) if changed != existing else existing


def plan_pattern_changes(
    entries: list[Any],
    threads: dict[int, LifeThread],
    known: dict[int, Pattern],
    user_id: UUID,
    conversation_day: date,
    now: datetime,
) -> PlannedPatterns:
    """Turn the Patterns the model wrote into new and changed Patterns to save.

    An entry whose "pattern" is a known Pattern's number changes it; one
    whose "pattern" is text starts a suspected Pattern, only if its evidence
    comes from two or more different Threads; if a view from it was offered
    in this Conversation, how the User took it is recorded too. An unknown number or one
    already used is skipped.

    Args:
        entries: The Patterns, as the model wrote them.
        threads: The Threads it was shown, by number.
        known: The Patterns it was shown, by number.
        user_id: The User whose Patterns they are.
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
            new_pattern = Pattern(
                id=uuid4(),
                user_id=user_id,
                pattern=text,
                state=PatternState.SUSPECTED,
                evidence=tuple(evidence),
                started_at=now,
                updated_at=now,
            )
            added.append(apply_reaction(entry, new_pattern, now))
            continue
        if not isinstance(value, int) or isinstance(value, bool):
            continue
        existing = known.get(value)
        if existing is None or value in used_numbers:
            continue
        used_numbers.add(value)
        pattern = change_known_pattern(entry, existing, threads, conversation_day, now)
        if pattern != existing:
            changed.append(pattern)
    return PlannedPatterns(added=added, changed=changed)


class PatternKeeper:
    """Keeps a User's Patterns when a Conversation ends, after its Life Threads.

    New Patterns are embedded, so they can be found by meaning.
    """

    def __init__(
        self,
        repositories: Repositories,
        chat_model: UsageRecordingChatModel,
        embedder: Embedder,
        clock: Clock,
    ) -> None:
        """Set up the keeper.

        Args:
            repositories: Where Life Threads, Patterns, Conversations and
                Day Summaries are stored.
            chat_model: Writes the Patterns and records the tokens used.
            embedder: Embeds the touched Threads and each new Pattern.
            clock: Tells the current time.
        """
        self._repositories = repositories
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
        """Update the User's Patterns from an ended Conversation.

        Runs whenever the User wrote something, so a view they took is
        always judged. The model sees the Threads the Conversation touched,
        the User's other Threads closest in meaning to those and to their
        texts, however old (up to the Admin-set number), all their Patterns,
        and the days
        behind the evidence of the Patterns linked to those Threads (up to
        the Admin-set number). An unreadable answer is asked again once; if
        it is still unreadable nothing changes.

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
        entries = self._ask(
            snapshot,
            describe_patterns_to_keep(
                touched_by_number,
                closest_by_number,
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
            entries, threads, known, user_id, conversation_day, now
        )
        self._repositories.patterns.save_many(
            added=[self._to_save(pattern) for pattern in planned.added],
            changed=[
                PatternToSave(pattern=pattern, embedding=None)
                for pattern in planned.changed
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
                thinking=settings.get(PATTERN_KEEPING_THINKING),
                instructions=settings.get(PATTERN_KEEPING_PROMPT),
                history=[ChatLine(role=ChatRole.USER, text=description)],
            )
            entries = read_pattern_keeping_answer(answer)
            if entries is not None:
                return entries
        return None
