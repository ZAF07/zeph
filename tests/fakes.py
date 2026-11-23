import hashlib
import json
import math
import re
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from companion.adapters.postgres.tables import EMBEDDING_SIZE
from companion.core.incoming_messages import MESSAGE_WAIT_PREFIX
from companion.core.models import (
    AccountIdentity,
    ChannelSticker,
    ChatLine,
    ModelAnswer,
    PhotoImage,
    StickerImage,
    ToolCallRecord,
    WebSearchResult,
)
from companion.core.ports import ChatTool
from companion.core.typing_keeper import TYPING_WAIT_PREFIX
from companion.core.woven_check_ins import BROUGHT_UP_CHECK_PROMPT

TOKENS_IN_PER_CALL = 120
TOKENS_OUT_PER_CALL = 30
PHOTO_TOKENS_IN = 900
PHOTO_TOKENS_OUT = 80
FAKE_PHOTO = PhotoImage(content=b"fake-jpeg-bytes", media_type="image/jpeg")


@dataclass(frozen=True)
class SentText:
    """A text message the fake chat channel was asked to send."""

    chat_id: int
    text: str


@dataclass(frozen=True)
class SentSticker:
    """A sticker the fake chat channel was asked to send."""

    chat_id: int
    file_id: str


@dataclass(frozen=True)
class SentReaction:
    """A reaction the fake chat channel was asked to put on a message."""

    chat_id: int
    message_id: int
    emoji: str


@dataclass(frozen=True)
class SentPhoto:
    """A photo the fake chat channel was asked to send."""

    chat_id: int
    file_id: str


class FakeChatChannel:
    """Chat channel that records sent messages instead of sending them.

    `events` lists texts, stickers, photos, reactions and typing in the
    order they happened. Queue exceptions in `text_send_failures` to make
    the next text sends raise them. Set `photo_send_failure` to make sending
    a photo raise it, `reaction_failure` to make reacting raise it, and
    `typing_failure` to make showing typing raise it.
    Sticker sets and sticker images it knows are set by tests; set
    `sticker_lookup_failure` to make looking them up raise it. Photos are
    served from `photos`, or `FAKE_PHOTO` for any other file ID; queue
    exceptions in `photo_download_failures` to make the next downloads fail.
    """

    def __init__(self) -> None:
        """Start with nothing sent and no sticker sets or images."""
        self.sent: list[SentText] = []
        self.sent_stickers: list[SentSticker] = []
        self.reactions: list[SentReaction] = []
        self.reaction_failure: Exception | None = None
        self.typing_shown_in: list[int] = []
        self.typing_failure: Exception | None = None
        self.events: list[str] = []
        self.sticker_sets: dict[str, list[ChannelSticker]] = {}
        self.sticker_images: dict[str, StickerImage] = {}
        self.sticker_lookup_failure: Exception | None = None
        self.photos: dict[str, PhotoImage] = {}
        self.photo_download_failures: list[Exception] = []
        self.downloaded_photos: list[str] = []
        self.sent_photos: list[SentPhoto] = []
        self.photo_send_failure: Exception | None = None
        self.text_send_failures: list[Exception] = []

    def send_text(self, chat_id: int, text: str) -> None:
        """Record a text message.

        Args:
            chat_id: The chat the message is for.
            text: The message text.

        Raises:
            Exception: The first of the queued `text_send_failures`, if any;
                the message is then not recorded.
        """
        if self.text_send_failures:
            raise self.text_send_failures.pop(0)
        self.sent.append(SentText(chat_id=chat_id, text=text))
        self.events.append(f"text: {text}")

    def send_sticker(self, chat_id: int, file_id: str) -> None:
        """Record a sticker.

        Args:
            chat_id: The chat the sticker is for.
            file_id: The sticker's file ID.
        """
        self.sent_stickers.append(SentSticker(chat_id=chat_id, file_id=file_id))
        self.events.append(f"sticker: {file_id}")

    def react(self, chat_id: int, message_id: int, emoji: str) -> None:
        """Record a reaction.

        Args:
            chat_id: The chat the message is in.
            message_id: The message reacted to.
            emoji: The reaction's emoji.

        Raises:
            Exception: The `reaction_failure` set on the fake, if any.
        """
        if self.reaction_failure is not None:
            raise self.reaction_failure
        self.reactions.append(SentReaction(chat_id, message_id, emoji))
        self.events.append(f"reaction: {emoji}")

    def get_sticker_set(self, name: str) -> list[ChannelSticker] | None:
        """Return a sticker set the test set up.

        Args:
            name: The set's name.

        Returns:
            Its stickers, or None if the test set up no such set.

        Raises:
            Exception: The `sticker_lookup_failure` set on the fake, if any.
        """
        if self.sticker_lookup_failure is not None:
            raise self.sticker_lookup_failure
        return self.sticker_sets.get(name)

    def get_sticker_image(self, file_id: str) -> StickerImage | None:
        """Return a sticker image the test set up.

        Args:
            file_id: The image's file ID.

        Returns:
            The image, or None if the test set up none.

        Raises:
            Exception: The `sticker_lookup_failure` set on the fake, if any.
        """
        if self.sticker_lookup_failure is not None:
            raise self.sticker_lookup_failure
        return self.sticker_images.get(file_id)

    def download_photo(self, file_id: str) -> PhotoImage:
        """Record the download and return the photo the test set up.

        Args:
            file_id: The photo's file ID.

        Returns:
            The photo set up for that file ID, or `FAKE_PHOTO`.

        Raises:
            Exception: The next queued `photo_download_failures`, if any.
        """
        self.downloaded_photos.append(file_id)
        if self.photo_download_failures:
            raise self.photo_download_failures.pop(0)
        return self.photos.get(file_id, FAKE_PHOTO)

    def send_photo(self, chat_id: int, file_id: str) -> None:
        """Record a photo sent by its file ID.

        Args:
            chat_id: The chat the photo is for.
            file_id: The photo's file ID.

        Raises:
            Exception: The `photo_send_failure` set on the fake, if any.
        """
        if self.photo_send_failure is not None:
            raise self.photo_send_failure
        self.sent_photos.append(SentPhoto(chat_id=chat_id, file_id=file_id))
        self.events.append(f"photo: {file_id}")

    def show_typing(self, chat_id: int) -> None:
        """Record that typing was shown.

        Args:
            chat_id: The chat it was shown in.

        Raises:
            Exception: `typing_failure`, if set; typing is then not recorded.
        """
        if self.typing_failure is not None:
            raise self.typing_failure
        self.typing_shown_in.append(chat_id)
        self.events.append("typing")

    def texts_sent_to(self, chat_id: int) -> list[str]:
        """List the texts sent to one chat, oldest first.

        Args:
            chat_id: The chat to look up.

        Returns:
            The texts sent to that chat.
        """
        return [message.text for message in self.sent if message.chat_id == chat_id]


class FakeAuthVerifier:
    """Auth provider that accepts tokens handed out by `token_for`.

    It also stands in for the auth provider's accounts: a deleted account is
    recorded and its tokens stop working. Deleting an account listed in
    `failing_deletes` fails, as if the auth provider were down.
    """

    def __init__(self) -> None:
        """Start with no known tokens, no deleted accounts and no failures."""
        self._identities_by_token: dict[str, AccountIdentity] = {}
        self.deleted_accounts: list[str] = []
        self.failing_deletes: set[str] = set()

    def token_for(self, auth_id: str, email: str) -> str:
        """Create a token that verifies as the given account.

        Args:
            auth_id: The account ID the auth provider would return.
            email: The account's email address.

        Returns:
            A bearer token for that account.
        """
        token = f"token-{auth_id}"
        self._identities_by_token[token] = AccountIdentity(auth_id=auth_id, email=email)
        return token

    def verify(self, token: str) -> AccountIdentity | None:
        """Look up the account for a token.

        Args:
            token: The bearer token from the request.

        Returns:
            The account identity, or None if the token is unknown.
        """
        return self._identities_by_token.get(token)

    def delete_account(self, auth_id: str) -> None:
        """Record a deleted account and stop its tokens working.

        Args:
            auth_id: The account ID.

        Raises:
            RuntimeError: If the account is listed in `failing_deletes`.
        """
        if auth_id in self.failing_deletes:
            raise RuntimeError("The auth provider is down")
        self.deleted_accounts.append(auth_id)
        self._identities_by_token = {
            token: identity
            for token, identity in self._identities_by_token.items()
            if identity.auth_id != auth_id
        }


class FakeClock:
    """Clock that only moves when told to, or when something sleeps on it."""

    def __init__(self, start: datetime) -> None:
        """Set the starting time.

        Args:
            start: The time the clock starts at.
        """
        self._now = start
        self.slept: list[float] = []

    def now(self) -> datetime:
        """Return the current fake time.

        Returns:
            The current fake time.
        """
        return self._now

    def advance(self, duration: timedelta) -> None:
        """Move the clock forward.

        Args:
            duration: How far to move.
        """
        self._now += duration

    def sleep(self, seconds: float) -> None:
        """Record a pause and move the clock forward by it, without waiting.

        Args:
            seconds: How long the pause is.
        """
        self.slept.append(seconds)
        self._now += timedelta(seconds=seconds)


@dataclass(frozen=True)
class ChatModelCall:
    """One call the scripted chat model received.

    Attributes:
        model: The model name asked for.
        thinking: Whether the model was asked to think first.
        instructions: The instructions given.
        history: The Conversation so far.
        tools: The tools the model was offered.
        tool_results: What each scripted tool call returned, in order.
    """

    model: str
    thinking: bool
    instructions: str
    history: list[ChatLine]
    tools: list[ChatTool] = field(default_factory=list)
    tool_results: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ToolCall:
    """A tool call to script before a reply, as a real model might make.

    Attributes:
        name: The tool's name.
        arguments: The arguments to call it with.
    """

    name: str
    arguments: dict[str, Any]


class FakeScheduler:
    """Scheduler that never runs on its own; tests run each tick by hand."""

    def __init__(self) -> None:
        """Start with no tick to run."""
        self._tick: Callable[[], None] | None = None
        self.stopped = False

    def start(self, tick: Callable[[], None]) -> None:
        """Keep the tick so a test can run it.

        Args:
            tick: The work to run on each tick.
        """
        self._tick = tick

    def stop(self) -> None:
        """Record that the scheduler was stopped."""
        self.stopped = True

    def tick(self) -> None:
        """Run one tick now, as the real scheduler would every so often."""
        assert self._tick is not None, "The app has not started the scheduler"
        self._tick()


class FakeTimer:
    """Timer that never runs on its own; tests run the waiting work by hand."""

    def __init__(self) -> None:
        """Start with nothing waiting."""
        self._waiting: dict[str, Callable[[], None]] = {}
        self.waits: list[tuple[str, float]] = []

    def start(self, key: str, seconds: float, work: Callable[[], None]) -> None:
        """Keep the work so a test can run it, replacing any under the same key.

        Args:
            key: Names the wait; starting it again restarts it.
            seconds: How long the real timer would wait.
            work: What to run when the wait ends.
        """
        self.waits.append((key, seconds))
        self._waiting[key] = work

    def run_waiting(self) -> None:
        """Run all waiting work now, as if every wait had ended."""
        waiting = list(self._waiting.values())
        self._waiting.clear()
        for work in waiting:
            work()

    def end_message_waits(self) -> None:
        """Run the waiting Message work now, as if each User had paused."""
        self._end_waits(MESSAGE_WAIT_PREFIX)

    def end_typing_waits(self) -> None:
        """Run the waiting typing work now, as if each typing wait had ended."""
        self._end_waits(TYPING_WAIT_PREFIX)

    def _end_waits(self, key_prefix: str) -> None:
        """Run the waiting work whose keys start with a prefix, as if its waits ended.

        Args:
            key_prefix: The start of the keys to run.
        """
        keys = [key for key in self._waiting if key.startswith(key_prefix)]
        for key in keys:
            self._waiting.pop(key)()


class FakeUserWorkQueue:
    """User work queue that runs work right away, on the caller's thread.

    Work added under a key whose work is running waits until that work is
    done, so each key's work still runs one piece at a time, in order. A
    failure is raised, so tests see it. A test can hold all work instead,
    to see what happens before it runs.
    """

    def __init__(self) -> None:
        """Start with nothing waiting, running work as it is added."""
        self.holding = False
        self._held: list[tuple[str, Callable[[], None]]] = []
        self._waiting: dict[str, list[Callable[[], None]]] = {}

    def add(self, key: str, work: Callable[[], None]) -> None:
        """Run the work now, unless the key's work is running or work is held.

        Args:
            key: Names one line of a User's work.
            work: What to run.
        """
        if self.holding:
            self._held.append((key, work))
            return
        line = self._waiting.get(key)
        if line is not None:
            line.append(work)
            return
        line = self._waiting[key] = [work]
        try:
            while line:
                line[0]()
                line.pop(0)
        finally:
            del self._waiting[key]

    def run_held(self) -> None:
        """Stop holding work and run all held work, in the order it was added."""
        self.holding = False
        held = list(self._held)
        self._held.clear()
        for key, work in held:
            self.add(key, work)


def understanding_answer(
    mood: str = "relaxed",
    intensity: str = "low",
    cause_known: bool = True,
    look_up_past: Sequence[str] = (),
    struggling: bool = False,
    asked_for_photo: bool = False,
    said: str = "They said hi.",
    means: str = "They're just saying hi.",
    feelings: dict[str, str] | None = None,
    wants: dict[str, str] | None = None,
) -> str:
    """Build the form the Understanding model answers with.

    Args:
        mood: How the User seems.
        intensity: How strongly: "low", "medium" or "high".
        cause_known: Whether the Companion knows why they feel that way.
        look_up_past: Phrases to search older Day Summaries with.
        struggling: Whether the User is struggling.
        asked_for_photo: Whether they asked to see one of their photos.
        said: What they said.
        means: What they mean.
        feelings: How they feel, as {"said", "read", "unclear"}; none said.
        wants: What they want, the same way; none said.

    Returns:
        The form as JSON.
    """
    return json.dumps(
        {
            "said": said,
            "means": means,
            "feelings": feelings or {"said": "", "read": "", "unclear": ""},
            "mood": mood,
            "intensity": intensity,
            "wants": wants or {"said": "", "read": "", "unclear": ""},
            "cause_known": cause_known,
            "struggling": struggling,
            "asked_for_photo": asked_for_photo,
            "look_up_past": list(look_up_past),
        }
    )


def reply_plan_answer(
    need: str = "Just chatting",
    memory_categories: Sequence[str] = (),
    guidance: str = "Just saying hi.",
    bring_up: Sequence[dict[str, Any]] = (),
    left_alone: Sequence[dict[str, Any]] = (),
    threads_touched: Sequence[int] = (),
    knowledge_documents: Sequence[object] = (),
    knowledge_search: str = "",
    lead_move: object = None,
    support_move: object = None,
    next_move: object = None,
    next_move_why: object = None,
    send_photo: object = True,
    ask_why: object = None,
    where_we_are: str = "",
    read: str = "",
    say_read: object = False,
    check_in: object = None,
    patterns_used: Sequence[object] = (),
    offer_pattern: object = None,
) -> str:
    """Build the form the Reply Plan model answers with.

    Args:
        need: The Need's name.
        memory_categories: The Memory Categories whose items matter.
        guidance: One sentence on what fits.
        bring_up: The Life Threads to bring up, e.g. {"thread": 1, "how":
            "lead"}.
        left_alone: The Life Threads to leave alone, e.g. {"thread": 1,
            "reason": "..."}.
        threads_touched: The numbers of the Life Threads the message touches.
        knowledge_documents: The listed numbers of the Knowledge documents
            to search, or anything else a model might write there; none
            means no Knowledge.
        knowledge_search: The phrase to search them with.
        lead_move: The lead Move's name, or anything else a model might
            write there; None for no Move.
        support_move: The supporting Move's name, the same way.
        next_move: The next Move's name, the same way.
        next_move_why: Why that Move comes next, or anything else a model
            might write there; None for no reason.
        send_photo: Whether a Shared Photo may be sent, or anything else a
            model might write there.
        ask_why: Whether to ask why; None leaves it out of the answer.
        where_we_are: One line on where the Conversation is now.
        read: Zeph's Read of what is really going on; "" for none.
        say_read: Whether the reply gives the Read now, or anything else a
            model might write there.
        check_in: The Check-in to weave in, e.g. {"kind": "A follow-up",
            "note": "..."}, or anything else a model might write there; None
            for none.
        patterns_used: The numbers of the Patterns in mind the Read is built
            on, or anything else a model might write there.
        offer_pattern: The number of the Pattern the reply offers, or
            anything else a model might write there; None for none.

    Returns:
        The form as JSON.
    """
    knowledge = (
        {"documents": list(knowledge_documents), "search": knowledge_search}
        if knowledge_documents
        else None
    )
    answer: dict[str, Any] = {
        "where_we_are": where_we_are,
        "read": read,
        "say_read": say_read,
        "need": need,
        "guidance": guidance,
        "lead_move": lead_move,
        "lead_move_why": None,
        "support_move": support_move,
        "support_move_why": None,
        "next_move": next_move,
        "next_move_why": next_move_why,
        "memory_categories": list(memory_categories),
        "threads_touched": list(threads_touched),
        "bring_up": list(bring_up),
        "left_alone": list(left_alone),
        "knowledge": knowledge,
        "send_photo": send_photo,
        "check_in": check_in,
        "patterns_used": list(patterns_used),
        "offer_pattern": offer_pattern,
    }
    if ask_why is not None:
        answer["ask_why"] = ask_why
    return json.dumps(answer)


DEFAULT_WHEN_IT_HELPS = "When someone wants a calm, steady practice."


class ScriptedChatModel:
    """Chat model that returns pre-written replies and records each call.

    Safeguard, memory processing, Understanding, Reply Plan, Life Thread keeping,
    Curiosity keeping, Move Outcome keeping, Portrait writing, Personal
    Sticker keeping, brought-up check and Knowledge "when it helps"
    drafting calls are told apart by their instructions and kept apart from
    reply calls, each with its own script. The Safeguard defaults to "none",
    the Understanding to `understanding_answer()`, the Reply Plan to
    `reply_plan_answer()`, Life Thread, Pattern, Curiosity and Move Outcome
    keeping to none kept, Portrait writing to an empty answer (no
    Portrait), the brought-up check to "no" and drafting to
    `DEFAULT_WHEN_IT_HELPS`, so tests about replies don't have to script
    them too. Set
    `before_next_reply` to run something once while the next reply is being
    "written", like a User acting during a slow model call, and
    `before_next_safeguard` likewise while the next text is being checked,
    `before_next_thread_keeping` while the next Life Threads are kept and
    `before_next_portrait` while the next Portrait is written.
    """

    def __init__(
        self,
        safeguard_prompt: str = "",
        memory_processing_prompt: str = "",
        understanding_prompt: str = "",
        reply_plan_prompt: str = "",
        sticker_keeping_prompt: str = "",
        thread_keeping_prompt: str = "",
        knowledge_when_it_helps_prompt: str = "",
        portrait_prompt: str = "",
        curiosity_keeping_prompt: str = "",
        move_outcome_keeping_prompt: str = "",
        pattern_keeping_prompt: str = "",
    ) -> None:
        """Start with no replies scripted, no calls and no delay.

        Args:
            safeguard_prompt: The instructions that mark a Safeguard call.
            memory_processing_prompt: The instructions that mark a
                post-conversation processing call.
            understanding_prompt: The instructions that mark an
                Understanding call.
            reply_plan_prompt: The prompt that ends a Reply Plan call's
                instructions, after the Outlook.
            sticker_keeping_prompt: The instructions that mark a Personal
                Sticker keeping call.
            thread_keeping_prompt: The instructions that mark a Life Thread
                keeping call.
            knowledge_when_it_helps_prompt: The instructions that mark a
                Knowledge "when it helps" drafting call.
            portrait_prompt: The instructions that mark a Portrait writing
                call.
            curiosity_keeping_prompt: The instructions that mark a Curiosity
                keeping call.
            move_outcome_keeping_prompt: The instructions that mark a Move
                Outcome keeping call.
            pattern_keeping_prompt: The instructions that mark a Pattern
                keeping call.
        """
        self._replies: list[str | Exception | ToolCall] = []
        self._safeguard_answers: list[str | Exception] = []
        self._processing_answers: list[str | Exception] = []
        self._understanding_answers: list[str | Exception] = []
        self._reply_plan_answers: list[str | Exception | ToolCall] = []
        self._sticker_keeping_answers: list[str | Exception] = []
        self._thread_keeping_answers: list[str | Exception] = []
        self._when_it_helps_answers: list[str | Exception] = []
        self._portrait_answers: list[str | Exception] = []
        self._curiosity_keeping_answers: list[str | Exception] = []
        self._brought_up_check_answers: list[str | Exception] = []
        self._move_outcome_keeping_answers: list[str | Exception] = []
        self._pattern_keeping_answers: list[str | Exception] = []
        self.safeguard_prompt = safeguard_prompt
        self.memory_processing_prompt = memory_processing_prompt
        self.understanding_prompt = understanding_prompt
        self.reply_plan_prompt = reply_plan_prompt
        self.sticker_keeping_prompt = sticker_keeping_prompt
        self.thread_keeping_prompt = thread_keeping_prompt
        self.knowledge_when_it_helps_prompt = knowledge_when_it_helps_prompt
        self.curiosity_keeping_prompt = curiosity_keeping_prompt
        self.portrait_prompt = portrait_prompt
        self.move_outcome_keeping_prompt = move_outcome_keeping_prompt
        self.pattern_keeping_prompt = pattern_keeping_prompt
        self.calls: list[ChatModelCall] = []
        self.safeguard_calls: list[ChatModelCall] = []
        self.processing_calls: list[ChatModelCall] = []
        self.understanding_calls: list[ChatModelCall] = []
        self.reply_plan_calls: list[ChatModelCall] = []
        self.sticker_keeping_calls: list[ChatModelCall] = []
        self.thread_keeping_calls: list[ChatModelCall] = []
        self.when_it_helps_calls: list[ChatModelCall] = []
        self.portrait_calls: list[ChatModelCall] = []
        self.curiosity_keeping_calls: list[ChatModelCall] = []
        self.brought_up_check_calls: list[ChatModelCall] = []
        self.move_outcome_keeping_calls: list[ChatModelCall] = []
        self.pattern_keeping_calls: list[ChatModelCall] = []
        self.call_order: list[str] = []
        self.delay_seconds = 0.0
        self.before_next_reply: Callable[[], None] | None = None
        self.before_next_safeguard: Callable[[], None] | None = None
        self.before_next_thread_keeping: Callable[[], None] | None = None
        self.before_next_portrait: Callable[[], None] | None = None

    def script(self, *replies: str | Exception | ToolCall) -> None:
        """Queue replies to return, one per call, in order.

        Args:
            replies: The reply texts; an exception is raised instead of
                returned, to act like a failing model. A tool call is run
                with the offered tool before the next reply is returned.
        """
        self._replies.extend(replies)

    def script_safeguard(self, *answers: str | Exception) -> None:
        """Queue Safeguard answers to return, one per Safeguard call.

        Args:
            answers: The risk labels; an exception is raised instead of
                returned, to act like a failing model.
        """
        self._safeguard_answers.extend(answers)

    def script_processing(self, *answers: str | Exception) -> None:
        """Queue post-conversation processing answers, one per call.

        Args:
            answers: The JSON answers; an exception is raised instead of
                returned, to act like a failing model.
        """
        self._processing_answers.extend(answers)

    def script_understanding(self, *answers: str | Exception) -> None:
        """Queue Understanding answers, one per call.

        Args:
            answers: The forms, e.g. from `understanding_answer()`; an
                exception is raised instead of returned, to act like a
                failing model.
        """
        self._understanding_answers.extend(answers)

    def script_reply_plan(self, *answers: str | Exception | ToolCall) -> None:
        """Queue Reply Plan answers, one per call.

        Args:
            answers: The forms, e.g. from `reply_plan_answer()`; an exception
                is raised instead of returned, to act like a failing model. A
                tool call is run with the offered tool before the next answer
                is returned.
        """
        self._reply_plan_answers.extend(answers)

    def script_thread_keeping(self, *answers: str | Exception) -> None:
        """Queue Life Thread keeping answers, one per call.

        Args:
            answers: The JSON answers; an exception is raised instead of
                returned, to act like a failing model.
        """
        self._thread_keeping_answers.extend(answers)

    def script_portrait(self, *answers: str | Exception) -> None:
        """Queue Portrait writing answers, one per call.

        Args:
            answers: The Portraits; an exception is raised instead of
                returned, to act like a failing model.
        """
        self._portrait_answers.extend(answers)

    def script_curiosity_keeping(self, *answers: str | Exception) -> None:
        """Queue Curiosity keeping answers, one per call.

        Args:
            answers: The JSON answers; an exception is raised instead of
                returned, to act like a failing model.
        """
        self._curiosity_keeping_answers.extend(answers)

    def script_move_outcome_keeping(self, *answers: str | Exception) -> None:
        """Queue Move Outcome keeping answers, one per call.

        Args:
            answers: The JSON answers; an exception is raised instead of
                returned, to act like a failing model.
        """
        self._move_outcome_keeping_answers.extend(answers)

    def script_pattern_keeping(self, *answers: str | Exception) -> None:
        """Queue Pattern keeping answers, one per call.

        Args:
            answers: The JSON answers; an exception is raised instead of
                returned, to act like a failing model.
        """
        self._pattern_keeping_answers.extend(answers)

    def script_brought_up_check(self, *answers: str | Exception) -> None:
        """Queue answers to whether a reply brought up its Check-in, one per call.

        Args:
            answers: "yes" or "no"; an exception is raised instead of
                returned, to act like a failing model.
        """
        self._brought_up_check_answers.extend(answers)

    def script_sticker_keeping(self, *answers: str | Exception) -> None:
        """Queue Personal Sticker keeping answers, one per call.

        Args:
            answers: The JSON answers; an exception is raised instead of
                returned, to act like a failing model.
        """
        self._sticker_keeping_answers.extend(answers)

    def script_when_it_helps(self, *answers: str | Exception) -> None:
        """Queue Knowledge "when it helps" drafts, one per drafting call.

        Args:
            answers: The drafts; an exception is raised instead of returned,
                to act like a failing model.
        """
        self._when_it_helps_answers.extend(answers)

    def generate(
        self,
        model: str,
        thinking: bool,
        instructions: str,
        history: list[ChatLine],
        tools: Sequence[ChatTool] = (),
    ) -> ModelAnswer:
        """Record the call and return the next scripted reply or answer.

        Args:
            model: The model name asked for.
            thinking: Whether the model was asked to think first.
            instructions: The instructions given.
            history: The Conversation so far.
            tools: The tools the model may call.

        Returns:
            The next scripted reply, or Safeguard answer for a Safeguard call,
            with the same token counts for every call.
        """
        call = ChatModelCall(
            model=model,
            thinking=thinking,
            instructions=instructions,
            history=history,
            tools=list(tools),
        )
        tool_calls: list[ToolCallRecord] = []
        if self.safeguard_prompt and instructions == self.safeguard_prompt:
            self.safeguard_calls.append(call)
            self.call_order.append("safeguard")
            if self.before_next_safeguard is not None:
                before_next, self.before_next_safeguard = (
                    self.before_next_safeguard,
                    None,
                )
                before_next()
            answer = (
                self._safeguard_answers.pop(0) if self._safeguard_answers else "none"
            )
        elif (
            self.curiosity_keeping_prompt
            and instructions == self.curiosity_keeping_prompt
        ):
            self.curiosity_keeping_calls.append(call)
            self.call_order.append("curiosity_keeping")
            answer = (
                self._curiosity_keeping_answers.pop(0)
                if self._curiosity_keeping_answers
                else json.dumps({"curiosities": []})
            )
        elif (
            self.move_outcome_keeping_prompt
            and instructions == self.move_outcome_keeping_prompt
        ):
            self.move_outcome_keeping_calls.append(call)
            self.call_order.append("move_outcome_keeping")
            answer = (
                self._move_outcome_keeping_answers.pop(0)
                if self._move_outcome_keeping_answers
                else json.dumps({"move_outcomes": []})
            )
        elif (
            self.pattern_keeping_prompt and instructions == self.pattern_keeping_prompt
        ):
            self.pattern_keeping_calls.append(call)
            self.call_order.append("pattern_keeping")
            answer = (
                self._pattern_keeping_answers.pop(0)
                if self._pattern_keeping_answers
                else json.dumps({"patterns": []})
            )
        elif (
            self.memory_processing_prompt
            and instructions == self.memory_processing_prompt
        ):
            self.processing_calls.append(call)
            self.call_order.append("processing")
            answer = self._processing_answers.pop(0)
        elif self.understanding_prompt and instructions == self.understanding_prompt:
            self.understanding_calls.append(call)
            self.call_order.append("understanding")
            answer = (
                self._understanding_answers.pop(0)
                if self._understanding_answers
                else understanding_answer()
            )
        elif self.reply_plan_prompt and instructions.endswith(self.reply_plan_prompt):
            self.reply_plan_calls.append(call)
            self.call_order.append("reply_plan")
            answer = (
                self._reply_plan_answers.pop(0)
                if self._reply_plan_answers
                else reply_plan_answer()
            )
            while isinstance(answer, ToolCall):
                [tool] = [tool for tool in tools if tool.name == answer.name]
                result = tool.run(answer.arguments)
                call.tool_results.append(result)
                tool_calls.append(ToolCallRecord(answer.name, answer.arguments, result))
                answer = self._reply_plan_answers.pop(0)
        elif self.thread_keeping_prompt and instructions == self.thread_keeping_prompt:
            self.thread_keeping_calls.append(call)
            self.call_order.append("thread_keeping")
            if self.before_next_thread_keeping is not None:
                before_next_thread_keeping = self.before_next_thread_keeping
                self.before_next_thread_keeping = None
                before_next_thread_keeping()
            answer = (
                self._thread_keeping_answers.pop(0)
                if self._thread_keeping_answers
                else json.dumps({"threads": []})
            )
        elif self.portrait_prompt and instructions == self.portrait_prompt:
            self.portrait_calls.append(call)
            self.call_order.append("portrait")
            if self.before_next_portrait is not None:
                before_next_portrait = self.before_next_portrait
                self.before_next_portrait = None
                before_next_portrait()
            answer = self._portrait_answers.pop(0) if self._portrait_answers else ""
        elif (
            self.sticker_keeping_prompt and instructions == self.sticker_keeping_prompt
        ):
            self.sticker_keeping_calls.append(call)
            self.call_order.append("sticker_keeping")
            answer = self._sticker_keeping_answers.pop(0)
        elif (
            self.knowledge_when_it_helps_prompt
            and instructions == self.knowledge_when_it_helps_prompt
        ):
            self.when_it_helps_calls.append(call)
            self.call_order.append("when_it_helps")
            answer = (
                self._when_it_helps_answers.pop(0)
                if self._when_it_helps_answers
                else DEFAULT_WHEN_IT_HELPS
            )
        elif instructions == BROUGHT_UP_CHECK_PROMPT:
            self.brought_up_check_calls.append(call)
            self.call_order.append("brought_up_check")
            answer = (
                self._brought_up_check_answers.pop(0)
                if self._brought_up_check_answers
                else "no"
            )
        else:
            self.calls.append(call)
            self.call_order.append("reply")
            time.sleep(self.delay_seconds)
            if self.before_next_reply is not None:
                before_next_reply, self.before_next_reply = self.before_next_reply, None
                before_next_reply()
            answer = self._replies.pop(0)
            while isinstance(answer, ToolCall):
                [tool] = [tool for tool in tools if tool.name == answer.name]
                result = tool.run(answer.arguments)
                call.tool_results.append(result)
                tool_calls.append(ToolCallRecord(answer.name, answer.arguments, result))
                answer = self._replies.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return ModelAnswer(
            text=answer,
            tokens_in=TOKENS_IN_PER_CALL,
            tokens_out=TOKENS_OUT_PER_CALL,
            tool_calls=tuple(tool_calls),
        )


@dataclass(frozen=True)
class PhotoViewerCall:
    """One look the fake photo viewer was asked for.

    Attributes:
        model: The model name asked for.
        thinking: Whether the model was asked to think first.
        instructions: The instructions given.
        photo: The photo it was shown.
    """

    model: str
    thinking: bool
    instructions: str
    photo: PhotoImage


class FakePhotoViewer:
    """Photo viewer that returns scripted descriptions and records each look.

    With nothing scripted it describes every photo as `DEFAULT_DESCRIPTION`.
    """

    DEFAULT_DESCRIPTION = "A photo of a mug of tea on a wooden table."

    def __init__(self) -> None:
        """Start with nothing scripted and no looks."""
        self._answers: list[str | Exception] = []
        self.calls: list[PhotoViewerCall] = []

    def script(self, *answers: str | Exception) -> None:
        """Queue answers to return, one per look, in order.

        Args:
            answers: The descriptions; an exception is raised instead of
                returned, to act like a failing model.
        """
        self._answers.extend(answers)

    def look(
        self, model: str, thinking: bool, instructions: str, photo: PhotoImage
    ) -> ModelAnswer:
        """Record the look and return the next scripted description.

        Args:
            model: The model name asked for.
            thinking: Whether the model was asked to think first.
            instructions: The instructions given.
            photo: The photo to look at.

        Returns:
            The description, with the same token counts for every look.

        Raises:
            Exception: The next scripted exception, if that is what's queued.
        """
        self.calls.append(PhotoViewerCall(model, thinking, instructions, photo))
        answer = self._answers.pop(0) if self._answers else self.DEFAULT_DESCRIPTION
        if isinstance(answer, Exception):
            raise answer
        return ModelAnswer(
            text=answer, tokens_in=PHOTO_TOKENS_IN, tokens_out=PHOTO_TOKENS_OUT
        )


class FakeEmbedder:
    """Embedder that turns the words in a text into a fixed-size vector.

    Each word longer than three letters adds to one slot, so texts sharing
    words are close and texts with none in common are far apart. Set
    `failure` to make every call raise it, like a broken model.
    """

    def __init__(self) -> None:
        """Start working, with no calls."""
        self.failure: Exception | None = None
        self.queries: list[str] = []

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        """Embed each text.

        Args:
            texts: The texts.

        Returns:
            One vector per text.
        """
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        """Record and embed a search message.

        Args:
            text: The message.

        Returns:
            Its vector.
        """
        self.queries.append(text)
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        """Count the text's longer words into slots and scale to length one.

        Args:
            text: The text.

        Returns:
            Its vector; never all zeros.

        Raises:
            Exception: The `failure` set on the fake, if any.
        """
        if self.failure is not None:
            raise self.failure
        vector = [0.0] * EMBEDDING_SIZE
        vector[0] = 0.01
        for word in re.findall(r"[a-z]{4,}", text.lower()):
            slot = int(hashlib.sha256(word.encode()).hexdigest(), 16) % EMBEDDING_SIZE
            vector[slot] += 1.0
        length = math.sqrt(sum(value * value for value in vector))
        return [value / length for value in vector]


class FakeWebSearch:
    """Web search that returns set results and pages, recording each request.

    Set `failure` to make every call raise it, like a broken service.
    """

    def __init__(self) -> None:
        """Start with no results, no pages and no requests."""
        self.results: list[WebSearchResult] = []
        self.pages: dict[str, str] = {}
        self.failure: Exception | None = None
        self.queries: list[str] = []
        self.fetched_urls: list[str] = []

    def search(self, query: str) -> list[WebSearchResult]:
        """Record the query and return the set results.

        Args:
            query: What to search for.

        Returns:
            The set results.

        Raises:
            Exception: The `failure` set on the fake, if any.
        """
        self.queries.append(query)
        if self.failure is not None:
            raise self.failure
        return self.results

    def fetch_page(self, url: str) -> str:
        """Record the address and return the set page text.

        Args:
            url: The page's address.

        Returns:
            The page's text, or "" if none was set.

        Raises:
            Exception: The `failure` set on the fake, if any.
        """
        self.fetched_urls.append(url)
        if self.failure is not None:
            raise self.failure
        return self.pages.get(url, "")
