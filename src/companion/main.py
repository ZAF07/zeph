from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy import Engine, create_engine

from companion.adapters.clerk.auth_verifier import ClerkAuthVerifier
from companion.adapters.clock import SystemClock
from companion.adapters.deepseek.chat_model import DeepSeekChatModel
from companion.adapters.fastembed.embedder import FastEmbedEmbedder
from companion.adapters.langgraph.conversation_engine import (
    LangGraphConversationEngine,
    build_postgres_checkpointer,
)
from companion.adapters.pgvector.vector_store import PgvectorKnowledgeVectorStore
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.adapters.pypdf.text_extractor import PypdfTextExtractor
from companion.adapters.scheduler import InProcessScheduler
from companion.adapters.tavily.web_search import TavilyWebSearch
from companion.adapters.telegram.chat_channel import TelegramChatChannel
from companion.app import AppDependencies, create_app
from companion.config import Settings, load_settings
from companion.core.conversations import ConversationServices
from companion.core.ports import (
    AuthVerifier,
    ChatChannel,
    ChatModel,
    Clock,
    ConversationEngine,
    DocumentTextExtractor,
    Embedder,
    KnowledgeVectorStore,
    Repositories,
    Scheduler,
    WebSearch,
)

SEED_DIR = Path(__file__).parent / "seed"
SEED_FILE = SEED_DIR / "platform_settings.yaml"
HELPLINES_SEED_FILE = SEED_DIR / "helplines.yaml"
MEMORY_CATEGORIES_SEED_FILE = SEED_DIR / "memory_categories.yaml"
CHECK_IN_KINDS_SEED_FILE = SEED_DIR / "check_in_kinds.yaml"
KNOWLEDGE_SEED_FILE = SEED_DIR / "knowledge" / "knowledge.yaml"
SCHEDULER_INTERVAL_SECONDS = 60


class UnknownAdapterError(Exception):
    """Raised when `.env` names an adapter that does not exist."""

    def __init__(self, setting_key: str, adapter_name: str) -> None:
        """Build the error message naming the setting and the bad value.

        Args:
            setting_key: The environment variable that chose the adapter.
            adapter_name: The value it was set to.
        """
        super().__init__(f"Unknown adapter '{adapter_name}' for {setting_key}")


def build_database_engine(settings: Settings) -> Engine:
    """Connect to the Postgres database the Postgres and pgvector adapters share.

    Args:
        settings: The loaded settings.

    Returns:
        The database engine.
    """
    return create_engine(settings.database_url, pool_pre_ping=True)


def build_repositories(settings: Settings, engine: Engine) -> Repositories:
    """Build the repositories chosen in `.env`.

    Args:
        settings: The loaded settings.
        engine: The database engine.

    Returns:
        The repositories.

    Raises:
        UnknownAdapterError: If the chosen adapter does not exist.
    """
    if settings.repositories_adapter == "postgres":
        return build_postgres_repositories(engine)
    raise UnknownAdapterError("REPOSITORIES_ADAPTER", settings.repositories_adapter)


def build_embedder(settings: Settings) -> Embedder:
    """Build the embedder chosen in `.env`.

    Args:
        settings: The loaded settings.

    Returns:
        The embedder.

    Raises:
        UnknownAdapterError: If the chosen adapter does not exist.
    """
    if settings.embedder_adapter == "fastembed":
        return FastEmbedEmbedder()
    raise UnknownAdapterError("EMBEDDER_ADAPTER", settings.embedder_adapter)


def build_text_extractor(settings: Settings) -> DocumentTextExtractor:
    """Build the Knowledge text extractor chosen in `.env`.

    Args:
        settings: The loaded settings.

    Returns:
        The text extractor.

    Raises:
        UnknownAdapterError: If the chosen adapter does not exist.
    """
    if settings.text_extractor_adapter == "pypdf":
        return PypdfTextExtractor()
    raise UnknownAdapterError("TEXT_EXTRACTOR_ADAPTER", settings.text_extractor_adapter)


def build_vector_store(settings: Settings, engine: Engine) -> KnowledgeVectorStore:
    """Build the Knowledge vector store chosen in `.env`.

    Args:
        settings: The loaded settings.
        engine: The database engine.

    Returns:
        The vector store.

    Raises:
        UnknownAdapterError: If the chosen adapter does not exist.
    """
    if settings.vector_store_adapter == "pgvector":
        return PgvectorKnowledgeVectorStore(engine)
    raise UnknownAdapterError("VECTOR_STORE_ADAPTER", settings.vector_store_adapter)


def build_web_search(settings: Settings) -> WebSearch:
    """Build the web search chosen in `.env`.

    Args:
        settings: The loaded settings.

    Returns:
        The web search.

    Raises:
        UnknownAdapterError: If the chosen adapter does not exist.
    """
    if settings.web_search_adapter == "tavily":
        return TavilyWebSearch(settings.tavily_api_key)
    raise UnknownAdapterError("WEB_SEARCH_ADAPTER", settings.web_search_adapter)


def build_chat_channel(settings: Settings) -> ChatChannel:
    """Build the chat channel chosen in `.env`.

    Args:
        settings: The loaded settings.

    Returns:
        The chat channel.

    Raises:
        UnknownAdapterError: If the chosen adapter does not exist.
    """
    if settings.chat_channel_adapter == "telegram":
        return TelegramChatChannel(settings.telegram_bot_token)
    raise UnknownAdapterError("CHAT_CHANNEL_ADAPTER", settings.chat_channel_adapter)


def build_auth_verifier(settings: Settings) -> AuthVerifier:
    """Build the auth verifier chosen in `.env`.

    Args:
        settings: The loaded settings.

    Returns:
        The auth verifier.

    Raises:
        UnknownAdapterError: If the chosen adapter does not exist.
    """
    if settings.auth_verifier_adapter == "clerk":
        return ClerkAuthVerifier(
            settings.clerk_secret_key, authorized_parties=[settings.dashboard_url]
        )
    raise UnknownAdapterError("AUTH_VERIFIER_ADAPTER", settings.auth_verifier_adapter)


def build_clock(settings: Settings) -> Clock:
    """Build the clock chosen in `.env`.

    Args:
        settings: The loaded settings.

    Returns:
        The clock.

    Raises:
        UnknownAdapterError: If the chosen adapter does not exist.
    """
    if settings.clock_adapter == "system":
        return SystemClock()
    raise UnknownAdapterError("CLOCK_ADAPTER", settings.clock_adapter)


def build_scheduler(settings: Settings) -> Scheduler:
    """Build the scheduler chosen in `.env`.

    Args:
        settings: The loaded settings.

    Returns:
        The scheduler.

    Raises:
        UnknownAdapterError: If the chosen adapter does not exist.
    """
    if settings.scheduler_adapter == "in_process":
        return InProcessScheduler(SCHEDULER_INTERVAL_SECONDS)
    raise UnknownAdapterError("SCHEDULER_ADAPTER", settings.scheduler_adapter)


def build_chat_model(settings: Settings) -> ChatModel:
    """Build the chat model chosen in `.env`.

    Args:
        settings: The loaded settings.

    Returns:
        The chat model.

    Raises:
        UnknownAdapterError: If the chosen adapter does not exist.
    """
    if settings.chat_model_adapter == "deepseek":
        return DeepSeekChatModel(settings.deepseek_api_key)
    raise UnknownAdapterError("CHAT_MODEL_ADAPTER", settings.chat_model_adapter)


def build_conversation_engine_factory(
    settings: Settings,
) -> Callable[[ConversationServices], ConversationEngine]:
    """Pick how to build the conversation engine chosen in `.env`.

    Args:
        settings: The loaded settings.

    Returns:
        A function that builds the engine around the core services.

    Raises:
        UnknownAdapterError: If the chosen adapter does not exist.
    """
    if settings.conversation_engine_adapter == "langgraph":
        checkpointer = build_postgres_checkpointer(settings.database_url)

        def build_langgraph_engine(
            services: ConversationServices,
        ) -> ConversationEngine:
            """Build the LangGraph engine with the Postgres checkpointer.

            Args:
                services: The core services the engine runs.

            Returns:
                The engine.
            """
            return LangGraphConversationEngine(services, checkpointer)

        return build_langgraph_engine
    raise UnknownAdapterError(
        "CONVERSATION_ENGINE_ADAPTER", settings.conversation_engine_adapter
    )


def build_production_app() -> FastAPI:
    """Build the backend app with the adapters chosen in `.env`.

    Used by uvicorn as an app factory.

    Returns:
        The FastAPI app.
    """
    settings = load_settings()
    engine = build_database_engine(settings)
    dependencies = AppDependencies(
        repositories=build_repositories(settings, engine),
        chat_channel=build_chat_channel(settings),
        chat_model=build_chat_model(settings),
        build_conversation_engine=build_conversation_engine_factory(settings),
        auth_verifier=build_auth_verifier(settings),
        text_extractor=build_text_extractor(settings),
        embedder=build_embedder(settings),
        knowledge_vector_store=build_vector_store(settings, engine),
        web_search=build_web_search(settings),
        clock=build_clock(settings),
        scheduler=build_scheduler(settings),
        telegram_webhook_secret=settings.telegram_webhook_secret,
        telegram_bot_username=settings.telegram_bot_username,
        dashboard_url=settings.dashboard_url,
        cors_origins=[settings.dashboard_url],
        initial_admin_emails=settings.initial_admin_email_set,
    )
    return create_app(dependencies)
