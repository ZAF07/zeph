from collections.abc import AsyncIterator
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
from companion.adapters.http.errors import add_core_error_handlers
from companion.adapters.telegram.webhook import build_telegram_webhook_router
from companion.core.admin_users import AdminUserService
from companion.core.chat_settings import SettingsTools
from companion.core.check_in_kinds import CheckInKindService
from companion.core.check_ins import CheckInService
from companion.core.conversations import ConversationService
from companion.core.features import FeatureService
from companion.core.helplines import HelplineService
from companion.core.home import HomeService
from companion.core.incoming_messages import IncomingMessageHandler
from companion.core.knowledge import KnowledgeService
from companion.core.knowledge_retrieval import KnowledgeRetrieval
from companion.core.life_threads import LifeThreadKeeper, ThreadReminder
from companion.core.me import MeService
from companion.core.memory_categories import MemoryCategoryService
from companion.core.memory_retrieval import MemoryRetrieval
from companion.core.message_retention import MessageRetention
from companion.core.model_call_log import ModelCallLog
from companion.core.needs import NeedService
from companion.core.personal_stickers import (
    PersonalStickerKeeper,
    PersonalStickerService,
)
from companion.core.photos import PhotoService, PhotoTools, SendPhotoTools
from companion.core.platform_settings import PlatformSettingsService
from companion.core.ports import (
    AuthAccounts,
    AuthVerifier,
    ChatChannel,
    ChatModel,
    Clock,
    DocumentTextExtractor,
    Embedder,
    KnowledgeVectorStore,
    PhotoViewer,
    Repositories,
    Scheduler,
    Timer,
    WebSearch,
)
from companion.core.post_conversation import PostConversationProcessor
from companion.core.reply_gate import ReplyGate
from companion.core.reply_service import ReplyService
from companion.core.response_composition import ResponseComposer
from companion.core.safeguard import Safeguard
from companion.core.scheduled_work import ScheduledWork
from companion.core.sticker_adding import StickerAdding
from companion.core.stickers import StickerLibraryService, StickerTools
from companion.core.telegram_connection import TelegramConnectionService
from companion.core.typing_keeper import TypingKeeper
from companion.core.understanding import UnderstandingService
from companion.core.usage import UsageLimiter, UsageRecordingChatModel
from companion.core.user_data import ChatDataDeletion, UserDataService
from companion.core.user_memory import UserMemoryService
from companion.core.user_snapshot import UserSnapshotLoader
from companion.core.users import UserService
from companion.core.web_search import WebSearchTools


@dataclass(frozen=True)
class AppDependencies:
    """Everything the backend needs from outside the core.

    Attributes:
        repositories: Where data is stored.
        chat_channel: Sends messages to people.
        chat_model: Generates the Companion's words.
        photo_viewer: Looks at the photos Users send.
        auth_verifier: Checks Dashboard bearer tokens.
        auth_accounts: Deletes accounts at the auth provider.
        text_extractor: Reads the text out of uploaded Knowledge files.
        embedder: Turns text into embeddings.
        knowledge_vector_store: Stores and searches Knowledge embeddings.
        web_search: Searches the web and reads pages for replies.
        clock: Tells the current time.
        scheduler: Runs the scheduled work while the app is up.
        timer: Runs work after a wait, like answering a Message once its
            User has paused.
        telegram_webhook_secret: The secret Telegram sends with each update.
        telegram_bot_username: The Companion's Telegram @username.
        dashboard_url: The Dashboard's public address.
        cors_origins: Browser origins allowed to call the Dashboard API.
        initial_admin_emails: Emails, in lower case, whose accounts become
            Admins on first sign-in.
        model_call_content_for_everyone: Whether the Model Call Log keeps
            full content for every User, as in an Eval run; otherwise only
            for Admins.
        model_call_developer_logs: Whether every model call's full content
            is written to the developer logs, as in local and worktree runs.
    """

    repositories: Repositories
    chat_channel: ChatChannel
    chat_model: ChatModel
    photo_viewer: PhotoViewer
    auth_verifier: AuthVerifier
    auth_accounts: AuthAccounts
    text_extractor: DocumentTextExtractor
    embedder: Embedder
    knowledge_vector_store: KnowledgeVectorStore
    web_search: WebSearch
    clock: Clock
    scheduler: Scheduler
    timer: Timer
    telegram_webhook_secret: str
    telegram_bot_username: str
    dashboard_url: str
    cors_origins: list[str] = field(default_factory=list)
    initial_admin_emails: frozenset[str] = frozenset()
    model_call_content_for_everyone: bool = False
    model_call_developer_logs: bool = False


def create_app(dependencies: AppDependencies) -> FastAPI:
    """Build the backend app from its dependencies.

    Args:
        dependencies: The adapters and settings to wire in.

    Returns:
        The FastAPI app.
    """
    typing_keeper = TypingKeeper(dependencies.chat_channel, dependencies.timer)
    feature_service = FeatureService(
        dependencies.repositories, dependencies.clock, dependencies.dashboard_url
    )
    user_memory_service = UserMemoryService(
        dependencies.repositories, feature_service, dependencies.clock
    )
    usage_limiter = UsageLimiter(dependencies.repositories, dependencies.clock)
    model_call_log = ModelCallLog(
        dependencies.repositories,
        dependencies.clock,
        content_for_everyone=dependencies.model_call_content_for_everyone,
        developer_logs=dependencies.model_call_developer_logs,
    )
    chat_model = UsageRecordingChatModel(
        dependencies.chat_model,
        dependencies.photo_viewer,
        usage_limiter,
        model_call_log,
        dependencies.clock,
    )
    user_snapshots = UserSnapshotLoader(dependencies.repositories, dependencies.clock)
    check_in_service = CheckInService(
        repositories=dependencies.repositories,
        features=feature_service,
        user_snapshots=user_snapshots,
        chat_model=chat_model,
        usage_limiter=usage_limiter,
        chat_channel=typing_keeper,
        clock=dependencies.clock,
    )
    user_service = UserService(
        dependencies.repositories.users,
        feature_service,
        user_memory_service,
        check_in_service,
        dependencies.clock,
        dependencies.initial_admin_emails,
    )
    telegram_connection_service = TelegramConnectionService(
        repositories=dependencies.repositories,
        chat_channel=typing_keeper,
        clock=dependencies.clock,
        dashboard_url=dependencies.dashboard_url,
    )
    helpline_service = HelplineService(dependencies.repositories.helplines)
    sticker_library = StickerLibraryService(
        dependencies.repositories, typing_keeper, dependencies.clock
    )
    personal_sticker_service = PersonalStickerService(
        dependencies.repositories, typing_keeper
    )
    conversation_service = ConversationService(
        repositories=dependencies.repositories,
        chat_channel=typing_keeper,
        clock=dependencies.clock,
    )
    sticker_adding = StickerAdding(
        repositories=dependencies.repositories,
        sticker_library=sticker_library,
        chat_channel=typing_keeper,
        deliver_notice=conversation_service.deliver_notice,
        timer=dependencies.timer,
        dashboard_url=dependencies.dashboard_url,
    )
    chat_data_deletion = ChatDataDeletion(
        dependencies.repositories, typing_keeper, dependencies.clock
    )
    safeguard = Safeguard(
        repositories=dependencies.repositories,
        helplines=helpline_service,
        chat_model=chat_model,
        clock=dependencies.clock,
    )
    photo_service = PhotoService(
        repositories=dependencies.repositories,
        chat_channel=typing_keeper,
        chat_model=chat_model,
        clock=dependencies.clock,
    )
    reply_gate = ReplyGate(
        conversations=conversation_service,
        safeguard=safeguard,
        data_deletion=chat_data_deletion,
        usage_limiter=usage_limiter,
    )
    reply_service = ReplyService(
        reply_gate=reply_gate,
        conversations=conversation_service,
        thread_reminder=ThreadReminder(
            repositories=dependencies.repositories,
            embedder=dependencies.embedder,
            clock=dependencies.clock,
        ),
        understanding=UnderstandingService(
            repositories=dependencies.repositories,
            chat_model=chat_model,
            clock=dependencies.clock,
        ),
        memory_retrieval=MemoryRetrieval(
            repositories=dependencies.repositories, embedder=dependencies.embedder
        ),
        knowledge_retrieval=KnowledgeRetrieval(
            repositories=dependencies.repositories,
            embedder=dependencies.embedder,
            vector_store=dependencies.knowledge_vector_store,
        ),
        response_composer=ResponseComposer(
            repositories=dependencies.repositories,
            chat_model=chat_model,
            features=feature_service,
            tool_providers=[
                WebSearchTools(
                    repositories=dependencies.repositories,
                    web_search=dependencies.web_search,
                ),
                SettingsTools(
                    repositories=dependencies.repositories,
                    users=user_service,
                    check_ins=check_in_service,
                    user_memory=user_memory_service,
                    data_deletion=chat_data_deletion,
                ),
                StickerTools(dependencies.repositories),
                sticker_adding,
                PhotoTools(dependencies.repositories, photo_service),
                SendPhotoTools(dependencies.repositories),
            ],
        ),
    )
    incoming_message_handler = IncomingMessageHandler(
        telegram_connections=telegram_connection_service,
        repositories=dependencies.repositories,
        reply_gate=reply_gate,
        reply_service=reply_service,
        chat_channel=typing_keeper,
        typing_keeper=typing_keeper,
        sticker_adding=sticker_adding,
        photo_service=photo_service,
        user_snapshots=user_snapshots,
        timer=dependencies.timer,
        dashboard_url=dependencies.dashboard_url,
    )

    user_data_service = UserDataService(
        repositories=dependencies.repositories,
        auth_accounts=dependencies.auth_accounts,
        clock=dependencies.clock,
    )
    scheduled_work = ScheduledWork(
        repositories=dependencies.repositories,
        post_conversation=PostConversationProcessor(
            repositories=dependencies.repositories,
            user_snapshots=user_snapshots,
            chat_model=chat_model,
            personal_sticker_keeper=PersonalStickerKeeper(
                repositories=dependencies.repositories,
                chat_model=chat_model,
                clock=dependencies.clock,
            ),
            life_thread_keeper=LifeThreadKeeper(
                repositories=dependencies.repositories,
                chat_model=chat_model,
                embedder=dependencies.embedder,
                clock=dependencies.clock,
            ),
            embedder=dependencies.embedder,
            clock=dependencies.clock,
        ),
        check_ins=check_in_service,
        message_retention=MessageRetention(
            repositories=dependencies.repositories,
            clock=dependencies.clock,
        ),
        user_data=user_data_service,
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
    add_core_error_handlers(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=dependencies.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    platform_settings_service = PlatformSettingsService(
        dependencies.repositories.platform_settings, dependencies.clock
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
            user_data_service=user_data_service,
            home_service=HomeService(
                repositories=dependencies.repositories,
                check_in_service=check_in_service,
                features=feature_service,
                user_memory_service=user_memory_service,
            ),
            me_service=MeService(
                repositories=dependencies.repositories,
                features=feature_service,
                user_memory_service=user_memory_service,
            ),
            photo_service=photo_service,
            personal_sticker_service=personal_sticker_service,
            platform_settings_service=platform_settings_service,
            telegram_bot_username=dependencies.telegram_bot_username,
        )
    )
    app.include_router(
        build_admin_api_router(
            current_admin=build_current_admin_dependency(current_user),
            admin_user_service=AdminUserService(dependencies.repositories),
            feature_service=feature_service,
            platform_settings_service=platform_settings_service,
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
                chat_model=dependencies.chat_model,
                clock=dependencies.clock,
            ),
            sticker_library=sticker_library,
            personal_sticker_service=personal_sticker_service,
            check_in_kind_service=CheckInKindService(
                dependencies.repositories, dependencies.clock
            ),
            check_in_service=check_in_service,
            usage_limiter=usage_limiter,
            model_call_log=model_call_log,
            need_service=NeedService(dependencies.repositories),
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
