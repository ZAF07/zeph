from dataclasses import dataclass, field

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from companion.adapters.http.dashboard_api import build_dashboard_api_router
from companion.adapters.telegram.webhook import build_telegram_webhook_router
from companion.core.incoming_messages import IncomingMessageHandler
from companion.core.ports import AuthVerifier, ChatChannel, Clock, Repositories
from companion.core.telegram_connection import TelegramConnectionService
from companion.core.users import UserService


@dataclass(frozen=True)
class AppDependencies:
    """Everything the backend needs from outside the core.

    Attributes:
        repositories: Where data is stored.
        chat_channel: Sends messages to people.
        auth_verifier: Checks Dashboard bearer tokens.
        clock: Tells the current time.
        telegram_webhook_secret: The secret Telegram sends with each update.
        telegram_bot_username: The Companion's Telegram @username.
        dashboard_url: The Dashboard's public address.
        cors_origins: Browser origins allowed to call the Dashboard API.
    """

    repositories: Repositories
    chat_channel: ChatChannel
    auth_verifier: AuthVerifier
    clock: Clock
    telegram_webhook_secret: str
    telegram_bot_username: str
    dashboard_url: str
    cors_origins: list[str] = field(default_factory=list)


def create_app(dependencies: AppDependencies) -> FastAPI:
    """Build the backend app from its dependencies.

    Args:
        dependencies: The adapters and settings to wire in.

    Returns:
        The FastAPI app.
    """
    user_service = UserService(dependencies.repositories.users, dependencies.clock)
    telegram_connection_service = TelegramConnectionService(
        repositories=dependencies.repositories,
        chat_channel=dependencies.chat_channel,
        clock=dependencies.clock,
        dashboard_url=dependencies.dashboard_url,
    )
    incoming_message_handler = IncomingMessageHandler(telegram_connection_service)

    app = FastAPI(title="Companion backend")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=dependencies.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(
        build_dashboard_api_router(
            auth_verifier=dependencies.auth_verifier,
            user_service=user_service,
            telegram_connection_service=telegram_connection_service,
            telegram_bot_username=dependencies.telegram_bot_username,
        )
    )
    app.include_router(
        build_telegram_webhook_router(
            incoming_message_handler, dependencies.telegram_webhook_secret
        )
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        """Report that the backend is up.

        Returns:
            A fixed status body.
        """
        return {"status": "ok"}

    return app
