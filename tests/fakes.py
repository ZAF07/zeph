from dataclasses import dataclass
from datetime import datetime, timedelta

from companion.core.models import AccountIdentity, ChatLine


@dataclass(frozen=True)
class SentText:
    """A text message the fake chat channel was asked to send."""

    chat_id: int
    text: str


class FakeChatChannel:
    """Chat channel that records sent messages instead of sending them."""

    def __init__(self) -> None:
        """Start with no sent messages."""
        self.sent: list[SentText] = []
        self.batches: list[list[str]] = []
        self.typing_shown_in: list[int] = []

    def send_text(self, chat_id: int, text: str) -> None:
        """Record a text message.

        Args:
            chat_id: The chat the message is for.
            text: The message text.
        """
        self.sent.append(SentText(chat_id=chat_id, text=text))

    def send_texts(self, chat_id: int, texts: list[str]) -> None:
        """Record several messages sent in a row as one batch.

        Args:
            chat_id: The chat the messages are for.
            texts: The message texts.
        """
        self.batches.append(list(texts))
        for text in texts:
            self.sent.append(SentText(chat_id=chat_id, text=text))

    def show_typing(self, chat_id: int) -> None:
        """Record that typing was shown.

        Args:
            chat_id: The chat it was shown in.
        """
        self.typing_shown_in.append(chat_id)

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
    """Clock that only moves when told to."""

    def __init__(self, start: datetime) -> None:
        """Set the starting time.

        Args:
            start: The time the clock starts at.
        """
        self._now = start

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


@dataclass(frozen=True)
class ChatModelCall:
    """One call the scripted chat model received."""

    model: str
    instructions: str
    history: list[ChatLine]


class ScriptedChatModel:
    """Chat model that returns pre-written replies and records each call."""

    def __init__(self) -> None:
        """Start with no replies scripted and no calls."""
        self._replies: list[str] = []
        self.calls: list[ChatModelCall] = []

    def script(self, *replies: str) -> None:
        """Queue replies to return, one per call, in order.

        Args:
            replies: The reply texts.
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
        return self._replies.pop(0)
