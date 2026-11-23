import logging

from companion.core.models import ChannelSticker, PhotoImage, StickerImage

logger = logging.getLogger(__name__)

SENT_TEXT_LOG_PREFIX = "Load test: sent a text to chat "
PLACEHOLDER_PHOTO = b"load-test photo"


class LoggingChatChannel:
    """Chat channel for load tests: logs what it would send, sends nothing.

    Each text is logged with its chat, which `make load-test` reads to see
    which Messages were answered and when. Nothing reaches Telegram.
    """

    def send_text(self, chat_id: int, text: str) -> None:
        """Log that a text was sent.

        Args:
            chat_id: The chat it is for.
            text: The text; not logged.
        """
        logger.info("%s%s", SENT_TEXT_LOG_PREFIX, chat_id)

    def show_typing(self, chat_id: int) -> None:
        """Do nothing; typing is shown too often to log.

        Args:
            chat_id: The chat.
        """

    def send_sticker(self, chat_id: int, file_id: str) -> None:
        """Log that a sticker was sent.

        Args:
            chat_id: The chat it is for.
            file_id: The sticker's file ID.
        """
        logger.info("Load test: sent a sticker to chat %s", chat_id)

    def react(self, chat_id: int, message_id: int, emoji: str) -> None:
        """Log that a reaction was put on a message.

        Args:
            chat_id: The chat the message is in.
            message_id: The message.
            emoji: The reaction.
        """
        logger.info("Load test: reacted in chat %s", chat_id)

    def send_photo(self, chat_id: int, file_id: str) -> None:
        """Log that a photo was sent.

        Args:
            chat_id: The chat it is for.
            file_id: The photo's file ID.
        """
        logger.info("Load test: sent a photo to chat %s", chat_id)

    def get_sticker_set(self, name: str) -> list[ChannelSticker] | None:
        """Know no sticker sets.

        Args:
            name: The set's name.

        Returns:
            None.
        """
        return None

    def get_sticker_image(self, file_id: str) -> StickerImage | None:
        """Know no sticker images.

        Args:
            file_id: The image's file ID.

        Returns:
            None.
        """
        return None

    def download_photo(self, file_id: str) -> PhotoImage:
        """Give placeholder bytes for any photo.

        The load-test photo viewer never reads them.

        Args:
            file_id: The photo's file ID.

        Returns:
            The placeholder image.
        """
        return PhotoImage(content=PLACEHOLDER_PHOTO, media_type="image/jpeg")
