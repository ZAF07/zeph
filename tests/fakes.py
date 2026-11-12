import hashlib
import math
import re
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from companion.adapters.postgres.tables import EMBEDDING_SIZE
from companion.core.models import AccountIdentity, ChatLine, WebSearchResult
from companion.core.ports import ChatTool


@dataclass(frozen=True)
class SentText:
    """A text message the fake chat channel was asked to send."""

    chat_id: int
    text: str


class FakeChatChannel:
    """Chat channel that records sent messages instead of sending them.

    `events` lists texts and typing in the order they happened.
    """

    def __init__(self) -> None:
        """Start with nothing sent."""
        self.sent: list[SentText] = []
        self.typing_shown_in: list[int] = []
        self.events: list[str] = []

    def send_text(self, chat_id: int, text: str) -> None:
        """Record a text message.

        Args:
            chat_id: The chat the message is for.
            text: The message text.
        """
        self.sent.append(SentText(chat_id=chat_id, text=text))
        self.events.append(f"text: {text}")

    def show_typing(self, chat_id: int) -> None:
        """Record that typing was shown.

        Args:
            chat_id: The chat it was shown in.
        """
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
    """Auth verifier that accepts tokens handed out by `token_for`."""

    def __init__(self) -> None:
        """Start with no known tokens."""
        self._identities_by_token: dict[str, AccountIdentity] = {}

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
        instructions: The instructions given.
        history: The Conversation so far.
        tools: The tools the model was offered.
        tool_results: What each scripted tool call returned, in order.
    """

    model: str
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


class ScriptedChatModel:
    """Chat model that returns pre-written replies and records each call.

    Safeguard, memory processing and memory retrieval calls are told apart
    by their instructions and kept apart from reply calls, each with its own
    script. The Safeguard defaults to "none" and retrieval to "none", so
    tests about replies don't have to script them too.
    """

    def __init__(
        self,
        safeguard_prompt: str = "",
        memory_processing_prompt: str = "",
        memory_retrieval_prompt: str = "",
    ) -> None:
        """Start with no replies scripted, no calls and no delay.

        Args:
            safeguard_prompt: The instructions that mark a Safeguard call.
            memory_processing_prompt: The instructions that mark a
                post-conversation processing call.
            memory_retrieval_prompt: The instructions that mark a memory
                retrieval call.
        """
        self._replies: list[str | Exception | ToolCall] = []
        self._safeguard_answers: list[str | Exception] = []
        self._processing_answers: list[str | Exception] = []
        self._retrieval_answers: list[str | Exception] = []
        self.safeguard_prompt = safeguard_prompt
        self.memory_processing_prompt = memory_processing_prompt
        self.memory_retrieval_prompt = memory_retrieval_prompt
        self.calls: list[ChatModelCall] = []
        self.safeguard_calls: list[ChatModelCall] = []
        self.processing_calls: list[ChatModelCall] = []
        self.retrieval_calls: list[ChatModelCall] = []
        self.call_order: list[str] = []
        self.delay_seconds = 0.0

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

    def script_retrieval(self, *answers: str | Exception) -> None:
        """Queue memory retrieval answers, one per call.

        Args:
            answers: The picked category names; an exception is raised
                instead of returned, to act like a failing model.
        """
        self._retrieval_answers.extend(answers)

    def generate(
        self,
        model: str,
        instructions: str,
        history: list[ChatLine],
        tools: Sequence[ChatTool] = (),
    ) -> str:
        """Record the call and return the next scripted reply or answer.

        Args:
            model: The model name asked for.
            instructions: The instructions given.
            history: The Conversation so far.
            tools: The tools the model may call.

        Returns:
            The next scripted reply, or Safeguard answer for a Safeguard call.
        """
        call = ChatModelCall(
            model=model, instructions=instructions, history=history, tools=list(tools)
        )
        if self.safeguard_prompt and instructions == self.safeguard_prompt:
            self.safeguard_calls.append(call)
            self.call_order.append("safeguard")
            answer = (
                self._safeguard_answers.pop(0) if self._safeguard_answers else "none"
            )
        elif (
            self.memory_processing_prompt
            and instructions == self.memory_processing_prompt
        ):
            self.processing_calls.append(call)
            self.call_order.append("processing")
            answer = self._processing_answers.pop(0)
        elif (
            self.memory_retrieval_prompt
            and instructions == self.memory_retrieval_prompt
        ):
            self.retrieval_calls.append(call)
            self.call_order.append("retrieval")
            answer = (
                self._retrieval_answers.pop(0) if self._retrieval_answers else "none"
            )
        else:
            self.calls.append(call)
            self.call_order.append("reply")
            time.sleep(self.delay_seconds)
            answer = self._replies.pop(0)
            while isinstance(answer, ToolCall):
                [tool] = [tool for tool in tools if tool.name == answer.name]
                call.tool_results.append(tool.run(answer.arguments))
                answer = self._replies.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


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
