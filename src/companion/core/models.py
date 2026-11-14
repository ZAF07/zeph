from dataclasses import dataclass, field
from datetime import date, datetime, time
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


class CheckInFrequency(StrEnum):
    """How often, at most, the Companion may send a User a Check-in."""

    WEEKLY = "weekly"
    FEW_TIMES_A_WEEK = "few_times_a_week"
    MOST_DAYS = "most_days"


class PauseLength(StrEnum):
    """How long a User pauses their Check-ins for."""

    DAY = "day"
    WEEK = "week"
    UNTIL_RESUMED = "until_resumed"


@dataclass(frozen=True)
class CheckInSettings:
    """A User's Check-in settings.

    Attributes:
        enabled: Whether the User opted in to Check-ins.
        frequency: How often, at most, a Check-in may be sent.
        quiet_hours_start: Local time when quiet hours begin.
        quiet_hours_end: Local time when quiet hours end; earlier than the
            start when quiet hours run past midnight.
        paused: Whether the User paused their Check-ins.
        paused_until: When a timed pause ends; None while paused means until
            the User resumes.
        next_due_at: When the next Check-in may be sent; never shown to the
            User.
    """

    enabled: bool = False
    frequency: CheckInFrequency = CheckInFrequency.FEW_TIMES_A_WEEK
    quiet_hours_start: time = time(22, 0)
    quiet_hours_end: time = time(7, 30)
    paused: bool = False
    paused_until: datetime | None = None
    next_due_at: datetime | None = None

    def is_paused_at(self, now: datetime) -> bool:
        """Tell whether Check-ins are paused at a given time.

        Args:
            now: The time to check at.

        Returns:
            True while paused; a timed pause ends by itself.
        """
        if not self.paused:
            return False
        return self.paused_until is None or now < self.paused_until


@dataclass(frozen=True)
class CheckInChanges:
    """Check-in settings a User wants to change; None leaves one as it is.

    Attributes:
        enabled: Whether Check-ins are on.
        frequency: How often, at most, a Check-in may be sent.
        quiet_hours_start: Local time when quiet hours begin.
        quiet_hours_end: Local time when quiet hours end.
    """

    enabled: bool | None = None
    frequency: CheckInFrequency | None = None
    quiet_hours_start: time | None = None
    quiet_hours_end: time | None = None


class ChatSetting(StrEnum):
    """A setting a User can change by telling the Companion in chat."""

    CHECK_IN_PAUSE = "check_in_pause"
    CHECK_IN_FREQUENCY = "check_in_frequency"
    QUIET_HOURS = "quiet_hours"
    USER_MEMORY = "user_memory"
    PHOTO_VIEWING = "photo_viewing"
    TIME_ZONE = "time_zone"


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
        photo_viewing_enabled: Whether the Companion may look at their photos.
        onboarding_completed_at: When they finished onboarding, if they have.
        role: Whether they are a plain User or an Admin.
        check_ins: Their Check-in settings.
        settings_changed_in_chat: When each setting was last changed in chat;
            a setting is left out once it is changed on the Dashboard.
        data_deletion_requested_at: When they asked in chat to delete their
            data and are yet to reply with the confirmation word; None if not.
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
    photo_viewing_enabled: bool = True
    onboarding_completed_at: datetime | None = None
    role: UserRole = UserRole.USER
    check_ins: CheckInSettings = field(default_factory=CheckInSettings)
    settings_changed_in_chat: dict[ChatSetting, datetime] = field(default_factory=dict)
    data_deletion_requested_at: datetime | None = None

    @property
    def has_finished_onboarding(self) -> bool:
        """Tell whether the User has finished onboarding.

        Returns:
            True once onboarding is done.
        """
        return self.onboarding_completed_at is not None


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
        check_ins: Their Check-in choices; left as they are by default.
    """

    name: str
    ai_notice_acknowledged: bool
    onboarding_reasons: tuple[str, ...]
    onboarding_note: str | None
    user_memory_enabled: bool
    country: str
    time_zone: str
    check_ins: CheckInChanges = field(default_factory=CheckInChanges)


@dataclass(frozen=True)
class PreferenceChanges:
    """Preferences a User wants to change; None means leave it as it is.

    Attributes:
        name: What the Companion should call them.
        user_memory_enabled: Whether the Companion may keep User Memory.
        photo_viewing_enabled: Whether the Companion may look at their photos.
        country: Two-letter country code.
        time_zone: IANA time zone name.
    """

    name: str | None = None
    user_memory_enabled: bool | None = None
    photo_viewing_enabled: bool | None = None
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


class MessageKind(StrEnum):
    """What kind of message it is."""

    TEXT = "text"
    STICKER = "sticker"
    PHOTO = "photo"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ChannelSticker:
    """A sticker as the chat channel knows it.

    Attributes:
        file_id: The ID used to send the sticker.
        file_unique_id: The ID that stays the same for the same sticker, used
            to tell whether it is already in the Sticker Library.
        emoji: The emoji the sticker stands for, if it has one.
        set_name: The sticker set it belongs to, if any.
        preview_file_id: The ID of an image of the sticker for the Dashboard;
            None if it has no image a browser can show.
    """

    file_id: str
    file_unique_id: str
    emoji: str | None
    set_name: str | None
    preview_file_id: str | None


@dataclass(frozen=True)
class ChannelPhoto:
    """A photo as the chat channel knows it. We keep only these IDs, never the image.

    Attributes:
        file_id: The ID used to download or send the photo.
        file_unique_id: The ID that stays the same for the same photo.
        too_big_to_download: True when the chat channel won't let the bot
            download it, so it can't be viewed.
        viewed: True once the Companion has looked at it and described it.
        description: What it shows, once described; "" until then.
        caption: The caption it came with, or its album's caption; "" if none.
    """

    file_id: str
    file_unique_id: str
    too_big_to_download: bool = False
    viewed: bool = False
    description: str = ""
    caption: str = ""


@dataclass(frozen=True)
class PhotoImage:
    """A photo's image, downloaded to be looked at and never kept.

    Attributes:
        content: The image's bytes.
        media_type: Its media type, e.g. "image/jpeg".
    """

    content: bytes
    media_type: str


@dataclass(frozen=True)
class IncomingMessage:
    """A message a person sent to the Companion, independent of chat channel.

    Attributes:
        sender_id: The sender's account ID on the chat channel.
        chat_id: The chat to reply in.
        sender_username: The sender's username on the chat channel, if any.
        text: The message text, or a photo's or file's caption; "" if none.
        kind: Whether it is text, a sticker, a photo, or something the
            Companion can't read yet, like a voice note or video.
        sticker: The sticker, for a sticker message.
        photo: The photo, for a photo message.
        attachment: What was sent instead of text, e.g. "voice note", for an
            unsupported message.
        album_id: For a photo or file sent with others at once, the ID they
            share.
        message_id: The chat channel's ID for the message, which puts an
            album's items in the order they were sent; 0 if not known.
        replied_sticker: The sticker this message replies to, if it replies
            to one.
    """

    sender_id: int
    chat_id: int
    sender_username: str | None
    text: str
    kind: MessageKind = MessageKind.TEXT
    sticker: ChannelSticker | None = None
    photo: ChannelPhoto | None = None
    attachment: str | None = None
    album_id: str | None = None
    message_id: int = 0
    replied_sticker: ChannelSticker | None = None


class MessageDirection(StrEnum):
    """Who a message in a Conversation came from."""

    INCOMING = "incoming"
    OUTGOING = "outgoing"


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
        content: The message text; for a photo, its caption and description.
        sent_at: When it was sent.
        photos: The photos the message came with, as chat channel IDs.
        sticker: The sticker a User sent, for a sticker message from them.
    """

    id: UUID
    conversation_id: UUID
    direction: MessageDirection
    kind: MessageKind
    content: str
    sent_at: datetime
    photos: tuple[ChannelPhoto, ...] = ()
    sticker: ChannelSticker | None = None


@dataclass(frozen=True)
class MessageToAnswer:
    """A connected User's message that the Companion should answer.

    Attributes:
        user_id: The User who sent it.
        chat_id: The chat to reply in.
        text: The message as the Companion reads it, e.g. "[sticker: 😂]"
            for a sticker, or "[photo: …] caption" for a photo.
        kind: What kind of message it is.
        photos: The photos it came with.
        safeguard_text: The message as the Safeguard reads it when that
            differs from `text`: with Photo Viewing off, the Safeguard still
            reads each photo's description. None when it is the same.
        sticker: The sticker, for a sticker message.
    """

    user_id: UUID
    chat_id: int
    text: str
    kind: MessageKind = MessageKind.TEXT
    photos: tuple[ChannelPhoto, ...] = ()
    safeguard_text: str | None = None
    sticker: ChannelSticker | None = None


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
class ModelAnswer:
    """What the chat model answered, and how many tokens it took.

    Attributes:
        text: The answer text.
        tokens_in: Tokens the model read, across every round of tool calls.
        tokens_out: Tokens the model wrote, across every round of tool calls.
    """

    text: str
    tokens_in: int = 0
    tokens_out: int = 0


@dataclass(frozen=True)
class DailyUsage:
    """What one User used on one of their days. Counts only, never content.

    Attributes:
        day: The User's day.
        user_id: The User's ID.
        user_name: What the Companion calls them, if set.
        user_email: Their account email, if known.
        user_time_zone: Their time zone, which decides their day; None for UTC.
        message_count: Messages that counted toward the daily message limit.
        tokens_in: Tokens the chat model read for them.
        tokens_out: Tokens the chat model wrote for them.
        web_search_count: Web searches and page reads made for them.
        message_limit_reached: True once a message was over the daily limit.
        web_search_limit_reached: True once a web search was over its limit.
    """

    day: date
    user_id: UUID
    user_name: str | None
    user_email: str | None
    user_time_zone: str | None
    message_count: int
    tokens_in: int
    tokens_out: int
    web_search_count: int
    message_limit_reached: bool
    web_search_limit_reached: bool


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
class SharedPhoto:
    """A photo that matters to a User, kept in their User Memory.

    Attributes:
        id: Our ID for it.
        user_id: The User who sent it.
        file_id: The chat channel's ID used to download or send it.
        file_unique_id: The chat channel's ID that stays the same for it.
        description: What it shows, written when it arrived.
        note: Why it matters to the User.
        caption: The caption it came with; "" if none.
        sent_at: When the User sent it.
        conversation_id: The Conversation it came in; None once that is gone.
    """

    id: UUID
    user_id: UUID
    file_id: str
    file_unique_id: str
    description: str
    note: str
    caption: str
    sent_at: datetime
    conversation_id: UUID | None


@dataclass(frozen=True)
class MemoryChanges:
    """What post-conversation processing changes in a User's User Memory.

    Attributes:
        added: New Memory Items to save.
        updated: Existing Memory Items with their new content and category.
        removed_ids: IDs of Memory Items to delete.
        new_shared_photos: New Shared Photos to save.
    """

    added: list[MemoryItem]
    updated: list[MemoryItem]
    removed_ids: list[UUID]
    new_shared_photos: list[SharedPhoto] = field(default_factory=list)


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
class KnowledgeFile:
    """A file an Admin gives a Knowledge document in place of its old one.

    Attributes:
        file_name: The file's name.
        file_type: What kind of file it is.
        content: The file's bytes.
    """

    file_name: str
    file_type: KnowledgeFileType
    content: bytes


@dataclass(frozen=True)
class KnowledgeDetailsChange:
    """Details an Admin changes on a Knowledge document; None keeps one.

    Attributes:
        title: Its new title.
        source: Who wrote or translated it.
        tradition: The tradition it belongs to.
    """

    title: str | None = None
    source: str | None = None
    tradition: str | None = None


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


@dataclass(frozen=True)
class WebSearchResult:
    """One result from a web search.

    Attributes:
        title: The page's title.
        url: The page's address.
        content: A short piece of the page that matches the search.
    """

    title: str
    url: str
    content: str


@dataclass(frozen=True)
class LibrarySticker:
    """A sticker in the Sticker Library.

    Attributes:
        id: Our ID for the sticker.
        file_id: The ID used to send it on the chat channel.
        file_unique_id: The ID that stays the same for the same sticker.
        emoji: The emoji it stands for, if it has one.
        set_name: The sticker set it came from, if any.
        preview_file_id: The ID of an image of it for the Dashboard, if any.
        note: When to use it, written by an Admin; "" until one is written,
            and the Companion only sends stickers that have a note.
        added_at: When it was added.
    """

    id: UUID
    file_id: str
    file_unique_id: str
    emoji: str | None
    set_name: str | None
    preview_file_id: str | None
    note: str
    added_at: datetime


@dataclass(frozen=True)
class PersonalSticker:
    """A sticker the Companion kept from one User, to reply in their own stickers.

    Attributes:
        id: Our ID for the sticker.
        user_id: The User it was kept from.
        file_id: The ID used to send it on the chat channel.
        file_unique_id: The ID that stays the same for the same sticker.
        emoji: The emoji it stands for, if it has one.
        set_name: The sticker set it came from, if any.
        preview_file_id: The ID of an image of it for the Dashboard, if any.
        note: When to use it, about the moment and never about the User.
        kept_at: When it was first kept.
        last_used_at: When the User or the Companion last sent it.
    """

    id: UUID
    user_id: UUID
    file_id: str
    file_unique_id: str
    emoji: str | None
    set_name: str | None
    preview_file_id: str | None
    note: str
    kept_at: datetime
    last_used_at: datetime


@dataclass(frozen=True)
class StickerImage:
    """An image of a sticker, for the Dashboard to show.

    Attributes:
        content: The image's bytes.
        media_type: Its media type, e.g. "image/webp".
    """

    content: bytes
    media_type: str


@dataclass(frozen=True)
class CheckInKindDetails:
    """What an Admin sets on a Check-in Kind.

    Attributes:
        name: Its name, e.g. "A casual hello".
        description: What it is, as the Check-in model and Users are told.
        allowed_without_user_memory: Whether it may be sent to a User with
            User Memory off.
    """

    name: str
    description: str
    allowed_without_user_memory: bool


@dataclass(frozen=True)
class CheckInKind:
    """A style of Check-in the Companion can send, managed by Admins.

    Attributes:
        id: Our ID for the Check-in Kind.
        name: Its name, e.g. "A casual hello".
        description: What it is, as the Check-in model and Users are told.
        allowed_without_user_memory: Whether it may be sent to a User with
            User Memory off.
        sort_order: Where it comes in the list.
        sends_shared_photo: Whether one of the User's Shared Photos is sent
            with its message. Fixed when the Kind is made; Admins can't
            change it.
    """

    id: UUID
    name: str
    description: str
    allowed_without_user_memory: bool
    sort_order: int
    sends_shared_photo: bool = False


@dataclass(frozen=True)
class CheckInKindOverview:
    """A Check-in Kind and how often it was sent lately, for Admins.

    Attributes:
        kind: The Check-in Kind.
        sent_count: How many Check-ins of this Kind were sent in the period
            asked for.
    """

    kind: CheckInKind
    sent_count: int


class CheckInOutcome(StrEnum):
    """What the Check-in service decided for a User who was due."""

    SENT = "sent"
    SKIPPED = "skipped"
    ASKED_ABOUT_FEWER = "asked_about_fewer"


DAILY_LIMIT_SKIP_REASON = "User had used up today's Daily Message Limit"


class CheckInStatus(StrEnum):
    """What happened after a Check-in decision."""

    SENT = "sent"
    REPLIED = "replied"
    NO_REPLY = "no_reply"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class CheckIn:
    """A Check-in decision for a User: sent, skipped, or asking about fewer.

    Attributes:
        id: Our ID for the Check-in.
        user_id: The User it was for.
        outcome: Whether it was sent, skipped, or was the one "would you like
            fewer?" message.
        decided_at: When it was sent or skipped.
        kind_id: Its Check-in Kind; None if skipped, asking about fewer, or
            the Kind was removed since.
        kind_name: The Check-in Kind's name; None when `kind_id` is.
        message: The text that was sent; None if skipped.
        skip_reason: Why the Check-in model skipped it; only Admins see it.
        replied_at: When the User replied, if they have.
        shared_photo_id: The Shared Photo sent after its message; None if
            none was sent or it was deleted since.
    """

    id: UUID
    user_id: UUID
    outcome: CheckInOutcome
    decided_at: datetime
    kind_id: UUID | None = None
    kind_name: str | None = None
    message: str | None = None
    skip_reason: str | None = None
    replied_at: datetime | None = None
    shared_photo_id: UUID | None = None

    @property
    def was_sent(self) -> bool:
        """Tell whether a message went to the User.

        Returns:
            True unless the Check-in was skipped.
        """
        return self.outcome != CheckInOutcome.SKIPPED

    @property
    def skipped_for_daily_limit(self) -> bool:
        """Tell whether it was skipped because the User had used up the daily limit.

        Returns:
            True for a limit skip.
        """
        return (
            self.outcome == CheckInOutcome.SKIPPED
            and self.skip_reason == DAILY_LIMIT_SKIP_REASON
        )


@dataclass(frozen=True)
class CheckInLogEntry:
    """A Check-in decision and who it was for, for Admins. Never the message.

    Attributes:
        check_in: The Check-in decision.
        user_name: The User's name, if known.
        user_email: The User's email address, if known.
    """

    check_in: CheckIn
    user_name: str | None
    user_email: str | None


class Feature(StrEnum):
    """An extra the Companion offers that Admins can switch off.

    Safety and a User's rights and privacy are never Features.
    """

    WEB_SEARCH = "web_search"
    STICKERS = "stickers"
    KNOWLEDGE = "knowledge"
    CHECK_INS = "check_ins"
    USER_MEMORY = "user_memory"
    SETTINGS_IN_CHAT = "settings_in_chat"
    PHOTO_VIEWING = "photo_viewing"
    PERSONAL_STICKERS = "personal_stickers"


@dataclass(frozen=True)
class FeatureSwitch:
    """A Feature's switch for everyone and its last change.

    Attributes:
        feature: The Feature.
        on: Whether the Feature is on for everyone.
        changed_by_email: The email of the Admin who last changed it; None if
            it still has its starting value.
        changed_at: When it was last changed; None if it never was.
    """

    feature: Feature
    on: bool
    changed_by_email: str | None
    changed_at: datetime | None


class UserFeatureSwitch(StrEnum):
    """An Admin's switch for one Feature for one User.

    "Default" follows the switch for everyone; "on" and "off" override it.
    """

    DEFAULT = "default"
    ON = "on"
    OFF = "off"


class FeatureReason(StrEnum):
    """Why a Feature works, or doesn't, for a User right now."""

    ON_FOR_EVERYONE = "on_for_everyone"
    ON_FOR_USER = "on_for_user"
    OFF_FOR_EVERYONE = "off_for_everyone"
    OFF_FOR_USER = "off_for_user"
    TURNED_OFF_BY_USER = "turned_off_by_user"
    STICKERS_OFF = "stickers_off"


@dataclass(frozen=True)
class FeatureStatus:
    """Whether a Feature works for a User, why, and the Admin's switch for them.

    Attributes:
        feature: The Feature.
        available: Whether the Admin side allows it for the User.
        works: Whether it works for the User right now: it is available,
            where the User has their own switch they have it on, and the
            Feature it needs, if any, works too.
        reason: Why it works or doesn't.
        switch: The Admin's switch for this User.
        changed_by_email: The email of the Admin who last changed the switch
            for this User; None when it is "default".
        changed_at: When the switch for this User was last changed; None
            when it is "default".
    """

    feature: Feature
    available: bool
    works: bool
    reason: FeatureReason
    switch: UserFeatureSwitch
    changed_by_email: str | None
    changed_at: datetime | None
