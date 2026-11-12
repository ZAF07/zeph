import os
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from langgraph.checkpoint.postgres import PostgresSaver
from sqlalchemy import Engine, create_engine, text
from testcontainers.community.postgres import PostgresContainer

from companion.adapters.deepseek.chat_model import DeepSeekChatModel
from companion.adapters.fastembed.embedder import FastEmbedEmbedder
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
from companion.adapters.postgres.tables import metadata
from companion.adapters.pypdf.text_extractor import PypdfTextExtractor
from companion.app import AppDependencies, create_app
from companion.config import MissingSettingsError, Settings, load_settings
from companion.core.conversations import ConversationServices
from evals.current_settings import (
    app_database_url,
    read_current_platform_settings,
    store_platform_settings,
)
from evals.report import EvalReport
from evals.token_counting_chat_model import TokenCountingChatModel
from tests.conftest import (
    BOT_USERNAME,
    CHECK_IN_KINDS_SEED_FILE,
    DASHBOARD_URL,
    HELPLINES_SEED_FILE,
    INITIAL_ADMIN_EMAIL,
    MEMORY_CATEGORIES_SEED_FILE,
    SEED_FILE,
    WEBHOOK_SECRET,
)
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    FakeWebSearch,
)

REPORT_KEY = pytest.StashKey[EvalReport]()
os.environ.setdefault("TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE", "/var/run/docker.sock")


def pytest_configure(config: pytest.Config) -> None:
    """Start an empty eval report for this run."""
    config.stash[REPORT_KEY] = EvalReport()


def pytest_terminal_summary(
    terminalreporter: Any, exitstatus: int, config: pytest.Config
) -> None:
    """Print the eval report after the test results."""
    terminalreporter.section("Eval report")
    for line in config.stash[REPORT_KEY].lines():
        terminalreporter.write_line(line)


@pytest.fixture(scope="session")
def eval_report(request: pytest.FixtureRequest) -> EvalReport:
    """The report this run's results are added to."""
    return request.config.stash[REPORT_KEY]


@pytest.fixture(scope="session")
def app_settings() -> Settings:
    """The settings from `.env`; stops the run if any are missing."""
    try:
        return load_settings()
    except MissingSettingsError as error:
        pytest.exit(f"{error}. Evals need the real keys in .env.", returncode=1)


@pytest.fixture(scope="session")
def current_platform_settings(
    app_settings: Settings, eval_report: EvalReport
) -> dict[str, Any]:
    """The app database's platform settings, or none to use the seed file."""
    database_url = app_database_url(app_settings)
    values = read_current_platform_settings(database_url)
    if values is None:
        eval_report.settings_source = (
            "the seed file (the app's database isn't reachable)"
        )
        return {}
    host = database_url.split("@")[-1]
    eval_report.settings_source = f"the app's database ({host})"
    return values


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    """Start a throwaway Postgres with pgvector and run migrations once."""
    with PostgresContainer("pgvector/pgvector:pg16", driver="psycopg") as postgres:
        url = postgres.get_connection_url()
        migrate(url)
        yield url


@pytest.fixture(scope="session")
def checkpointer(database_url: str) -> PostgresSaver:
    """The LangGraph Postgres checkpointer on the eval database."""
    return build_postgres_checkpointer(database_url)


@pytest.fixture(scope="session")
def chat_model(
    app_settings: Settings, eval_report: EvalReport
) -> TokenCountingChatModel:
    """The real DeepSeek chat model, counting tokens for the report."""
    return TokenCountingChatModel(
        DeepSeekChatModel(app_settings.deepseek_api_key), eval_report
    )


@pytest.fixture(scope="session")
def embedder() -> FastEmbedEmbedder:
    """The real fastembed embedder, loaded once."""
    return FastEmbedEmbedder()


@pytest.fixture
def engine(
    database_url: str, current_platform_settings: dict[str, Any]
) -> Iterator[Engine]:
    """Give each eval an empty database with the current settings and seeds."""
    engine = create_engine(database_url)
    table_names = ", ".join(table.name for table in metadata.sorted_tables)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {table_names} CASCADE"))
    if current_platform_settings:
        store_platform_settings(engine, current_platform_settings)
    seed_platform_settings(engine, SEED_FILE)
    seed_helplines(engine, HELPLINES_SEED_FILE)
    seed_memory_categories(engine, MEMORY_CATEGORIES_SEED_FILE)
    seed_check_in_kinds(engine, CHECK_IN_KINDS_SEED_FILE)
    yield engine
    engine.dispose()


@pytest.fixture
def clock() -> FakeClock:
    """A clock that starts now and moves only when told or slept on."""
    return FakeClock(datetime.now(UTC))


@pytest.fixture
def chat_channel() -> FakeChatChannel:
    """A chat channel that records what the Companion sent."""
    return FakeChatChannel()


@pytest.fixture
def auth_verifier() -> FakeAuthVerifier:
    """An auth verifier that accepts tokens it handed out."""
    return FakeAuthVerifier()


@pytest.fixture
def client(
    engine: Engine,
    checkpointer: PostgresSaver,
    clock: FakeClock,
    chat_channel: FakeChatChannel,
    chat_model: TokenCountingChatModel,
    auth_verifier: FakeAuthVerifier,
    embedder: FastEmbedEmbedder,
) -> Iterator[TestClient]:
    """A test client for the backend with the real LLM and embedder.

    Everything on the reply path is real except the chat channel (which
    records), the clock (so typing pauses don't wait), auth, the scheduler and
    web search (so no Tavily credits are spent).
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
        web_search=FakeWebSearch(),
        clock=clock,
        scheduler=FakeScheduler(),
        telegram_webhook_secret=WEBHOOK_SECRET,
        telegram_bot_username=BOT_USERNAME,
        dashboard_url=DASHBOARD_URL,
        initial_admin_emails=frozenset({INITIAL_ADMIN_EMAIL}),
    )
    with TestClient(create_app(dependencies)) as test_client:
        yield test_client
