import logging
import threading
from collections import defaultdict
from collections.abc import Callable, Sequence
from uuid import UUID

from companion.core.models import (
    ChannelPhoto,
    ConversationTurn,
    IncomingMessage,
    MessageKind,
    UserRole,
)
from companion.core.photos import PhotoService
from companion.core.ports import ChatChannel, ConversationEngine, Repositories, Timer
from companion.core.stickers import StickerLibraryService, sticker_message_text
from companion.core.telegram_connection import TelegramConnectionService

logger = logging.getLogger(__name__)


def readable_text(message: IncomingMessage) -> str:
    """Write an incoming message the way the Companion reads it.

    Args:
        message: The incoming message.

    Returns:
        The text; "[sticker: 😂]" for a sticker; "[voice note] caption" for
        something the Companion can't open that came with a caption.
    """
    if message.kind == MessageKind.STICKER:
        return sticker_message_text(message.sticker.emoji if message.sticker else None)
    if message.kind == MessageKind.UNSUPPORTED:
        return f"[{message.attachment or 'attachment'}] {message.text.strip()}"
    return message.text


class IncomingMessageHandler:
    """Decides what to do with each message people send the Companion.

    A User's messages are answered one at a time, so a reply always sees
    every earlier message, even when several arrive at once. Photos sent
    together as an album are collected and answered as one message.
    """

    def __init__(
        self,
        telegram_connections: TelegramConnectionService,
        repositories: Repositories,
        conversation_engine: ConversationEngine,
        chat_channel: ChatChannel,
        sticker_library: StickerLibraryService,
        photo_service: PhotoService,
        timer: Timer,
        dashboard_url: str,
    ) -> None:
        """Set up the handler.

        Args:
            telegram_connections: Handles `/start <token>` messages.
            repositories: Where Users, Telegram Connections and settings are
                stored.
            conversation_engine: Answers connected Users' messages.
            chat_channel: Sends replies that need no Conversation.
            sticker_library: Adds the stickers Admins send.
            photo_service: Describes the photos Users send.
            timer: Waits for the rest of an album to arrive.
            dashboard_url: The Dashboard's address, put into some replies.
        """
        self._telegram_connections = telegram_connections
        self._sticker_library = sticker_library
        self._photo_service = photo_service
        self._timer = timer
        self._repositories = repositories
        self._conversation_engine = conversation_engine
        self._chat_channel = chat_channel
        self._dashboard_url = dashboard_url
        self._turn_locks: defaultdict[UUID, threading.Lock] = defaultdict(
            threading.Lock
        )
        self._turn_locks_guard = threading.Lock()
        self._albums: dict[str, list[IncomingMessage]] = {}
        self._albums_guard = threading.Lock()

    def handle(self, message: IncomingMessage) -> None:
        """Handle one incoming message.

        `/start <token>` makes a Telegram Connection. Anyone else without a
        Telegram Connection is pointed to the Dashboard to sign up. A sticker
        from an Admin goes into the Sticker Library. A photo is described
        first, so the Safeguard and the reply read what it shows; an album's
        photos wait until `photo_album_wait_seconds` pass after the last one
        arrives, then are answered together as one message. A voice
        note, video or other message the Companion can't read gets the
        unsupported reply, unless it has a caption, which is answered
        instead. Any other message from a connected User is answered by the
        Companion; if that fails, they get a short fallback reply instead of
        silence.

        Args:
            message: The incoming message.
        """
        if self._telegram_connections.is_start_command(message):
            self._telegram_connections.handle_start(message)
            return

        connection = self._repositories.telegram_connections.get_by_telegram_user(
            message.sender_id
        )
        if connection is None:
            reply = self._repositories.platform_settings.get(
                "unknown_telegram_user_reply"
            )
            self._chat_channel.send_text(
                message.chat_id, reply.replace("{dashboard_url}", self._dashboard_url)
            )
            return

        settings = self._repositories.platform_settings
        sticker = message.sticker if message.kind == MessageKind.STICKER else None
        if sticker is not None and self._is_admin(connection.user_id):
            if self._sticker_library.add_sent_sticker(sticker):
                reply = settings.get("sticker_added_reply")
            else:
                reply = settings.get("sticker_already_in_library_reply")
            self._chat_channel.send_text(
                message.chat_id, reply.replace("{dashboard_url}", self._dashboard_url)
            )
            return
        if message.kind == MessageKind.UNSUPPORTED and not message.text.strip():
            self._chat_channel.send_text(
                message.chat_id, settings.get("unsupported_message_reply")
            )
            return

        if message.album_id is not None:
            self._collect_album_photo(connection.user_id, message)
            return
        self._answer(
            connection.user_id,
            message.chat_id,
            lambda: self._turn_for(connection.user_id, message),
        )

    def _collect_album_photo(self, user_id: UUID, message: IncomingMessage) -> None:
        """Keep an album's photo and restart the wait for the rest of the album.

        Args:
            user_id: The User who sent it.
            message: The photo message, with its album ID.
        """
        album_key = f"{message.sender_id}:{message.album_id}"
        with self._albums_guard:
            self._albums.setdefault(album_key, []).append(message)
        self._timer.start(
            album_key,
            self._repositories.platform_settings.get("photo_album_wait_seconds"),
            lambda: self._answer_album(user_id, album_key),
        )

    def _answer_album(self, user_id: UUID, album_key: str) -> None:
        """Answer an album's collected photos as one message.

        Args:
            user_id: The User who sent it.
            album_key: Names the collected album.
        """
        with self._albums_guard:
            messages = self._albums.pop(album_key, [])
        if not messages:
            return
        caption = next((m.text for m in messages if m.text.strip()), "")
        photos = [m.photo for m in messages if m.photo is not None]
        chat_id = messages[0].chat_id
        self._answer(
            user_id,
            chat_id,
            lambda: self._photo_turn(user_id, chat_id, photos, caption),
        )

    def _answer(
        self,
        user_id: UUID,
        chat_id: int,
        build_turn: Callable[[], ConversationTurn],
    ) -> None:
        """Answer a User's message after their earlier ones, with a fallback on failure.

        Args:
            user_id: The User who sent it.
            chat_id: The chat to reply in.
            build_turn: Turns the message into the turn the Companion answers.
        """
        with self._turn_lock_for(user_id):
            try:
                self._conversation_engine.handle(build_turn())
            except Exception:
                logger.exception("Could not answer a message from a User")
                self._chat_channel.send_text(
                    chat_id,
                    self._repositories.platform_settings.get("reply_failed_message"),
                )

    def _turn_for(self, user_id: UUID, message: IncomingMessage) -> ConversationTurn:
        """Turn a connected User's message into the turn the Companion answers.

        Args:
            user_id: The User who sent it.
            message: The incoming message.

        Returns:
            The turn; a photo's text holds its description.
        """
        if message.photo is None:
            return ConversationTurn(
                user_id=user_id,
                chat_id=message.chat_id,
                text=readable_text(message),
                kind=message.kind,
            )
        return self._photo_turn(user_id, message.chat_id, [message.photo], message.text)

    def _photo_turn(
        self,
        user_id: UUID,
        chat_id: int,
        photos: Sequence[ChannelPhoto],
        caption: str,
    ) -> ConversationTurn:
        """Describe a User's photos and turn them into the turn the Companion answers.

        Args:
            user_id: The User who sent them.
            chat_id: The chat to reply in.
            photos: The photo, or an album's photos.
            caption: The caption; "" if none.

        Returns:
            The turn, whose text holds each photo's description.
        """
        photo_message = self._photo_service.read_message(user_id, photos, caption)
        return ConversationTurn(
            user_id=user_id,
            chat_id=chat_id,
            text=photo_message.text,
            kind=MessageKind.PHOTO,
            photos=photo_message.photos,
        )

    def _is_admin(self, user_id: UUID) -> bool:
        """Tell whether a User is an Admin right now.

        Args:
            user_id: The User.

        Returns:
            True if they are an Admin.
        """
        user = self._repositories.users.get(user_id)
        return user is not None and user.role == UserRole.ADMIN

    def _turn_lock_for(self, user_id: UUID) -> threading.Lock:
        """Get the lock that keeps one User's turns from overlapping.

        Args:
            user_id: The User.

        Returns:
            That User's lock.
        """
        with self._turn_locks_guard:
            return self._turn_locks[user_id]
