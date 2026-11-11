from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from companion.core.models import (
    AccountIdentity,
    ChatLine,
    ConnectionToken,
    Conversation,
    ConversationMessage,
    ConversationTurn,
    TelegramConnection,
    User,
)


class Clock(Protocol):
    """Tells the current time."""

    def now(self) -> datetime:
        """Return the current time.

        Returns:
            The current time, timezone-aware in UTC.
        """
        ...

    def sleep(self, seconds: float) -> None:
        """Wait before carrying on.

        Args:
            seconds: How long to wait.
        """
        ...


class ChatChannel(Protocol):
    """Sends messages to people on the chat channel (Telegram for the MVP)."""

    def send_text(self, chat_id: int, text: str) -> None:
        """Send one text message.

        Args:
            chat_id: The chat to send to.
            text: The message text.
        """
        ...

    def show_typing(self, chat_id: int) -> None:
        """Show that the Companion is typing.

        Args:
            chat_id: The chat to show it in.
        """
        ...


class ChatModel(Protocol):
    """Generates the Companion's words with a large language model."""

    def generate(self, model: str, instructions: str, history: list[ChatLine]) -> str:
        """Generate the next reply.

        Args:
            model: The model to use, e.g. "deepseek-chat".
            instructions: What the model should be and do (Persona and prompt).
            history: The Conversation so far, oldest first.

        Returns:
            The reply text.
        """
        ...


class ConversationEngine(Protocol):
    """Runs the steps of answering a connected User's message."""

    def handle(self, turn: ConversationTurn) -> None:
        """Answer one message: save it, compose a reply and send it.

        Args:
            turn: The message to answer.
        """
        ...


class AuthVerifier(Protocol):
    """Turns a Dashboard request token into an account identity."""

    def verify(self, token: str) -> AccountIdentity | None:
        """Check a bearer token.

        Args:
            token: The bearer token from the request.

        Returns:
            The account identity, or None if the token is not valid.
        """
        ...


class UserRepository(Protocol):
    """Stores Users."""

    def get_by_auth_id(self, auth_id: str) -> User | None:
        """Find a User by the auth provider's account ID.

        Args:
            auth_id: The auth provider's account ID.

        Returns:
            The User, or None if there is none.
        """
        ...

    def add(self, user: User) -> User:
        """Save a new User, or return the existing one with the same auth ID.

        Args:
            user: The User to save.

        Returns:
            The saved User.
        """
        ...


class TelegramConnectionRepository(Protocol):
    """Stores Telegram Connections."""

    def get_by_user(self, user_id: UUID) -> TelegramConnection | None:
        """Find a User's Telegram Connection.

        Args:
            user_id: The User's ID.

        Returns:
            The connection, or None if the User has none.
        """
        ...

    def get_by_telegram_user(self, telegram_user_id: int) -> TelegramConnection | None:
        """Find the Telegram Connection for a Telegram account.

        Args:
            telegram_user_id: The Telegram account's ID.

        Returns:
            The connection, or None if the account is not connected.
        """
        ...

    def save(self, connection: TelegramConnection) -> None:
        """Save a User's Telegram Connection, replacing any they had.

        Args:
            connection: The connection to save.
        """
        ...


class ConnectionTokenRepository(Protocol):
    """Stores connection tokens."""

    def add(self, token: ConnectionToken) -> None:
        """Save a new connection token.

        Args:
            token: The token to save.
        """
        ...

    def get(self, token: str) -> ConnectionToken | None:
        """Find a connection token by its code.

        Args:
            token: The code.

        Returns:
            The token, or None if there is none.
        """
        ...

    def get_latest_for_user(self, user_id: UUID) -> ConnectionToken | None:
        """Find the newest connection token a User asked for.

        Args:
            user_id: The User's ID.

        Returns:
            The newest token, or None if the User has never asked for one.
        """
        ...

    def claim(self, token: str, used_at: datetime) -> bool:
        """Mark a token used, in one step, only if it is still active.

        Args:
            token: The code.
            used_at: When it is being used.

        Returns:
            True if this call claimed the token; False if it was already used,
            refused or expired, so two requests can never both use one token.
        """
        ...

    def mark_rejected(self, token: str, rejected_at: datetime) -> None:
        """Record that a token was refused because the Telegram account is taken.

        Args:
            token: The code.
            rejected_at: When it was refused.
        """
        ...


class ConversationRepository(Protocol):
    """Stores Conversations and their messages."""

    def get_latest_for_user(self, user_id: UUID) -> Conversation | None:
        """Find a User's newest Conversation.

        Args:
            user_id: The User's ID.

        Returns:
            The newest Conversation, or None if the User has never had one.
        """
        ...

    def add(self, conversation: Conversation) -> None:
        """Save a new Conversation.

        Args:
            conversation: The Conversation to save.
        """
        ...

    def add_message(self, message: ConversationMessage) -> None:
        """Save a message and make it the Conversation's newest message.

        Args:
            message: The message to save.
        """
        ...

    def list_messages(self, conversation_id: UUID) -> list[ConversationMessage]:
        """List a Conversation's messages, oldest first.

        Args:
            conversation_id: The Conversation's ID.

        Returns:
            The messages.
        """
        ...


class PlatformSettingsRepository(Protocol):
    """Reads admin-managed platform settings and content."""

    def get(self, key: str) -> Any:
        """Read one setting.

        Args:
            key: The setting's key.

        Returns:
            The setting's value.

        Raises:
            KeyError: If the setting does not exist.
        """
        ...


@dataclass(frozen=True)
class Repositories:
    """Every repository the core needs, so adapters can be swapped as one."""

    users: UserRepository
    telegram_connections: TelegramConnectionRepository
    connection_tokens: ConnectionTokenRepository
    conversations: ConversationRepository
    platform_settings: PlatformSettingsRepository
