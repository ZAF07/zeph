import logging
import threading
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from uuid import UUID

from companion.core.models import (
    ChannelPhoto,
    IncomingMessage,
    MessageKind,
    MessageToAnswer,
    PlatformSettings,
    TextToScreen,
    UserSnapshot,
)
from companion.core.photos import PhotoService
from companion.core.platform_settings import (
    DASHBOARD_URL_PLACEHOLDER,
    MESSAGE_WAIT_SECONDS,
    REPLY_FAILED_MESSAGE,
    UNKNOWN_TELEGRAM_USER_REPLY,
    UNSUPPORTED_MESSAGE_REPLY,
)
from companion.core.ports import ChatChannel, Repositories, Timer
from companion.core.reply_gate import ReplyGate, Stopped
from companion.core.reply_service import ReplyService
from companion.core.sticker_adding import StickerAdding
from companion.core.stickers import sticker_message_text
from companion.core.telegram_connection import TelegramConnectionService
from companion.core.user_snapshot import UserSnapshotLoader

logger = logging.getLogger(__name__)

MESSAGE_WAIT_PREFIX = "message:"


def message_wait_key(user_id: UUID) -> str:
    """Name the wait for a User to pause, so each new text restarts it.

    Args:
        user_id: The User.

    Returns:
        The timer key for that User's Message wait.
    """
    return f"{MESSAGE_WAIT_PREFIX}{user_id}"


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


def group_albums(
    album_items: Sequence[IncomingMessage],
) -> list[list[IncomingMessage]]:
    """Group Album photos and files by the Album they came in.

    Args:
        album_items: The items, in the order they arrived.

    Returns:
        One list per Album, in the order the Albums arrived, each in the
        order its items were sent.
    """
    albums: dict[str | None, list[IncomingMessage]] = {}
    for item in album_items:
        albums.setdefault(item.album_id, []).append(item)
    return [
        sorted(items, key=lambda item: item.message_id) for items in albums.values()
    ]


@dataclass
class PendingMessage:
    """What a User has sent in a Message they haven't paused after yet.

    Attributes:
        chat_id: The chat to reply in.
        conversation_id: The Conversation its latest screened text was saved
            into; None until a text is screened.
        texts: Its screened texts as the Companion reads them, in order.
        album_items: Its Album photos and files, screened together once the
            User pauses.
    """

    chat_id: int
    conversation_id: UUID | None = None
    texts: list[str] = field(default_factory=list)
    album_items: list[IncomingMessage] = field(default_factory=list)

    def add_screened(self, conversation_id: UUID, text: str) -> None:
        """Add a text that passed the Safeguard.

        Args:
            conversation_id: The Conversation it was saved into.
            text: The text as the Companion reads it.
        """
        self.conversation_id = conversation_id
        self.texts.append(text)


class IncomingMessageHandler:
    """Decides what to do with each message people send the Companion.

    A connected User's texts are gathered into one Message until they pause
    for `message_wait_seconds`, then answered together with one reply. Each
    text is saved and checked by the Safeguard as it arrives, so a crisis
    is never held back by the wait. A User's turns run one at a time, so a
    text that arrives while a reply is being written starts a new Message.
    """

    def __init__(
        self,
        telegram_connections: TelegramConnectionService,
        repositories: Repositories,
        reply_gate: ReplyGate,
        reply_service: ReplyService,
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
            reply_gate: Saves each text and checks it for crisis.
            reply_service: Answers connected Users' Messages.
            chat_channel: Sends replies that need no Conversation.
            sticker_adding: Adds the stickers Admins send in adding mode or
                reply "add this" to.
            photo_service: Describes the photos Users send.
            user_snapshots: Reads the User once at the start of each turn.
            timer: Waits for the User to pause before answering their Message.
            dashboard_url: The Dashboard's address, put into some replies.
        """
        self._telegram_connections = telegram_connections
        self._sticker_adding = sticker_adding
        self._photo_service = photo_service
        self._user_snapshots = user_snapshots
        self._timer = timer
        self._repositories = repositories
        self._reply_gate = reply_gate
        self._reply_service = reply_service
        self._chat_channel = chat_channel
        self._dashboard_url = dashboard_url
        self._turn_locks: defaultdict[UUID, threading.Lock] = defaultdict(
            threading.Lock
        )
        self._turn_locks_guard = threading.Lock()
        self._pending_messages: dict[UUID, PendingMessage] = {}
        self._texts_being_checked: Counter[UUID] = Counter()
        self._pending_messages_guard = threading.Lock()

    def handle(self, message: IncomingMessage) -> None:
        """Handle one incoming message.

        `/start <token>` makes a Telegram Connection. Anyone else without a
        Telegram Connection is pointed to the Dashboard to sign up. A sticker
        from an Admin in adding mode goes into the Sticker Library; any other
        message ends adding mode, with a summary of what was added, and is
        then handled as normal. An Admin's "add this" reply to a sticker adds
        it. A voice note, video or other message the Companion can't read
        gets the unsupported reply, unless it has a caption, which is
        answered instead. Anything else from a connected User joins their
        Message: a photo is described first, so the Safeguard and the reply
        read what it shows; an Album's photos are described and checked
        together once the User pauses. If saving or checking a text fails,
        the User gets a short fallback reply instead of silence.

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
            reply = self._repositories.platform_settings.load().get(
                UNKNOWN_TELEGRAM_USER_REPLY
            )
            self._chat_channel.send_text(
                message.chat_id,
                reply.replace(DASHBOARD_URL_PLACEHOLDER, self._dashboard_url),
            )
            return

        if message.kind == MessageKind.STICKER and self._sticker_adding.add_if_adding(
            connection.user_id, message
        ):
            return
        self._sticker_adding.finish(connection.user_id)
        if self._sticker_adding.add_if_asked(connection.user_id, message):
            return
        if message.album_id is not None:
            self._hold_album_item(connection.user_id, message)
            return
        if message.kind == MessageKind.UNSUPPORTED and not message.text.strip():
            self._chat_channel.send_text(
                message.chat_id,
                self._repositories.platform_settings.load().get(
                    UNSUPPORTED_MESSAGE_REPLY
                ),
            )
            return
        self._screen_text(connection.user_id, message)

    def _hold_album_item(self, user_id: UUID, message: IncomingMessage) -> None:
        """Add an Album's photo or file to the User's Message and restart the wait.

        Args:
            user_id: The User who sent it.
            message: The photo or file message, with its Album ID.
        """
        with self._pending_messages_guard:
            pending = self._pending_messages.setdefault(
                user_id, PendingMessage(chat_id=message.chat_id)
            )
            pending.album_items.append(message)
        self._restart_wait(user_id, self._repositories.platform_settings.load())

    def _screen_text(self, user_id: UUID, message: IncomingMessage) -> None:
        """Save a text and check it for crisis now, then restart the wait.

        While the text is being checked, the wait ending doesn't answer the
        Message, so a slow check never splits it. A crisis gets the Crisis
        Reply straight away and drops the rest of the User's Message, so it
        isn't answered normally. A check that fails gets the fallback reply
        and drops the rest of the Message too.

        Args:
            user_id: The User who sent it.
            message: The incoming message.
        """
        with self._pending_messages_guard:
            self._texts_being_checked[user_id] += 1
        try:
            with self._turn_lock_for(user_id):
                settings = self._repositories.platform_settings.load()
                try:
                    snapshot = self._user_snapshots.load(user_id, settings)
                    text = self._text_to_screen(snapshot, message)
                    result = self._reply_gate.screen(text, snapshot)
                except Exception:
                    logger.exception("Could not check a text from a User")
                    self._drop_pending_message(user_id)
                    self._chat_channel.send_text(
                        message.chat_id, settings.get(REPLY_FAILED_MESSAGE)
                    )
                    return
                if isinstance(result, Stopped):
                    self._drop_pending_message(user_id)
                    return
                with self._pending_messages_guard:
                    pending = self._pending_messages.setdefault(
                        user_id, PendingMessage(chat_id=message.chat_id)
                    )
                    pending.add_screened(result.conversation_id, text.text)
        finally:
            with self._pending_messages_guard:
                self._texts_being_checked[user_id] -= 1
                if not self._texts_being_checked[user_id]:
                    del self._texts_being_checked[user_id]
        self._restart_wait(user_id, settings)

    def _drop_pending_message(self, user_id: UUID) -> None:
        """Forget what the User has sent so far, so it isn't answered normally.

        Args:
            user_id: The User.
        """
        with self._pending_messages_guard:
            self._pending_messages.pop(user_id, None)

    def _take_pending_message(self, user_id: UUID) -> PendingMessage | None:
        """Take the User's Message to answer, unless a text of theirs is being checked.

        Args:
            user_id: The User.

        Returns:
            The Message, or None if there is none or a text is still being
            checked; that text restarts the wait once checked.
        """
        with self._pending_messages_guard:
            if self._texts_being_checked[user_id]:
                return None
            return self._pending_messages.pop(user_id, None)

    def _is_checking_a_text(self, user_id: UUID) -> bool:
        """Tell whether a text from the User is waiting for or being checked.

        Args:
            user_id: The User.

        Returns:
            True while any of their texts is not yet checked.
        """
        with self._pending_messages_guard:
            return bool(self._texts_being_checked[user_id])

    def _restart_wait(self, user_id: UUID, settings: PlatformSettings) -> None:
        """Start the wait for the User to pause, restarting any wait under way.

        Args:
            user_id: The User.
            settings: The platform settings, which say how long to wait.
        """
        self._timer.start(
            message_wait_key(user_id),
            settings.get(MESSAGE_WAIT_SECONDS),
            lambda: self._answer_message(user_id),
        )

    def _answer_message(self, user_id: UUID) -> None:
        """Answer everything the User sent before pausing with one reply.

        Any Albums are described and checked for crisis first; a crisis gets
        the Crisis Reply and the Message isn't answered normally. An Album
        with no photos and no caption gets the unsupported reply. The
        platform settings and the User are read once, inside their turn, and
        that snapshot is used for the whole reply. If the reply fails the
        User gets a short fallback reply instead of silence.

        Args:
            user_id: The User who paused.
        """
        if self._is_checking_a_text(user_id):
            return
        with self._turn_lock_for(user_id):
            pending = self._take_pending_message(user_id)
            if pending is None:
                return
            settings = self._repositories.platform_settings.load()
            try:
                snapshot = self._user_snapshots.load(user_id, settings)
                for album_items in group_albums(pending.album_items):
                    album_text = self._album_text_to_screen(
                        snapshot, pending.chat_id, album_items
                    )
                    if album_text is None:
                        continue
                    result = self._reply_gate.screen(album_text, snapshot)
                    if isinstance(result, Stopped):
                        return
                    pending.add_screened(result.conversation_id, album_text.text)
                if pending.conversation_id is None:
                    return
                self._reply_service.handle(
                    MessageToAnswer(
                        user_id=user_id,
                        chat_id=pending.chat_id,
                        conversation_id=pending.conversation_id,
                        text="\n".join(pending.texts),
                    ),
                    snapshot,
                )
            except Exception:
                logger.exception("Could not answer a Message from a User")
                self._chat_channel.send_text(
                    pending.chat_id, settings.get(REPLY_FAILED_MESSAGE)
                )

    def _album_text_to_screen(
        self,
        snapshot: UserSnapshot,
        chat_id: int,
        album_items: Sequence[IncomingMessage],
    ) -> TextToScreen | None:
        """Turn an Album's items into one text of the Message.

        Files the Companion can't open, like a video, are marked in the text
        ("[video] caption"). An Album with no photos and no caption gets the
        unsupported reply instead.

        Args:
            snapshot: The User who sent it.
            chat_id: The chat it came from.
            album_items: The Album's items, in the order sent.

        Returns:
            The text to screen, or None when the Album has nothing to answer.
        """
        photos = [item.photo for item in album_items if item.photo]
        caption = album_caption(album_items)
        if photos:
            return self._photo_text_to_screen(snapshot, chat_id, photos, caption)
        if not any(item.text.strip() for item in album_items):
            self._chat_channel.send_text(
                chat_id, snapshot.settings.get(UNSUPPORTED_MESSAGE_REPLY)
            )
            return None
        return TextToScreen(
            user_id=snapshot.user.id,
            chat_id=chat_id,
            text=caption,
            kind=MessageKind.UNSUPPORTED,
        )

    def _text_to_screen(
        self, snapshot: UserSnapshot, message: IncomingMessage
    ) -> TextToScreen:
        """Turn a connected User's message into one text of their Message.

        Args:
            snapshot: The User who sent it.
            message: The incoming message.

        Returns:
            The text to screen; a photo's text holds its description.
        """
        if message.photo is None:
            return TextToScreen(
                user_id=snapshot.user.id,
                chat_id=message.chat_id,
                text=readable_text(message),
                kind=message.kind,
                sticker=message.sticker,
            )
        return self._photo_text_to_screen(
            snapshot, message.chat_id, [message.photo], message.text
        )

    def _photo_text_to_screen(
        self,
        snapshot: UserSnapshot,
        chat_id: int,
        photos: Sequence[ChannelPhoto],
        caption: str,
    ) -> TextToScreen:
        """Describe a User's photos and turn them into one text of their Message.

        Args:
            snapshot: The User who sent them.
            chat_id: The chat to reply in.
            photos: The photo, or an Album's photos.
            caption: The caption; "" if none.

        Returns:
            The text to screen, which holds each photo's description, or,
            with Photo Viewing off, whose Safeguard text does.
        """
        photo_message = self._photo_service.read_message(snapshot, photos, caption)
        return TextToScreen(
            user_id=snapshot.user.id,
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
