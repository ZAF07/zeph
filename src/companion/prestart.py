import sys
from functools import partial

from sqlalchemy import create_engine

from companion.adapters.knowledge_seed import read_knowledge_seed
from companion.adapters.postgres.database import (
    migrate,
    seed_helplines,
    seed_memory_categories,
    seed_platform_settings,
)
from companion.adapters.pypdf.text_extractor import PypdfTextExtractor
from companion.adapters.telegram.chat_channel import TelegramChatChannel
from companion.config import MissingSettingsError, load_settings
from companion.core.knowledge import KnowledgeService
from companion.main import (
    HELPLINES_SEED_FILE,
    KNOWLEDGE_SEED_FILE,
    MEMORY_CATEGORIES_SEED_FILE,
    SEED_FILE,
    build_clock,
    build_embedder,
    build_repositories,
    build_vector_store,
)


def prepare() -> None:
    """Get everything ready before the backend starts serving.

    Checks settings, migrates the database, loads seed data (embedding the
    starter Knowledge on first run) and registers the Telegram webhook.
    """
    settings = load_settings()
    migrate(settings.database_url)
    engine = create_engine(settings.database_url)
    seed_platform_settings(engine, SEED_FILE)
    seed_helplines(engine, HELPLINES_SEED_FILE)
    seed_memory_categories(engine, MEMORY_CATEGORIES_SEED_FILE)
    KnowledgeService(
        repositories=build_repositories(settings, engine),
        text_extractor=PypdfTextExtractor(),
        embedder=build_embedder(settings),
        vector_store=build_vector_store(settings, engine),
        clock=build_clock(settings),
    ).seed_starter_set(partial(read_knowledge_seed, KNOWLEDGE_SEED_FILE))
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
