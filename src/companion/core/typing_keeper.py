import logging
import threading
from collections import defaultdict

from companion.core.models import ChannelSticker, PhotoImage, StickerImage
from companion.core.ports import ChatChannel, Timer

logger = logging.getLogger(__name__)

TYPING_WAIT_PREFIX = "typing:"


def typing_wait_key(chat_id: int) -> str:
    """Name the wait before typing is shown again in a chat.

    Args:
        chat_id: The chat.

    Returns:
        The timer key for that chat's typing wait.
    """
    return f"{TYPING_WAIT_PREFIX}{chat_id}"


class TypingKeeper:
    """Chat channel that can keep "typing" shown in a chat while a reply is worked on.

    The chat channel hides typing after a few seconds, so `keep_up` shows it
    again every few seconds. It stops as soon as a text, sticker or photo is
    sent to that chat, or `stop` is called, so typing never shows after the
    message it led up to. Every call is passed on to the real chat channel.
    """

    def __init__(self, chat_channel: ChatChannel, timer: Timer) -> None:
        """Set up the keeper with no chat kept typing.

        Args:
            chat_channel: The real chat channel.
            timer: Waits between showing typing again.
        """
        self._chat_channel = chat_channel
        self._timer = timer
        self._chats_kept_typing: set[int] = set()
        self._chat_locks: defaultdict[int, threading.Lock] = defaultdict(threading.Lock)
        self._chat_locks_guard = threading.Lock()

    def keep_up(self, chat_id: int, every_seconds: float) -> None:
        """Show typing again every so often until a message is sent to the chat.

        Does nothing if the chat is already kept typing.

        Args:
            chat_id: The chat.
            every_seconds: How long to wait before showing typing again.
        """
        with self._lock_for(chat_id):
            if chat_id in self._chats_kept_typing:
                return
            self._chats_kept_typing.add(chat_id)
        self._wait_to_show_again(chat_id, every_seconds)

    def stop(self, chat_id: int) -> None:
        """Stop showing typing again in a chat.

        Waits for typing being shown right now, so none shows after this.

        Args:
            chat_id: The chat.
        """
        with self._lock_for(chat_id):
            self._chats_kept_typing.discard(chat_id)

    def send_text(self, chat_id: int, text: str) -> None:
        """Stop keeping typing up in the chat, then send one text message.

        Args:
            chat_id: The chat to send to.
            text: The message text.
        """
        self.stop(chat_id)
        self._chat_channel.send_text(chat_id, text)

    def show_typing(self, chat_id: int) -> None:
        """Show that the Companion is typing.

        Args:
            chat_id: The chat to show it in.
        """
        self._chat_channel.show_typing(chat_id)

    def send_sticker(self, chat_id: int, file_id: str) -> None:
        """Stop keeping typing up in the chat, then send one sticker.

        Args:
            chat_id: The chat to send to.
            file_id: The sticker's file ID.
        """
        self.stop(chat_id)
        self._chat_channel.send_sticker(chat_id, file_id)

    def react(self, chat_id: int, message_id: int, emoji: str) -> None:
        """Put an emoji reaction on a message someone sent.

        Args:
            chat_id: The chat the message is in.
            message_id: The message's ID.
            emoji: The reaction.
        """
        self._chat_channel.react(chat_id, message_id, emoji)

    def send_photo(self, chat_id: int, file_id: str) -> None:
        """Stop keeping typing up in the chat, then send one photo.

        Args:
            chat_id: The chat to send to.
            file_id: The photo's file ID.
        """
        self.stop(chat_id)
        self._chat_channel.send_photo(chat_id, file_id)

    def get_sticker_set(self, name: str) -> list[ChannelSticker] | None:
        """Look up every sticker in a sticker set.

        Args:
            name: The set's name.

        Returns:
            Its stickers in order, or None if there is no such set.
        """
        return self._chat_channel.get_sticker_set(name)

    def get_sticker_image(self, file_id: str) -> StickerImage | None:
        """Download an image of a sticker.

        Args:
            file_id: The image's file ID.

        Returns:
            The image, or None if it isn't one a browser can show.
        """
        return self._chat_channel.get_sticker_image(file_id)

    def download_photo(self, file_id: str) -> PhotoImage:
        """Download a photo someone sent.

        Args:
            file_id: The photo's file ID.

        Returns:
            The photo.
        """
        return self._chat_channel.download_photo(file_id)

    def _wait_to_show_again(self, chat_id: int, every_seconds: float) -> None:
        """Start the wait before typing is shown again in a chat.

        Args:
            chat_id: The chat.
            every_seconds: How long to wait.
        """
        self._timer.start(
            typing_wait_key(chat_id),
            every_seconds,
            lambda: self._show_again(chat_id, every_seconds),
        )

    def _show_again(self, chat_id: int, every_seconds: float) -> None:
        """Show typing again, then wait to show it once more, unless it was stopped.

        If showing typing fails, the error is logged and the next try still
        comes, so one failed call doesn't end it.

        Args:
            chat_id: The chat.
            every_seconds: How long to wait before the next time.
        """
        with self._lock_for(chat_id):
            if chat_id not in self._chats_kept_typing:
                return
            try:
                self._chat_channel.show_typing(chat_id)
            except Exception:
                logger.exception("Could not show typing again")
        self._wait_to_show_again(chat_id, every_seconds)

    def _lock_for(self, chat_id: int) -> threading.Lock:
        """Get the lock that keeps showing typing and stopping it in order for a chat.

        Args:
            chat_id: The chat.

        Returns:
            That chat's lock.
        """
        with self._chat_locks_guard:
            return self._chat_locks[chat_id]
