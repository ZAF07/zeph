import hmac
from typing import Annotated, Any

from fastapi import APIRouter, Body, Header, HTTPException, status

from companion.core.incoming_messages import IncomingMessageHandler
from companion.core.models import IncomingMessage

SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"


def parse_update(update: dict[str, Any]) -> IncomingMessage | None:
    """Turn a Telegram update into a channel-neutral incoming message.

    Args:
        update: The JSON body Telegram posted to the webhook.

    Returns:
        The incoming message, or None for updates that are not text messages.
    """
    message = update.get("message")
    if not isinstance(message, dict):
        return None
    text = message.get("text")
    sender = message.get("from")
    chat = message.get("chat")
    if not isinstance(text, str) or not isinstance(sender, dict):
        return None
    if not isinstance(chat, dict):
        return None
    return IncomingMessage(
        sender_id=int(sender["id"]),
        chat_id=int(chat["id"]),
        sender_username=sender.get("username"),
        text=text,
    )


def build_telegram_webhook_router(
    handler: IncomingMessageHandler, webhook_secret: str
) -> APIRouter:
    """Build the route Telegram posts updates to.

    Requests without the right secret token header are refused with 401.

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
