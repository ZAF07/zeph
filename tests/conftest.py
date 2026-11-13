import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient
from langgraph.checkpoint.postgres import PostgresSaver
from sqlalchemy import Engine, create_engine, text
from testcontainers.community.postgres import PostgresContainer

from companion.adapters.langgraph.conversation_engine import (
    LangGraphConversationEngine,
    build_postgres_checkpointer,
)
from companion.adapters.pgvector.vector_store import PgvectorKnowledgeVectorStore
from companion.adapters.postgres.database import (
    migrate,
    seed_check_in_kinds,
    seed_helplines,
    seed_memory_categories,
    seed_platform_settings,
)
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.adapters.pypdf.text_extractor import PypdfTextExtractor
from companion.app import AppDependencies, create_app
from companion.core.conversations import ConversationServices
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeEmbedder,
    FakeScheduler,
    FakeWebSearch,
    ScriptedChatModel,
)

WEBHOOK_SECRET = "test-webhook-secret"
BOT_USERNAME = "zeph_test_bot"
DASHBOARD_URL = "http://dashboard.test"
INITIAL_ADMIN_EMAIL = "owner@example.com"
os.environ.setdefault("TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE", "/var/run/docker.sock")

SEED_DIR = Path(__file__).parent.parent / "src/companion/seed"
SEED_FILE = SEED_DIR / "platform_settings.yaml"
HELPLINES_SEED_FILE = SEED_DIR / "helplines.yaml"
MEMORY_CATEGORIES_SEED_FILE = SEED_DIR / "memory_categories.yaml"
CHECK_IN_KINDS_SEED_FILE = SEED_DIR / "check_in_kinds.yaml"
KNOWLEDGE_SEED_FILE = SEED_DIR / "knowledge" / "knowledge.yaml"


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    """Start a throwaway Postgres with pgvector and run migrations once."""
    with PostgresContainer("pgvector/pgvector:pg16", driver="psycopg") as postgres:
        url = postgres.get_connection_url()
        migrate(url)
        yield url


@pytest.fixture(scope="session")
def checkpointer(database_url: str) -> PostgresSaver:
    """The LangGraph Postgres checkpointer, set up once on the test database."""
    return build_postgres_checkpointer(database_url)


@pytest.fixture
def engine(database_url: str) -> Iterator[Engine]:
    """Give each test an empty, freshly seeded database."""
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE users, telegram_connections, connection_tokens, "
                "conversations, conversation_messages, platform_settings, "
                "helplines, safeguard_events, memory_categories, memory_items, "
                "conversation_summaries, knowledge_documents, knowledge_chunks, "
                "daily_usage, stickers, check_in_kinds, check_ins, "
                "feature_switches CASCADE"
            )
        )
    seed_platform_settings(engine, SEED_FILE)
    seed_helplines(engine, HELPLINES_SEED_FILE)
    seed_memory_categories(engine, MEMORY_CATEGORIES_SEED_FILE)
    seed_check_in_kinds(engine, CHECK_IN_KINDS_SEED_FILE)
    yield engine
    engine.dispose()


@pytest.fixture
def clock() -> FakeClock:
    """A fake clock starting at a fixed time."""
    return FakeClock(datetime(2026, 11, 11, 9, 0, tzinfo=UTC))


@pytest.fixture
def chat_channel() -> FakeChatChannel:
    """A chat channel that records what was sent."""
    return FakeChatChannel()


@pytest.fixture
def auth_verifier() -> FakeAuthVerifier:
    """An auth verifier that accepts tokens it handed out."""
    return FakeAuthVerifier()


@pytest.fixture
def embedder() -> FakeEmbedder:
    """An embedder that turns words into vectors, with no model."""
    return FakeEmbedder()


@pytest.fixture
def web_search() -> FakeWebSearch:
    """A web search that returns set results, with no service behind it."""
    return FakeWebSearch()


@pytest.fixture
def scheduler() -> FakeScheduler:
    """A scheduler whose ticks tests run by hand."""
    return FakeScheduler()


@pytest.fixture
def chat_model(seeded_settings: dict[str, Any]) -> ScriptedChatModel:
    """A chat model that returns scripted replies and answers for each service."""
    return ScriptedChatModel(
        safeguard_prompt=seeded_settings["safeguard_prompt"],
        memory_processing_prompt=seeded_settings["memory_processing_prompt"],
        memory_retrieval_prompt=seeded_settings["memory_retrieval_prompt"],
    )


@pytest.fixture
def client(
    engine: Engine,
    checkpointer: PostgresSaver,
    clock: FakeClock,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    auth_verifier: FakeAuthVerifier,
    embedder: FakeEmbedder,
    web_search: FakeWebSearch,
    scheduler: FakeScheduler,
) -> Iterator[TestClient]:
    """A test client for the backend wired with fakes and the real database.

    The conversation engine is the real LangGraph one, so tests run the same
    graph as production. Knowledge uses the real pgvector store and text
    extractor with a fake embedder. The app is started, so its scheduler has
    the tick.
    """

    def build_conversation_engine(
        services: ConversationServices,
    ) -> LangGraphConversationEngine:
        return LangGraphConversationEngine(services, checkpointer)

    dependencies = AppDependencies(
        repositories=build_postgres_repositories(engine),
        chat_channel=chat_channel,
        chat_model=chat_model,
        build_conversation_engine=build_conversation_engine,
        auth_verifier=auth_verifier,
        auth_accounts=auth_verifier,
        text_extractor=PypdfTextExtractor(),
        embedder=embedder,
        knowledge_vector_store=PgvectorKnowledgeVectorStore(engine),
        web_search=web_search,
        clock=clock,
        scheduler=scheduler,
        telegram_webhook_secret=WEBHOOK_SECRET,
        telegram_bot_username=BOT_USERNAME,
        dashboard_url=DASHBOARD_URL,
        initial_admin_emails=frozenset({INITIAL_ADMIN_EMAIL}),
    )
    with TestClient(create_app(dependencies)) as test_client:
        yield test_client


@pytest.fixture
def seeded_settings() -> dict[str, Any]:
    """The platform settings from the seed file, as a fresh install has them."""
    settings: dict[str, Any] = yaml.safe_load(SEED_FILE.read_text())
    return settings
