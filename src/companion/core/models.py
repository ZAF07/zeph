from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class AccountIdentity:
    """Who a Dashboard request is from, as told by the auth provider.

    Attributes:
        auth_id: The auth provider's ID for the account (the Clerk user ID).
        email: The account's email address, if known.
    """

    auth_id: str
    email: str | None


class UserRole(StrEnum):
    """What a User may do on the platform."""

    USER = "user"
    ADMIN = "admin"


@dataclass(frozen=True)
class User:
    """A person with an account who converses with the Companion.

    Attributes:
        id: Our ID for the User.
        auth_id: The auth provider's ID for the account; unique per User.
        email: The User's email address, if known.
        created_at: When the User signed up.
        name: What the Companion calls the User, once they have said.
        onboarding_reasons: The "What brings you here?" choices they picked.
        onboarding_note: What brings them here, in their own words, if given.
        country: Two-letter country code, used to pick Helplines.
        time_zone: IANA time zone name, e.g. "Asia/Singapore".
        ai_notice_acknowledged_at: When they ticked "I understand" on the
            AI notice, if they have.
        user_memory_enabled: Whether the Companion may keep User Memory.
        onboarding_completed_at: When they finished onboarding, if they have.
        role: Whether they are a plain User or an Admin.
    """

    id: UUID
    auth_id: str
    email: str | None
    created_at: datetime
    name: str | None = None
    onboarding_reasons: tuple[str, ...] = ()
    onboarding_note: str | None = None
    country: str | None = None
    time_zone: str | None = None
    ai_notice_acknowledged_at: datetime | None = None
    user_memory_enabled: bool = True
    onboarding_completed_at: datetime | None = None
    role: UserRole = UserRole.USER


@dataclass(frozen=True)
class UserOverview:
    """What Admins see about a User: activity counts, never message text.

    Attributes:
        user: The User.
        telegram_connected: Whether they have a Telegram Connection.
        conversation_count: How many Conversations they have had.
        messages_sent: How many messages they have sent the Companion.
    """

    user: User
    telegram_connected: bool
    conversation_count: int
    messages_sent: int


@dataclass(frozen=True)
class OnboardingAnswers:
    """What a new User told the Dashboard during onboarding.

    Attributes:
        name: What the Companion should call them.
        ai_notice_acknowledged: Whether they ticked "I understand".
        onboarding_reasons: The "What brings you here?" choices they picked.
        onboarding_note: What brings them here, in their own words.
        user_memory_enabled: Whether the Companion may keep User Memory.
        country: Two-letter country code.
        time_zone: IANA time zone name.
    """

    name: str
    ai_notice_acknowledged: bool
    onboarding_reasons: tuple[str, ...]
    onboarding_note: str | None
    user_memory_enabled: bool
    country: str
    time_zone: str


@dataclass(frozen=True)
class PreferenceChanges:
    """Preferences a User wants to change; None means leave it as it is.

    Attributes:
        name: What the Companion should call them.
        user_memory_enabled: Whether the Companion may keep User Memory.
        country: Two-letter country code.
        time_zone: IANA time zone name.
    """

    name: str | None = None
    user_memory_enabled: bool | None = None
    country: str | None = None
    time_zone: str | None = None


@dataclass(frozen=True)
class TelegramConnection:
    """The link between a User and their Telegram account.

    Attributes:
        user_id: The User this connection belongs to.
        telegram_user_id: The Telegram account's ID; linked to one User only.
        telegram_chat_id: The chat the Companion sends messages to.
        telegram_username: The Telegram @username, if the account has one.
        connected_at: When the connection was made.
    """

    user_id: UUID
    telegram_user_id: int
    telegram_chat_id: int
    telegram_username: str | None
    connected_at: datetime


class ConnectionTokenStatus(StrEnum):
    """Where a connection token stands."""

    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"
    CONNECTED_ELSEWHERE = "connected_elsewhere"


@dataclass(frozen=True)
class ConnectionToken:
    """A one-time, expiring code a User sends to the Companion to connect Telegram.

    Attributes:
        user_id: The User who asked for the token.
        token: The code itself, e.g. "7Q2K-ZEPH".
        created_at: When the token was made.
        expires_at: When the token stops working.
        used_at: When the token made a Telegram Connection, if it has.
        rejected_at: When the token was refused because the Telegram account
            already belongs to another User, if it was.
    """

    user_id: UUID
    token: str
    created_at: datetime
    expires_at: datetime
    used_at: datetime | None
    rejected_at: datetime | None

    def status_at(self, now: datetime) -> ConnectionTokenStatus:
        """Work out the token's status at a given time.

        Args:
            now: The time to check at.

        Returns:
            The token's status.
        """
        if self.used_at is not None:
            return ConnectionTokenStatus.USED
        if self.rejected_at is not None:
            return ConnectionTokenStatus.CONNECTED_ELSEWHERE
        if now >= self.expires_at:
            return ConnectionTokenStatus.EXPIRED
        return ConnectionTokenStatus.ACTIVE


@dataclass(frozen=True)
class IncomingMessage:
    """A message a person sent to the Companion, independent of chat channel.

    Attributes:
        sender_id: The sender's account ID on the chat channel.
        chat_id: The chat to reply in.
        sender_username: The sender's username on the chat channel, if any.
        text: The message text.
    """

    sender_id: int
    chat_id: int
    sender_username: str | None
    text: str


class MessageDirection(StrEnum):
    """Who a message in a Conversation came from."""

    INCOMING = "incoming"
    OUTGOING = "outgoing"


class MessageKind(StrEnum):
    """What kind of message it is."""

    TEXT = "text"


@dataclass(frozen=True)
class Conversation:
    """A run of messages between a User and the Companion.

    A Conversation ends once the quiet gap passes with no new message.

    Attributes:
        id: Our ID for the Conversation.
        user_id: The User taking part.
        started_at: When the first message was sent.
        last_message_at: When the newest message was sent.
        ended_at: When the scheduler saw the quiet gap pass and ended it; a
            later message starts a new Conversation.
    """

    id: UUID
    user_id: UUID
    started_at: datetime
    last_message_at: datetime
    ended_at: datetime | None = None


@dataclass(frozen=True)
class ConversationMessage:
    """One saved message in a Conversation.

    Attributes:
        id: Our ID for the message.
        conversation_id: The Conversation it belongs to.
        direction: Whether the User sent it or the Companion did.
        kind: What kind of message it is.
        content: The message text.
        sent_at: When it was sent.
    """

    id: UUID
    conversation_id: UUID
    direction: MessageDirection
    kind: MessageKind
    content: str
    sent_at: datetime


@dataclass(frozen=True)
class ConversationTurn:
    """A connected User's message that the Companion should answer.

    Attributes:
        user_id: The User who sent it.
        chat_id: The chat to reply in.
        text: The message text.
    """

    user_id: UUID
    chat_id: int
    text: str


class ChatRole(StrEnum):
    """Who said a line in the history given to the chat model."""

    USER = "user"
    COMPANION = "companion"


@dataclass(frozen=True)
class ChatLine:
    """One line of history given to the chat model.

    Attributes:
        role: Who said it.
        text: What was said.
    """

    role: ChatRole
    text: str


@dataclass(frozen=True)
class StoredSetting:
    """A platform setting's value and when it was last saved.

    Attributes:
        key: The setting's key.
        value: Its value.
        updated_at: When it was last saved.
        updated_by_name: The name, or else email, of the Admin who last saved
            it; None if it still has its seeded value.
    """

    key: str
    value: Any
    updated_at: datetime
    updated_by_name: str | None


class RiskType(StrEnum):
    """What kind of crisis the Safeguard sees in a message, if any.

    `UNCLEAR` means the model twice gave no label; it is treated as a crisis,
    because missing a real one is worse than a false alarm.
    """

    NONE = "none"
    SUICIDE_OR_SELF_HARM = "suicide_or_self_harm"
    DANGER_TO_OTHERS = "danger_to_others"
    ABUSE = "abuse"
    MEDICAL_EMERGENCY = "medical_emergency"
    UNCLEAR = "unclear"


@dataclass(frozen=True)
class HelplineDetails:
    """What an Admin enters for a Helpline.

    Attributes:
        name: The Helpline's name, e.g. "Samaritans of Singapore (SOS)".
        number: The phone number, or a web address for a directory.
        hours: When it is open, e.g. "24 hours", if known.
    """

    name: str
    number: str
    hours: str | None


@dataclass(frozen=True)
class Helpline:
    """A crisis support contact shared in the Crisis Reply.

    Attributes:
        id: Our ID for the Helpline.
        country: Two-letter country code; None for the international fallback.
        details: Its name, number and hours.
        sort_order: Where it comes in its country's list, lowest first.
    """

    id: UUID
    country: str | None
    details: HelplineDetails
    sort_order: int


@dataclass(frozen=True)
class HelplinesToShare:
    """The Helplines a Crisis Reply shares with one User.

    Attributes:
        helplines: The Helplines, in order.
        country: The country they are for; None when they are the
            international fallback.
    """

    helplines: list[Helpline]
    country: str | None


@dataclass(frozen=True)
class SafeguardEvent:
    """A record that the Safeguard detected a crisis. Never holds message text.

    Attributes:
        id: Our ID for the event.
        user_id: The User it happened for.
        risk_type: What kind of crisis it was.
        created_at: When it happened.
        helplines_country: The country whose Helplines were shared; None if
            the international fallback was shared instead.
    """

    id: UUID
    user_id: UUID
    risk_type: RiskType
    created_at: datetime
    helplines_country: str | None


@dataclass(frozen=True)
class SafeguardEventOverview:
    """A Safeguard Event as Admins see it, with who the User is.

    Attributes:
        event: The event.
        user_name: The User's name, if they have given one.
        user_email: The User's email, if known.
    """

    event: SafeguardEvent
    user_name: str | None
    user_email: str | None


@dataclass(frozen=True)
class MemoryCategory:
    """The kind of fact a Memory Item records. Managed by Admins.

    Attributes:
        id: Our ID for the category.
        name: Its name, e.g. "Goals".
        description: What belongs in it, as the chat model is told.
        always_include: Whether its Memory Items go into every reply.
        archived: Whether it is archived: it keeps its Memory Items but gets
            no new ones.
        sort_order: Where it comes in the list, lowest first.
    """

    id: UUID
    name: str
    description: str
    always_include: bool
    archived: bool
    sort_order: int


@dataclass(frozen=True)
class MemoryCategoryDetails:
    """A Memory Category's details, as an Admin enters them.

    Attributes:
        name: Its name, e.g. "Work".
        description: What belongs in it, as the chat model is told.
        always_include: Whether its Memory Items go into every reply.
    """

    name: str
    description: str
    always_include: bool


@dataclass(frozen=True)
class MemoryCategoryOverview:
    """A Memory Category and how many Memory Items, across all Users, it has.

    Attributes:
        category: The Memory Category.
        item_count: How many Memory Items are in it.
    """

    category: MemoryCategory
    item_count: int


class MemorySource(StrEnum):
    """Where a Memory Item came from."""

    CONVERSATION = "conversation"
    ONBOARDING = "onboarding"


@dataclass(frozen=True)
class MemoryItem:
    """A single fact about a User, in one Memory Category.

    Attributes:
        id: Our ID for the item.
        user_id: The User it is about.
        category_id: The Memory Category it belongs to.
        content: The fact, e.g. "Started a new role in September".
        source: Where it came from.
        source_conversation_id: The Conversation it was last learned in, if
            it came from one.
        created_at: When it was first saved.
        updated_at: When it was last changed.
    """

    id: UUID
    user_id: UUID
    category_id: UUID
    content: str
    source: MemorySource
    source_conversation_id: UUID | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class MemoryChanges:
    """What post-conversation processing changes in a User's Memory Items.

    Attributes:
        added: New Memory Items to save.
        updated: Existing Memory Items with their new content and category.
        removed_ids: IDs of Memory Items to delete.
    """

    added: list[MemoryItem]
    updated: list[MemoryItem]
    removed_ids: list[UUID]


@dataclass(frozen=True)
class MemoryGroup:
    """A User's Memory Items in one Memory Category.

    Attributes:
        category: The Memory Category.
        items: Its Memory Items, oldest first.
    """

    category: MemoryCategory
    items: list[MemoryItem]


@dataclass(frozen=True)
class ConversationSummary:
    """A short account of what one Conversation covered and how the User seemed.

    Attributes:
        id: Our ID for the summary.
        conversation_id: The Conversation it sums up.
        user_id: The User who took part.
        summary: What was talked about.
        mood: How the User seemed, e.g. "unsettled at first, then calmer".
        created_at: When it was written.
    """

    id: UUID
    conversation_id: UUID
    user_id: UUID
    summary: str
    mood: str
    created_at: datetime


class KnowledgeFileType(StrEnum):
    """The kinds of file a Knowledge document can be uploaded as."""

    TEXT = "text"
    MARKDOWN = "markdown"
    PDF = "pdf"


class KnowledgeStatus(StrEnum):
    """Where a Knowledge document is in being made ready for replies."""

    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"


@dataclass(frozen=True)
class KnowledgeUpload:
    """A Knowledge document as an Admin uploads it.

    Attributes:
        title: Its title, e.g. "Dhammapada".
        source: Who wrote or translated it, e.g. "Seneca, trans. Gummere".
        tradition: The tradition it belongs to, e.g. "Buddhism".
        file_name: The uploaded file's name.
        file_type: What kind of file it is.
        content: The file's bytes.
    """

    title: str
    source: str
    tradition: str
    file_name: str
    file_type: KnowledgeFileType
    content: bytes


@dataclass(frozen=True)
class KnowledgeDocument:
    """A document in the Knowledge library, without its file.

    Attributes:
        id: Our ID for the document.
        title: Its title.
        source: Who wrote or translated it.
        tradition: The tradition it belongs to.
        file_name: The uploaded file's name.
        file_type: What kind of file it was.
        status: Whether it is pending, ready for replies, or failed.
        failure_reason: Why it failed, as Admins are told; None unless failed.
        text_edited: Whether an Admin edited its text since it was last read
            from its file.
        created_at: When it was uploaded.
    """

    id: UUID
    title: str
    source: str
    tradition: str
    file_name: str
    file_type: KnowledgeFileType
    status: KnowledgeStatus
    failure_reason: str | None
    text_edited: bool
    created_at: datetime


@dataclass(frozen=True)
class KnowledgeDocumentWithText:
    """A Knowledge document with the text replies draw on.

    Attributes:
        document: The document.
        text: The text read from its file or edited by an Admin; None until
            its file has been read.
    """

    document: KnowledgeDocument
    text: str | None


@dataclass(frozen=True)
class EmbeddedChunk:
    """One piece of a Knowledge document, with its embedding.

    Attributes:
        text: The piece's text.
        embedding: Its embedding, from the embedder.
    """

    text: str
    embedding: list[float]


@dataclass(frozen=True)
class KnowledgeChunkMatch:
    """A Knowledge chunk found by a search, best match first.

    Attributes:
        document_id: The document the chunk is from.
        text: The chunk's text.
    """

    document_id: UUID
    text: str
