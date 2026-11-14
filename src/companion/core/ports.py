from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Protocol
from uuid import UUID

from companion.core.models import (
    AccountIdentity,
    ChannelSticker,
    ChatLine,
    CheckIn,
    CheckInKind,
    CheckInKindDetails,
    CheckInKindOverview,
    CheckInLogEntry,
    ConnectionToken,
    Conversation,
    ConversationMessage,
    ConversationSummary,
    DailyUsage,
    EmbeddedChunk,
    Feature,
    FeatureSwitch,
    Helpline,
    HelplineDetails,
    KnowledgeChunkMatch,
    KnowledgeDetailsChange,
    KnowledgeDocument,
    KnowledgeFile,
    KnowledgeFileType,
    KnowledgeStatus,
    KnowledgeUpload,
    LibrarySticker,
    MemoryCategory,
    MemoryCategoryDetails,
    MemoryCategoryOverview,
    MemoryChanges,
    MemoryItem,
    ModelAnswer,
    ModelCall,
    ModelCallTraceDetails,
    ModelCallTraceOverview,
    ModelStep,
    Need,
    NextDueTimeChange,
    PersonalSticker,
    PhotoImage,
    PlatformSettings,
    RiskType,
    SafeguardEvent,
    SafeguardEventOverview,
    SharedPhoto,
    StickerImage,
    StoredSetting,
    TelegramConnection,
    Understanding,
    User,
    UserOverview,
    WebSearchResult,
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


class Timer(Protocol):
    """Runs work once after a wait, in the background."""

    def start(self, key: str, seconds: float, work: Callable[[], None]) -> None:
        """Run work after a wait; starting the same key again restarts its wait.

        Args:
            key: Names the wait, so a later start can restart it.
            seconds: How long to wait.
            work: What to run when the wait ends.
        """
        ...


class MessageRefusedError(Exception):
    """Raised when the chat channel clearly refused a message, so it never arrived."""


class ChatBlockedError(Exception):
    """Raised when the chat channel can't reach the person, e.g. they blocked us."""


class ChatChannel(Protocol):
    """Sends messages to people on the chat channel (Telegram for the MVP)."""

    def send_text(self, chat_id: int, text: str) -> None:
        """Send one text message.

        Args:
            chat_id: The chat to send to.
            text: The message text.

        Raises:
            ChatBlockedError: If it can't reach the person, e.g. they blocked us.
            MessageRefusedError: If the chat channel clearly refused it.
            Exception: Any other failure, such as a timeout; the message may
                or may not have arrived.
        """
        ...

    def show_typing(self, chat_id: int) -> None:
        """Show that the Companion is typing.

        Args:
            chat_id: The chat to show it in.
        """
        ...

    def send_sticker(self, chat_id: int, file_id: str) -> None:
        """Send one sticker.

        Args:
            chat_id: The chat to send to.
            file_id: The sticker's file ID.
        """
        ...

    def react(self, chat_id: int, message_id: int, emoji: str) -> None:
        """Put an emoji reaction on a message someone sent.

        Args:
            chat_id: The chat the message is in.
            message_id: The message's ID.
            emoji: The reaction.
        """
        ...

    def send_photo(self, chat_id: int, file_id: str) -> None:
        """Send one photo the chat channel already has, by its file ID.

        Args:
            chat_id: The chat to send to.
            file_id: The photo's file ID.

        Raises:
            Exception: If the chat channel refuses the photo.
        """
        ...

    def get_sticker_set(self, name: str) -> list[ChannelSticker] | None:
        """Look up every sticker in a sticker set.

        Args:
            name: The set's name.

        Returns:
            Its stickers in order, or None if there is no such set.
        """
        ...

    def get_sticker_image(self, file_id: str) -> StickerImage | None:
        """Download an image of a sticker.

        Args:
            file_id: The image's file ID.

        Returns:
            The image, or None if it isn't one a browser can show.
        """
        ...

    def download_photo(self, file_id: str) -> PhotoImage:
        """Download a photo someone sent.

        Args:
            file_id: The photo's file ID.

        Returns:
            The photo's image.

        Raises:
            Exception: If it can't be downloaded or isn't a JPEG, PNG or WebP
                image.
        """
        ...


@dataclass(frozen=True)
class ChatTool:
    """A tool the chat model may call while writing a reply.

    Attributes:
        name: The tool's name, e.g. "web_search".
        description: When and how to use it, as the model is told.
        parameters: JSON Schema of the arguments it takes.
        run: Runs the tool with the model's arguments and returns what the
            model is told back; it never raises.
    """

    name: str
    description: str
    parameters: dict[str, Any]
    run: Callable[[dict[str, Any]], str]


class ChatModel(Protocol):
    """Generates the Companion's words with a large language model."""

    def generate(
        self,
        model: str,
        instructions: str,
        history: list[ChatLine],
        tools: Sequence[ChatTool] = (),
    ) -> ModelAnswer:
        """Generate the next reply, calling tools first if the model wants to.

        Args:
            model: The model to use, e.g. "deepseek-chat".
            instructions: What the model should be and do (Persona and prompt).
            history: The Conversation so far, oldest first.
            tools: The tools the model may call; none by default.

        Returns:
            The reply text and the tokens it took.
        """
        ...


class PhotoViewer(Protocol):
    """Looks at a photo with a model that can see images."""

    def look(self, model: str, instructions: str, photo: PhotoImage) -> ModelAnswer:
        """Look at a photo and write what the instructions ask for.

        Args:
            model: The model to use, e.g. "deepseek-chat".
            instructions: What to write about the photo.
            photo: The photo's image.

        Returns:
            The text and the tokens it took.

        Raises:
            Exception: If the model can't be reached or fails.
        """
        ...


class WebSearch(Protocol):
    """Searches the web and reads web pages."""

    def search(self, query: str) -> list[WebSearchResult]:
        """Search the web.

        Args:
            query: What to search for.

        Returns:
            The best results, best first.
        """
        ...

    def fetch_page(self, url: str) -> str:
        """Read the text of a web page.

        Args:
            url: The page's address.

        Returns:
            The page's text, or "" if it could not be read.
        """
        ...


class TextExtractionError(Exception):
    """Raised when no text can be read from a Knowledge document's file.

    The message says why, in words fit to show Admins.
    """


class DocumentTextExtractor(Protocol):
    """Reads the text out of an uploaded Knowledge document's file."""

    def extract(self, file_type: KnowledgeFileType, content: bytes) -> str:
        """Read a file's text.

        Args:
            file_type: What kind of file it is.
            content: The file's bytes.

        Returns:
            The text, which may be blank if the file has none.

        Raises:
            TextExtractionError: If the file can't be read.
        """
        ...


class Embedder(Protocol):
    """Turns text into embeddings, so similar texts can be found."""

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        """Embed pieces of Knowledge to be searched later.

        Args:
            texts: The pieces' texts.

        Returns:
            One embedding per text, in the same order.
        """
        ...

    def embed_query(self, text: str) -> list[float]:
        """Embed a message to search Knowledge with.

        Args:
            text: The message.

        Returns:
            Its embedding.
        """
        ...


class KnowledgeVectorStore(Protocol):
    """Stores Knowledge chunk embeddings and finds the closest ones."""

    def replace_chunks(self, document_id: UUID, chunks: list[EmbeddedChunk]) -> None:
        """Save a document's chunks in place of any it had, in one step.

        Args:
            document_id: The document the chunks are from.
            chunks: The chunks, in reading order.
        """
        ...

    def delete_chunks(self, document_id: UUID) -> None:
        """Remove every chunk of a document.

        Args:
            document_id: The document.
        """
        ...

    def search(self, embedding: list[float], limit: int) -> list[KnowledgeChunkMatch]:
        """Find the chunks closest to an embedding.

        Args:
            embedding: What to search with.
            limit: The most chunks to return.

        Returns:
            The closest chunks, best match first.
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


class AuthAccounts(Protocol):
    """Manages accounts at the auth provider."""

    def delete_account(self, auth_id: str) -> None:
        """Delete an account at the auth provider, so it can't sign in again.

        Args:
            auth_id: The auth provider's account ID.
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

    def get_many(self, user_ids: Sequence[UUID]) -> list[User]:
        """Find many Users by our IDs, in one query.

        Args:
            user_ids: The Users' IDs.

        Returns:
            The Users found, in the order of the IDs given.
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

    def demote_to_user(self, user_id: UUID) -> User:
        """Make an Admin a plain User.

        Args:
            user_id: The Admin's ID.

        Returns:
            The saved User.
        """
        ...

    def delete(self, user_id: UUID) -> bool:
        """Delete a User: their profile and settings.

        Args:
            user_id: The User's ID.

        Returns:
            True if they were deleted; False if there was no such User.
        """
        ...


class PendingAuthAccountDeletionRepository(Protocol):
    """Stores the auth provider accounts still to delete, by auth ID only."""

    def add(self, auth_id: str, added_at: datetime) -> None:
        """Note an auth provider account as still to delete.

        Adding one already on the list changes nothing.

        Args:
            auth_id: The auth provider's account ID.
            added_at: When it was added.
        """
        ...

    def list_auth_ids(self) -> list[str]:
        """List the auth IDs of the accounts still to delete, oldest first.

        Returns:
            The auth IDs.
        """
        ...

    def complete(self, auth_id: str) -> None:
        """Take an account off the list, once it is deleted at the auth provider.

        Args:
            auth_id: The auth provider's account ID.
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

    def list_for_users(
        self, user_ids: Sequence[UUID]
    ) -> dict[UUID, TelegramConnection]:
        """Find many Users' Telegram Connections, in one query.

        Args:
            user_ids: The Users' IDs.

        Returns:
            Each User's connection; a User with none is left out.
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

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's Telegram Connection.

        Args:
            user_id: The User's ID.
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

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete every connection token of a User's.

        Args:
            user_id: The User's ID.
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

    def list_latest_for_users(
        self, user_ids: Sequence[UUID]
    ) -> dict[UUID, Conversation]:
        """Find many Users' newest Conversations, in one query.

        Args:
            user_ids: The Users' IDs.

        Returns:
            Each User's newest Conversation; a User who never had one is
            left out.
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

    def add_message_if_open(self, message: ConversationMessage) -> bool:
        """Save a message, but only if its Conversation has not been ended.

        The check and the save must happen as one step, so a Conversation
        being ended at the same time either takes the message in first or
        refuses it.

        Args:
            message: The message to save.

        Returns:
            True if it was saved; False if the Conversation was ended.
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

    def delete_messages_sent_before(self, cutoff: datetime) -> None:
        """Delete every message sent before a time; Conversations stay.

        Args:
            cutoff: Messages sent before this are deleted.
        """
        ...

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's Conversations and their messages.

        Args:
            user_id: The User's ID.
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

    def list_overviews(self) -> list[MemoryCategoryOverview]:
        """List every Memory Category with its Memory Item count, in sort order.

        Returns:
            The categories, archived ones included.
        """
        ...

    def get(self, category_id: UUID) -> MemoryCategory | None:
        """Find a Memory Category.

        Args:
            category_id: The category's ID.

        Returns:
            The category, or None if there is none.
        """
        ...

    def add(self, details: MemoryCategoryDetails) -> MemoryCategory:
        """Save a new, active Memory Category last in the list.

        Args:
            details: Its name, description and "always include".

        Returns:
            The saved category.
        """
        ...

    def update(self, category: MemoryCategory) -> MemoryCategory:
        """Save a Memory Category's name, description and flags.

        Args:
            category: The category with its new values.

        Returns:
            The saved category.
        """
        ...


class NeedRepository(Protocol):
    """Stores Needs."""

    def list_all(self) -> list[Need]:
        """List every Need in sort order.

        Returns:
            The Needs.
        """
        ...


class UnderstandingRepository(Protocol):
    """Stores the Understanding made for each answered Message."""

    def add(self, understanding: Understanding) -> None:
        """Save an Understanding.

        Args:
            understanding: The Understanding to save.
        """
        ...

    def list_for_conversation(self, conversation_id: UUID) -> list[Understanding]:
        """List a Conversation's Understandings, oldest first.

        Args:
            conversation_id: The Conversation's ID.

        Returns:
            The Understandings.
        """
        ...


class UserMemoryRepository(Protocol):
    """Stores each User's Memory Items, Conversation Summaries and Shared Photos."""

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
            changes: The changes to the User's Memory Items and the new
                Shared Photos.
        """
        ...

    def list_shared_photos(self, user_id: UUID) -> list[SharedPhoto]:
        """List a User's Shared Photos, newest first.

        Args:
            user_id: The User's ID.

        Returns:
            The Shared Photos.
        """
        ...

    def list_users_with_shared_photos(self, user_ids: Sequence[UUID]) -> set[UUID]:
        """Find which of many Users have any Shared Photos, in one query.

        Args:
            user_ids: The Users' IDs.

        Returns:
            The IDs of those with at least one Shared Photo.
        """
        ...

    def get_shared_photo(self, user_id: UUID, photo_id: UUID) -> SharedPhoto | None:
        """Find one of a User's Shared Photos.

        Args:
            user_id: The User's ID.
            photo_id: The Shared Photo's ID.

        Returns:
            The Shared Photo, or None if the User has no such photo.
        """
        ...

    def delete_shared_photo(self, user_id: UUID, photo_id: UUID) -> bool:
        """Delete one of a User's Shared Photos.

        Args:
            user_id: The User's ID.
            photo_id: The Shared Photo's ID.

        Returns:
            True if it was deleted; False if the User has no such photo.
        """
        ...

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's Memory Items, Conversation Summaries and Shared Photos.

        Args:
            user_id: The User's ID.
        """
        ...


class PlatformSettingsRepository(Protocol):
    """Stores admin-managed platform settings and content."""

    def load(self) -> PlatformSettings:
        """Read every setting in one query.

        Returns:
            The settings as they are now.
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

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's Safeguard Events.

        Args:
            user_id: The User's ID.
        """
        ...


class ModelCallRepository(Protocol):
    """Stores the Model Call Log."""

    def add(self, call: ModelCall) -> None:
        """Save one model call.

        Args:
            call: The call to save.
        """
        ...

    def list_traces(
        self,
        user_id: UUID | None,
        since: datetime | None,
        step: ModelStep | None,
        errors_only: bool,
        limit: int,
    ) -> list[ModelCallTraceOverview]:
        """List traces with who they were for, newest first.

        Args:
            user_id: Only this User's traces; None for every User.
            since: Only traces started at or after this time; None for all time.
            step: Only traces with a call for this step; None for every step.
            errors_only: Only traces with a failed call.
            limit: The most traces to list.

        Returns:
            The traces.
        """
        ...

    def get_trace(self, trace_id: UUID) -> ModelCallTraceDetails | None:
        """Read one trace with every call in it.

        Args:
            trace_id: The trace's ID.

        Returns:
            The trace, or None if there is no such trace.
        """
        ...

    def delete_started_before(self, cutoff: datetime) -> None:
        """Delete every call that started before a time.

        Args:
            cutoff: Calls that started before this are deleted.
        """
        ...

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's calls.

        Args:
            user_id: The User's ID.
        """
        ...


class KnowledgeDocumentRepository(Protocol):
    """Stores Knowledge documents and their uploaded files."""

    def list_all(self) -> list[KnowledgeDocument]:
        """List every Knowledge document, newest upload first.

        Returns:
            The documents.
        """
        ...

    def get(self, document_id: UUID) -> KnowledgeDocument | None:
        """Find a Knowledge document.

        Args:
            document_id: The document's ID.

        Returns:
            The document, or None if there is none.
        """
        ...

    def get_content(self, document_id: UUID) -> bytes:
        """Read a Knowledge document's uploaded file.

        Args:
            document_id: The document's ID.

        Returns:
            The file's bytes.
        """
        ...

    def get_text(self, document_id: UUID) -> str | None:
        """Read the text a Knowledge document's replies draw on.

        Args:
            document_id: The document's ID.

        Returns:
            The saved text, or None if none has been saved.
        """
        ...

    def save_text(
        self, document_id: UUID, text: str, edited: bool
    ) -> KnowledgeDocument | None:
        """Save the text a Knowledge document's replies draw on.

        Args:
            document_id: The document's ID.
            text: The text.
            edited: Whether an Admin wrote it, rather than it being read from
                the file.

        Returns:
            The saved document, or None if it has been deleted.
        """
        ...

    def update_details(
        self, document_id: UUID, change: KnowledgeDetailsChange
    ) -> KnowledgeDocument | None:
        """Save new details on a Knowledge document.

        Args:
            document_id: The document's ID.
            change: The details to change; a None field is kept.

        Returns:
            The saved document, or None if there is none.
        """
        ...

    def replace_file(
        self, document_id: UUID, file: KnowledgeFile
    ) -> KnowledgeDocument | None:
        """Give a Knowledge document a new file and make it pending.

        Its saved text and edited flag are cleared, so the new file is read.

        Args:
            document_id: The document's ID.
            file: The new file.

        Returns:
            The saved document, or None if there is none.
        """
        ...

    def add(self, upload: KnowledgeUpload, created_at: datetime) -> KnowledgeDocument:
        """Save a new, pending Knowledge document with its file.

        Args:
            upload: The document and its file.
            created_at: When it was uploaded.

        Returns:
            The saved document.
        """
        ...

    def set_status(
        self, document_id: UUID, status: KnowledgeStatus, failure_reason: str | None
    ) -> KnowledgeDocument | None:
        """Save where a Knowledge document is in being made ready.

        Args:
            document_id: The document's ID.
            status: Its new status.
            failure_reason: Why it failed; None unless it failed.

        Returns:
            The saved document, or None if it has been deleted.
        """
        ...

    def delete(self, document_id: UUID) -> None:
        """Remove a Knowledge document and its file.

        Args:
            document_id: The document's ID.
        """
        ...


class UsageRepository(Protocol):
    """Stores what each User used on each day."""

    def claim_web_search(self, user_id: UUID, day: date, daily_limit: int) -> bool:
        """Count one web search for a User's day, in one step, if under the limit.

        Args:
            user_id: The User's ID.
            day: The User's day.
            daily_limit: The most web searches allowed in a day.

        Returns:
            True if the search was counted; False if the limit was reached,
            so two searches at once can never go over it.
        """
        ...

    def count_web_searches(self, user_id: UUID, day: date) -> int:
        """Count a User's web searches on a day.

        Args:
            user_id: The User's ID.
            day: The User's day.

        Returns:
            How many web searches they made.
        """
        ...

    def count_messages(self, user_id: UUID, day: date) -> int:
        """Count a User's messages on a day.

        Args:
            user_id: The User's ID.
            day: The User's day.

        Returns:
            How many of their messages counted toward the daily message limit.
        """
        ...

    def count_messages_on_days(self, days: Mapping[UUID, date]) -> dict[UUID, int]:
        """Count many Users' messages, each on their own day, in one query.

        Args:
            days: Each User's ID and their day.

        Returns:
            Each User's count; 0 if nothing was recorded that day.
        """
        ...

    def claim_message(self, user_id: UUID, day: date, daily_limit: int) -> bool:
        """Count one message for a User's day, in one step, if under the limit.

        Args:
            user_id: The User's ID.
            day: The User's day.
            daily_limit: The most messages allowed in a day.

        Returns:
            True if the message was counted; False if the limit was reached.
        """
        ...

    def add_tokens(
        self, user_id: UUID, day: date, tokens_in: int, tokens_out: int
    ) -> None:
        """Add chat model tokens to a User's day.

        Args:
            user_id: The User's ID.
            day: The User's day.
            tokens_in: Tokens the model read.
            tokens_out: Tokens the model wrote.
        """
        ...

    def list_since(self, first_day: date) -> list[DailyUsage]:
        """List every User's usage from a day on.

        Args:
            first_day: The earliest day to list.

        Returns:
            One entry per User per day, newest day first, then by User.
        """
        ...

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's Usage.

        Args:
            user_id: The User's ID.
        """
        ...


class StickerRepository(Protocol):
    """Stores the Sticker Library."""

    def list_all(self) -> list[LibrarySticker]:
        """List every sticker in the order they were added.

        Returns:
            The stickers.
        """
        ...

    def get(self, sticker_id: UUID) -> LibrarySticker | None:
        """Find a sticker.

        Args:
            sticker_id: The sticker's ID.

        Returns:
            The sticker, or None if there is none.
        """
        ...

    def add_new(self, new_stickers: list[ChannelSticker], added_at: datetime) -> int:
        """Add stickers without a note, skipping any already in the library.

        Args:
            new_stickers: The stickers, in order.
            added_at: When they are being added.

        Returns:
            How many were added.
        """
        ...

    def save_note(self, sticker_id: UUID, note: str) -> LibrarySticker | None:
        """Save a sticker's "when to use" note.

        Args:
            sticker_id: The sticker's ID.
            note: The note.

        Returns:
            The saved sticker, or None if there is none.
        """
        ...

    def delete(self, sticker_id: UUID) -> bool:
        """Remove a sticker.

        Args:
            sticker_id: The sticker's ID.

        Returns:
            True if it was removed; False if there was none.
        """
        ...


class PersonalStickerRepository(Protocol):
    """Stores the stickers kept from each User."""

    def list_for_user(self, user_id: UUID) -> list[PersonalSticker]:
        """List a User's Personal Stickers, most recently used first.

        Args:
            user_id: The User.

        Returns:
            The stickers.
        """
        ...

    def get(self, user_id: UUID, sticker_id: UUID) -> PersonalSticker | None:
        """Find one of a User's Personal Stickers.

        Args:
            user_id: The User it must belong to.
            sticker_id: The sticker's ID.

        Returns:
            The sticker, or None if the User has none with that ID.
        """
        ...

    def save_many(self, stickers: list[PersonalSticker]) -> None:
        """Keep stickers, replacing the User's own copy of the same sticker.

        A sticker the User already has, by its unchanging ID, keeps its ID,
        when it was first kept and its later last use; the rest is replaced.

        Args:
            stickers: The stickers to keep.
        """
        ...

    def mark_used(self, user_id: UUID, sticker_id: UUID, used_at: datetime) -> None:
        """Note that one of a User's Personal Stickers was just sent.

        Args:
            user_id: The User it belongs to.
            sticker_id: The sticker's ID.
            used_at: When it was sent.
        """
        ...

    def keep_most_recently_used(self, user_id: UUID, limit: int) -> None:
        """Drop a User's Personal Stickers used longest ago, beyond a limit.

        Args:
            user_id: The User.
            limit: How many to keep.
        """
        ...

    def delete(self, user_id: UUID, sticker_id: UUID) -> bool:
        """Remove one of a User's Personal Stickers.

        Args:
            user_id: The User it must belong to.
            sticker_id: The sticker's ID.

        Returns:
            True if it was removed; False if the User had none with that ID.
        """
        ...

    def count_for_user(self, user_id: UUID) -> int:
        """Count a User's Personal Stickers.

        Args:
            user_id: The User.

        Returns:
            How many they have.
        """
        ...

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's Personal Stickers.

        Args:
            user_id: The User's ID.
        """
        ...


class CheckInRepository(Protocol):
    """Stores Check-in Kinds and the Check-in decisions made for Users."""

    def list_kinds(self) -> list[CheckInKind]:
        """List every Check-in Kind in order.

        Returns:
            The Check-in Kinds.
        """
        ...

    def list_kind_overviews(self, sent_since: datetime) -> list[CheckInKindOverview]:
        """List every Check-in Kind in order with how often it was sent lately.

        Args:
            sent_since: Only Check-ins sent after this are counted.

        Returns:
            The Check-in Kinds with their send counts.
        """
        ...

    def get_kind(self, kind_id: UUID) -> CheckInKind | None:
        """Find one Check-in Kind.

        Args:
            kind_id: The Check-in Kind's ID.

        Returns:
            The Check-in Kind, or None if there is no such Kind.
        """
        ...

    def add_kind(self, details: CheckInKindDetails) -> CheckInKind:
        """Add a Check-in Kind last in the list.

        Args:
            details: Its name and description.

        Returns:
            The saved Check-in Kind.
        """
        ...

    def update_kind(self, kind: CheckInKind) -> CheckInKind:
        """Save a Check-in Kind's name, description and User Memory flag.

        Args:
            kind: The Check-in Kind with its new values.

        Returns:
            The saved Check-in Kind.
        """
        ...

    def delete_kind(self, kind_id: UUID) -> bool:
        """Remove a Check-in Kind; past Check-ins of it keep no Kind.

        Args:
            kind_id: The Check-in Kind's ID.

        Returns:
            True if it was removed; False if there was no such Kind.
        """
        ...

    def list_due_users(self, now: datetime) -> list[User]:
        """List onboarded Users with Check-ins on whose next one is due.

        Users whose Check-ins are off on the Admin side, for everyone or for
        them, are left out but stay due. Pause and quiet hours are not
        checked here.

        Args:
            now: The time to check at.

        Returns:
            The Users whose next due time is at or before now; a User with no
            due time is never due.
        """
        ...

    def save_next_due_times(self, changes: Sequence[NextDueTimeChange]) -> None:
        """Save many Users' next due times, in one statement.

        A User whose due time changed since it was read is left as it is, so
        a settings change made meanwhile is kept.

        Args:
            changes: Each User's due time as read and the one to save.
        """
        ...

    def set_due_now_unless_due_later(self, user_id: UUID, now: datetime) -> None:
        """Make a User with Check-ins on due now, unless they are due later.

        A due time of now also wins over a tick that read the old one and is
        holding the User back meanwhile.

        Args:
            user_id: The User's ID.
            now: The current time.
        """
        ...

    def add(
        self, check_in: CheckIn, next_due_at: datetime, pause_until_resumed: bool
    ) -> None:
        """Save a Check-in decision and the User's next due time, together.

        Only the next due time and, when asked, the pause are changed, so
        settings the User changed meanwhile are kept.

        Args:
            check_in: The Check-in decision.
            next_due_at: When the User's next Check-in may be sent.
            pause_until_resumed: Whether to also pause the User's Check-ins
                until they resume.
        """
        ...

    def undo_add(
        self,
        check_in: CheckIn,
        next_due_at: datetime,
        end_pause: bool,
        skipped: CheckIn | None,
    ) -> None:
        """Take back a saved Check-in that was never sent, together.

        Only the next due time and, when asked, the pause are changed, so
        settings the User changed meanwhile are kept.

        Args:
            check_in: The saved Check-in to remove.
            next_due_at: When the User's next Check-in may be sent.
            end_pause: Whether to end the pause that saving it started.
            skipped: A Skipped Check-in to save in its place; None for none.
        """
        ...

    def remove_shared_photo(self, check_in_id: UUID) -> None:
        """Mark a sent Check-in as having sent no Shared Photo.

        Args:
            check_in_id: The Check-in's ID.
        """
        ...

    def list_recent(self, user_id: UUID, limit: int) -> list[CheckIn]:
        """List a User's newest Check-in decisions, newest first.

        Args:
            user_id: The User's ID.
            limit: The most to list.

        Returns:
            The Check-ins.
        """
        ...

    def list_recent_for_users(
        self, user_ids: Sequence[UUID], limit: int, sent_only: bool
    ) -> dict[UUID, list[CheckIn]]:
        """List many Users' newest Check-in decisions, in one query.

        Args:
            user_ids: The Users' IDs.
            limit: The most to list per User.
            sent_only: Whether to leave out Skipped Check-ins.

        Returns:
            Each User's Check-ins, newest first; a User with none is left out.
        """
        ...

    def list_log(self, since: datetime) -> list[CheckInLogEntry]:
        """List every User's Check-in decisions since a time, newest first.

        Args:
            since: Only decisions after this are listed.

        Returns:
            The decisions with who each User is.
        """
        ...

    def claim_reply(
        self, user_id: UUID, replied_at: datetime, sent_since: datetime
    ) -> CheckIn | None:
        """Mark the User's newest sent Check-in replied, if it can still be.

        Skipped Check-ins are passed over, since nothing was sent.

        Args:
            user_id: The User's ID.
            replied_at: When they replied.
            sent_since: A Check-in sent at or before this can't get a reply.

        Returns:
            The Check-in they replied to, or None if their newest sent
            Check-in was already replied to, was sent before `sent_since`, or
            they have none.
        """
        ...

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's Check-in history.

        Args:
            user_id: The User's ID.
        """
        ...


class FeatureSwitchRepository(Protocol):
    """Stores each Feature's switches, for everyone and per User."""

    def list_for_everyone(self) -> list[FeatureSwitch]:
        """List the stored switches for everyone.

        Returns:
            The switches that are stored, in no set order.
        """
        ...

    def save_for_everyone(
        self, feature: Feature, on: bool, changed_at: datetime, changed_by: UUID
    ) -> None:
        """Save a Feature's switch for everyone.

        Args:
            feature: The Feature.
            on: Whether it is on for everyone.
            changed_at: When it is being changed.
            changed_by: The Admin changing it.
        """
        ...

    def list_for_user(self, user_id: UUID) -> list[FeatureSwitch]:
        """List the switches stored for one User.

        Only switches set to "on" or "off" are stored.

        Args:
            user_id: The User.

        Returns:
            The User's switches, in no set order.
        """
        ...

    def list_for_users(
        self, user_ids: Sequence[UUID]
    ) -> dict[UUID, list[FeatureSwitch]]:
        """List the switches stored for many Users, in one query.

        Args:
            user_ids: The Users.

        Returns:
            Each User's switches, in no set order; a User with none is left
            out.
        """
        ...

    def save_for_user(
        self,
        user_id: UUID,
        feature: Feature,
        on: bool,
        changed_at: datetime,
        changed_by: UUID,
    ) -> None:
        """Save a Feature's switch for one User as on or off.

        Args:
            user_id: The User.
            feature: The Feature.
            on: Whether it is on for the User.
            changed_at: When it is being changed.
            changed_by: The Admin changing it.
        """
        ...

    def remove_for_user(self, user_id: UUID, feature: Feature) -> None:
        """Remove a Feature's switch for one User, so it follows everyone's.

        Args:
            user_id: The User.
            feature: The Feature.
        """
        ...

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's own Feature Switches.

        Args:
            user_id: The User's ID.
        """
        ...


@dataclass(frozen=True)
class Repositories:
    """Every repository the core needs, so adapters can be swapped as one.

    `with repositories.transaction() as transaction:` runs changes across
    them in one transaction: all of it is saved, or none. Starting one inside
    another joins the outer one.
    """

    users: UserRepository
    telegram_connections: TelegramConnectionRepository
    connection_tokens: ConnectionTokenRepository
    conversations: ConversationRepository
    platform_settings: PlatformSettingsRepository
    helplines: HelplineRepository
    safeguard_events: SafeguardEventRepository
    memory_categories: MemoryCategoryRepository
    needs: NeedRepository
    understandings: UnderstandingRepository
    user_memory: UserMemoryRepository
    knowledge_documents: KnowledgeDocumentRepository
    usage: UsageRepository
    stickers: StickerRepository
    personal_stickers: PersonalStickerRepository
    check_ins: CheckInRepository
    feature_switches: FeatureSwitchRepository
    pending_auth_account_deletions: PendingAuthAccountDeletionRepository
    model_calls: ModelCallRepository
    transaction: Callable[[], AbstractContextManager["Transaction"]]


class Transaction(Protocol):
    """One transaction across the repositories, with locks for rules that need them."""

    @property
    def repositories(self) -> Repositories:
        """The repositories, each working inside this transaction."""
        ...

    def lock_admins(self) -> list[UUID]:
        """Lock the Admins until the transaction ends, and list them.

        Another transaction locking them waits for this one, then sees its
        changes.

        Returns:
            The IDs of the Users who are Admins.
        """
        ...
