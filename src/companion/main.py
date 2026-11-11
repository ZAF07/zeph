from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy import create_engine

from companion.adapters.clerk.auth_verifier import ClerkAuthVerifier
from companion.adapters.clock import SystemClock
from companion.adapters.deepseek.chat_model import DeepSeekChatModel
from companion.adapters.langgraph.conversation_engine import (
    LangGraphConversationEngine,
    build_postgres_checkpointer,
)
from companion.adapters.postgres.repositories import build_postgres_repositories
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
    Repositories,
)

SEED_FILE = Path(__file__).parent / "seed" / "platform_settings.yaml"


class UnknownAdapterError(Exception):
    """Raised when `.env` names an adapter that does not exist."""

    def __init__(self, setting_key: str, adapter_name: str) -> None:
        """Build the error message naming the setting and the bad value.

        Args:
            setting_key: The environment variable that chose the adapter.
            adapter_name: The value it was set to.
        """
        super().__init__(f"Unknown adapter '{adapter_name}' for {setting_key}")


def build_repositories(settings: Settings) -> Repositories:
    """Build the repositories chosen in `.env`.

    Args:
        settings: The loaded settings.

    Returns:
        The repositories.

    Raises:
        UnknownAdapterError: If the chosen adapter does not exist.
    """
    if settings.repositories_adapter == "postgres":
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        return build_postgres_repositories(engine)
    raise UnknownAdapterError("REPOSITORIES_ADAPTER", settings.repositories_adapter)


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
    dependencies = AppDependencies(
        repositories=build_repositories(settings),
        chat_channel=build_chat_channel(settings),
        chat_model=build_chat_model(settings),
        build_conversation_engine=build_conversation_engine_factory(settings),
        auth_verifier=build_auth_verifier(settings),
        clock=build_clock(settings),
        telegram_webhook_secret=settings.telegram_webhook_secret,
        telegram_bot_username=settings.telegram_bot_username,
        dashboard_url=settings.dashboard_url,
        cors_origins=[settings.dashboard_url],
    )
    return create_app(dependencies)
