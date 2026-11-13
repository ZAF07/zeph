import hmac
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Body, Header, HTTPException, status

from companion.adapters.telegram.chat_channel import parse_sticker
from companion.core.incoming_messages import IncomingMessageHandler
from companion.core.models import ChannelPhoto, IncomingMessage, MessageKind

SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"
BOT_DOWNLOAD_LIMIT_BYTES = 20 * 1024 * 1024
PHOTO_FILE_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
ATTACHMENT_NAMES = (
    ("voice", "voice note"),
    ("video_note", "video message"),
    ("video", "video"),
    ("animation", "GIF"),
    ("audio", "audio"),
    ("document", "file"),
    ("location", "location"),
    ("contact", "contact"),
    ("poll", "poll"),
    ("dice", "dice"),
    ("story", "story"),
)


def attachment_name(message: dict[str, Any]) -> str | None:
    """Name what a Telegram message holds instead of text.

    Args:
        message: The Telegram message.

    Returns:
        E.g. "voice note" or "video"; None for anything else, like a pinned
        message or other service message.
    """
    for field, name in ATTACHMENT_NAMES:
        if field in message:
            return name
    return None


def parse_photo(message: dict[str, Any]) -> ChannelPhoto | None:
    """Read the photo in a Telegram message, if it has one.

    A normal photo comes in several sizes; the largest is read. A JPEG, PNG
    or WebP image sent as a file is a photo too, but one over the bot
    download limit can't be viewed. A GIF is an animation, not a photo.

    Args:
        message: The Telegram message.

    Returns:
        The photo, or None if the message has none.
    """
    sizes = message.get("photo")
    if isinstance(sizes, list) and sizes:
        largest = max(
            sizes, key=lambda size: size.get("width", 0) * size.get("height", 0)
        )
        return ChannelPhoto(
            file_id=str(largest["file_id"]),
            file_unique_id=str(largest["file_unique_id"]),
        )
    document = message.get("document")
    if (
        isinstance(document, dict)
        and "animation" not in message
        and document.get("mime_type") in PHOTO_FILE_TYPES
    ):
        file_size = document.get("file_size")
        return ChannelPhoto(
            file_id=str(document["file_id"]),
            file_unique_id=str(document["file_unique_id"]),
            too_big_to_download=isinstance(file_size, int)
            and file_size > BOT_DOWNLOAD_LIMIT_BYTES,
        )
    return None


def parse_update(update: dict[str, Any]) -> IncomingMessage | None:
    """Turn a Telegram update into a channel-neutral incoming message.

    Text, stickers and photos are read; a voice note, video, GIF or other
    attachment is an unsupported message that keeps its caption.

    Args:
        update: The JSON body Telegram posted to the webhook.

    Returns:
        The incoming message, or None for updates that are not messages
        and for service messages, like a pinned message.
    """
    message = update.get("message")
    if not isinstance(message, dict):
        return None
    sender = message.get("from")
    chat = message.get("chat")
    if not isinstance(sender, dict) or not isinstance(chat, dict):
        return None
    sender_id = int(sender["id"])
    chat_id = int(chat["id"])
    username = sender.get("username")
    text = message.get("text")
    if isinstance(text, str):
        return IncomingMessage(sender_id, chat_id, username, text)
    sticker = message.get("sticker")
    if isinstance(sticker, dict):
        return IncomingMessage(
            sender_id,
            chat_id,
            username,
            text="",
            kind=MessageKind.STICKER,
            sticker=parse_sticker(sticker),
        )
    caption = message.get("caption")
    photo = parse_photo(message)
    if photo is not None:
        return IncomingMessage(
            sender_id,
            chat_id,
            username,
            text=caption if isinstance(caption, str) else "",
            kind=MessageKind.PHOTO,
            photo=photo,
        )
    attachment = attachment_name(message)
    if attachment is None:
        return None
    return IncomingMessage(
        sender_id,
        chat_id,
        username,
        text=caption if isinstance(caption, str) else "",
        kind=MessageKind.UNSUPPORTED,
        attachment=attachment,
    )


def build_telegram_webhook_router(
    handler: IncomingMessageHandler, webhook_secret: str
) -> APIRouter:
    """Build the route Telegram posts updates to.

    Requests without the right secret token header are refused with 401.
    Each message is handled after the response is sent, so Telegram is not
    kept waiting while the Companion composes a reply.

    Args:
        handler: Handles each incoming message.
        webhook_secret: The secret token Telegram sends with every update.

    Returns:
        The router.
    """
    router = APIRouter()

    @router.post("/telegram/webhook")
    def receive_update(
        update: Annotated[dict[str, Any], Body()],
        background_tasks: BackgroundTasks,
        secret_token: Annotated[str | None, Header(alias=SECRET_HEADER)] = None,
    ) -> dict[str, bool]:
        """Receive one Telegram update.

        Args:
            update: The JSON body Telegram posted.
            background_tasks: Runs the handler after the response is sent.
            secret_token: The secret token header Telegram sends.

        Returns:
            An acknowledgement Telegram ignores.
        """
        if secret_token is None or not hmac.compare_digest(
            secret_token, webhook_secret
        ):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bad secret token")
        message = parse_update(update)
        if message is not None:
            background_tasks.add_task(handler.handle, message)
        return {"ok": True}

    return router
