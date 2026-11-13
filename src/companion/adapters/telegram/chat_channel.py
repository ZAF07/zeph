from pathlib import PurePosixPath
from typing import Any

import httpx

from companion.core.models import ChannelSticker, PhotoImage, StickerImage

TELEGRAM_API_URL = "https://api.telegram.org"
IMAGE_MEDIA_TYPES = {
    ".webp": "image/webp",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

IMAGE_SIGNATURES = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
)


class PhotoDownloadError(Exception):
    """Raised when Telegram gives no file, or a file that isn't a photo."""


def photo_media_type(content: bytes) -> str | None:
    """Tell what kind of image a file is from its first bytes.

    Args:
        content: The file's bytes.

    Returns:
        "image/jpeg", "image/png" or "image/webp", or None for anything else.
    """
    for signature, media_type in IMAGE_SIGNATURES:
        if content.startswith(signature):
            return media_type
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    return None


def parse_sticker(sticker: dict[str, Any]) -> ChannelSticker:
    """Turn a Telegram sticker object into a channel-neutral sticker.

    A still sticker is its own image; an animated or video sticker is shown
    by its thumbnail, if it has one.

    Args:
        sticker: The sticker object from the Bot API.

    Returns:
        The sticker.
    """
    file_id = str(sticker["file_id"])
    thumbnail = sticker.get("thumbnail")
    is_still = not sticker.get("is_animated") and not sticker.get("is_video")
    if is_still:
        preview_file_id: str | None = file_id
    elif isinstance(thumbnail, dict):
        preview_file_id = str(thumbnail["file_id"])
    else:
        preview_file_id = None
    emoji = sticker.get("emoji")
    set_name = sticker.get("set_name")
    return ChannelSticker(
        file_id=file_id,
        file_unique_id=str(sticker["file_unique_id"]),
        emoji=emoji if isinstance(emoji, str) else None,
        set_name=set_name if isinstance(set_name, str) else None,
        preview_file_id=preview_file_id,
    )


class TelegramChatChannel:
    """Sends messages through the Telegram Bot API."""

    def __init__(self, bot_token: str, http_client: httpx.Client | None = None) -> None:
        """Set up the channel.

        Args:
            bot_token: The bot token from BotFather.
            http_client: The HTTP client to use; a new one is made if not given.
        """
        self._bot_url = f"{TELEGRAM_API_URL}/bot{bot_token}"
        self._file_url = f"{TELEGRAM_API_URL}/file/bot{bot_token}"
        self._http = http_client or httpx.Client(timeout=10)

    def send_text(self, chat_id: int, text: str) -> None:
        """Send one text message.

        Args:
            chat_id: The chat to send to.
            text: The message text.
        """
        self._call("sendMessage", {"chat_id": chat_id, "text": text})

    def show_typing(self, chat_id: int) -> None:
        """Show that the Companion is typing.

        Args:
            chat_id: The chat to show it in.
        """
        self._call("sendChatAction", {"chat_id": chat_id, "action": "typing"})

    def send_sticker(self, chat_id: int, file_id: str) -> None:
        """Send one sticker.

        Args:
            chat_id: The chat to send to.
            file_id: The sticker's file ID.
        """
        self._call("sendSticker", {"chat_id": chat_id, "sticker": file_id})

    def get_sticker_set(self, name: str) -> list[ChannelSticker] | None:
        """Look up every sticker in a sticker set.

        Args:
            name: The set's name.

        Returns:
            Its stickers in order, or None if Telegram has no such set.

        Raises:
            httpx.HTTPError: If Telegram can't be reached or fails.
        """
        try:
            result = self._call("getStickerSet", {"name": name})
        except httpx.HTTPStatusError as error:
            if error.response.status_code == httpx.codes.BAD_REQUEST:
                return None
            raise
        stickers = result.get("stickers")
        if not isinstance(stickers, list):
            return None
        return [parse_sticker(sticker) for sticker in stickers]

    def get_sticker_image(self, file_id: str) -> StickerImage | None:
        """Download an image of a sticker.

        Args:
            file_id: The image's file ID.

        Returns:
            The image, or None if it isn't a WebP, JPEG or PNG image.

        Raises:
            httpx.HTTPError: If Telegram can't be reached or fails.
        """
        file_path = self._file_path(file_id)
        if file_path is None:
            return None
        media_type = IMAGE_MEDIA_TYPES.get(PurePosixPath(file_path).suffix.lower())
        if media_type is None:
            return None
        return StickerImage(content=self._download(file_path), media_type=media_type)

    def download_photo(self, file_id: str) -> PhotoImage:
        """Download a photo someone sent.

        The kind of image is read from the file itself, since a file sent as
        a document can have any name.

        Args:
            file_id: The photo's file ID.

        Returns:
            The photo's image.

        Raises:
            httpx.HTTPError: If Telegram can't be reached or fails.
            PhotoDownloadError: If Telegram gives no file, or it isn't a
                JPEG, PNG or WebP image.
        """
        file_path = self._file_path(file_id)
        if file_path is None:
            raise PhotoDownloadError("Telegram gave no file path for the photo")
        content = self._download(file_path)
        media_type = photo_media_type(content)
        if media_type is None:
            raise PhotoDownloadError("The file is not a JPEG, PNG or WebP image")
        return PhotoImage(content=content, media_type=media_type)

    def register_webhook(self, url: str, secret_token: str) -> None:
        """Tell Telegram where to post updates.

        Args:
            url: The public webhook address.
            secret_token: The secret Telegram will send in each update's header.
        """
        self._call(
            "setWebhook",
            {"url": url, "secret_token": secret_token, "allowed_updates": ["message"]},
        )

    def get_bot_username(self) -> str:
        """Ask Telegram for the bot's @username.

        Returns:
            The bot's username.
        """
        result = self._call("getMe", {})
        return str(result["username"])

    def _file_path(self, file_id: str) -> str | None:
        """Ask Telegram where a file can be downloaded from.

        Args:
            file_id: The file's ID.

        Returns:
            The file's path on Telegram's file server, or None if it gave none.
        """
        file_path = self._call("getFile", {"file_id": file_id}).get("file_path")
        return file_path if isinstance(file_path, str) else None

    def _download(self, file_path: str) -> bytes:
        """Download a file from Telegram's file server.

        Args:
            file_path: The path `getFile` gave.

        Returns:
            The file's bytes.

        Raises:
            httpx.HTTPStatusError: If Telegram refuses the download.
        """
        response = self._http.get(f"{self._file_url}/{file_path}")
        response.raise_for_status()
        return response.content

    def _call(self, method: str, payload: dict[str, object]) -> dict[str, object]:
        """Call one Bot API method.

        Args:
            method: The Bot API method name.
            payload: The JSON body.

        Returns:
            The method's `result` value.

        Raises:
            httpx.HTTPStatusError: If Telegram refuses the call.
        """
        response = self._http.post(f"{self._bot_url}/{method}", json=payload)
        response.raise_for_status()
        body: dict[str, object] = response.json()
        result = body.get("result")
        return result if isinstance(result, dict) else {}
