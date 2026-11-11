from dataclasses import dataclass
from datetime import datetime, timedelta

from companion.core.models import AccountIdentity


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

    def send_text(self, chat_id: int, text: str) -> None:
        """Record a text message.

        Args:
            chat_id: The chat the message is for.
            text: The message text.
        """
        self.sent.append(SentText(chat_id=chat_id, text=text))

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
