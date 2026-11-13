from companion.config import load_settings
from companion.prestart import register_telegram_webhook
from tests.test_config import COMPLETE_ENVIRONMENT


def test_webhook_is_registered_by_default() -> None:
    registered: list[tuple[str, str]] = []
    settings = load_settings(COMPLETE_ENVIRONMENT)

    register_telegram_webhook(
        settings, lambda url, secret: registered.append((url, secret))
    )

    assert registered == [("https://zeph.ngrok.app/telegram/webhook", "hook-secret")]


def test_webhook_is_not_registered_when_turned_off() -> None:
    registered: list[tuple[str, str]] = []
    settings = load_settings(
        {**COMPLETE_ENVIRONMENT, "TELEGRAM_WEBHOOK_REGISTER": "false"}
    )

    register_telegram_webhook(
        settings, lambda url, secret: registered.append((url, secret))
    )

    assert registered == []
