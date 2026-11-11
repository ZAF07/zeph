import sys

from sqlalchemy import create_engine

from companion.adapters.postgres.database import migrate, seed_platform_settings
from companion.adapters.telegram.chat_channel import TelegramChatChannel
from companion.config import MissingSettingsError, load_settings
from companion.main import SEED_FILE


def prepare() -> None:
    """Get everything ready before the backend starts serving.

    Checks settings, migrates the database, loads seed data and registers the
    Telegram webhook.
    """
    settings = load_settings()
    migrate(settings.database_url)
    engine = create_engine(settings.database_url)
    seed_platform_settings(engine, SEED_FILE)
    engine.dispose()
    webhook_url = f"{settings.webhook_base_url.rstrip('/')}/telegram/webhook"
    TelegramChatChannel(settings.telegram_bot_token).register_webhook(
        webhook_url, settings.telegram_webhook_secret
    )
    print(f"Telegram webhook registered at {webhook_url}")


if __name__ == "__main__":
    try:
        prepare()
    except MissingSettingsError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
