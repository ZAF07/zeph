from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Protocol
from uuid import UUID

from companion.core.models import (
    AccountIdentity,
    AgendaChanges,
    CatalogPattern,
    ChannelSticker,
    ChatLine,
    CheckIn,
    CheckInKind,
    CheckInKindDetails,
    CheckInKindOverview,
    CheckInLogEntry,
    CheckInNowRequest,
    CheckInShape,
    ConnectionToken,
    Conversation,
    ConversationMessage,
    CopySeedSlot,
    CopySlot,
    CountedUnmatchedEntry,
    Curiosity,
    CuriosityChanges,
    DailyUsage,
    DaySummary,
    DeletedQuote,
    EmbeddedChunk,
    ExclusionFlag,
    Exploration,
    ExplorationTry,
    Familiarity,
    FamiliarityCounts,
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
    LifeThread,
    LifeThreadToSave,
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
    Move,
    MoveDetails,
    MoveOutcome,
    MoveOutcomeToSave,
    Need,
    NeedDetails,
    NextDueTimeChange,
    Observation,
    Pattern,
    PatternMove,
    PatternToSave,
    PatternTypeVersion,
    PersonalSticker,
    PhotoImage,
    PlatformSettings,
    Prediction,
    ReactionToPattern,
    ReplyPlan,
    ReplyPlanShape,
    RiskType,
    SafeguardEvent,
    SafeguardEventOverview,
    SharedPhoto,
    StickerImage,
    StoredSetting,
    TaggingShape,
    TelegramConnection,
    ThoughtExperiment,
    ThoughtExperimentDetails,
    Understanding,
    UnderstandingShape,
    UnmatchedEntry,
    User,
    UserOverview,
    UserPage,
    UserPortrait,
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


class UserWorkQueue(Protocol):
    """Runs Users' chat work in the background, each User's in order.

    Work added under the same key runs one piece at a time, in the order it
    was added. Work under different keys runs side by side, up to the
    queue's limit of pieces running at once. A piece that fails is logged,
    and later work under its key still runs.
    """

    def add(self, key: str, work: Callable[[], None]) -> None:
        """Add a piece of work to the end of a key's line, and return at once.

        Args:
            key: Names one line of a User's work, e.g. their texts to check.
            work: What to run when its turn comes.
        """
        ...


class MessageRefusedError(Exception):
    """Raised when the chat channel clearly refused a message, so it never arrived."""


class ChatBlockedError(Exception):
    """Raised when the chat channel can't reach the person, e.g. they blocked us."""


class ChatChannel(Protocol):
    """Sends messages to people on the chat channel (Telegram for the MVP)."""

    def send_text(
        self, chat_id: int, text: str, reply_to_message_id: int | None = None
    ) -> None:
        """Send one text message, optionally as a reply to an earlier one.

        A reply whose earlier message can't be found is sent on its own.

        Args:
            chat_id: The chat to send to.
            text: The message text.
            reply_to_message_id: The chat channel's ID of the message it replies
                to; None to send it on its own.

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
        thinking: bool,
        instructions: str,
        history: list[ChatLine],
        tools: Sequence[ChatTool] = (),
        message_instructions: str = "",
    ) -> ModelAnswer:
        """Generate the next reply, calling tools first if the model wants to.

        A model that can't do the thinking asked for does the closest it can
        and logs a warning; it never fails for it.

        The model reads `instructions` and then `message_instructions` as one
        text (see `join_instructions`). They are given apart so a provider's
        prompt cache can keep `instructions`, which stay the same from call
        to call, and read them back on the next call.

        Args:
            model: The model to use, e.g. "deepseek/deepseek-v4.1-flash-1017".
            thinking: Whether the model should think before it answers.
            instructions: What the model should be and do (Persona and
                prompt): the part that stays the same from call to call.
            history: The Conversation so far, oldest first.
            tools: The tools the model may call; none by default.
            message_instructions: The instructions made for this one call,
                read after `instructions`; "" by default.

        Returns:
            The reply text and the tokens it took.
        """
        ...


class PhotoViewer(Protocol):
    """Looks at a photo with a model that can see images."""

    def look(
        self, model: str, thinking: bool, instructions: str, photo: PhotoImage
    ) -> ModelAnswer:
        """Look at a photo and write what the instructions ask for.

        A model that can't do the thinking asked for does the closest it can
        and logs a warning; it never fails for it.

        Args:
            model: The model to use, e.g. "deepseek/deepseek-v4.1-flash-1017".
            thinking: Whether the model should think before it answers.
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

    def search(
        self,
        embedding: list[float],
        document_ids: Sequence[UUID],
        min_closeness: float,
        limit: int,
    ) -> list[KnowledgeChunkMatch]:
        """Find the chunks of some documents closest to an embedding.

        Closeness is cosine similarity.

        Args:
            embedding: What to search with.
            document_ids: The documents to search; only their chunks count.
            min_closeness: How close a chunk must be, from 0 to 1.
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

    def mark_pattern_noticing_told(self, user_id: UUID, told_at: datetime) -> User:
        """Save that a User was told about Pattern noticing, the first time only.

        Args:
            user_id: The User's ID.
            told_at: When they pressed "Got it".

        Returns:
            The saved User.
        """
        ...

    def familiarity_counts(self, user_id: UUID) -> FamiliarityCounts:
        """Count what the Companion has of a User, for their Familiarity.

        Args:
            user_id: The User's ID.

        Returns:
            Their Conversations, Life Threads, Observations from real
            stories and Patterns in each state.
        """
        ...

    def save_familiarity(self, user_id: UUID, familiarity: Familiarity) -> None:
        """Save how well the Companion knows a User.

        Args:
            user_id: The User's ID.
            familiarity: Their Familiarity now.
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

    def list_user_messages_between(
        self, user_id: UUID, start: datetime, end: datetime | None = None
    ) -> list[ConversationMessage]:
        """List every message a User and the Companion sent in a span of time.

        Messages from every one of the User's Conversations are listed
        together, in one query.

        Args:
            user_id: The User's ID.
            start: The earliest time sent, included.
            end: The latest time sent, left out; None for no end.

        Returns:
            The messages, in the order they were saved.
        """
        ...

    def list_started_between(
        self, user_id: UUID, start: datetime, end: datetime
    ) -> list[Conversation]:
        """List a User's Conversations that started in a span of time.

        Args:
            user_id: The User's ID.
            start: The earliest start, included.
            end: The latest start, left out.

        Returns:
            The Conversations, oldest first.
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


class NameTakenError(Exception):
    """Raised when a save would give a second Move or Need the same name."""


class NeedRepository(Protocol):
    """Stores Needs, each with the Moves it rules out."""

    def list_all(self) -> list[Need]:
        """List every Need in sort order.

        Returns:
            The Needs.
        """
        ...

    def get(self, need_id: UUID) -> Need | None:
        """Find one Need.

        Args:
            need_id: The Need's ID.

        Returns:
            The Need, or None if there is no such Need.
        """
        ...

    def add(self, details: NeedDetails) -> Need:
        """Add a Need last in the list; it is never the fallback.

        Args:
            details: Its name, when it fits, how to reply and the Moves it
                rules out.

        Returns:
            The saved Need.

        Raises:
            NameTakenError: If another Need already has the name.
        """
        ...

    def update(self, need_id: UUID, details: NeedDetails) -> Need:
        """Save a Need's name, when it fits, how to reply and ruled-out Moves.

        Args:
            need_id: The Need's ID.
            details: Its new values.

        Returns:
            The saved Need.

        Raises:
            NameTakenError: If another Need already has the name.
        """
        ...

    def delete(self, need_id: UUID) -> None:
        """Remove a Need.

        Args:
            need_id: The Need's ID.
        """
        ...

    def set_sort_orders(self, sort_orders: Mapping[UUID, int]) -> None:
        """Save new sort orders for several Needs in one step.

        Args:
            sort_orders: The new sort order for each Need ID.
        """
        ...


class MoveRepository(Protocol):
    """Stores Moves."""

    def list_all(self) -> list[Move]:
        """List every Move in sort order.

        Returns:
            The Moves.
        """
        ...

    def get(self, move_id: UUID) -> Move | None:
        """Find one Move.

        Args:
            move_id: The Move's ID.

        Returns:
            The Move, or None if there is no such Move.
        """
        ...

    def add(self, details: MoveDetails) -> Move:
        """Add a Move last in the list.

        Args:
            details: Its name, when it fits, how to do it and needed Feature.

        Returns:
            The saved Move.

        Raises:
            NameTakenError: If another Move already has the name, ignoring case.
        """
        ...

    def update(self, move_id: UUID, details: MoveDetails) -> Move:
        """Save a Move's name, when it fits, how to do it and needed Feature.

        Args:
            move_id: The Move's ID.
            details: Its new values.

        Returns:
            The saved Move.

        Raises:
            NameTakenError: If another Move already has the name, ignoring case.
        """
        ...

    def delete(self, move_id: UUID) -> None:
        """Remove a Move, and with it every Need's rule-out of it.

        Args:
            move_id: The Move's ID.
        """
        ...

    def set_sort_orders(self, sort_orders: Mapping[UUID, int]) -> None:
        """Save new sort orders for several Moves in one step.

        Args:
            sort_orders: The new sort order for each Move ID.
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


class ReplyPlanRepository(Protocol):
    """Stores the Reply Plan made for each answered Message."""

    def add(self, reply_plan: ReplyPlan) -> None:
        """Save a Reply Plan.

        Args:
            reply_plan: The Reply Plan to save.
        """
        ...

    def list_for_conversation(self, conversation_id: UUID) -> list[ReplyPlan]:
        """List a Conversation's Reply Plans, oldest first.

        Args:
            conversation_id: The Conversation's ID.

        Returns:
            The Reply Plans.
        """
        ...

    def count_since(self, user_id: UUID, since: datetime) -> int:
        """Count the Reply Plans made for a User after a time, in any Conversation.

        Args:
            user_id: The User's ID.
            since: The time; Reply Plans made at it or before are left out.

        Returns:
            How many there are.
        """
        ...


class LifeThreadRepository(Protocol):
    """Stores each User's Life Threads, found by name or by meaning."""

    def find_reminded(
        self,
        user_id: UUID,
        named: Sequence[str],
        embedding: list[float] | None,
        min_closeness: float,
        limit: int,
    ) -> list[LifeThread]:
        """Find the User's Threads a message reminds the Companion of.

        A Thread counts if one of its name keys is among the names given,
        however close its story is, or if its story is at least as close in
        meaning as asked. Open Threads come first, then those named, then
        the closest. Age doesn't matter.

        Args:
            user_id: The User's ID; only their Threads are searched.
            named: The words and short phrases in the message, in lower case
                and one word apart, e.g. "mei", "my sister".
            embedding: The message embedded; None to find by name only.
            min_closeness: How close in meaning a story must be, from 0 to 1.
            limit: The most to return.

        Returns:
            The Threads, in that order.
        """
        ...

    def list_raised_in(self, conversation_id: UUID) -> list[LifeThread]:
        """List the Threads last brought up in a Conversation.

        Args:
            conversation_id: The Conversation's ID.

        Returns:
            The Threads, oldest started first.
        """
        ...

    def keep_in_mind(
        self, conversation_id: UUID, thread_ids: Sequence[UUID], at: datetime
    ) -> None:
        """Note that Threads came to mind in a Conversation, so they stay in mind.

        A Thread already in mind keeps when it first came to mind.

        Args:
            conversation_id: The Conversation's ID.
            thread_ids: The Threads' IDs.
            at: When they came to mind.
        """
        ...

    def list_in_mind(self, conversation_id: UUID) -> list[LifeThread]:
        """List the Threads that came to mind in a Conversation.

        Args:
            conversation_id: The Conversation's ID.

        Returns:
            The Threads, the first to come to mind first.
        """
        ...

    def save_many(
        self,
        added: Sequence[LifeThreadToSave],
        changed: Sequence[LifeThreadToSave],
    ) -> None:
        """Add new Threads and save changed ones, in one step.

        A changed Thread saved with no embedding keeps the one it had. A
        changed Thread that was deleted meanwhile stays deleted.

        Args:
            added: The new Threads.
            changed: The changed Threads.
        """
        ...

    def mark_raised(
        self, thread_ids: Sequence[UUID], conversation_id: UUID, raised_at: datetime
    ) -> None:
        """Note that Threads were just brought up in a Conversation.

        The last reaction stays until the Conversation's end records a new
        one, so a brushed-off Thread raised while User Memory is off still
        waits.

        Args:
            thread_ids: The Threads' IDs.
            conversation_id: The Conversation they were brought up in.
            raised_at: When the reply that brought them up was sent.
        """
        ...

    def list_for_user(self, user_id: UUID) -> list[LifeThread]:
        """List a User's Threads, open first, then the latest updated.

        Args:
            user_id: The User's ID.

        Returns:
            The Threads.
        """
        ...

    def delete(self, user_id: UUID, thread_id: UUID) -> bool:
        """Delete one of a User's Threads.

        Args:
            user_id: The User's ID.
            thread_id: The Thread's ID.

        Returns:
            True if it was deleted; False if the User has no such Thread.
        """
        ...

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete every one of a User's Life Threads.

        Args:
            user_id: The User's ID.
        """
        ...

    def find_closest(
        self,
        user_id: UUID,
        embedding: list[float],
        leave_out: Sequence[UUID],
        limit: int,
    ) -> list[LifeThread]:
        """Find a User's Threads closest in meaning, however old, open or settled.

        Threads with no embedding are never found.

        Args:
            user_id: The User's ID; only their Threads are searched.
            embedding: What the Threads are compared with.
            leave_out: Threads not to return, e.g. ones already given.
            limit: The most to return.

        Returns:
            The closest Threads, closest first.
        """
        ...


class ObservationRepository(Protocol):
    """Stores each User's Observations, which outlive Message Retention (ADR-0027)."""

    def add_many(self, observations: Sequence[Observation]) -> None:
        """Save new Observations, all together.

        Args:
            observations: The Observations; none saves nothing.
        """
        ...

    def settle(self, settled: Sequence[Observation]) -> None:
        """Save unclear Observations made clear, with the Pattern Type now named.

        Args:
            settled: The Observations, each with one Pattern Type and its
                sign; none saves nothing.
        """
        ...

    def list_for_user(self, user_id: UUID) -> list[Observation]:
        """List a User's Observations, oldest tagged first.

        Args:
            user_id: The User's ID.

        Returns:
            The Observations.
        """
        ...

    def delete(self, user_id: UUID, observation_id: UUID) -> bool:
        """Delete one of a User's Observations.

        Args:
            user_id: The User's ID.
            observation_id: The Observation's ID.

        Returns:
            True if it was deleted; False if the User has no such Observation.
        """
        ...

    def delete_of_pattern_type(self, user_id: UUID, pattern_type_id: str) -> None:
        """Delete a User's Observations whose first Pattern Type is the one given.

        An unclear Observation that names it second is kept: it belongs
        first to another Pattern.

        Args:
            user_id: The User's ID.
            pattern_type_id: The Pattern Type's ID.
        """
        ...

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's Observations, exclusion flags and deleted-quote records.

        Args:
            user_id: The User's ID.
        """
        ...

    def note_deleted_quotes(self, deleted: Sequence[DeletedQuote]) -> None:
        """Keep a record of quotes a User deleted, so none is kept again.

        Args:
            deleted: The records; one already kept is left as it is.
        """
        ...

    def list_deleted_quote_hashes(
        self, user_id: UUID, conversation_id: UUID
    ) -> frozenset[str]:
        """List the hashes of the quotes a User deleted from one Conversation.

        Args:
            user_id: The User's ID.
            conversation_id: The Conversation the quotes were said in.

        Returns:
            The hashes; none when they deleted no quote from it.
        """
        ...

    def replace_exclusion_flags(
        self, user_id: UUID, flags: Sequence[ExclusionFlag]
    ) -> None:
        """Save the exclusions that apply to a User now, in place of the old ones.

        Args:
            user_id: The User's ID.
            flags: The exclusions that apply now; none clears them.
        """
        ...

    def list_exclusion_flags(self, user_id: UUID) -> list[ExclusionFlag]:
        """List the exclusions that apply to a User now.

        Args:
            user_id: The User's ID.

        Returns:
            The flags from the last time their Observations were tagged.
        """
        ...


class PatternRepository(Protocol):
    """Stores each User's Patterns, and the log of their moves.

    A Pattern with no Pattern Type (an unmatched one) has its own words and
    evidence and is found by meaning; only those are read by the methods
    that return a `Pattern`. A Pattern of
    a Pattern Type is fed by Observations and moved by code.
    """

    def list_for_user(self, user_id: UUID) -> list[Pattern]:
        """List a User's Patterns with no Pattern Type, oldest started first.

        Args:
            user_id: The User's ID.

        Returns:
            The Patterns, each with its evidence oldest first.
        """
        ...

    def find_close_ids(
        self, user_id: UUID, embedding: list[float], min_closeness: float
    ) -> list[UUID]:
        """Find the User's Patterns at least as close in meaning as asked.

        Patterns with no embedding are never found.

        Args:
            user_id: The User's ID; only their Patterns are searched.
            embedding: What the Patterns are compared with.
            min_closeness: How close in meaning a Pattern must be, from 0 to 1.

        Returns:
            The Patterns' IDs, closest first.
        """
        ...

    def keep_in_mind(
        self, conversation_id: UUID, pattern_ids: Sequence[UUID], at: datetime
    ) -> None:
        """Note that Patterns came to mind in a Conversation, so they stay in mind.

        A Pattern already in mind keeps when it first came to mind.

        Args:
            conversation_id: The Conversation's ID.
            pattern_ids: The Patterns' IDs.
            at: When they came to mind.
        """
        ...

    def list_in_mind_ids(self, conversation_id: UUID) -> list[UUID]:
        """List the Patterns that came to mind in a Conversation.

        Args:
            conversation_id: The Conversation's ID.

        Returns:
            The Patterns' IDs, the first to come to mind first.
        """
        ...

    def save_many(
        self, added: Sequence[PatternToSave], changed: Sequence[PatternToSave]
    ) -> None:
        """Add new Patterns and save changed ones, in one step.

        Evidence not kept yet is added, unless its Life Thread or Pattern was
        deleted meanwhile; evidence already kept is left as it is. A Pattern left
        with no evidence is deleted. A changed Pattern saved with no
        embedding keeps the one it had.

        Args:
            added: The new Patterns.
            changed: The changed Patterns.
        """
        ...

    def delete_without_evidence(self, user_id: UUID) -> None:
        """Delete a User's Patterns that have no evidence left.

        Args:
            user_id: The User's ID.
        """
        ...

    def list_not_matched(self) -> list[Pattern]:
        """List every User's Patterns with no Pattern Type and none matched.

        Returns:
            The Patterns, each User's together, oldest started first, each
            with its evidence oldest first.
        """
        ...

    def save_match(self, pattern_id: UUID, pattern_type_id: str) -> None:
        """Save the Pattern Type a Pattern with none of its own was found to fit.

        The Pattern keeps its words, state and evidence.

        Args:
            pattern_id: The Pattern's ID.
            pattern_type_id: The Pattern Type's ID.
        """
        ...

    def list_of_pattern_types(self, user_id: UUID) -> list[CatalogPattern]:
        """List a User's Patterns of Pattern Types, oldest started first.

        Args:
            user_id: The User's ID.

        Returns:
            The Patterns.
        """
        ...

    def save_moves(
        self,
        added: Sequence[CatalogPattern],
        changed: Sequence[CatalogPattern],
        deleted_ids: Sequence[UUID],
        moves: Sequence[PatternMove],
    ) -> None:
        """Save what scoring or the ready gate changed in a User's Patterns, at once.

        Args:
            added: Patterns noticed for the first time.
            changed: Patterns that moved or that the ready gate judged, with
                their state, blocking check, narrowings, when the other
                side was last argued and when they were shared.
            deleted_ids: Patterns with no Observations left; their moves stay.
            moves: The moves, added to the log in order.
        """
        ...

    def list_moves(self, user_id: UUID) -> list[PatternMove]:
        """List every move of a User's Patterns, oldest first.

        Args:
            user_id: The User's ID.

        Returns:
            The moves, including those of Patterns since deleted.
        """
        ...

    def count_shared_since(
        self, user_ids: Sequence[UUID], since: datetime
    ) -> dict[UUID, int]:
        """Count the Patterns shared with many Users since a time, in one query.

        It counts the logged moves to shared, so a Pattern deleted since
        still counts.

        Args:
            user_ids: The Users' IDs.
            since: Only Patterns shared after this are counted.

        Returns:
            Each User's count; a User with none is left out.
        """
        ...

    def list_users_with_pattern_ready_by(
        self, user_ids: Sequence[UUID], ready_by: datetime
    ) -> set[UUID]:
        """Find which of many Users have a Pattern ready since a time, in one query.

        Args:
            user_ids: The Users' IDs.
            ready_by: Only a Pattern that became ready at or before this
                counts.

        Returns:
            The IDs of the Users with such a Pattern.
        """
        ...

    def add_prediction(self, prediction: Prediction) -> None:
        """Save a Prediction given for a shared Pattern.

        Args:
            prediction: The Prediction.
        """
        ...

    def save_prediction_outcomes(self, settled: Sequence[Prediction]) -> None:
        """Save how some Predictions went.

        Args:
            settled: The Predictions, each with its outcome and when it
                was read or set.
        """
        ...

    def list_predictions(self, user_id: UUID) -> list[Prediction]:
        """List the Predictions given to a User, oldest first.

        Args:
            user_id: The User's ID.

        Returns:
            The Predictions.
        """
        ...

    def add_reactions(self, reactions: Sequence[ReactionToPattern]) -> None:
        """Save how a User took Patterns in one Conversation.

        A Pattern keeps one reaction per Conversation: a second one read
        from the same Conversation is left out.

        Args:
            reactions: The reactions.
        """
        ...

    def list_reactions(self, user_id: UUID) -> list[ReactionToPattern]:
        """List how a User took the Patterns they were told, oldest first.

        Args:
            user_id: The User's ID.

        Returns:
            The reactions.
        """
        ...

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's Patterns, the log of their moves and "never again" marks.

        Args:
            user_id: The User's ID.
        """
        ...

    def mark_never_again(
        self, user_id: UUID, pattern_type_id: str, marked_at: datetime
    ) -> None:
        """Mark a Pattern Type as never to be noted or shared for a User again.

        Args:
            user_id: The User's ID.
            pattern_type_id: The Pattern Type's ID.
            marked_at: When it was marked; one already marked stays as it is.
        """
        ...

    def list_never_again(self, user_id: UUID) -> frozenset[str]:
        """List the Pattern Types never to be noted or shared for a User again.

        Args:
            user_id: The User's ID.

        Returns:
            Their IDs; none when the User marked none.
        """
        ...


class MoveOutcomeRepository(Protocol):
    """Stores each User's Move Outcomes, found by meaning."""

    def add_many(self, outcomes: Sequence[MoveOutcomeToSave]) -> None:
        """Save new Move Outcomes, in one step.

        Args:
            outcomes: The Move Outcomes, each with its embedding.
        """
        ...

    def list_for_user(self, user_id: UUID) -> list[MoveOutcome]:
        """List a User's Move Outcomes, newest made first.

        Args:
            user_id: The User's ID.

        Returns:
            The Move Outcomes.
        """
        ...

    def delete(self, user_id: UUID, outcome_id: UUID) -> bool:
        """Delete one of a User's Move Outcomes.

        Args:
            user_id: The User's ID.
            outcome_id: The Move Outcome's ID.

        Returns:
            True if it was deleted; False if the User has no such Move Outcome.
        """
        ...

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete every one of a User's Move Outcomes.

        Args:
            user_id: The User's ID.
        """
        ...

    def find_by_meaning(
        self,
        user_id: UUID,
        embedding: list[float],
        min_closeness: float,
        limit: int,
    ) -> list[MoveOutcome]:
        """Find a User's Move Outcomes closest in meaning to a search.

        Args:
            user_id: The User's ID; only their Move Outcomes are searched.
            embedding: The search's embedding.
            min_closeness: How close a Move Outcome's situation and feeling
                must be, from 0 to 1.
            limit: The most to return.

        Returns:
            The closest Move Outcomes, closest first.
        """
        ...


class UserPortraitRepository(Protocol):
    """Stores each User's User Portrait, and whether it must be written again.

    A save only lands when what it was written from was read after the last
    save or clear, so a deleted Portrait, or one written before a deletion,
    never comes back.
    """

    def find(self, user_id: UUID) -> UserPortrait | None:
        """Find a User's Portrait.

        Args:
            user_id: The User's ID.

        Returns:
            The Portrait; None if they have none, or it was cleared.
        """
        ...

    def save(self, portrait: UserPortrait) -> None:
        """Save a User's Portrait, unless a newer one or a clear came first.

        A rewrite asked for before its `written_at` is done by this save.

        Args:
            portrait: The Portrait; `written_at` is when what it was written
                from was read.
        """
        ...

    def clear(self, user_id: UUID, cleared_at: datetime) -> bool:
        """Clear a User's Portrait, so no Portrait written before now lands.

        Args:
            user_id: The User's ID.
            cleared_at: When it is being cleared.

        Returns:
            True if they had a Portrait.
        """
        ...

    def request_rewrite(self, user_id: UUID, requested_at: datetime) -> None:
        """Ask for a User's Portrait to be written again, after a deletion.

        Args:
            user_id: The User's ID.
            requested_at: When the deletion happened.
        """
        ...

    def list_rewrite_requests(self) -> list[UUID]:
        """List the Users whose Portrait must be written again.

        Returns:
            Their IDs, the longest waiting first.
        """
        ...

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's Portrait and any rewrite asked for.

        Args:
            user_id: The User's ID.
        """
        ...


class ExplorationRepository(Protocol):
    """Stores each User's Explorations and their tries, which are never shown.

    An Exploration goes with its Pattern, and a try with its aimed Curiosity.
    Saving the Agenda also adds and closes aimed Curiosities, so an
    Exploration's changes, tries and Curiosities are saved in one step.
    """

    def list_for_user(self, user_id: UUID) -> list[Exploration]:
        """List a User's Explorations, oldest first.

        Args:
            user_id: The User's ID.

        Returns:
            The Explorations.
        """
        ...

    def list_tries(self, user_id: UUID) -> list[ExplorationTry]:
        """List every try of a User's, oldest first.

        Args:
            user_id: The User's ID.

        Returns:
            The tries.
        """
        ...

    def save_agenda(self, changes: AgendaChanges) -> None:
        """Save what keeping a User's Agenda changed, in one step.

        A new aimed Curiosity whose Observation was deleted meanwhile is not
        added, nor is its try.

        Args:
            changes: The changes.
        """
        ...

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete every one of a User's Explorations and their tries.

        Args:
            user_id: The User's ID.
        """
        ...


class UnmatchedEntryRepository(Protocol):
    """Stores what keeps turning up that fits no Pattern Type, for Admins.

    An entry holds a general description and an Admin's mark, and no User.
    Unmatched Patterns are grouped under it by `patterns.unmatched_entry_id`.
    """

    def join_or_add(
        self,
        new_entry: UnmatchedEntry,
        embedding: list[float],
        min_closeness: float,
        created_at: datetime,
    ) -> UUID:
        """Find the entry a general description belongs under, or add one.

        Done one at a time across the whole platform, so two Conversations
        ending at the same moment never add two entries for the same thing.

        Args:
            new_entry: The entry to add when none is close enough, holding
                the general description.
            embedding: The general description embedded.
            min_closeness: How close in meaning an entry must be to be
                joined, from 0 to 1.
            created_at: When the new entry is added.

        Returns:
            The ID of the closest entry at least that close, the oldest
            first when two are as close; the new entry's ID if it was added.
        """
        ...

    def list_counted(self) -> list[CountedUnmatchedEntry]:
        """List the entries that appear for at least one User.

        A User counts once for an entry, however many of their unmatched
        Patterns are grouped under it; a Pattern the matching command
        linked to a Pattern Type doesn't count.

        Returns:
            The entries, most Users first, then oldest first.
        """
        ...

    def get_counted(self, entry_id: UUID) -> CountedUnmatchedEntry | None:
        """Get one entry with how many Users it appears for now.

        Args:
            entry_id: The entry's ID.

        Returns:
            The entry, also when it appears for no User; None if there is
            no such entry.
        """
        ...

    def save_mark(self, entry: UnmatchedEntry) -> None:
        """Save an entry's mark.

        Args:
            entry: The entry with its new mark, the Pattern Type it is
                folded into, the Users it appeared for and when.
        """
        ...


class ThoughtExperimentRepository(Protocol):
    """Stores the Thought Experiments Admins manage. None is ever deleted."""

    def list_all(self) -> list[ThoughtExperiment]:
        """List every Thought Experiment, archived ones too, oldest first.

        Returns:
            The Thought Experiments.
        """
        ...

    def get(self, thought_experiment_id: UUID) -> ThoughtExperiment | None:
        """Find one Thought Experiment.

        Args:
            thought_experiment_id: Its ID.

        Returns:
            It, or None if there is no such one.
        """
        ...

    def add(self, thought_experiment: ThoughtExperiment) -> None:
        """Store a new Thought Experiment.

        Args:
            thought_experiment: It, with its ID.
        """
        ...

    def update(
        self,
        thought_experiment_id: UUID,
        details: ThoughtExperimentDetails,
        now: datetime,
    ) -> ThoughtExperiment:
        """Change what an Admin set on a Thought Experiment.

        Args:
            thought_experiment_id: Its ID; it exists.
            details: Its new values.
            now: When it changed.

        Returns:
            It, saved.
        """
        ...

    def archive(self, thought_experiment_id: UUID, now: datetime) -> ThoughtExperiment:
        """Archive a Thought Experiment, so it is never asked again.

        Args:
            thought_experiment_id: Its ID; it exists.
            now: When it was archived.

        Returns:
            It, saved.
        """
        ...

    def close_waiting(self, thought_experiment_id: UUID) -> None:
        """Close every waiting Curiosity that would put it to a User.

        Both an Exploration's try and a starter for a new User.

        Args:
            thought_experiment_id: Its ID.
        """
        ...

    def asked_counts(self) -> dict[UUID, int]:
        """Count how many times each Thought Experiment was put to a User.

        Returns:
            How many of its Curiosities were asked, by its ID, whether for an
            Exploration or as a starter; one never asked is left out.
        """
        ...


class CuriosityRepository(Protocol):
    """Stores each User's Curiosities, which are internal and never shown.

    Deleting the Memory Item or Life Thread a Curiosity came from deletes
    the Curiosity too, however the item or Thread is deleted.
    """

    def list_waiting(self, user_id: UUID) -> list[Curiosity]:
        """List a User's waiting Curiosities, oldest first.

        Args:
            user_id: The User's ID.

        Returns:
            The Curiosities.
        """
        ...

    def list_raised_in(self, conversation_id: UUID) -> list[Curiosity]:
        """List the Curiosities raised in a Conversation, first raised first.

        Args:
            conversation_id: The Conversation's ID.

        Returns:
            The Curiosities.
        """
        ...

    def list_aimed(self, user_id: UUID) -> list[Curiosity]:
        """List a User's aimed Curiosities, in any state, oldest first.

        Args:
            user_id: The User's ID.

        Returns:
            The Curiosities with the aim of an Exploration's need.
        """
        ...

    def list_starters(self, user_id: UUID) -> list[Curiosity]:
        """List a User's starter Thought Experiment Curiosities, oldest first.

        Args:
            user_id: The User's ID.

        Returns:
            The Curiosities with the starter aim, in any state.
        """
        ...

    def list_about_predictions(self, user_id: UUID) -> list[Curiosity]:
        """List a User's Curiosities about Predictions, oldest first.

        Args:
            user_id: The User's ID.

        Returns:
            The Curiosities with the Prediction aim, in any state.
        """
        ...

    def list_recently_raised(self, user_id: UUID, limit: int) -> list[Curiosity]:
        """List the Curiosities most recently raised with a User, newest first.

        Args:
            user_id: The User's ID.
            limit: The most to return.

        Returns:
            The Curiosities.
        """
        ...

    def list_asked_to_drop(self, user_id: UUID) -> list[Curiosity]:
        """List the Curiosities a User asked Zeph to drop, newest raised first.

        Args:
            user_id: The User's ID.

        Returns:
            The Curiosities.
        """
        ...

    def save_changes(self, changes: CuriosityChanges) -> None:
        """Add, update and record reactions to Curiosities, in one step.

        A new one whose Memory Item or Life Thread was deleted meanwhile is
        not added. An updated one is saved only while it is still waiting,
        and a reaction only on one that was raised.

        Args:
            changes: The changes.
        """
        ...

    def list_waiting_for_users(
        self, user_ids: Sequence[UUID]
    ) -> dict[UUID, list[Curiosity]]:
        """List many Users' waiting Curiosities, in one query.

        Args:
            user_ids: The Users' IDs.

        Returns:
            Each User's waiting Curiosities, oldest first; a User with none
            is left out.
        """
        ...

    def mark_raised(
        self,
        curiosity_ids: Sequence[UUID],
        conversation_id: UUID | None,
        raised_at: datetime,
    ) -> None:
        """Note that waiting Curiosities were just raised.

        Args:
            curiosity_ids: The Curiosities' IDs; any no longer waiting is
                left as it is.
            conversation_id: The Conversation they were raised in; None when
                a Check-in raised them and no Conversation has started yet.
            raised_at: When the reply or Check-in that raised them was sent.
        """
        ...

    def link_to_conversation(self, curiosity_id: UUID, conversation_id: UUID) -> None:
        """Note the Conversation a Check-in's Curiosity was raised in.

        Args:
            curiosity_id: The Curiosity's ID; left as it is unless it was
                raised with no Conversation.
            conversation_id: The Conversation the User's reply started.
        """
        ...

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete every one of a User's Curiosities.

        Args:
            user_id: The User's ID.
        """
        ...


class UserMemoryRepository(Protocol):
    """Stores each User's Memory Items, Day Summaries and Shared Photos."""

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
    ) -> list[DaySummary]:
        """List a User's Day Summaries, newest day first.

        Args:
            user_id: The User's ID.
            limit: The most to return; None for all of them.

        Returns:
            The Day Summaries.
        """
        ...

    def list_summaries_for_days(
        self, user_id: UUID, days: Sequence[date]
    ) -> list[DaySummary]:
        """List a User's Day Summaries of some days.

        Args:
            user_id: The User's ID.
            days: The days, in the User's time zone.

        Returns:
            The Summaries those days have, newest day first.
        """
        ...

    def find_summaries_by_meaning(
        self,
        user_id: UUID,
        embeddings: Sequence[list[float]],
        min_closeness: float,
        limit: int,
        leave_out: Sequence[UUID],
    ) -> list[DaySummary]:
        """Find a User's Day Summaries closest in meaning to any search.

        Closeness is cosine similarity. Summaries with no embedding are never
        found.

        Args:
            user_id: The User's ID; only their Summaries are searched.
            embeddings: The searches, one embedding each.
            min_closeness: How close a Summary must be to one search, from 0
                to 1.
            limit: The most to return.
            leave_out: Summaries not to return, e.g. ones already given.

        Returns:
            The closest Summaries, closest first.
        """
        ...

    def delete_summary(self, user_id: UUID, summary_id: UUID) -> bool:
        """Delete one of a User's Day Summaries.

        Args:
            user_id: The User's ID.
            summary_id: The Day Summary's ID.

        Returns:
            True if it was deleted; False if the User has no such summary.
        """
        ...

    def save_processed_conversation(
        self,
        conversation_id: UUID,
        processed_at: datetime,
        summary: DaySummary | None,
        changes: MemoryChanges,
        summary_embedding: list[float] | None = None,
    ) -> None:
        """Save what processing an ended Conversation produced, in one step.

        The Conversation is marked processed at the same time, so it is
        never processed twice. The Day Summary replaces the one already
        kept for the User's day, keeping its ID.

        Args:
            conversation_id: The Conversation that was processed.
            processed_at: When processing finished.
            summary: The rewritten Day Summary of the day the Conversation
                started; None when nothing is saved.
            changes: The changes to the User's Memory Items and the new
                Shared Photos.
            summary_embedding: The Summary's embedding, so it can be found
                by meaning; None if it has none.
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
        """Delete a User's Memory Items, Day Summaries and Shared Photos.

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


class CopyRepository(Protocol):
    """Stores website Copy, kept apart from platform settings (ADR-0019)."""

    def list_slots(self) -> list[CopySlot]:
        """List every slot, by tab order and then page order.

        Returns:
            The slots, with when and by whom each was last saved.
        """
        ...

    def texts(self) -> dict[str, str]:
        """Read every slot's current text.

        Returns:
            Each slot's text by key.
        """
        ...

    def save_texts(
        self, texts: Mapping[str, str], updated_at: datetime, updated_by: UUID
    ) -> None:
        """Save new texts for several slots in one step.

        Args:
            texts: The new text for each slot key.
            updated_at: When they are being saved.
            updated_by: The Admin saving them.
        """
        ...

    def sync_with_seed(self, seed: Sequence[CopySeedSlot], now: datetime) -> None:
        """Make the stored slots follow the seed, in one step.

        Slots not stored yet are added with the seed text. Stored slots keep
        their text; their name, tab, order, max length and placeholders take
        the seed's. Stored slots missing from the seed are removed.

        Args:
            seed: Every slot the seed file defines.
            now: When new slots are added.
        """
        ...


class PatternCatalogRepository(Protocol):
    """Stores every loaded version of each Pattern Type (ADR-0025)."""

    def list_versions(self) -> list[PatternTypeVersion]:
        """List every stored version of every Pattern Type.

        Returns:
            The versions, by Pattern Type ID and then newest loaded first.
        """
        ...

    def save_loaded(self, versions: Sequence[PatternTypeVersion]) -> None:
        """Keep the versions just loaded as the catalog, in one step.

        A version not stored yet is added. Versions stored earlier stay as
        they were. Exactly the given versions are then the current ones.

        Args:
            versions: The version of each Pattern Type its file now holds.
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

    def happened_since(self, user_id: UUID, since: datetime) -> bool:
        """Say whether a User had a Safeguard Event after a time.

        Args:
            user_id: The User's ID.
            since: The time; events at it or before are left out.

        Returns:
            True when there is one.
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

    def set_understanding_shape(
        self, trace_id: UUID, shape: UnderstandingShape
    ) -> None:
        """Save the Understanding's shape on a trace's newest Understanding call.

        Args:
            trace_id: The trace's ID.
            shape: The Understanding's shape.
        """
        ...

    def set_reply_plan_shape(self, trace_id: UUID, shape: ReplyPlanShape) -> None:
        """Save the Reply Plan's shape on a trace's newest Reply Plan call.

        Args:
            trace_id: The trace's ID.
            shape: The Reply Plan's shape.
        """
        ...

    def set_check_in_shape(self, trace_id: UUID, shape: CheckInShape) -> None:
        """Save a woven-in Check-in decision's shape on a trace's newest Check-in call.

        Args:
            trace_id: The trace's ID.
            shape: The decision's shape.
        """
        ...

    def set_tagging_shape(self, trace_id: UUID, shape: TaggingShape) -> None:
        """Save a Pattern tagging call's shape on a trace's newest tagging call.

        Args:
            trace_id: The trace's ID.
            shape: How many Observations were tagged and dropped.
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

    def fill_blank_when_it_helps(self, document_id: UUID, when_it_helps: str) -> None:
        """Save a Knowledge document's "when it helps" only if it is still blank.

        Checked in the same step as the save, so a description an Admin
        saved meanwhile is never overwritten.

        Args:
            document_id: The document's ID.
            when_it_helps: The description.
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
        them, are left out but stay due, unless a Check in Now is waiting.
        Pause and quiet hours are not checked here.

        Args:
            now: The time to check at.

        Returns:
            The Users whose next due time is at or before now; a User with no
            due time is never due.
        """
        ...

    def list_opted_in_users(self, search: str, limit: int, offset: int) -> UserPage:
        """List one page of the Users who opted in to Check-ins.

        Args:
            search: Only Users whose name or email holds this, in any case;
                "" for every one.
            limit: The most Users on the page.
            offset: How many matching Users come before the page.

        Returns:
            The page, soonest Due Time first and Users with none last, and
            how many Users match.
        """
        ...

    def save_next_due_times(self, changes: Sequence[NextDueTimeChange]) -> None:
        """Save many Users' next due times, and why each is held back, in one statement.

        A User whose due time changed since it was read is left as it is, so
        a settings change made meanwhile is kept. The Due Time a User was
        first held back at is kept, so their rhythm counts from it.

        Args:
            changes: Each User's due time as read, the one to save, and why
                they are held back.
        """
        ...

    def request_check_ins_now(
        self, user_ids: Sequence[UUID], requested_by: UUID, now: datetime
    ) -> None:
        """Save a Check in Now on many Users and make them due now, in one statement.

        Making them due now ends any hold back, so why it was held back is
        cleared.

        Args:
            user_ids: The Users' IDs.
            requested_by: The Admin who asked.
            now: When they asked.
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
        self,
        check_in: CheckIn,
        due_at_read: datetime | None,
        next_due_at: datetime,
        pause_until_resumed: bool,
        check_in_now: CheckInNowRequest | None = None,
    ) -> bool:
        """Save a Check-in decision and the User's next due time, if still due.

        Nothing is saved if their due time changed since it was read, e.g.
        because a reply wove this Check-in in already. A decision ends any
        hold back, so why it was held back and the Due Time they were first
        held back at are cleared. The Check in Now it was decided for is
        cleared too; one asked for since is kept.

        Only the next due time and, when asked, the pause are changed, so
        settings the User changed meanwhile are kept.

        Args:
            check_in: The Check-in decision.
            due_at_read: The User's due time as read for the decision.
            next_due_at: When the User's next Check-in may be sent.
            pause_until_resumed: Whether to also pause the User's Check-ins
                until they resume.
            check_in_now: The Check in Now it was decided for; None for a
                scheduled one.

        Returns:
            True if it was saved.
        """
        ...

    def add_woven_in(
        self,
        check_in: CheckIn,
        due_at_read: datetime,
        next_due_at: datetime,
        check_in_now: CheckInNowRequest | None = None,
    ) -> bool:
        """Save a Woven-in Check-in and the User's next due time, if still due.

        Nothing is saved if their due time changed since it was read, e.g.
        because a tick or another reply decided on this Check-in already. A
        decision ends any hold back, so why it was held back and the Due
        Time they were first held back at are cleared. The Check in Now it
        was woven in for is cleared too; one asked for since is kept.

        Args:
            check_in: The Woven-in Check-in.
            due_at_read: The User's due time as read for the reply.
            next_due_at: When the User's next Check-in may be sent.
            check_in_now: The Check in Now it was woven in for; None for a
                scheduled one.

        Returns:
            True if it was saved.
        """
        ...

    def undo_add(
        self,
        check_in: CheckIn,
        next_due_at: datetime,
        end_pause: bool,
        skipped: CheckIn | None,
        held_back_due_at: datetime | None,
        check_in_now: CheckInNowRequest | None,
    ) -> None:
        """Take back a saved Check-in that was never sent, together.

        Only the next due time, the Due Time they were first held back at,
        any Check in Now and, when asked, the pause are changed, so settings
        the User changed meanwhile are kept.

        Args:
            check_in: The saved Check-in to remove.
            next_due_at: When the User's next Check-in may be sent.
            end_pause: Whether to end the pause that saving it started.
            skipped: A Skipped Check-in to save in its place; None for none.
            held_back_due_at: The Due Time it was first due at, so the next
                one keeps the rhythm; None for none.
            check_in_now: The Check in Now it was sent for, put back to wait
                again; None for none.
        """
        ...

    def remove_shared_photo(self, check_in_id: UUID) -> None:
        """Mark a sent Check-in as having sent no Shared Photo.

        Args:
            check_in_id: The Check-in's ID.
        """
        ...

    def count_curiosity_check_ins_since(
        self, user_ids: Sequence[UUID], since: datetime
    ) -> dict[UUID, int]:
        """Count many Users' sent Check-ins that asked a Curiosity, in one query.

        Args:
            user_ids: The Users' IDs.
            since: Only Check-ins sent after this are counted.

        Returns:
            Each User's count; a User with none is left out.
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
            The decisions with who each User is and, for a Check in Now,
            which Admin asked.
        """
        ...

    def claim_reply(
        self,
        user_id: UUID,
        replied_at: datetime,
        sent_since: datetime,
        woven_in_only: bool = False,
    ) -> CheckIn | None:
        """Mark the User's newest sent Check-in replied, if it can still be.

        Skipped Check-ins are passed over, since nothing was sent.

        Args:
            user_id: The User's ID.
            replied_at: When they replied.
            sent_since: A Check-in sent at or before this can't get a reply.
            woven_in_only: Whether only a Woven-in Check-in may be claimed.

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
    copy: CopyRepository
    pattern_catalog: PatternCatalogRepository
    helplines: HelplineRepository
    safeguard_events: SafeguardEventRepository
    memory_categories: MemoryCategoryRepository
    needs: NeedRepository
    moves: MoveRepository
    understandings: UnderstandingRepository
    reply_plans: ReplyPlanRepository
    user_memory: UserMemoryRepository
    life_threads: LifeThreadRepository
    patterns: PatternRepository
    observations: ObservationRepository
    curiosities: CuriosityRepository
    explorations: ExplorationRepository
    thought_experiments: ThoughtExperimentRepository
    unmatched_entries: UnmatchedEntryRepository
    move_outcomes: MoveOutcomeRepository
    user_portraits: UserPortraitRepository
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

    def lock_user(self, user_id: UUID) -> None:
        """Lock one User until the transaction ends.

        Another transaction locking them waits for this one, then sees its
        changes. Scoring their Patterns and deleting their Observations take
        it, so neither works from what the other is changing.

        Args:
            user_id: The User's ID.
        """
        ...
