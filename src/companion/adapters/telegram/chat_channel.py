import time
from collections.abc import Callable

import httpx

TELEGRAM_API_URL = "https://api.telegram.org"
TYPING_SECONDS_PER_CHARACTER = 0.04
MIN_TYPING_SECONDS = 0.8
MAX_TYPING_SECONDS = 3.0


def typing_pause_seconds(text: str) -> float:
    """Work out how long to show typing before sending a message.

    Longer messages take longer to "type", within a short range.

    Args:
        text: The message about to be sent.

    Returns:
        The pause in seconds.
    """
    pause = len(text) * TYPING_SECONDS_PER_CHARACTER
    return min(max(pause, MIN_TYPING_SECONDS), MAX_TYPING_SECONDS)


class TelegramChatChannel:
    """Sends messages through the Telegram Bot API."""

    def __init__(
        self,
        bot_token: str,
        http_client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Set up the channel.

        Args:
            bot_token: The bot token from BotFather.
            http_client: The HTTP client to use; a new one is made if not given.
            sleep: Waits a number of seconds; replaced in tests.
        """
        self._bot_url = f"{TELEGRAM_API_URL}/bot{bot_token}"
        self._http = http_client or httpx.Client(timeout=10)
        self._sleep = sleep

    def send_text(self, chat_id: int, text: str) -> None:
        """Send one text message.

        Args:
            chat_id: The chat to send to.
            text: The message text.
        """
        self._call("sendMessage", {"chat_id": chat_id, "text": text})

    def send_texts(self, chat_id: int, texts: list[str]) -> None:
        """Send several short messages in a row, typing before each later one.

        The first message goes straight away, since typing was already shown
        while the reply was being written.

        Args:
            chat_id: The chat to send to.
            texts: The message texts, in the order to send them.
        """
        for position, text in enumerate(texts):
            if position > 0:
                self.show_typing(chat_id)
                self._sleep(typing_pause_seconds(text))
            self.send_text(chat_id, text)

    def show_typing(self, chat_id: int) -> None:
        """Show that the Companion is typing.

        Args:
            chat_id: The chat to show it in.
        """
        self._call("sendChatAction", {"chat_id": chat_id, "action": "typing"})

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
