import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from companion.core.life_threads import (
    MOST_THREADS_AT_CONVERSATION_END,
    REACTION_WORDS,
    describe_thread,
    find_threads_in,
    incoming_texts,
    read_text,
)
from companion.core.memory_retrieval import format_day
from companion.core.models import (
    BringUpWay,
    ChatLine,
    ChatRole,
    ConversationMessage,
    Curiosity,
    CuriosityChanges,
    CuriositySensitivity,
    CuriosityState,
    CuriosityToRaise,
    Feature,
    LifeThread,
    MemoryItem,
    ModelStep,
    ThreadReaction,
    UserSnapshot,
)
from companion.core.platform_settings import (
    CURIOSITIES_PER_CONVERSATION,
    CURIOSITIES_WAITING_LIMIT,
    CURIOSITY_KEEPING_MODEL,
    CURIOSITY_KEEPING_PROMPT,
)
from companion.core.ports import Clock, Embedder, Repositories
from companion.core.transcripts import to_transcript_lines
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

RECENTLY_RAISED_TO_SHOW = 10
HOW_TO_RAISE_WORDS = {
    BringUpWay.LEAD: "Open with it.",
    BringUpWay.WEAVE: (
        "Ask it in this reply, after answering what they said, tied to it "
        "where you can."
    ),
}


@dataclass(frozen=True)
class NumberedCuriosity:
    """A Curiosity, numbered for the model that is shown it.

    Attributes:
        number: Its number in the list the model is shown, from 1.
        curiosity: The Curiosity.
    """

    number: int
    curiosity: Curiosity


@dataclass(frozen=True)
class DueCuriosities:
    """The Curiosities the Understanding may bring up in a reply.

    Attributes:
        offered: The waiting Curiosities whose day has come, numbered; none
            once the Conversation has raised as many as it may.
        raised_here: How many were already raised in this Conversation.
        per_conversation: The most that may be raised in one Conversation.
    """

    offered: tuple[NumberedCuriosity, ...]
    raised_here: int
    per_conversation: int

    @property
    def left(self) -> int:
        """How many more may be raised in this Conversation.

        Returns:
            The number; never below 0.
        """
        return max(self.per_conversation - self.raised_here, 0)


NO_DUE_CURIOSITIES = DueCuriosities(offered=(), raised_here=0, per_conversation=0)


def format_date(day: date) -> str:
    """Write a day like "13 Nov 2026".

    Args:
        day: The day.

    Returns:
        The day.
    """
    return f"{day.day} {day:%b %Y}"


def describe_due_curiosities(due: DueCuriosities, time_zone: str | None) -> str:
    """Write the due Curiosities as the Understanding model reads them.

    Args:
        due: The Curiosities it may bring up, and how many it still may.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        How many were raised of the most allowed, then one line per
        Curiosity; "None." if none is offered.
    """
    lines = [
        f"[{item.number}] {item.curiosity.question} Why: {item.curiosity.why} "
        f"Sensitivity: {item.curiosity.sensitivity.value}. "
        f"Saved {format_day(item.curiosity.created_at, time_zone)}."
        for item in due.offered
    ]
    return (
        f"(raised {due.raised_here} of at most {due.per_conversation} in this "
        f"Conversation):\n" + ("\n".join(lines) or "None.")
    )


def format_curiosities_for_reply(chosen: Sequence[CuriosityToRaise]) -> str:
    """Write the reply's section on the Curiosities to bring up.

    Args:
        chosen: The Curiosities the Understanding chose, and how.

    Returns:
        The section; "" if none was chosen.
    """
    if not chosen:
        return ""
    lines = [
        f"- {item.question} {HOW_TO_RAISE_WORDS[item.how]} Why you wonder: {item.why}"
        for item in chosen
    ]
    return (
        "Something you've been wondering about them, to ask the way a friend "
        "would:\n" + "\n".join(lines)
    )


class CuriosityRaiser:
    """Offers the Understanding the Curiosities whose day has come.

    No model call: it lists the User's waiting Curiosities whose "not
    before" day has come in their time zone, until the Conversation has
    raised as many as Admins allow, and marks raised the ones a reply
    brought up.
    """

    def __init__(self, repositories: Repositories, clock: Clock) -> None:
        """Set up the raiser.

        Args:
            repositories: Where Curiosities are stored.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._clock = clock

    def due(self, snapshot: UserSnapshot, conversation_id: UUID) -> DueCuriosities:
        """List the Curiosities the Understanding may bring up now.

        Args:
            snapshot: The User being answered.
            conversation_id: The Conversation the Message is in.

        Returns:
            The due Curiosities, oldest first; none when Curiosities doesn't
            work for the User.
        """
        if not snapshot.works(Feature.CURIOSITIES):
            return NO_DUE_CURIOSITIES
        store = self._repositories.curiosities
        per_conversation = snapshot.settings.get(CURIOSITIES_PER_CONVERSATION)
        raised_here = len(store.list_raised_in(conversation_id))
        if raised_here >= per_conversation:
            return DueCuriosities((), raised_here, per_conversation)
        waiting = [
            curiosity
            for curiosity in store.list_waiting(snapshot.user.id)
            if curiosity.not_before is None or curiosity.not_before <= snapshot.today
        ]
        return DueCuriosities(
            offered=tuple(
                NumberedCuriosity(number, curiosity)
                for number, curiosity in enumerate(waiting, start=1)
            ),
            raised_here=raised_here,
            per_conversation=per_conversation,
        )

    def mark_raised(
        self, conversation_id: UUID, raised: Sequence[CuriosityToRaise]
    ) -> None:
        """Note that the reply just sent brought up some Curiosities.

        Args:
            conversation_id: The Conversation the reply was sent in.
            raised: The Curiosities the Understanding chose to bring up.
        """
        self._repositories.curiosities.mark_raised(
            [item.curiosity_id for item in raised], conversation_id, self._clock.now()
        )


@dataclass(frozen=True)
class CuriosityKeepingContext:
    """What the Curiosities the keeping model wrote are checked against.

    Attributes:
        user_id: The User they are about.
        now: When the changes are made.
        known: The waiting Curiosities and those raised in this
            Conversation, by the number the model was shown.
        raised_here: The IDs of those raised in this Conversation.
        items: The User's Memory Items, by number.
        threads: The Life Threads the model was shown, by number.
    """

    user_id: UUID
    now: datetime
    known: dict[int, Curiosity]
    raised_here: set[UUID]
    items: dict[int, MemoryItem]
    threads: dict[int, LifeThread]


def read_curiosity_keeping_answer(answer: str) -> list[Any] | None:
    """Read the Curiosities the keeping model wrote from its JSON answer.

    Text around the JSON object, such as a code fence, is ignored.

    Args:
        answer: The model's answer.

    Returns:
        The Curiosities, as the model wrote them; None if it can't be read.
    """
    start, end = answer.find("{"), answer.rfind("}")
    if start == -1 or end < start:
        return None
    try:
        parsed = json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or not isinstance(parsed.get("curiosities"), list):
        return None
    entries: list[Any] = parsed["curiosities"]
    return entries


def read_day(value: Any) -> date | None:
    """Read a day the model wrote as YYYY-MM-DD.

    Args:
        value: The value, e.g. "2026-11-13".

    Returns:
        The day; None if it isn't one.
    """
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def read_sensitivity(value: Any, default: CuriositySensitivity) -> CuriositySensitivity:
    """Read how sensitive the model said a Curiosity is.

    Args:
        value: The value, e.g. "high".
        default: What an odd or missing value reads as.

    Returns:
        The sensitivity.
    """
    if value in {level.value for level in CuriositySensitivity}:
        return CuriositySensitivity(value)
    return default


def read_number(entry: dict[str, Any], key: str) -> int | None:
    """Read a number the model wrote for something it was shown.

    Args:
        entry: The Curiosity, as the model wrote it.
        key: The field's name, e.g. "memory_item".

    Returns:
        The number; None if it isn't a whole number.
    """
    value = entry.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def plan_new_curiosity(
    entry: dict[str, Any], context: CuriosityKeepingContext
) -> Curiosity | None:
    """Turn a new Curiosity the model wrote into one to save.

    Args:
        entry: The Curiosity, as the model wrote it.
        context: What it is checked against.

    Returns:
        The Curiosity; None if it has no question or a "not before" day that
        can't be read. An unknown Memory Item or Thread number is left out.
    """
    question = read_text(entry, "ask")
    not_before_given = entry.get("not_before")
    not_before = read_day(not_before_given)
    if question is None or (not_before_given is not None and not_before is None):
        return None
    item = context.items.get(read_number(entry, "memory_item") or 0)
    thread = context.threads.get(read_number(entry, "thread") or 0)
    return Curiosity(
        id=uuid4(),
        user_id=context.user_id,
        question=question,
        why=read_text(entry, "why") or "",
        not_before=not_before,
        sensitivity=read_sensitivity(
            entry.get("sensitivity"), CuriositySensitivity.LOW
        ),
        state=CuriosityState.WAITING,
        created_at=context.now,
        source_memory_item_id=item.id if item else None,
        source_life_thread_id=thread.id if thread else None,
    )


def plan_waiting_change(entry: dict[str, Any], existing: Curiosity) -> Curiosity:
    """Apply what the model wrote about a waiting Curiosity.

    Args:
        entry: What it wrote, e.g. {"curiosity": 2, "close": true}.
        existing: The waiting Curiosity.

    Returns:
        It closed, or with its new details; a "not before" day that can't be
        read keeps the old one.
    """
    if entry.get("close") is True:
        return replace(existing, state=CuriosityState.CLOSED)
    not_before = existing.not_before
    if "not_before" in entry:
        given = entry["not_before"]
        not_before = None if given is None else read_day(given) or not_before
    return replace(
        existing,
        question=read_text(entry, "ask") or existing.question,
        why=read_text(entry, "why") or existing.why,
        not_before=not_before,
        sensitivity=read_sensitivity(entry.get("sensitivity"), existing.sensitivity),
    )


def plan_curiosity_changes(
    entries: list[Any], context: CuriosityKeepingContext
) -> CuriosityChanges:
    """Turn the Curiosities the model wrote into changes that are safe to save.

    An entry without a number is a new Curiosity. One with the number of a
    waiting Curiosity changes or closes it, and one with the number of a
    Curiosity raised in this Conversation records how the User took it. An
    unknown number, or a number already used, is skipped.

    Args:
        entries: The Curiosities, as the model wrote them.
        context: What they are checked against.

    Returns:
        The new and changed Curiosities and the reactions.
    """
    added: list[Curiosity] = []
    updated: list[Curiosity] = []
    reactions: dict[UUID, ThreadReaction] = {}
    used_numbers: set[int] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if "curiosity" not in entry:
            new = plan_new_curiosity(entry, context)
            if new is not None:
                added.append(new)
            continue
        number = read_number(entry, "curiosity")
        existing = context.known.get(number or 0)
        if number is None or existing is None or number in used_numbers:
            continue
        used_numbers.add(number)
        if existing.id in context.raised_here:
            reaction = entry.get("reaction")
            if reaction in {value.value for value in ThreadReaction}:
                reactions[existing.id] = ThreadReaction(reaction)
            continue
        changed = plan_waiting_change(entry, existing)
        if changed != existing:
            updated.append(changed)
    return CuriosityChanges(added=added, updated=updated, reactions=reactions)


def close_oldest_over_limit(
    changes: CuriosityChanges, waiting: Sequence[Curiosity], limit: int
) -> CuriosityChanges:
    """Close the oldest waiting Curiosities so no more than the limit wait.

    Args:
        changes: The changes the model asked for.
        waiting: The User's waiting Curiosities before them, oldest first.
        limit: The most that may wait at once.

    Returns:
        The changes, closing the oldest still waiting; if the new ones alone
        are over the limit, only the newest of them are added.
    """
    updated = {curiosity.id: curiosity for curiosity in changes.updated}
    still_waiting = [
        updated.get(curiosity.id, curiosity)
        for curiosity in waiting
        if updated.get(curiosity.id, curiosity).state == CuriosityState.WAITING
    ]
    over = len(still_waiting) + len(changes.added) - limit
    if over <= 0:
        return changes
    for curiosity in still_waiting[:over]:
        updated[curiosity.id] = replace(curiosity, state=CuriosityState.CLOSED)
    added_over = max(over - len(still_waiting), 0)
    return replace(
        changes, added=changes.added[added_over:], updated=list(updated.values())
    )


def describe_curiosity(curiosity: Curiosity, raised_here: set[UUID]) -> str:
    """Write one Curiosity as the keeping model reads it.

    Args:
        curiosity: The Curiosity.
        raised_here: The IDs of those raised in this Conversation.

    Returns:
        E.g. "(waiting; not before 13 Nov 2026; sensitivity low) How did the
        presentation go? Why: They were nervous."
    """
    if curiosity.id in raised_here:
        state = "brought up in this Conversation"
    else:
        day = (
            f"not before {format_date(curiosity.not_before)}"
            if curiosity.not_before
            else "any day"
        )
        state = f"waiting; {day}; sensitivity {curiosity.sensitivity.value}"
    return f"({state}) {curiosity.question} Why: {curiosity.why}"


def describe_curiosities_to_keep(
    context: CuriosityKeepingContext,
    category_names: dict[UUID, str],
    recently_raised: Sequence[Curiosity],
    messages: list[ConversationMessage],
    snapshot: UserSnapshot,
) -> str:
    """Write what the Curiosity keeping model is given.

    Args:
        context: The Curiosities, Memory Items and Threads it may name.
        category_names: Every Memory Category's name, by ID.
        recently_raised: Curiosities raised in earlier Conversations, newest
            first.
        messages: The Conversation's messages, oldest first.
        snapshot: The User whose Conversation it was.

    Returns:
        Today's date, the Memory Items, Threads and Curiosities, those asked
        recently, and the Conversation.
    """
    time_zone = snapshot.user.time_zone
    item_lines = "\n".join(
        f"[{number}] ({category_names.get(item.category_id, 'Other')}) {item.content}"
        for number, item in context.items.items()
    )
    thread_lines = "\n".join(
        f"[{number}] {describe_thread(thread, time_zone)}"
        for number, thread in context.threads.items()
    )
    curiosity_lines = "\n".join(
        f"[{number}] {describe_curiosity(curiosity, context.raised_here)}"
        for number, curiosity in context.known.items()
    )
    recent_lines = "\n".join(
        f"- {curiosity.question} ("
        + (
            REACTION_WORDS[curiosity.reaction]
            if curiosity.reaction
            else "not known how they took it"
        )
        + ")"
        for curiosity in recently_raised
    )
    return (
        f"Today: {snapshot.today:%A} {format_date(snapshot.today)}\n\n"
        f"What Zeph remembers about them:\n{item_lines or 'Nothing yet.'}\n\n"
        f"Life Threads this Conversation touches:\n{thread_lines or 'None.'}\n\n"
        f"Curiosities waiting or brought up in this Conversation:\n"
        f"{curiosity_lines or 'None yet.'}\n\n"
        f"Asked recently, don't ask again:\n{recent_lines or 'Nothing yet.'}\n\n"
        f"The Conversation:\n{to_transcript_lines(messages)}"
    )


class CuriosityKeeper:
    """Writes, updates and closes a User's Curiosities when a Conversation ends.

    It also records how the User took each Curiosity raised in the
    Conversation. No more than the Admin-set number wait at once: the oldest
    waiting ones are closed.
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
            repositories: Where Curiosities, Memory Items and Life Threads are
                stored.
            chat_model: Writes the Curiosities and records the tokens used.
            embedder: Embeds the Conversation to find the Threads it touches.
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
    ) -> None:
        """Update the User's Curiosities from an ended Conversation.

        The model sees the User's Memory Items, the Threads the Conversation
        touches, their waiting Curiosities, those raised in it and those
        raised recently. An unreadable answer is asked again once; if it is
        still unreadable nothing changes.

        Args:
            snapshot: The User whose Conversation it was; User Memory and
                Curiosities work for them.
            conversation_id: The ended Conversation.
            messages: Its messages, oldest first.
        """
        texts = incoming_texts(messages)
        if not texts:
            return
        store = self._repositories.curiosities
        user_id = snapshot.user.id
        waiting = store.list_waiting(user_id)
        raised_here = store.list_raised_in(conversation_id)
        threads = {
            thread.id: thread
            for thread in [
                *self._repositories.life_threads.list_raised_in(conversation_id),
                *find_threads_in(
                    self._repositories,
                    self._embedder,
                    snapshot,
                    texts,
                    MOST_THREADS_AT_CONVERSATION_END,
                ),
            ]
        }
        context = CuriosityKeepingContext(
            user_id=user_id,
            now=self._clock.now(),
            known=dict(enumerate([*raised_here, *waiting], start=1)),
            raised_here={curiosity.id for curiosity in raised_here},
            items=dict(
                enumerate(self._repositories.user_memory.list_items(user_id), start=1)
            ),
            threads=dict(enumerate(threads.values(), start=1)),
        )
        recently_raised = [
            curiosity
            for curiosity in store.list_recently_raised(
                user_id, RECENTLY_RAISED_TO_SHOW
            )
            if curiosity.raised_conversation_id != conversation_id
        ]
        category_names = {
            category.id: category.name
            for category in self._repositories.memory_categories.list_all()
        }
        entries = self._ask(
            snapshot,
            describe_curiosities_to_keep(
                context, category_names, recently_raised, messages, snapshot
            ),
        )
        if entries is None:
            logger.warning("Curiosity keeping gave no readable answer")
            return
        store.save_changes(
            close_oldest_over_limit(
                plan_curiosity_changes(entries, context),
                waiting,
                snapshot.settings.get(CURIOSITIES_WAITING_LIMIT),
            )
        )

    def _ask(self, snapshot: UserSnapshot, description: str) -> list[Any] | None:
        """Ask the model about the Curiosities, once more if it can't be read.

        Args:
            snapshot: The User whose Conversation it was.
            description: What it is given.

        Returns:
            The Curiosities it wrote, or None if both answers were unreadable.
        """
        settings = snapshot.settings
        for _ in range(2):
            answer = self._chat_model.generate(
                snapshot=snapshot,
                step=ModelStep.CURIOSITIES,
                model=settings.get(CURIOSITY_KEEPING_MODEL),
                instructions=settings.get(CURIOSITY_KEEPING_PROMPT),
                history=[ChatLine(role=ChatRole.USER, text=description)],
            )
            entries = read_curiosity_keeping_answer(answer)
            if entries is not None:
                return entries
        return None
