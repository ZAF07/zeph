import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from testcontainers.community.postgres import PostgresContainer

from companion.adapters.postgres.database import migrate, seed_platform_settings
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.app import AppDependencies, create_app
from tests.fakes import FakeAuthVerifier, FakeChatChannel, FakeClock

WEBHOOK_SECRET = "test-webhook-secret"
BOT_USERNAME = "zeph_test_bot"
DASHBOARD_URL = "http://dashboard.test"
os.environ.setdefault("TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE", "/var/run/docker.sock")

SEED_FILE = Path(__file__).parent.parent / "src/companion/seed/platform_settings.yaml"


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    """Start a throwaway Postgres with pgvector and run migrations once."""
    with PostgresContainer("pgvector/pgvector:pg16", driver="psycopg") as postgres:
        url = postgres.get_connection_url()
        migrate(url)
        yield url


@pytest.fixture
def engine(database_url: str) -> Iterator[Engine]:
    """Give each test an empty, freshly seeded database."""
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE users, telegram_connections, connection_tokens, "
                "platform_settings CASCADE"
            )
        )
    seed_platform_settings(engine, SEED_FILE)
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
def client(
    engine: Engine,
    clock: FakeClock,
    chat_channel: FakeChatChannel,
    auth_verifier: FakeAuthVerifier,
) -> TestClient:
    """A test client for the backend wired with fakes and the real database."""
    dependencies = AppDependencies(
        repositories=build_postgres_repositories(engine),
        chat_channel=chat_channel,
        auth_verifier=auth_verifier,
        clock=clock,
        telegram_webhook_secret=WEBHOOK_SECRET,
        telegram_bot_username=BOT_USERNAME,
        dashboard_url=DASHBOARD_URL,
    )
    return TestClient(create_app(dependencies))


@pytest.fixture
def seeded_settings() -> dict[str, Any]:
    """The platform settings from the seed file, as a fresh install has them."""
    settings: dict[str, Any] = yaml.safe_load(SEED_FILE.read_text())
    return settings
