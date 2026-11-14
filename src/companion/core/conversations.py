import logging
from datetime import datetime
from uuid import UUID, uuid4

from companion.core.models import (
    ChannelPhoto,
    ChannelSticker,
    CheckIn,
    Conversation,
    ConversationMessage,
    LibrarySticker,
    MessageDirection,
    MessageKind,
    PersonalSticker,
)
from companion.core.photos import sent_shared_photo_text
from companion.core.ports import (
    ChatChannel,
    Clock,
    PlatformSettingsRepository,
    Repositories,
)
from companion.core.stickers import sticker_message_text
from companion.core.timing import check_in_reply_window, is_open, quiet_gap

logger = logging.getLogger(__name__)


def typing_pause_seconds(text: str, settings: PlatformSettingsRepository) -> float:
    """Work out how long to show typing before sending a message.

    Longer messages take longer to "type", within the range set by Admins.

    Args:
        text: The message about to be sent.
        settings: Holds the typing pace and its lower and upper limits.

    Returns:
        The pause in seconds.
    """
    pause = len(text) * settings.get("typing_seconds_per_character")
    shortest = settings.get("min_typing_seconds")
    longest = settings.get("max_typing_seconds")
    return float(min(max(pause, shortest), longest))


class ConversationService:
    """Saves messages into Conversations and sends the Companion's replies."""

    def __init__(
        self, repositories: Repositories, chat_channel: ChatChannel, clock: Clock
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where Conversations and settings are stored.
            chat_channel: Sends messages to the User.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._chat_channel = chat_channel
        self._clock = clock

    def record_incoming(
        self,
        user_id: UUID,
        chat_id: int,
        text: str,
        kind: MessageKind = MessageKind.TEXT,
        photos: tuple[ChannelPhoto, ...] = (),
        sticker: ChannelSticker | None = None,
    ) -> UUID:
        """Save a User's message and show that the Companion is typing.

        The message joins the User's open Conversation, or starts a new one if
        the quiet gap has passed since the last message. If the scheduler ends
        the Conversation just before the message is saved, the message is
        refused and tried again; it then starts a new Conversation, which
        cannot already be ended. So the message is never left out of a
        Conversation's processing.

        Args:
            user_id: The User who sent it.
            chat_id: The chat it came from.
            text: The message as the Companion reads it.
            kind: What kind of message it is.
            photos: The photos it came with, kept as chat channel IDs.
            sticker: The sticker, for a sticker message.

        Returns:
            The ID of the Conversation the message was added to.
        """
        saved = False
        while not saved:
            conversation_id = self._open_conversation_id(user_id)
            saved = self._repositories.conversations.add_message_if_open(
                ConversationMessage(
                    id=uuid4(),
                    conversation_id=conversation_id,
                    direction=MessageDirection.INCOMING,
                    kind=kind,
                    content=text,
                    sent_at=self._clock.now(),
                    photos=photos,
                    sticker=sticker,
                )
            )
        self._chat_channel.show_typing(chat_id)
        return conversation_id

    def deliver_reply(
        self,
        user_id: UUID,
        conversation_id: UUID,
        chat_id: int,
        reply_parts: list[str],
        sticker_id: UUID | None = None,
        shared_photo_id: UUID | None = None,
    ) -> None:
        """Send the Companion's reply, one short message at a time.

        Before each message the Companion shows typing for a while, as a
        person would. Each message is saved as soon as it is sent. The
        Shared Photo, if any, comes next, then the sticker. The Shared Photo
        is looked up by the User's own ID and skipped if it was deleted
        meanwhile; if the chat channel refuses it, the error is logged and
        the rest of the reply still goes. The sticker is found in the
        Sticker Library or the User's own Personal Stickers, and skipped if
        it was removed meanwhile; one of theirs is noted as just used.

        Args:
            user_id: The User being answered.
            conversation_id: The Conversation being answered.
            chat_id: The chat to send to.
            reply_parts: The short messages that make up the reply, in order.
            sticker_id: The sticker to send after them, from the Sticker
                Library or the User's Personal Stickers.
            shared_photo_id: The User's Shared Photo to send back after them.
        """
        settings = self._repositories.platform_settings
        for part in reply_parts:
            self._chat_channel.show_typing(chat_id)
            self._clock.sleep(typing_pause_seconds(part, settings))
            self._chat_channel.send_text(chat_id, part)
            self._save(conversation_id, MessageDirection.OUTGOING, part)
        if shared_photo_id is not None:
            self._send_shared_photo(user_id, conversation_id, chat_id, shared_photo_id)
        sticker = self._find_sticker(user_id, sticker_id) if sticker_id else None
        if sticker is not None:
            self._chat_channel.send_sticker(chat_id, sticker.file_id)
            if isinstance(sticker, PersonalSticker):
                self._repositories.personal_stickers.mark_used(
                    user_id, sticker.id, self._clock.now()
                )
            self._save(
                conversation_id,
                MessageDirection.OUTGOING,
                sticker_message_text(sticker.emoji),
                MessageKind.STICKER,
            )

    def _find_sticker(
        self, user_id: UUID, sticker_id: UUID
    ) -> LibrarySticker | PersonalSticker | None:
        """Find a sticker in the Sticker Library or the User's Personal Stickers.

        Args:
            user_id: The User whose Personal Stickers may hold it.
            sticker_id: The sticker's ID.

        Returns:
            The sticker, or None if it is in neither.
        """
        library_sticker = self._repositories.stickers.get(sticker_id)
        if library_sticker is not None:
            return library_sticker
        return self._repositories.personal_stickers.get(user_id, sticker_id)

    def _send_shared_photo(
        self, user_id: UUID, conversation_id: UUID, chat_id: int, photo_id: UUID
    ) -> None:
        """Send one of the User's Shared Photos back and save it.

        Args:
            user_id: The User whose Shared Photo it must be.
            conversation_id: The Conversation being answered.
            chat_id: The chat to send to.
            photo_id: The Shared Photo's ID.
        """
        photo = self._repositories.user_memory.get_shared_photo(user_id, photo_id)
        if photo is None:
            return
        try:
            self._chat_channel.send_photo(chat_id, photo.file_id)
        except Exception:
            logger.exception("Could not send a Shared Photo")
            return
        self._save(
            conversation_id,
            MessageDirection.OUTGOING,
            sent_shared_photo_text(photo.description),
            MessageKind.PHOTO,
        )

    def deliver_at_once(self, conversation_id: UUID, chat_id: int, text: str) -> None:
        """Send one message straight away, without a typing pause, and save it.

        Used for the Crisis Reply, which must never wait, and the daily
        limit reply.

        Args:
            conversation_id: The Conversation being answered.
            chat_id: The chat to send to.
            text: The message, sent whole even if it has blank lines.
        """
        self._chat_channel.send_text(chat_id, text)
        self._save(conversation_id, MessageDirection.OUTGOING, text)

    def deliver_notice(self, user_id: UUID, chat_id: int, text: str) -> None:
        """Send a message the Companion wasn't asked to write, and save it.

        It joins the User's open Conversation, or starts one, so later
        replies know it was said. Used for the summary after an Admin adds
        stickers in chat.

        Args:
            user_id: The User it is for.
            chat_id: The chat to send to.
            text: The message.
        """
        self._chat_channel.send_text(chat_id, text)
        self._save(self._open_conversation_id(user_id), MessageDirection.OUTGOING, text)

    def _open_conversation_id(self, user_id: UUID) -> UUID:
        """Find the User's open Conversation, or start a new one.

        A Conversation is open until it is ended or the quiet gap passes. A
        new Conversation started within the reply window of the User's
        newest Check-in answers it: it starts with that Check-in and any
        Shared Photo sent with it, so the reply has them as context, and the
        Check-in is marked replied.

        Args:
            user_id: The User.

        Returns:
            The open Conversation's ID.
        """
        settings = self._repositories.platform_settings
        now = self._clock.now()
        latest = self._repositories.conversations.get_latest_for_user(user_id)
        if latest is not None and is_open(latest, now, quiet_gap(settings)):
            return latest.id
        conversation = Conversation(
            id=uuid4(), user_id=user_id, started_at=now, last_message_at=now
        )
        self._repositories.conversations.add(conversation)
        check_in = self._repositories.check_ins.claim_reply(
            user_id, replied_at=now, sent_since=now - check_in_reply_window(settings)
        )
        if check_in is not None:
            self._start_with_check_in(conversation.id, check_in)
        return conversation.id

    def _start_with_check_in(self, conversation_id: UUID, check_in: CheckIn) -> None:
        """Save a Check-in and any Shared Photo sent with it to a new Conversation.

        Args:
            conversation_id: The Conversation that answers the Check-in.
            check_in: The Check-in it answers.
        """
        if check_in.message is not None:
            self._save(
                conversation_id,
                MessageDirection.OUTGOING,
                check_in.message,
                sent_at=check_in.decided_at,
            )
        if check_in.shared_photo_id is None:
            return
        photo = self._repositories.user_memory.get_shared_photo(
            check_in.user_id, check_in.shared_photo_id
        )
        if photo is not None:
            self._save(
                conversation_id,
                MessageDirection.OUTGOING,
                sent_shared_photo_text(photo.description),
                MessageKind.PHOTO,
                sent_at=check_in.decided_at,
            )

    def _save(
        self,
        conversation_id: UUID,
        direction: MessageDirection,
        text: str,
        kind: MessageKind = MessageKind.TEXT,
        sent_at: datetime | None = None,
        photos: tuple[ChannelPhoto, ...] = (),
    ) -> None:
        """Save one message to a Conversation.

        Args:
            conversation_id: The Conversation.
            direction: Who sent it.
            text: The message as the Companion reads it.
            kind: What kind of message it is.
            sent_at: When it was sent; now if not given.
            photos: The photos it came with.
        """
        self._repositories.conversations.add_message(
            ConversationMessage(
                id=uuid4(),
                conversation_id=conversation_id,
                direction=direction,
                kind=kind,
                content=text,
                sent_at=sent_at or self._clock.now(),
                photos=photos,
            )
        )
