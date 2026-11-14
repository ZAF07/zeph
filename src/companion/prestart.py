import sys
from collections.abc import Callable
from functools import partial

from companion.adapters.knowledge_seed import read_knowledge_seed
from companion.adapters.postgres.database import (
    migrate,
    seed_check_in_kinds,
    seed_helplines,
    seed_memory_categories,
    seed_needs,
    seed_platform_settings,
)
from companion.adapters.telegram.chat_channel import TelegramChatChannel
from companion.config import MissingSettingsError, Settings, load_settings
from companion.core.knowledge import KnowledgeService
from companion.main import (
    CHECK_IN_KINDS_SEED_FILE,
    HELPLINES_SEED_FILE,
    KNOWLEDGE_SEED_FILE,
    MEMORY_CATEGORIES_SEED_FILE,
    NEEDS_SEED_FILE,
    SEED_FILE,
    build_clock,
    build_database_engine,
    build_embedder,
    build_repositories,
    build_text_extractor,
    build_vector_store,
)


def register_telegram_webhook(
    settings: Settings, register_webhook: Callable[[str, str], None]
) -> None:
    """Point the bot's Telegram webhook at this backend, unless turned off.

    Only one stack can own the bot's webhook, so worktree stacks set
    `TELEGRAM_WEBHOOK_REGISTER=false` and leave it with the main stack.

    Args:
        settings: The settings holding the webhook address, secret and switch.
        register_webhook: Registers a webhook URL with its secret token.
    """
    if not settings.telegram_webhook_register:
        print("Telegram webhook registration is turned off; skipping it")
        return
    webhook_url = f"{settings.webhook_base_url.rstrip('/')}/telegram/webhook"
    register_webhook(webhook_url, settings.telegram_webhook_secret)
    print(f"Telegram webhook registered at {webhook_url}")


def prepare() -> None:
    """Get everything ready before the backend starts serving.

    Checks settings, migrates the database, loads seed data (embedding the
    starter Knowledge on first run, finishing any upload a restart
    interrupted and saving the text of documents uploaded before text was
    saved) and registers the Telegram webhook unless turned off.
    """
    settings = load_settings()
    migrate(settings.database_url)
    engine = build_database_engine(settings)
    seed_platform_settings(engine, SEED_FILE)
    seed_helplines(engine, HELPLINES_SEED_FILE)
    seed_memory_categories(engine, MEMORY_CATEGORIES_SEED_FILE)
    seed_check_in_kinds(engine, CHECK_IN_KINDS_SEED_FILE)
    seed_needs(engine, NEEDS_SEED_FILE)
    knowledge_service = KnowledgeService(
        repositories=build_repositories(settings, engine),
        text_extractor=build_text_extractor(settings),
        embedder=build_embedder(settings),
        vector_store=build_vector_store(settings, engine),
        clock=build_clock(settings),
    )
    knowledge_service.ingest_pending()
    knowledge_service.read_missing_texts()
    knowledge_service.seed_starter_set(
        partial(read_knowledge_seed, KNOWLEDGE_SEED_FILE)
    )
    engine.dispose()
    register_telegram_webhook(
        settings, TelegramChatChannel(settings.telegram_bot_token).register_webhook
    )


if __name__ == "__main__":
    try:
        prepare()
    except MissingSettingsError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
