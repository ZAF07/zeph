import logging
import threading
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from uuid import UUID

from companion.core.model_call_log import start_trace
from companion.core.models import (
    ChannelPhoto,
    IncomingMessage,
    MessageKind,
    MessageToAnswer,
    ModelCallTrace,
    PlatformSettings,
    TextToScreen,
    TraceKind,
    UserSnapshot,
)
from companion.core.photos import PhotoService
from companion.core.platform_settings import (
    DASHBOARD_URL_PLACEHOLDER,
    MESSAGE_WAIT_SECONDS,
    REPLY_FAILED_MESSAGE,
    TYPING_REPEAT_SECONDS,
    UNKNOWN_TELEGRAM_USER_REPLY,
    UNSUPPORTED_MESSAGE_REPLY,
)
from companion.core.ports import ChatChannel, Repositories, Timer, UserWorkQueue
from companion.core.reply_attempt import ReplyAttempt, ReplyDroppedError
from companion.core.reply_gate import ReplyGate, ReplyNeeded, Stopped
from companion.core.reply_service import ReplyService
from companion.core.sticker_adding import StickerAdding
from companion.core.stickers import sticker_message_text
from companion.core.telegram_connection import TelegramConnectionService
from companion.core.typing_keeper import TypingKeeper
from companion.core.user_snapshot import UserSnapshotLoader

logger = logging.getLogger(__name__)

MESSAGE_WAIT_PREFIX = "message:"
TEXTS_LINE_PREFIX = "texts:"
REPLIES_LINE_PREFIX = "replies:"


def message_wait_key(user_id: UUID) -> str:
    """Name the wait for a User to pause, so each new text restarts it.

    Args:
        user_id: The User.

    Returns:
        The timer key for that User's Message wait.
    """
    return f"{MESSAGE_WAIT_PREFIX}{user_id}"


def texts_line_key(sender_id: int) -> str:
    """Name the line of work that handles what one sender sends, in order.

    Args:
        sender_id: The sender's chat channel ID.

    Returns:
        The work queue key for that sender's messages.
    """
    return f"{TEXTS_LINE_PREFIX}{sender_id}"


def replies_line_key(user_id: UUID) -> str:
    """Name the line of work that writes one User's replies, in order.

    Args:
        user_id: The User.

    Returns:
        The work queue key for that User's replies.
    """
    return f"{REPLIES_LINE_PREFIX}{user_id}"


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
        trace: The Model Call Log trace every model call for it goes in,
            from the first text's Safeguard check to the reply.
        house_rules: What the house rules said to a dropped reply to it;
            None until a reply passes them.
    """

    chat_id: int
    conversation_id: UUID | None = None
    texts: list[str] = field(default_factory=list)
    album_items: list[IncomingMessage] = field(default_factory=list)
    trace: ModelCallTrace = field(
        default_factory=lambda: start_trace(TraceKind.MESSAGE)
    )
    house_rules: ReplyNeeded | None = None

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
    is never held back by the wait or by a reply being written. The work
    runs on the User work queue, never on the caller's thread: a sender's
    messages are handled one at a time, in order, on one line, and a User's
    replies are written one at a time on another. A text that arrives while
    a reply is being written, before any of it is sent, drops that reply,
    and the Message is answered again with every text once the User pauses;
    once part of a reply is sent, a new text starts the next Message. The
    texts waiting to be answered, and the reply being written, are only
    read and changed under one guard, since texts are checked while a reply
    is written. From the first text until something is sent back, typing is
    shown again every `typing_repeat_seconds`, so the chat never looks dead.
    """

    def __init__(
        self,
        telegram_connections: TelegramConnectionService,
        repositories: Repositories,
        reply_gate: ReplyGate,
        reply_service: ReplyService,
        chat_channel: ChatChannel,
        typing_keeper: TypingKeeper,
        sticker_adding: StickerAdding,
        photo_service: PhotoService,
        user_snapshots: UserSnapshotLoader,
        timer: Timer,
        work_queue: UserWorkQueue,
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
            typing_keeper: Keeps typing shown while a Message is answered.
            sticker_adding: Adds the stickers Admins send in adding mode or
                reply "add this" to.
            photo_service: Describes the photos Users send.
            user_snapshots: Reads the User once at the start of each turn.
            timer: Waits for the User to pause before answering their Message.
            work_queue: Runs each sender's messages, and each User's replies,
                in order, apart from the caller's thread.
            dashboard_url: The Dashboard's address, put into some replies.
        """
        self._telegram_connections = telegram_connections
        self._sticker_adding = sticker_adding
        self._photo_service = photo_service
        self._user_snapshots = user_snapshots
        self._timer = timer
        self._work_queue = work_queue
        self._repositories = repositories
        self._reply_gate = reply_gate
        self._reply_service = reply_service
        self._chat_channel = chat_channel
        self._typing_keeper = typing_keeper
        self._dashboard_url = dashboard_url
        self._pending_messages: dict[UUID, PendingMessage] = {}
        self._messages_not_yet_handled: Counter[UUID] = Counter()
        self._answers_held_back: set[UUID] = set()
        self._replies_being_written: dict[UUID, ReplyAttempt] = {}
        self._pending_messages_guard = threading.Lock()

    def handle(self, message: IncomingMessage) -> None:
        """Add an incoming message to its sender's line of work, and return at once.

        `/start <token>` makes a Telegram Connection. Anyone else without a
        Telegram Connection is pointed to the Dashboard to sign up. A
        connected User's message counts as not yet handled from now until
        its turn ends, so their Message isn't answered without it.

        Args:
            message: The incoming message.
        """
        line_key = texts_line_key(message.sender_id)
        if self._telegram_connections.is_start_command(message):
            self._work_queue.add(
                line_key, lambda: self._telegram_connections.handle_start(message)
            )
            return
        connection = self._repositories.telegram_connections.get_by_telegram_user(
            message.sender_id
        )
        if connection is None:
            self._work_queue.add(line_key, lambda: self._point_to_dashboard(message))
            return
        user_id = connection.user_id
        with self._pending_messages_guard:
            self._messages_not_yet_handled[user_id] += 1
        self._work_queue.add(line_key, lambda: self._receive(user_id, message))

    def _point_to_dashboard(self, message: IncomingMessage) -> None:
        """Tell someone without a Telegram Connection to sign up on the Dashboard.

        Args:
            message: Their message.
        """
        reply = self._repositories.platform_settings.load().get(
            UNKNOWN_TELEGRAM_USER_REPLY
        )
        self._chat_channel.send_text(
            message.chat_id,
            reply.replace(DASHBOARD_URL_PLACEHOLDER, self._dashboard_url),
        )

    def _receive(self, user_id: UUID, message: IncomingMessage) -> None:
        """Handle one message from a connected User, on their line of work.

        A sticker from an Admin in adding mode goes into the Sticker Library;
        any other message ends adding mode, with a summary of what was added,
        and is then handled as normal. An Admin's "add this" reply to a
        sticker adds it. A voice note, video or other message the Companion
        can't read gets the unsupported reply, unless it has a caption, which
        is answered instead. Anything else joins their Message: a photo is
        described first, so the Safeguard and the reply read what it shows;
        an Album's photos are described and checked together once the User
        pauses. If saving or checking a text fails, the User gets a short
        fallback reply instead of silence.

        Args:
            user_id: The User who sent it.
            message: The incoming message.
        """
        try:
            self._receive_from_user(user_id, message)
        finally:
            self._finish_handling(user_id)

    def _receive_from_user(self, user_id: UUID, message: IncomingMessage) -> None:
        """Send a connected User's message where it belongs.

        Args:
            user_id: The User who sent it.
            message: The incoming message.
        """
        if message.kind == MessageKind.STICKER and self._sticker_adding.add_if_adding(
            user_id, message
        ):
            return
        self._sticker_adding.finish(user_id)
        if self._sticker_adding.add_if_asked(user_id, message):
            return
        if message.album_id is not None:
            self._hold_album_item(user_id, message)
            return
        if message.kind == MessageKind.UNSUPPORTED and not message.text.strip():
            self._chat_channel.send_text(
                message.chat_id,
                self._repositories.platform_settings.load().get(
                    UNSUPPORTED_MESSAGE_REPLY
                ),
            )
            return
        self._screen_text(user_id, message)

    def _hold_album_item(self, user_id: UUID, message: IncomingMessage) -> None:
        """Add an Album's photo or file to the User's Message and restart the wait.

        A reply being written to the Message, none of it sent yet, starts
        over with the photo or file in it.

        Args:
            user_id: The User who sent it.
            message: The photo or file message, with its Album ID.
        """
        self._start_over_reply_being_written(user_id)
        with self._pending_messages_guard:
            pending = self._pending_messages.setdefault(
                user_id, PendingMessage(chat_id=message.chat_id)
            )
            pending.album_items.append(message)
        self._restart_wait(user_id, self._repositories.platform_settings.load())

    def _screen_text(self, user_id: UUID, message: IncomingMessage) -> None:
        """Save a text and check it for crisis now, then restart the wait.

        A reply being written to the Message, none of it sent yet, starts
        over with this text in it. From when the text arrives until it is
        checked, the wait ending doesn't answer the Message, so a slow check
        or a busy queue never splits it.
        A crisis gets the Crisis Reply straight away and drops the rest of
        the User's Message, so it isn't answered normally, and a reply being
        written to it. A check that fails gets the fallback reply
        and drops the rest of the Message too.

        Args:
            user_id: The User who sent it.
            message: The incoming message.
        """
        self._start_over_reply_being_written(user_id)
        settings = self._repositories.platform_settings.load()
        self._typing_keeper.keep_up(
            message.chat_id, settings.get(TYPING_REPEAT_SECONDS)
        )
        with self._pending_messages_guard:
            trace = self._pending_messages.setdefault(
                user_id, PendingMessage(chat_id=message.chat_id)
            ).trace
        try:
            snapshot = self._user_snapshots.load(user_id, settings, trace)
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
        self._restart_wait(user_id, settings)

    def _finish_handling(self, user_id: UUID) -> None:
        """Count one of the User's messages as handled.

        Once all of them are, an answer held back for them is added to the
        User's line of replies, unless a new wait was started meanwhile.

        Args:
            user_id: The User.
        """
        with self._pending_messages_guard:
            self._messages_not_yet_handled[user_id] -= 1
            if self._messages_not_yet_handled[user_id]:
                return
            del self._messages_not_yet_handled[user_id]
            if user_id not in self._answers_held_back:
                return
            self._answers_held_back.discard(user_id)
        self._queue_answer(user_id)

    def _drop_pending_message(self, user_id: UUID) -> None:
        """Forget what the User has sent so far, so it isn't answered normally.

        Args:
            user_id: The User.
        """
        with self._pending_messages_guard:
            self._pending_messages.pop(user_id, None)

    def _start_over_reply_being_written(self, user_id: UUID) -> None:
        """Drop the User's reply being written, if none of it is sent yet.

        Its Message stays waiting, so it is answered again with every text
        once the User pauses.

        Args:
            user_id: The User.
        """
        with self._pending_messages_guard:
            attempt = self._replies_being_written.get(user_id)
        if attempt is not None:
            attempt.drop()

    def _start_reply(self, user_id: UUID) -> tuple[PendingMessage, ReplyAttempt] | None:
        """Start a try at answering the User's Message, unless a message isn't handled.

        The Message stays waiting until the reply starts being sent, so a
        text that drops the try joins it.

        Args:
            user_id: The User.

        Returns:
            The Message and the try at answering it, or None if there is no
            Message or one of the User's messages is not yet handled; the
            answer is then held back until it is.
        """
        with self._pending_messages_guard:
            if self._messages_not_yet_handled[user_id]:
                self._answers_held_back.add(user_id)
                return None
            pending = self._pending_messages.get(user_id)
            if pending is None:
                return None
            attempt = ReplyAttempt(
                on_sending=lambda: self._forget_answered_message(user_id, pending),
                house_rules=pending.house_rules,
            )
            self._replies_being_written[user_id] = attempt
            return pending, attempt

    def _forget_answered_message(self, user_id: UUID, pending: PendingMessage) -> None:
        """Stop the User's answered Message from waiting, so new texts start the next.

        Args:
            user_id: The User.
            pending: The Message that was answered.
        """
        with self._pending_messages_guard:
            if self._pending_messages.get(user_id) is pending:
                del self._pending_messages[user_id]

    def _end_reply(
        self, user_id: UUID, pending: PendingMessage, attempt: ReplyAttempt
    ) -> bool:
        """End a try at answering the User's Message.

        A Message whose try wasn't dropped stops waiting. A dropped one keeps
        waiting, with what the house rules said, to be answered again.

        Args:
            user_id: The User.
            pending: The Message the try answered.
            attempt: The try.

        Returns:
            True if a new text dropped the try.
        """
        with self._pending_messages_guard:
            was_dropped = attempt.finish()
            del self._replies_being_written[user_id]
            pending.house_rules = attempt.house_rules
            if not was_dropped and self._pending_messages.get(user_id) is pending:
                del self._pending_messages[user_id]
        return was_dropped

    def _restart_wait(self, user_id: UUID, settings: PlatformSettings) -> None:
        """Start the wait for the User to pause, restarting any wait under way.

        When the wait ends, answering the Message is added to the User's
        line of replies. A new wait replaces an answer held back.

        Args:
            user_id: The User.
            settings: The platform settings, which say how long to wait.
        """
        with self._pending_messages_guard:
            self._answers_held_back.discard(user_id)
        self._timer.start(
            message_wait_key(user_id),
            settings.get(MESSAGE_WAIT_SECONDS),
            lambda: self._queue_answer(user_id),
        )

    def _queue_answer(self, user_id: UUID) -> None:
        """Add answering the User's Message to their line of replies.

        Args:
            user_id: The User.
        """
        self._work_queue.add(
            replies_line_key(user_id), lambda: self._answer_message(user_id)
        )

    def _answer_message(self, user_id: UUID) -> None:
        """Answer everything the User sent before pausing with one reply.

        The platform settings and the User are read once, when the reply
        starts, and that snapshot is used for the whole reply. If a new text
        drops the reply before any of it is sent, nothing more is sent: the
        new text restarts the wait, and the Message is answered again then.
        If the reply fails the User gets a short fallback reply instead of
        silence, unless a new text dropped it meanwhile, since it is then
        answered again. Typing is kept up until something is sent, and stops once
        the answer ends, unless the reply was dropped.

        Args:
            user_id: The User who paused.
        """
        started = self._start_reply(user_id)
        if started is None:
            return
        pending, attempt = started
        settings = self._repositories.platform_settings.load()
        self._typing_keeper.keep_up(
            pending.chat_id, settings.get(TYPING_REPEAT_SECONDS)
        )
        failed = False
        try:
            self._try_answer(user_id, pending, attempt, settings)
        except ReplyDroppedError:
            logger.info("A new text started a User's reply over")
        except Exception:
            logger.exception("Could not answer a Message from a User")
            failed = True
        was_dropped = self._end_reply(user_id, pending, attempt)
        if was_dropped:
            return
        if failed:
            self._chat_channel.send_text(
                pending.chat_id, settings.get(REPLY_FAILED_MESSAGE)
            )
        self._typing_keeper.stop(pending.chat_id)

    def _try_answer(
        self,
        user_id: UUID,
        pending: PendingMessage,
        attempt: ReplyAttempt,
        settings: PlatformSettings,
    ) -> None:
        """Try once to answer the User's Message.

        Any Albums are described and checked for crisis first, each once,
        even if the try is dropped; a crisis gets the Crisis Reply and drops
        the rest of the Message, so it isn't answered normally. An Album with
        no photos and no caption gets the unsupported reply.

        Args:
            user_id: The User who paused.
            pending: Their Message.
            attempt: This try at answering it.
            settings: The platform settings, read once for the reply.

        Raises:
            ReplyDroppedError: If a new text dropped the try before any of
                the reply was sent.
        """
        snapshot = self._user_snapshots.load(user_id, settings, pending.trace)
        with self._pending_messages_guard:
            album_items = list(pending.album_items)
        for items in group_albums(album_items):
            album_text = self._album_text_to_screen(snapshot, pending.chat_id, items)
            if album_text is None:
                self._remove_album_items(pending, items)
                continue
            result = self._reply_gate.screen(album_text, snapshot)
            self._remove_album_items(pending, items)
            if isinstance(result, Stopped):
                self._drop_pending_message(user_id)
                return
            with self._pending_messages_guard:
                pending.add_screened(result.conversation_id, album_text.text)
        with self._pending_messages_guard:
            conversation_id = pending.conversation_id
            text = "\n".join(pending.texts)
        if conversation_id is None:
            return
        self._reply_service.handle(
            MessageToAnswer(
                user_id=user_id,
                chat_id=pending.chat_id,
                conversation_id=conversation_id,
                text=text,
            ),
            snapshot,
            attempt,
        )

    def _remove_album_items(
        self, pending: PendingMessage, items: Sequence[IncomingMessage]
    ) -> None:
        """Take an Album's items out of a Message once they are screened.

        Args:
            pending: The Message.
            items: The Album's items.
        """
        with self._pending_messages_guard:
            pending.album_items = [
                item
                for item in pending.album_items
                if not any(item is screened for screened in items)
            ]

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
