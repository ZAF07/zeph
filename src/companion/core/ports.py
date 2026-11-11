from collections.abc import Callable, Mapping, Sequence
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
    ConversationSummary,
    ConversationTurn,
    Helpline,
    HelplineDetails,
    MemoryCategory,
    MemoryChanges,
    MemoryItem,
    RiskType,
    SafeguardEvent,
    SafeguardEventOverview,
    StoredSetting,
    TelegramConnection,
    User,
    UserOverview,
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


class Scheduler(Protocol):
    """Runs due work over and over, a tick at a time, while the backend is up."""

    def start(self, tick: Callable[[], None]) -> None:
        """Start running the tick every so often.

        Args:
            tick: The work to run on each tick.
        """
        ...

    def stop(self) -> None:
        """Stop running ticks."""
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
        """Answer one message: save it, check it with the Safeguard, then reply.

        On a crisis the Crisis Reply is sent and no reply is composed;
        otherwise the reply is given the User Memory that matters.

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

    def get(self, user_id: UUID) -> User | None:
        """Find a User by our ID.

        Args:
            user_id: The User's ID.

        Returns:
            The User, or None if there is none.
        """
        ...

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

    def update(self, user: User) -> User:
        """Save changes to an existing User's profile and preferences.

        Args:
            user: The User with their new values.

        Returns:
            The saved User.
        """
        ...

    def list_overviews(self) -> list[UserOverview]:
        """List every User with their activity counts, newest sign-up first.

        Returns:
            One overview per User.
        """
        ...

    def count_admins(self) -> int:
        """Count the Users who are Admins.

        Returns:
            How many Admins there are.
        """
        ...

    def promote_to_admin(self, user_id: UUID) -> User:
        """Make a User an Admin.

        Args:
            user_id: The User's ID.

        Returns:
            The saved User.
        """
        ...

    def demote_unless_last_admin(self, user_id: UUID) -> User | None:
        """Make an Admin a plain User, in one step, unless they are the only one.

        Two Admins demoting each other at the same time can never leave the
        platform without an Admin.

        Args:
            user_id: The Admin's ID.

        Returns:
            The saved User, or None if they are the last Admin.
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

    def end_quiet(self, quiet_since: datetime, ended_at: datetime) -> None:
        """End every open Conversation with no message since a given time.

        Args:
            quiet_since: Conversations whose newest message is at or before
                this time are ended.
            ended_at: When they are being ended.
        """
        ...

    def list_ended_unprocessed(self) -> list[Conversation]:
        """List ended Conversations not yet processed, oldest first.

        Returns:
            The Conversations.
        """
        ...


class MemoryCategoryRepository(Protocol):
    """Stores Memory Categories."""

    def list_all(self) -> list[MemoryCategory]:
        """List every Memory Category, archived ones included, in sort order.

        Returns:
            The categories.
        """
        ...


class UserMemoryRepository(Protocol):
    """Stores each User's Memory Items and Conversation Summaries."""

    def list_items(self, user_id: UUID) -> list[MemoryItem]:
        """List a User's Memory Items in the order they were saved.

        Args:
            user_id: The User's ID.

        Returns:
            The Memory Items.
        """
        ...

    def delete_item(self, user_id: UUID, item_id: UUID) -> bool:
        """Delete one of a User's Memory Items.

        Args:
            user_id: The User's ID.
            item_id: The Memory Item's ID.

        Returns:
            True if it was deleted; False if the User has no such item.
        """
        ...

    def delete_all_items(self, user_id: UUID) -> None:
        """Delete every one of a User's Memory Items.

        Args:
            user_id: The User's ID.
        """
        ...

    def replace_onboarding_items(self, user_id: UUID, items: list[MemoryItem]) -> None:
        """Swap the User's Memory Items from onboarding for new ones, in one step.

        Args:
            user_id: The User's ID.
            items: The new Memory Items from onboarding.
        """
        ...

    def list_summaries(
        self, user_id: UUID, limit: int | None = None
    ) -> list[ConversationSummary]:
        """List a User's Conversation Summaries, newest first.

        Args:
            user_id: The User's ID.
            limit: The most to return; None for all of them.

        Returns:
            The Conversation Summaries.
        """
        ...

    def delete_summary(self, user_id: UUID, summary_id: UUID) -> bool:
        """Delete one of a User's Conversation Summaries.

        Args:
            user_id: The User's ID.
            summary_id: The Conversation Summary's ID.

        Returns:
            True if it was deleted; False if the User has no such summary.
        """
        ...

    def save_processed_conversation(
        self,
        conversation_id: UUID,
        processed_at: datetime,
        summary: ConversationSummary | None,
        changes: MemoryChanges,
    ) -> None:
        """Save what processing an ended Conversation produced, in one step.

        The Conversation is marked processed at the same time, so it is
        never processed twice.

        Args:
            conversation_id: The Conversation that was processed.
            processed_at: When processing finished.
            summary: Its Conversation Summary; None when nothing is saved.
            changes: The changes to the User's Memory Items.
        """
        ...


class PlatformSettingsRepository(Protocol):
    """Stores admin-managed platform settings and content."""

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

    def get_many(self, keys: Sequence[str]) -> list[StoredSetting]:
        """Read several settings with when and by whom they were last saved.

        Args:
            keys: The settings' keys.

        Returns:
            The settings that exist, in the order of `keys`.
        """
        ...

    def save_many(
        self, values: Mapping[str, Any], updated_at: datetime, updated_by: UUID
    ) -> None:
        """Save new values for several settings in one step.

        Args:
            values: The new value for each setting key.
            updated_at: When they are being saved.
            updated_by: The Admin saving them.
        """
        ...


class HelplineRepository(Protocol):
    """Stores Helplines per country and the one international fallback."""

    def list_countries(self) -> list[Helpline]:
        """List every country's Helplines, by country and then sort order.

        Returns:
            The Helplines, without the international fallback.
        """
        ...

    def list_for_country(self, country: str) -> list[Helpline]:
        """List one country's Helplines in sort order.

        Args:
            country: Two-letter country code.

        Returns:
            The Helplines; empty if the country has none.
        """
        ...

    def get(self, helpline_id: UUID) -> Helpline | None:
        """Find a Helpline, the international fallback included.

        Args:
            helpline_id: The Helpline's ID.

        Returns:
            The Helpline, or None if there is none.
        """
        ...

    def get_international_fallback(self) -> Helpline:
        """Read the international fallback.

        Returns:
            The international fallback.
        """
        ...

    def add(self, country: str, details: HelplineDetails) -> Helpline:
        """Save a new Helpline last in its country's list.

        Args:
            country: Two-letter country code.
            details: Its name, number and hours.

        Returns:
            The saved Helpline.
        """
        ...

    def update(
        self, helpline_id: UUID, country: str | None, details: HelplineDetails
    ) -> Helpline:
        """Change a Helpline; one moved to another country goes last there.

        Args:
            helpline_id: The Helpline's ID.
            country: Its country; None only for the international fallback.
            details: Its new name, number and hours.

        Returns:
            The saved Helpline.
        """
        ...

    def delete(self, helpline_id: UUID) -> None:
        """Remove a Helpline.

        Args:
            helpline_id: The Helpline's ID.
        """
        ...

    def set_sort_orders(self, sort_orders: Mapping[UUID, int]) -> None:
        """Save new sort orders for several Helplines in one step.

        Args:
            sort_orders: The new sort order for each Helpline ID.
        """
        ...


class SafeguardEventRepository(Protocol):
    """Stores Safeguard Events."""

    def add(self, event: SafeguardEvent) -> None:
        """Save a Safeguard Event.

        Args:
            event: The event to save.
        """
        ...

    def list_overviews(
        self, since: datetime | None, risk_type: RiskType | None
    ) -> list[SafeguardEventOverview]:
        """List Safeguard Events with who the User is, newest first.

        Args:
            since: Only events at or after this time; None for all time.
            risk_type: Only events of this risk type; None for every type.

        Returns:
            The events.
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
    helplines: HelplineRepository
    safeguard_events: SafeguardEventRepository
    memory_categories: MemoryCategoryRepository
    user_memory: UserMemoryRepository
