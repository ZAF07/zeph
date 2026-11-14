import json
import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from companion.core.memory_retrieval import format_day
from companion.core.models import (
    BringUpWay,
    ChatLine,
    ChatRole,
    ConversationMessage,
    LifeThread,
    LifeThreadToSave,
    MessageDirection,
    ModelStep,
    ThreadReaction,
    ThreadToBringUp,
    UnderstandingForm,
    UserSnapshot,
)
from companion.core.platform_settings import (
    LIFE_THREAD_BRUSHED_OFF_WAIT,
    LIFE_THREAD_KEEPING_MODEL,
    LIFE_THREAD_KEEPING_PROMPT,
    LIFE_THREADS_CLOSENESS_PERCENT,
    LIFE_THREADS_PER_REPLY,
)
from companion.core.ports import Clock, Embedder, Repositories
from companion.core.transcripts import to_transcript_lines
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

RECENT_TEXTS_TO_REMIND = 3
LONGEST_NAME_IN_WORDS = 3
MOST_THREADS_AT_CONVERSATION_END = 10
REACTION_WORDS = {
    ThreadReaction.ENGAGED: "they engaged",
    ThreadReaction.BRUSHED_OFF: "they brushed it off",
    ThreadReaction.ASKED_TO_DROP: "they asked you to drop it",
}
BRING_UP_WORDS = {
    BringUpWay.LEAD: "lead with it",
    BringUpWay.WEAVE: "weave it in if the moment allows",
}


@dataclass(frozen=True)
class RemindedThread:
    """A Life Thread the Companion was reminded of, numbered for the models.

    Attributes:
        number: Its number in the list the model is shown, from 1.
        thread: The Thread.
        hold_back: Why it must not be brought up now; "" if it may be.
    """

    number: int
    thread: LifeThread
    hold_back: str


def to_words(text: str) -> list[str]:
    """Split a text into its words, in lower case and without punctuation.

    Args:
        text: The text, e.g. "Mei's wedding!".

    Returns:
        The words, e.g. ["mei", "s", "wedding"].
    """
    return re.findall(r"[^\W_]+", text.lower())


def name_key(name: str) -> str:
    """Write a person or thing in a Thread the way messages are matched to it.

    Args:
        name: The name, e.g. "Aunt Rosa".

    Returns:
        It in lower case, one word apart, e.g. "aunt rosa"; "" if it has no
        words.
    """
    return " ".join(to_words(name))


def name_keys(people: Sequence[str]) -> tuple[str, ...]:
    """Write a Thread's people or things the way messages are matched to them.

    A name with a note in brackets, or several names in one, counts as each
    of them: "Mei (sister)" is found by "Mei" and by "sister".

    Args:
        people: The people or things, as the model wrote them.

    Returns:
        Their keys, as `name_key` writes them, each once.
    """
    keys: dict[str, None] = {}
    for name in people:
        for part in re.split(r"[(),/;]", name):
            if key := name_key(part):
                keys[key] = None
    return tuple(keys)


def name_phrases(texts: Sequence[str]) -> list[str]:
    """List the words and short runs of words in some texts, to match names.

    Args:
        texts: The texts, e.g. the User's last few messages.

    Returns:
        Each run of one to three words in a text, as `name_key` writes
        names, each once.
    """
    phrases: dict[str, None] = {}
    for text in texts:
        words = to_words(text)
        for start in range(len(words)):
            for length in range(1, LONGEST_NAME_IN_WORDS + 1):
                if start + length <= len(words):
                    phrases[" ".join(words[start : start + length])] = None
    return list(phrases)


def incoming_texts(messages: Sequence[ConversationMessage]) -> list[str]:
    """List the texts the User sent, oldest first.

    Args:
        messages: The Conversation's messages, oldest first.

    Returns:
        The texts of the User's messages.
    """
    return [
        message.content
        for message in messages
        if message.direction == MessageDirection.INCOMING and message.content
    ]


def hold_back_reason(
    thread: LifeThread,
    conversation_id: UUID,
    now: datetime,
    brushed_off_wait: timedelta,
    time_zone: str | None,
) -> str:
    """Say why a Thread must not be brought up now, if it mustn't.

    It isn't raised twice in a Conversation, waits a while after the User
    brushed it off, and is never raised again once they asked to drop it.

    Args:
        thread: The Thread.
        conversation_id: The Conversation being answered.
        now: The current time.
        brushed_off_wait: How long to wait after they brushed it off.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        The reason, or "" if it may be brought up.
    """
    if thread.last_raised_conversation_id == conversation_id:
        return "you already brought it up in this Conversation"
    if thread.last_reaction == ThreadReaction.ASKED_TO_DROP:
        return "they asked you to drop it; only talk about it if they raise it"
    if (
        thread.last_reaction == ThreadReaction.BRUSHED_OFF
        and thread.last_raised_at is not None
        and now < thread.last_raised_at + brushed_off_wait
    ):
        wait_until = format_day(thread.last_raised_at + brushed_off_wait, time_zone)
        return f"they brushed it off; wait until {wait_until}"
    return ""


def describe_thread(thread: LifeThread, time_zone: str | None) -> str:
    """Write a Thread's title, state, people or things and story on one line.

    Args:
        thread: The Thread.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        E.g. "Falling-out with Mei (open; updated 3 Feb 2026). People or
        things: Mei, sister. Story: ..."
    """
    state = "open" if thread.is_open else "settled"
    people = ", ".join(thread.people) or "none named"
    return (
        f"{thread.title} ({state}; updated "
        f"{format_day(thread.updated_at, time_zone)}). "
        f"People or things: {people}. Story: {thread.story}"
    )


def describe_reminded_threads(
    reminded: Sequence[RemindedThread], time_zone: str | None
) -> str:
    """Write the reminded Threads as the Understanding model reads them.

    Args:
        reminded: The Threads, numbered.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        One line per Thread with when it was last brought up and how they
        took it, and why not to bring it up now; "None." if there are none.
    """
    lines = []
    for item in reminded:
        thread = item.thread
        line = f"[{item.number}] {describe_thread(thread, time_zone)}"
        if thread.last_raised_at is not None:
            reaction = (
                REACTION_WORDS[thread.last_reaction]
                if thread.last_reaction
                else "not known how they took it"
            )
            line += (
                f" Last brought up {format_day(thread.last_raised_at, time_zone)}; "
                f"{reaction}."
            )
        if item.hold_back:
            line += f" Don't bring it up: {item.hold_back}."
        lines.append(line)
    return "\n".join(lines) or "None."


def format_threads_for_reply(
    reminded: Sequence[RemindedThread],
    form: UnderstandingForm | None,
    time_zone: str | None,
) -> str:
    """Write the reply's section on Life Threads.

    With a form, the Threads it touches or brings up go in with their
    stories, then how to bring each up, then what to leave alone. Without
    one, because the Understanding failed, every reminded Thread that isn't
    held back goes in with its story and nothing is brought up.

    Args:
        reminded: The Threads the Companion was reminded of.
        form: The Understanding's form; None if it couldn't be made.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        The section; "" if there is nothing to tell.
    """
    if form is None:
        mattering = [item.thread for item in reminded if not item.hold_back]
        bring_up_lines: list[str] = []
        left_alone_lines: list[str] = []
    else:
        left_alone_ids = {item.thread_id for item in form.left_alone}
        mattering_titles = set(form.threads_touched) | {
            item.title for item in form.bring_up
        }
        mattering = [
            item.thread
            for item in reminded
            if item.thread.title in mattering_titles
            and item.thread.id not in left_alone_ids
        ]
        bring_up_lines = [
            f"- {item.title}: {BRING_UP_WORDS[item.how]}." for item in form.bring_up
        ]
        left_alone_lines = [
            f"- {item.title}: {item.reason}" for item in form.left_alone
        ]
    sections = []
    if mattering:
        sections.append(
            "Ongoing stories in their life that matter here:\n"
            + "\n".join(
                f"- {describe_thread(thread, time_zone)}" for thread in mattering
            )
        )
    if bring_up_lines:
        sections.append(
            "Bring up, the way a friend who remembers would:\n"
            + "\n".join(bring_up_lines)
        )
    if left_alone_lines:
        sections.append(
            "Leave alone, don't raise these:\n" + "\n".join(left_alone_lines)
        )
    return "\n\n".join(sections)


def find_threads_in(
    repositories: Repositories,
    embedder: Embedder,
    snapshot: UserSnapshot,
    texts: Sequence[str],
    limit: int,
) -> list[LifeThread]:
    """Find the User's Threads that some of their texts name or are close to.

    A Thread counts if the texts name someone or something in it, or if its
    story is at least as close in meaning as the Admin-set bar. If the texts
    can't be embedded, the failure is logged and Threads are found by name
    only.

    Args:
        repositories: Where Life Threads are stored.
        embedder: Embeds the texts.
        snapshot: The User whose Threads are searched.
        texts: Their texts, oldest first.
        limit: The most Threads to return.

    Returns:
        The Threads, open first, then those named, then the closest.
    """
    try:
        embedding: list[float] | None = embedder.embed_query("\n".join(texts))
    except Exception:
        logger.exception("Could not embed the texts to find Life Threads by")
        embedding = None
    return repositories.life_threads.find_reminded(
        snapshot.user.id,
        name_phrases(texts),
        embedding,
        min_closeness=snapshot.settings.get(LIFE_THREADS_CLOSENESS_PERCENT) / 100,
        limit=limit,
    )


class ThreadReminder:
    """Reminds the Companion of the User's Life Threads before each reply.

    No model call: one search finds the User's Threads that name someone or
    something in their last few texts, or whose story is close in meaning
    to them, however old.
    """

    def __init__(
        self, repositories: Repositories, embedder: Embedder, clock: Clock
    ) -> None:
        """Set up the reminder.

        Args:
            repositories: Where Conversations and Life Threads are stored.
            embedder: Embeds the User's last few texts.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._embedder = embedder
        self._clock = clock

    def remind(
        self, snapshot: UserSnapshot, conversation_id: UUID
    ) -> list[RemindedThread]:
        """Find the User's Threads that the Message reminds the Companion of.

        Open Threads come first. Only those named, or at least as close in
        meaning as the Admin-set bar, count, up to the Admin-set number.
        Each says why it must not be brought up now, if it mustn't. If the
        texts can't be embedded, Threads are found by name only.

        Args:
            snapshot: The User being answered.
            conversation_id: The Conversation the Message is in.

        Returns:
            The Threads, numbered from 1.
        """
        settings = snapshot.settings
        limit = settings.get(LIFE_THREADS_PER_REPLY)
        messages = self._repositories.conversations.list_messages(conversation_id)
        recent_texts = incoming_texts(messages)[-RECENT_TEXTS_TO_REMIND:]
        if limit < 1 or not recent_texts:
            return []
        threads = find_threads_in(
            self._repositories, self._embedder, snapshot, recent_texts, limit
        )
        now = self._clock.now()
        wait = settings.get(LIFE_THREAD_BRUSHED_OFF_WAIT)
        return [
            RemindedThread(
                number=number,
                thread=thread,
                hold_back=hold_back_reason(
                    thread, conversation_id, now, wait, snapshot.user.time_zone
                ),
            )
            for number, thread in enumerate(threads, start=1)
        ]

    def mark_raised(
        self, conversation_id: UUID, brought_up: Sequence[ThreadToBringUp]
    ) -> None:
        """Note that the reply just sent brought up some Threads.

        Args:
            conversation_id: The Conversation the reply was sent in.
            brought_up: The Threads the Understanding chose to bring up.
        """
        self._repositories.life_threads.mark_raised(
            [item.thread_id for item in brought_up], conversation_id, self._clock.now()
        )


def read_thread_keeping_answer(answer: str) -> list[Any] | None:
    """Read the Threads the keeping model wrote from its JSON answer.

    Text around the JSON object, such as a code fence, is ignored.

    Args:
        answer: The model's answer.

    Returns:
        The Threads, as the model wrote them; None if it can't be read.
    """
    start, end = answer.find("{"), answer.rfind("}")
    if start == -1 or end < start:
        return None
    try:
        parsed = json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or not isinstance(parsed.get("threads"), list):
        return None
    threads: list[Any] = parsed["threads"]
    return threads


def read_text(entry: dict[str, Any], key: str) -> str | None:
    """Read a non-empty text field from one Thread the model wrote.

    Args:
        entry: The Thread, as the model wrote it.
        key: The field's name.

    Returns:
        The text without surrounding spaces, or None if missing or empty.
    """
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def read_people(entry: dict[str, Any]) -> tuple[str, ...] | None:
    """Read the people or things in one Thread the model wrote.

    Args:
        entry: The Thread, as the model wrote it.

    Returns:
        The names that have words in them, each once; None if not given.
    """
    value = entry.get("people")
    if not isinstance(value, list):
        return None
    names: dict[str, None] = {}
    for name in value:
        if isinstance(name, str) and name_key(name):
            names[name.strip()] = None
    return tuple(names)


def plan_thread_changes(
    entries: list[Any],
    known: dict[int, LifeThread],
    raised_here: set[UUID],
    user_id: UUID,
    now: datetime,
) -> list[LifeThread]:
    """Turn the Threads the model wrote into new and changed Threads to save.

    An entry with a known Thread's number changes that Thread; one without a
    number starts a Thread if it has a title and story. An unknown number,
    a number already used, or a reaction for a Thread not brought up in this
    Conversation is skipped.

    Args:
        entries: The Threads, as the model wrote them.
        known: The Threads the model was shown, by number.
        raised_here: The IDs of those brought up in this Conversation.
        user_id: The User whose Threads they are.
        now: When the changes are made.

    Returns:
        The new and changed Threads.
    """
    planned: list[LifeThread] = []
    used_numbers: set[int] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        title, story = read_text(entry, "title"), read_text(entry, "story")
        people = read_people(entry)
        is_open = entry.get("open")
        number = entry.get("thread")
        if number is None:
            if title is None or story is None:
                continue
            planned.append(
                LifeThread(
                    id=uuid4(),
                    user_id=user_id,
                    title=title,
                    story=story,
                    people=people or (),
                    is_open=is_open if isinstance(is_open, bool) else True,
                    started_at=now,
                    updated_at=now,
                )
            )
            continue
        if not isinstance(number, int) or number in used_numbers:
            continue
        existing = known.get(number)
        if existing is None:
            continue
        used_numbers.add(number)
        reaction = entry.get("reaction")
        changed = replace(
            existing,
            title=title or existing.title,
            story=story or existing.story,
            people=people if people is not None else existing.people,
            is_open=is_open if isinstance(is_open, bool) else existing.is_open,
            last_reaction=(
                ThreadReaction(reaction)
                if existing.id in raised_here
                and reaction in {value.value for value in ThreadReaction}
                else existing.last_reaction
            ),
        )
        if changed != existing:
            story_changed = (changed.title, changed.story, changed.people) != (
                existing.title,
                existing.story,
                existing.people,
            )
            planned.append(
                replace(changed, updated_at=now) if story_changed else changed
            )
    return planned


def describe_threads_to_keep(
    known: dict[int, LifeThread],
    raised_here: set[UUID],
    messages: list[ConversationMessage],
    now: datetime,
    time_zone: str | None,
) -> str:
    """Write what the Life Thread keeping model is given.

    Args:
        known: The Threads it may update, by number.
        raised_here: The IDs of those brought up in this Conversation.
        messages: The Conversation's messages, oldest first.
        now: The current time.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        Today's date, the Threads and the Conversation.
    """
    thread_lines = "\n".join(
        f"[{number}] {describe_thread(thread, time_zone)}"
        + (" Brought up in this Conversation." if thread.id in raised_here else "")
        for number, thread in known.items()
    )
    return (
        f"Today: {format_day(now, time_zone)}\n\n"
        f"Life Threads Zeph follows that this may touch:\n"
        f"{thread_lines or 'None yet.'}\n\n"
        f"The Conversation:\n{to_transcript_lines(messages)}"
    )


class LifeThreadKeeper:
    """Starts and adds to a User's Life Threads when a Conversation ends.

    It also records how the User took each Thread brought up in the
    Conversation. Changed Threads are embedded again, so they are found by
    meaning.
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
            repositories: Where Life Threads are stored.
            chat_model: Writes the Threads and records the tokens used.
            embedder: Embeds each new or changed Thread.
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
        """Update the User's Threads from an ended Conversation.

        The model sees the Threads the whole Conversation reminds the
        Companion of, plus those brought up in it. An unreadable answer is
        asked again once; if it is still unreadable nothing changes. A
        Thread that can't be embedded is still saved.

        Args:
            snapshot: The User whose Conversation it was; User Memory works
                for them.
            conversation_id: The ended Conversation.
            messages: Its messages, oldest first.
        """
        threads = self._repositories.life_threads
        texts = incoming_texts(messages)
        if not texts:
            return
        raised = threads.list_raised_in(conversation_id)
        raised_ids = {thread.id for thread in raised}
        reminded = find_threads_in(
            self._repositories,
            self._embedder,
            snapshot,
            texts,
            MOST_THREADS_AT_CONVERSATION_END,
        )
        known_threads = {thread.id: thread for thread in [*raised, *reminded]}
        known = dict(enumerate(known_threads.values(), start=1))
        now = self._clock.now()
        entries = self._ask(
            snapshot,
            describe_threads_to_keep(
                known, raised_ids, messages, now, snapshot.user.time_zone
            ),
        )
        if entries is None:
            logger.warning("Life Thread keeping gave no readable answer")
            return
        planned = plan_thread_changes(entries, known, raised_ids, snapshot.user.id, now)
        threads.save_many(
            added=[
                self._to_save(thread)
                for thread in planned
                if thread.id not in known_threads
            ],
            changed=[
                self._to_save(thread)
                for thread in planned
                if thread.id in known_threads
            ],
        )

    def _to_save(self, thread: LifeThread) -> LifeThreadToSave:
        """Add a Thread's name keys and embedding, so it can be found.

        Args:
            thread: The new or changed Thread.

        Returns:
            It with its name keys and embedding; no embedding if that failed.
        """
        try:
            [embedding] = self._embedder.embed_passages(
                [f"{thread.title}. {thread.story}"]
            )
        except Exception:
            logger.exception("Could not embed a Life Thread")
            embedding = None
        return LifeThreadToSave(
            thread=thread,
            name_keys=name_keys(thread.people),
            embedding=embedding,
        )

    def _ask(self, snapshot: UserSnapshot, description: str) -> list[Any] | None:
        """Ask the model about the Threads, once more if it can't be read.

        Args:
            snapshot: The User whose Conversation it was.
            description: The Threads and the Conversation.

        Returns:
            The Threads it wrote, or None if both answers were unreadable.
        """
        settings = snapshot.settings
        for _ in range(2):
            answer = self._chat_model.generate(
                snapshot=snapshot,
                step=ModelStep.LIFE_THREADS,
                model=settings.get(LIFE_THREAD_KEEPING_MODEL),
                instructions=settings.get(LIFE_THREAD_KEEPING_PROMPT),
                history=[ChatLine(role=ChatRole.USER, text=description)],
            )
            entries = read_thread_keeping_answer(answer)
            if entries is not None:
                return entries
        return None
