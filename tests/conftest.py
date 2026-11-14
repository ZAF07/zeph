import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, make_url, text
from testcontainers.community.postgres import PostgresContainer

from companion.adapters.pgvector.vector_store import PgvectorKnowledgeVectorStore
from companion.adapters.postgres.database import (
    migrate,
    seed_check_in_kinds,
    seed_helplines,
    seed_memory_categories,
    seed_needs,
    seed_platform_settings,
)
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.adapters.pypdf.text_extractor import PypdfTextExtractor
from companion.app import AppDependencies, create_app
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeEmbedder,
    FakePhotoViewer,
    FakeScheduler,
    FakeTimer,
    FakeWebSearch,
    ScriptedChatModel,
)

WEBHOOK_SECRET = "test-webhook-secret"
BOT_USERNAME = "zeph_test_bot"
DASHBOARD_URL = "http://dashboard.test"
INITIAL_ADMIN_EMAIL = "owner@example.com"
POSTGRES_CONTAINER = pytest.StashKey[PostgresContainer]()
os.environ.setdefault("TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE", "/var/run/docker.sock")

SEED_DIR = Path(__file__).parent.parent / "src/companion/seed"
SEED_FILE = SEED_DIR / "platform_settings.yaml"
HELPLINES_SEED_FILE = SEED_DIR / "helplines.yaml"
MEMORY_CATEGORIES_SEED_FILE = SEED_DIR / "memory_categories.yaml"
CHECK_IN_KINDS_SEED_FILE = SEED_DIR / "check_in_kinds.yaml"
NEEDS_SEED_FILE = SEED_DIR / "needs.yaml"
KNOWLEDGE_SEED_FILE = SEED_DIR / "knowledge" / "knowledge.yaml"


class CompanionTestClient(TestClient):
    """A test client that can also reach the test database for setup."""

    def __init__(self, app: Any, engine: Engine, timer: FakeTimer) -> None:
        """Wrap the app and remember the test database and timer."""
        super().__init__(app)
        self.engine = engine
        self.timer = timer


def pytest_configure(config: pytest.Config) -> None:
    """Start one throwaway Postgres with pgvector for the whole test run.

    Only the main pytest process starts it. Parallel workers (pytest-xdist)
    are handed its URL, so a run uses one container however many workers
    it has.

    Args:
        config: This pytest process's config, which keeps the container.
    """
    if hasattr(config, "workerinput"):
        return
    postgres = PostgresContainer("pgvector/pgvector:pg16", driver="psycopg")
    postgres.start()
    config.stash[POSTGRES_CONTAINER] = postgres


def pytest_unconfigure(config: pytest.Config) -> None:
    """Stop the test run's Postgres once the run is over.

    Args:
        config: This pytest process's config, which keeps the container.
    """
    postgres = config.stash.get(POSTGRES_CONTAINER, None)
    if postgres is not None:
        postgres.stop()


@pytest.hookimpl(optionalhook=True)
def pytest_configure_node(node: Any) -> None:
    """Hand a starting pytest-xdist worker the test run's Postgres URL.

    Args:
        node: The worker being started.
    """
    node.workerinput["server_url"] = server_url(node.config)


def server_url(config: pytest.Config) -> str:
    """The URL of the test run's Postgres, as seen from this process.

    Args:
        config: This pytest process's config.

    Returns:
        The URL of the Postgres the main process started.
    """
    if hasattr(config, "workerinput"):
        url: str = config.workerinput["server_url"]
        return url
    return config.stash[POSTGRES_CONTAINER].get_connection_url()


def worker_database_name(worker_id: str) -> str:
    """Name of the database one pytest process runs its tests against.

    Args:
        worker_id: The pytest-xdist worker id, or "master" when not parallel.

    Returns:
        A database name only this process uses.
    """
    return f"companion_test_{worker_id}"


@pytest.fixture(scope="session")
def database_url(request: pytest.FixtureRequest, worker_id: str) -> str:
    """Make this process its own empty database and run migrations once.

    Each parallel worker gets its own database in the shared Postgres, so
    tests in different workers never see each other's data.
    """
    url = make_url(server_url(request.config))
    database_name = worker_database_name(worker_id)
    server = create_engine(url, isolation_level="AUTOCOMMIT")
    with server.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    server.dispose()
    database_url = url.set(database=database_name).render_as_string(hide_password=False)
    migrate(database_url)
    return database_url


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
                "feature_switches, user_feature_switches, shared_photos, "
                "personal_stickers, pending_auth_account_deletions, needs CASCADE"
            )
        )
    seed_platform_settings(engine, SEED_FILE)
    seed_helplines(engine, HELPLINES_SEED_FILE)
    seed_memory_categories(engine, MEMORY_CATEGORIES_SEED_FILE)
    seed_check_in_kinds(engine, CHECK_IN_KINDS_SEED_FILE)
    seed_needs(engine, NEEDS_SEED_FILE)
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
def photo_viewer() -> FakePhotoViewer:
    """A photo viewer that returns scripted descriptions, with no model."""
    return FakePhotoViewer()


@pytest.fixture
def scheduler() -> FakeScheduler:
    """A scheduler whose ticks tests run by hand."""
    return FakeScheduler()


@pytest.fixture
def timer() -> FakeTimer:
    """A timer whose waiting work tests run by hand."""
    return FakeTimer()


@pytest.fixture
def chat_model(seeded_settings: dict[str, Any]) -> ScriptedChatModel:
    """A chat model that returns scripted replies and answers for each service."""
    return ScriptedChatModel(
        safeguard_prompt=seeded_settings["safeguard_prompt"],
        memory_processing_prompt=seeded_settings["memory_processing_prompt"],
        understanding_prompt=seeded_settings["understanding_prompt"],
        sticker_keeping_prompt=seeded_settings["personal_sticker_keeping_prompt"],
        thread_keeping_prompt=seeded_settings["life_thread_keeping_prompt"],
        knowledge_when_it_helps_prompt=seeded_settings[
            "knowledge_when_it_helps_prompt"
        ],
    )


@pytest.fixture
def client(
    engine: Engine,
    clock: FakeClock,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    auth_verifier: FakeAuthVerifier,
    embedder: FakeEmbedder,
    web_search: FakeWebSearch,
    photo_viewer: FakePhotoViewer,
    scheduler: FakeScheduler,
    timer: FakeTimer,
) -> Iterator[TestClient]:
    """A test client for the backend wired with fakes and the real database.

    Replies run through the real core services, as in production. Knowledge
    uses the real pgvector store and text extractor with a fake embedder. The
    app is started, so its scheduler has the tick.
    """

    dependencies = AppDependencies(
        repositories=build_postgres_repositories(engine),
        chat_channel=chat_channel,
        chat_model=chat_model,
        photo_viewer=photo_viewer,
        auth_verifier=auth_verifier,
        auth_accounts=auth_verifier,
        text_extractor=PypdfTextExtractor(),
        embedder=embedder,
        knowledge_vector_store=PgvectorKnowledgeVectorStore(engine),
        web_search=web_search,
        clock=clock,
        scheduler=scheduler,
        timer=timer,
        telegram_webhook_secret=WEBHOOK_SECRET,
        telegram_bot_username=BOT_USERNAME,
        dashboard_url=DASHBOARD_URL,
        initial_admin_emails=frozenset({INITIAL_ADMIN_EMAIL}),
    )
    with CompanionTestClient(create_app(dependencies), engine, timer) as test_client:
        yield test_client


@pytest.fixture
def seeded_settings() -> dict[str, Any]:
    """The platform settings from the seed file, as a fresh install has them."""
    settings: dict[str, Any] = yaml.safe_load(SEED_FILE.read_text())
    return settings
