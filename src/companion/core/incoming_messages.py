import logging
import threading
from collections import defaultdict
from collections.abc import Callable, Sequence
from uuid import UUID

from companion.core.models import (
    ChannelPhoto,
    IncomingMessage,
    MessageKind,
    MessageToAnswer,
    UserSnapshot,
)
from companion.core.photos import PhotoService
from companion.core.ports import ChatChannel, ConversationEngine, Repositories, Timer
from companion.core.sticker_adding import StickerAdding
from companion.core.stickers import sticker_message_text
from companion.core.telegram_connection import TelegramConnectionService
from companion.core.user_snapshot import UserSnapshotLoader

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


def album_caption(messages: Sequence[IncomingMessage]) -> str:
    """Write an album's caption, marking the files the Companion can't open.

    Args:
        messages: The album's items, in the order sent.

    Returns:
        E.g. "[video] our trip": a marker for each unsupported file, then
        the caption from whichever item has it.
    """
    markers = [
        f"[{message.attachment or 'attachment'}]"
        for message in messages
        if message.kind == MessageKind.UNSUPPORTED
    ]
    caption = next(
        (message.text.strip() for message in messages if message.text.strip()), ""
    )
    return " ".join([*markers, caption]).strip()


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
        sticker_adding: StickerAdding,
        photo_service: PhotoService,
        user_snapshots: UserSnapshotLoader,
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
            sticker_adding: Adds the stickers Admins send in adding mode or
                reply "add this" to.
            photo_service: Describes the photos Users send.
            user_snapshots: Reads the User once at the start of each reply.
            timer: Waits for the rest of an album to arrive.
            dashboard_url: The Dashboard's address, put into some replies.
        """
        self._telegram_connections = telegram_connections
        self._sticker_adding = sticker_adding
        self._photo_service = photo_service
        self._user_snapshots = user_snapshots
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
        from an Admin in adding mode goes into the Sticker Library; any other
        message ends adding mode, with a summary of what was added, and is
        then handled as normal. An Admin's "add this" reply to a sticker adds
        it. A photo is described
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

        if message.kind == MessageKind.STICKER and self._sticker_adding.add_if_adding(
            connection.user_id, message
        ):
            return
        self._sticker_adding.finish(connection.user_id)
        if self._sticker_adding.add_if_asked(connection.user_id, message):
            return
        settings = self._repositories.platform_settings
        if message.album_id is not None:
            self._collect_album_item(connection.user_id, message)
            return
        if message.kind == MessageKind.UNSUPPORTED and not message.text.strip():
            self._chat_channel.send_text(
                message.chat_id, settings.get("unsupported_message_reply")
            )
            return
        self._answer(
            connection.user_id,
            message.chat_id,
            lambda user: self._message_to_answer(user, message),
        )

    def _collect_album_item(self, user_id: UUID, message: IncomingMessage) -> None:
        """Keep an album's photo or file and restart the wait for the rest of it.

        Args:
            user_id: The User who sent it.
            message: The photo or file message, with its album ID.
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
        """Answer an album's collected items as one message, in the order sent.

        Files the Companion can't open, like a video, are marked in the text
        ("[video] caption"). An album with no photos and no caption gets the
        unsupported reply once.

        Args:
            user_id: The User who sent it.
            album_key: Names the collected album.
        """
        with self._albums_guard:
            messages = self._albums.pop(album_key, [])
        if not messages:
            return
        messages.sort(key=lambda message: message.message_id)
        chat_id = messages[0].chat_id
        photos = [message.photo for message in messages if message.photo]
        caption = album_caption(messages)
        if photos:
            self._answer(
                user_id,
                chat_id,
                lambda user: self._photo_message_to_answer(
                    user, chat_id, photos, caption
                ),
            )
            return
        if not any(message.text.strip() for message in messages):
            self._chat_channel.send_text(
                chat_id,
                self._repositories.platform_settings.get("unsupported_message_reply"),
            )
            return
        self._answer(
            user_id,
            chat_id,
            lambda user: MessageToAnswer(
                user_id=user_id,
                chat_id=chat_id,
                text=caption,
                kind=MessageKind.UNSUPPORTED,
            ),
        )

    def _answer(
        self,
        user_id: UUID,
        chat_id: int,
        build_message: Callable[[UserSnapshot], MessageToAnswer],
    ) -> None:
        """Answer a User's message after their earlier ones, with a fallback on failure.

        The User is read once, inside their turn, and that snapshot is used
        for the whole reply.

        Args:
            user_id: The User who sent it.
            chat_id: The chat to reply in.
            build_message: Builds the message the Companion answers from the
                User snapshot.
        """
        with self._turn_lock_for(user_id):
            try:
                user = self._user_snapshots.load(user_id)
                self._conversation_engine.handle(build_message(user), user)
            except Exception:
                logger.exception("Could not answer a message from a User")
                self._chat_channel.send_text(
                    chat_id,
                    self._repositories.platform_settings.get("reply_failed_message"),
                )

    def _message_to_answer(
        self, user: UserSnapshot, message: IncomingMessage
    ) -> MessageToAnswer:
        """Turn a connected User's message into the message the Companion answers.

        Args:
            user: The User who sent it.
            message: The incoming message.

        Returns:
            The message to answer; a photo's text holds its description.
        """
        if message.photo is None:
            return MessageToAnswer(
                user_id=user.user.id,
                chat_id=message.chat_id,
                text=readable_text(message),
                kind=message.kind,
                sticker=message.sticker,
            )
        return self._photo_message_to_answer(
            user, message.chat_id, [message.photo], message.text
        )

    def _photo_message_to_answer(
        self,
        user: UserSnapshot,
        chat_id: int,
        photos: Sequence[ChannelPhoto],
        caption: str,
    ) -> MessageToAnswer:
        """Describe a User's photos and turn them into the message to answer.

        Args:
            user: The User who sent them.
            chat_id: The chat to reply in.
            photos: The photo, or an album's photos.
            caption: The caption; "" if none.

        Returns:
            The message to answer, whose text holds each photo's description, or, with
            Photo Viewing off, whose Safeguard text does.
        """
        photo_message = self._photo_service.read_message(user, photos, caption)
        return MessageToAnswer(
            user_id=user.user.id,
            chat_id=chat_id,
            text=photo_message.text,
            kind=MessageKind.PHOTO,
            photos=photo_message.photos,
            safeguard_text=photo_message.safeguard_text,
        )

    def _turn_lock_for(self, user_id: UUID) -> threading.Lock:
        """Get the lock that keeps one User's turns from overlapping.

        Args:
            user_id: The User.

        Returns:
            That User's lock.
        """
        with self._turn_locks_guard:
            return self._turn_locks[user_id]
