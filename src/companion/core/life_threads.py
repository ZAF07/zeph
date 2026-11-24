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
    ReplyPlanForm,
    ThreadReaction,
    ThreadToBringUp,
    UserSnapshot,
)
from companion.core.platform_settings import (
    LIFE_THREAD_BRUSHED_OFF_WAIT,
    LIFE_THREAD_KEEPING_MODEL,
    LIFE_THREAD_KEEPING_PROMPT,
    LIFE_THREAD_KEEPING_THINKING,
    LIFE_THREADS_CLOSENESS_PERCENT,
    LIFE_THREADS_PER_REPLY,
    LIFE_THREADS_TEXTS_TO_SEARCH,
)
from companion.core.ports import Clock, Embedder, Repositories
from companion.core.transcripts import to_transcript_lines
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

RECENT_TEXTS_TO_SEARCH = 3
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


def incoming_messages(
    messages: Sequence[ConversationMessage],
) -> list[ConversationMessage]:
    """List the User's messages that have text, oldest first.

    Args:
        messages: The Conversation's messages, oldest first.

    Returns:
        The User's messages with non-empty content.
    """
    return [
        message
        for message in messages
        if message.direction == MessageDirection.INCOMING and message.content
    ]


def incoming_texts(messages: Sequence[ConversationMessage]) -> list[str]:
    """List the texts the User sent, oldest first.

    Args:
        messages: The Conversation's messages, oldest first.

    Returns:
        The texts of the User's messages.
    """
    return [message.content for message in incoming_messages(messages)]


def recent_texts_to_search(
    messages: Sequence[ConversationMessage], count: int = RECENT_TEXTS_TO_SEARCH
) -> list[str]:
    """List the User's last few texts and what they reply to, to search on.

    A text that replies to an earlier one comes after that Replied-to Text,
    so a reply to an old text searches on what the old text said too.

    Args:
        messages: The Conversation's messages, oldest first.
        count: How many of their latest texts to list.

    Returns:
        Their last `count` texts, oldest first, each after its Replied-to
        Text if it has one with words; none if `count` is 0.
    """
    if count < 1:
        return []
    texts: list[str] = []
    for message in incoming_messages(messages)[-count:]:
        if message.replied_to is not None and message.replied_to.text:
            texts.append(message.replied_to.text)
        texts.append(message.content)
    return texts


def threads_in_mind(
    found: Sequence[LifeThread], earlier: Sequence[LifeThread], limit: int
) -> list[LifeThread]:
    """List the Threads in mind for a reply, at most the Admin-set number.

    The Threads this message found come first, then those that came to mind
    earlier in the Conversation, the first to come to mind first, each once.

    Args:
        found: The Threads this message found, in search order.
        earlier: The Threads in mind in the Conversation, the first to come
            to mind first; may include ones in `found`.
        limit: The most Threads in mind at once.

    Returns:
        The Threads, at most `limit` of them.
    """
    found_ids = {thread.id for thread in found}
    earlier_only = [thread for thread in earlier if thread.id not in found_ids]
    return [*found, *earlier_only][: max(limit, 0)]


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
    """Write the reminded Threads as the Reply Plan model reads them.

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
    form: ReplyPlanForm | None,
    time_zone: str | None,
) -> str:
    """Write the reply's section on the Life Threads that matter here.

    Only the Threads the Reply Plan picked go in: those it touches or
    brings up, with their stories, then how to bring each up; the ones to
    leave alone are left out, for `format_threads_left_alone`. Without a
    form, because the Reply Plan failed, no Thread goes in, so a wide
    memory never crowds the reply.

    Args:
        reminded: The Threads the Companion was reminded of.
        form: The Reply Plan's form; None if it couldn't be made.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        The section; "" if there is nothing to tell.
    """
    if form is None:
        return ""
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
    return "\n\n".join(sections)


def format_threads_left_alone(form: ReplyPlanForm | None) -> str:
    """Write the reply's section on the Life Threads to leave alone.

    Args:
        form: The Reply Plan's form; None if it couldn't be made.

    Returns:
        The Threads to leave alone, each with why; "" if there are none.
    """
    if form is None or not form.left_alone:
        return ""
    lines = [f"- {item.title}: {item.reason}" for item in form.left_alone]
    return "Leave alone, don't raise these:\n" + "\n".join(lines)


def find_threads_in(
    repositories: Repositories,
    embedder: Embedder,
    snapshot: UserSnapshot,
    texts: Sequence[str],
    limit: int,
    meaning: str = "",
) -> list[LifeThread]:
    """Find the User's Threads that some of their texts name or are close to.

    A Thread counts if the texts name someone or something in it, or if its
    story is at least as close in meaning as the Admin-set bar to the texts
    and what they mean. If they can't be embedded, the failure is logged and
    Threads are found by name only.

    Args:
        repositories: Where Life Threads are stored.
        embedder: Embeds the texts.
        snapshot: The User whose Threads are searched.
        texts: Their texts, oldest first.
        limit: The most Threads to return.
        meaning: What the Understanding says they mean, searched on with the
            texts; "" for the texts alone.

    Returns:
        The Threads, open first, then those named, then the closest.
    """
    search = "\n".join([meaning, *texts] if meaning else texts)
    try:
        embedding: list[float] | None = embedder.embed_query(search)
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
    something in their latest texts, or whose story is close in meaning to
    those texts and what the Understanding says they mean, however old.
    Threads that came to mind earlier in the Conversation stay in mind until
    it ends.
    """

    def __init__(
        self, repositories: Repositories, embedder: Embedder, clock: Clock
    ) -> None:
        """Set up the reminder.

        Args:
            repositories: Where Conversations and Life Threads are stored.
            embedder: Embeds what the User means and their latest texts.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._embedder = embedder
        self._clock = clock

    def remind(
        self, snapshot: UserSnapshot, conversation_id: UUID, meaning: str
    ) -> list[RemindedThread]:
        """Find the User's Threads that the Message reminds the Companion of.

        The search uses what the User means and the Admin-set number of
        their latest texts. Only Threads named, or at least as close in
        meaning as the Admin-set bar, come to mind, open ones first. Every
        one found is kept in mind for the rest of the Conversation. Threads
        that came to mind earlier follow, as `threads_in_mind` orders and
        caps them at the Admin-set number. Each says why it must not be
        brought up now, if it mustn't. If the search can't be embedded,
        Threads are found by name only.

        Args:
            snapshot: The User being answered.
            conversation_id: The Conversation the Message is in.
            meaning: What the Understanding says the User means; "" if it
                failed.

        Returns:
            The Threads, numbered from 1.
        """
        settings = snapshot.settings
        life_thread_repository = self._repositories.life_threads
        limit = settings.get(LIFE_THREADS_PER_REPLY)
        messages = self._repositories.conversations.list_messages(conversation_id)
        recent_texts = recent_texts_to_search(
            messages, settings.get(LIFE_THREADS_TEXTS_TO_SEARCH)
        )
        found = (
            find_threads_in(
                self._repositories,
                self._embedder,
                snapshot,
                recent_texts,
                limit,
                meaning,
            )
            if limit > 0 and recent_texts
            else []
        )
        now = self._clock.now()
        life_thread_repository.keep_in_mind(
            conversation_id, [thread.id for thread in found], now
        )
        threads = threads_in_mind(
            found, life_thread_repository.list_in_mind(conversation_id), limit
        )
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
            brought_up: The Threads the Reply Plan chose to bring up.
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
    """Read a non-empty text field from one entry a model wrote.

    Args:
        entry: The entry, such as a Thread, as the model wrote it.
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
        f"The Conversation:\n{to_transcript_lines(messages, time_zone)}"
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
    ) -> list[LifeThread]:
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

        Returns:
            The Threads the Conversation touched: those it started or
            changed, as saved, and those brought up in it.
        """
        threads = self._repositories.life_threads
        texts = incoming_texts(messages)
        if not texts:
            return []
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
            return raised
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
        planned_ids = {thread.id for thread in planned}
        return planned + [thread for thread in raised if thread.id not in planned_ids]

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
                thinking=settings.get(LIFE_THREAD_KEEPING_THINKING),
                instructions=settings.get(LIFE_THREAD_KEEPING_PROMPT),
                history=[ChatLine(role=ChatRole.USER, text=description)],
            )
            entries = read_thread_keeping_answer(answer)
            if entries is not None:
                return entries
        return None
