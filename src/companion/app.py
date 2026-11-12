from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from companion.adapters.http.admin_api import build_admin_api_router
from companion.adapters.http.auth import (
    build_current_admin_dependency,
    build_current_user_dependency,
)
from companion.adapters.http.dashboard_api import build_dashboard_api_router
from companion.adapters.telegram.webhook import build_telegram_webhook_router
from companion.core.admin_users import AdminUserService
from companion.core.check_in_kinds import CheckInKindService
from companion.core.check_ins import CheckInService
from companion.core.conversations import ConversationService, ConversationServices
from companion.core.helplines import HelplineService
from companion.core.incoming_messages import IncomingMessageHandler
from companion.core.knowledge import KnowledgeService
from companion.core.knowledge_retrieval import KnowledgeRetrieval
from companion.core.memory_categories import MemoryCategoryService
from companion.core.memory_retrieval import MemoryRetrieval
from companion.core.platform_settings import PlatformSettingsService
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
from companion.core.post_conversation import PostConversationProcessor
from companion.core.response_composition import ResponseComposer
from companion.core.safeguard import Safeguard
from companion.core.scheduled_work import ScheduledWork
from companion.core.stickers import StickerLibraryService, StickerTools
from companion.core.telegram_connection import TelegramConnectionService
from companion.core.usage import UsageLimiter, UsageRecordingChatModel
from companion.core.user_memory import UserMemoryService
from companion.core.users import UserService
from companion.core.web_search import WebSearchTools


@dataclass(frozen=True)
class AppDependencies:
    """Everything the backend needs from outside the core.

    Attributes:
        repositories: Where data is stored.
        chat_channel: Sends messages to people.
        chat_model: Generates the Companion's words.
        build_conversation_engine: Builds the conversation engine around the
            core services it runs.
        auth_verifier: Checks Dashboard bearer tokens.
        text_extractor: Reads the text out of uploaded Knowledge files.
        embedder: Turns text into embeddings.
        knowledge_vector_store: Stores and searches Knowledge embeddings.
        web_search: Searches the web and reads pages for replies.
        clock: Tells the current time.
        scheduler: Runs the scheduled work while the app is up.
        telegram_webhook_secret: The secret Telegram sends with each update.
        telegram_bot_username: The Companion's Telegram @username.
        dashboard_url: The Dashboard's public address.
        cors_origins: Browser origins allowed to call the Dashboard API.
        initial_admin_emails: Emails, in lower case, whose accounts become
            Admins on first sign-in.
    """

    repositories: Repositories
    chat_channel: ChatChannel
    chat_model: ChatModel
    build_conversation_engine: Callable[[ConversationServices], ConversationEngine]
    auth_verifier: AuthVerifier
    text_extractor: DocumentTextExtractor
    embedder: Embedder
    knowledge_vector_store: KnowledgeVectorStore
    web_search: WebSearch
    clock: Clock
    scheduler: Scheduler
    telegram_webhook_secret: str
    telegram_bot_username: str
    dashboard_url: str
    cors_origins: list[str] = field(default_factory=list)
    initial_admin_emails: frozenset[str] = frozenset()


def create_app(dependencies: AppDependencies) -> FastAPI:
    """Build the backend app from its dependencies.

    Args:
        dependencies: The adapters and settings to wire in.

    Returns:
        The FastAPI app.
    """
    user_memory_service = UserMemoryService(
        dependencies.repositories, dependencies.clock
    )
    usage_limiter = UsageLimiter(dependencies.repositories, dependencies.clock)
    chat_model = UsageRecordingChatModel(dependencies.chat_model, usage_limiter)
    check_in_service = CheckInService(
        repositories=dependencies.repositories,
        chat_model=chat_model,
        chat_channel=dependencies.chat_channel,
        clock=dependencies.clock,
    )
    user_service = UserService(
        dependencies.repositories.users,
        user_memory_service,
        check_in_service,
        dependencies.clock,
        dependencies.initial_admin_emails,
    )
    telegram_connection_service = TelegramConnectionService(
        repositories=dependencies.repositories,
        chat_channel=dependencies.chat_channel,
        clock=dependencies.clock,
        dashboard_url=dependencies.dashboard_url,
    )
    helpline_service = HelplineService(dependencies.repositories.helplines)
    sticker_library = StickerLibraryService(
        dependencies.repositories, dependencies.chat_channel, dependencies.clock
    )
    safeguard = Safeguard(
        repositories=dependencies.repositories,
        helplines=helpline_service,
        chat_model=chat_model,
        clock=dependencies.clock,
    )
    conversation_engine = dependencies.build_conversation_engine(
        ConversationServices(
            conversations=ConversationService(
                repositories=dependencies.repositories,
                chat_channel=dependencies.chat_channel,
                clock=dependencies.clock,
            ),
            safeguard=safeguard,
            usage_limiter=usage_limiter,
            memory_retrieval=MemoryRetrieval(
                repositories=dependencies.repositories,
                chat_model=chat_model,
            ),
            knowledge_retrieval=KnowledgeRetrieval(
                repositories=dependencies.repositories,
                embedder=dependencies.embedder,
                vector_store=dependencies.knowledge_vector_store,
            ),
            response_composer=ResponseComposer(
                repositories=dependencies.repositories,
                chat_model=chat_model,
                web_search_tools=WebSearchTools(
                    repositories=dependencies.repositories,
                    web_search=dependencies.web_search,
                    clock=dependencies.clock,
                ),
                sticker_tools=StickerTools(dependencies.repositories),
            ),
        )
    )
    incoming_message_handler = IncomingMessageHandler(
        telegram_connections=telegram_connection_service,
        repositories=dependencies.repositories,
        conversation_engine=conversation_engine,
        chat_channel=dependencies.chat_channel,
        sticker_library=sticker_library,
        dashboard_url=dependencies.dashboard_url,
    )

    scheduled_work = ScheduledWork(
        repositories=dependencies.repositories,
        post_conversation=PostConversationProcessor(
            repositories=dependencies.repositories,
            chat_model=chat_model,
            clock=dependencies.clock,
        ),
        check_ins=check_in_service,
        clock=dependencies.clock,
    )

    @asynccontextmanager
    async def run_scheduler(app: FastAPI) -> AsyncIterator[None]:
        """Run the scheduled work for as long as the app is up.

        Args:
            app: The app starting up.

        Yields:
            Control back to the app until it shuts down.
        """
        dependencies.scheduler.start(scheduled_work.tick)
        yield
        dependencies.scheduler.stop()

    app = FastAPI(title="Companion backend", lifespan=run_scheduler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=dependencies.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    current_user = build_current_user_dependency(
        dependencies.auth_verifier, user_service
    )
    app.include_router(
        build_dashboard_api_router(
            current_user=current_user,
            user_service=user_service,
            user_memory_service=user_memory_service,
            check_in_service=check_in_service,
            telegram_connection_service=telegram_connection_service,
            platform_settings=dependencies.repositories.platform_settings,
            telegram_bot_username=dependencies.telegram_bot_username,
        )
    )
    app.include_router(
        build_admin_api_router(
            current_admin=build_current_admin_dependency(current_user),
            admin_user_service=AdminUserService(dependencies.repositories.users),
            platform_settings_service=PlatformSettingsService(
                dependencies.repositories.platform_settings, dependencies.clock
            ),
            helpline_service=helpline_service,
            safeguard=safeguard,
            memory_category_service=MemoryCategoryService(
                dependencies.repositories, dependencies.clock
            ),
            knowledge_service=KnowledgeService(
                repositories=dependencies.repositories,
                text_extractor=dependencies.text_extractor,
                embedder=dependencies.embedder,
                vector_store=dependencies.knowledge_vector_store,
                clock=dependencies.clock,
            ),
            sticker_library=sticker_library,
            check_in_kind_service=CheckInKindService(
                dependencies.repositories, dependencies.clock
            ),
            check_in_service=check_in_service,
            usage_limiter=usage_limiter,
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
