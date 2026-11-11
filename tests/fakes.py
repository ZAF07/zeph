import time
from dataclasses import dataclass
from datetime import datetime, timedelta

from companion.core.models import AccountIdentity, ChatLine


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
    """

    model: str
    instructions: str
    history: list[ChatLine]


class ScriptedChatModel:
    """Chat model that returns pre-written replies and records each call."""

    def __init__(self) -> None:
        """Start with no replies scripted, no calls and no delay."""
        self._replies: list[str | Exception] = []
        self.calls: list[ChatModelCall] = []
        self.delay_seconds = 0.0

    def script(self, *replies: str | Exception) -> None:
        """Queue replies to return, one per call, in order.

        Args:
            replies: The reply texts; an exception is raised instead of
                returned, to act like a failing model.
        """
        self._replies.extend(replies)

    def generate(self, model: str, instructions: str, history: list[ChatLine]) -> str:
        """Record the call and return the next scripted reply.

        Args:
            model: The model name asked for.
            instructions: The instructions given.
            history: The Conversation so far.

        Returns:
            The next scripted reply.
        """
        self.calls.append(
            ChatModelCall(model=model, instructions=instructions, history=history)
        )
        time.sleep(self.delay_seconds)
        reply = self._replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply
