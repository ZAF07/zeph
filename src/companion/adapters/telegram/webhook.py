import hmac
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Header, HTTPException, status

from companion.adapters.telegram.chat_channel import parse_sticker
from companion.core.incoming_messages import IncomingMessageHandler
from companion.core.models import (
    ChannelPhoto,
    ChannelSticker,
    IncomingMessage,
    MessageKind,
    RepliedToSender,
    RepliedToText,
)

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
REPLIED_TO_TEXT_MAX_CHARACTERS = 500


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


def parse_replied_sticker(message: dict[str, Any]) -> ChannelSticker | None:
    """Read the sticker a Telegram message replies to, if it replies to one.

    Args:
        message: The Telegram message.

    Returns:
        The sticker, or None if the message doesn't reply to a sticker.
    """
    replied = message.get("reply_to_message")
    if not isinstance(replied, dict):
        return None
    sticker = replied.get("sticker")
    return parse_sticker(sticker) if isinstance(sticker, dict) else None


def cut_short(text: str, max_characters: int) -> str:
    """Cut a text to at most a number of characters, marking where it was cut.

    Args:
        text: The text.
        max_characters: How many characters to keep.

    Returns:
        The text, or its start followed by "…" when it was longer.
    """
    return text if len(text) <= max_characters else f"{text[:max_characters]}…"


def replied_to_kind_and_text(replied: dict[str, Any]) -> tuple[MessageKind, str]:
    """Read what kind of message a reply points at and what it said.

    Args:
        replied: The Telegram message replied to.

    Returns:
        Its kind and its text, caption or sticker emoji; "" if it has none.
    """
    sticker = replied.get("sticker")
    if isinstance(sticker, dict):
        emoji = sticker.get("emoji")
        return MessageKind.STICKER, emoji if isinstance(emoji, str) else ""
    text = replied.get("text")
    if isinstance(text, str):
        return MessageKind.TEXT, text
    caption = replied.get("caption")
    caption_text = caption if isinstance(caption, str) else ""
    if parse_photo(replied) is not None:
        return MessageKind.PHOTO, caption_text
    return MessageKind.UNSUPPORTED, caption_text


def parse_replied_to(message: dict[str, Any]) -> RepliedToText | None:
    """Read the earlier text a Telegram message replies to, if it replies to one.

    It is read only from the update, never from saved messages, so it works
    however old the earlier text is. A bot sent it if the sender is a bot,
    which in a private chat is the Companion. The part the User highlighted
    is read instead of the whole text.

    Args:
        message: The Telegram message.

    Returns:
        The Replied-to Text, or None if the message doesn't reply to one.
    """
    replied = message.get("reply_to_message")
    if not isinstance(replied, dict):
        return None
    sender = replied.get("from")
    from_bot = isinstance(sender, dict) and bool(sender.get("is_bot"))
    kind, text = replied_to_kind_and_text(replied)
    quote = message.get("quote")
    if isinstance(quote, dict) and isinstance(quote.get("text"), str):
        text = quote["text"]
    return RepliedToText(
        sender=RepliedToSender.COMPANION if from_bot else RepliedToSender.USER,
        sent_at=datetime.fromtimestamp(int(replied.get("date", 0)), UTC),
        kind=kind,
        text=cut_short(text, REPLIED_TO_TEXT_MAX_CHARACTERS),
    )


def parse_update(update: dict[str, Any]) -> IncomingMessage | None:
    """Turn a Telegram update into a channel-neutral incoming message.

    Text, stickers and photos are read, with the earlier text they reply
    to, if any, and the sticker a text replies to. A voice note, video, GIF
    or other attachment is an unsupported message that keeps its caption. A photo or
    attachment sent with others at once keeps the album ID they share.

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
    message_id = int(message.get("message_id", 0))
    text = message.get("text")
    if isinstance(text, str):
        return IncomingMessage(
            sender_id,
            chat_id,
            username,
            text,
            message_id=message_id,
            replied_sticker=parse_replied_sticker(message),
            replied_to=parse_replied_to(message),
        )
    sticker = message.get("sticker")
    if isinstance(sticker, dict):
        return IncomingMessage(
            sender_id,
            chat_id,
            username,
            text="",
            kind=MessageKind.STICKER,
            sticker=parse_sticker(sticker),
            message_id=message_id,
            replied_to=parse_replied_to(message),
        )
    caption = message.get("caption")
    media_group_id = message.get("media_group_id")
    album_id = str(media_group_id) if media_group_id is not None else None
    photo = parse_photo(message)
    if photo is not None:
        return IncomingMessage(
            sender_id,
            chat_id,
            username,
            text=caption if isinstance(caption, str) else "",
            kind=MessageKind.PHOTO,
            photo=photo,
            album_id=album_id,
            message_id=message_id,
            replied_to=parse_replied_to(message),
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
        album_id=album_id,
        message_id=message_id,
    )


def build_telegram_webhook_router(
    handler: IncomingMessageHandler, webhook_secret: str
) -> APIRouter:
    """Build the route Telegram posts updates to.

    Requests without the right secret token header are refused with 401.
    Each message is only handed to the handler, which adds it to the User
    work queue, so neither Telegram nor a web thread waits while the
    Companion composes a reply.

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
        secret_token: Annotated[str | None, Header(alias=SECRET_HEADER)] = None,
    ) -> dict[str, bool]:
        """Receive one Telegram update.

        Args:
            update: The JSON body Telegram posted.
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
            handler.handle(message)
        return {"ok": True}

    return router
