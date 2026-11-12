from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Engine, create_engine, insert, select
from sqlalchemy.exc import SQLAlchemyError

from companion.adapters.postgres.tables import platform_settings
from companion.config import Settings

COMPOSE_DATABASE_HOST = "postgres"


def app_database_url(settings: Settings) -> str:
    """Build the URL of the app's own database, as seen from this machine.

    Docker Compose names the database host "postgres"; outside Compose the
    same database is published on localhost.

    Args:
        settings: The settings from `.env`.

    Returns:
        The database URL.
    """
    if settings.postgres_host == COMPOSE_DATABASE_HOST:
        settings = settings.model_copy(update={"postgres_host": "localhost"})
    return settings.database_url


def read_current_platform_settings(database_url: str) -> dict[str, Any] | None:
    """Read the platform settings Admins have in the app's database.

    Args:
        database_url: The app's database URL.

    Returns:
        Every setting's value by key, or None if the database can't be
        reached or holds no settings.
    """
    engine = create_engine(database_url, connect_args={"connect_timeout": 3})
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                select(platform_settings.c.key, platform_settings.c.value)
            ).all()
    except SQLAlchemyError:
        return None
    finally:
        engine.dispose()
    return {row.key: row.value for row in rows} or None


def store_platform_settings(engine: Engine, values: dict[str, Any]) -> None:
    """Store platform settings in an empty eval database.

    Seeding afterwards only adds keys still missing, so these values win.

    Args:
        engine: The eval database.
        values: Each setting's value by key.
    """
    now = datetime.now(UTC)
    rows = [
        {"key": key, "value": value, "updated_at": now} for key, value in values.items()
    ]
    with engine.begin() as connection:
        connection.execute(insert(platform_settings).values(rows))
