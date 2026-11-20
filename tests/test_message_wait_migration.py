import importlib
from types import ModuleType

from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
from tests.test_moves_migration import downgrade_to


def message_wait_migration() -> ModuleType:
    """Load the longer Message wait migration module."""
    return importlib.import_module(
        "companion.adapters.postgres.migrations.versions.0066_longer_message_wait"
    )


def store_message_wait(engine: Engine, seconds: int) -> None:
    """Store a Message wait value, as an Admin or the old seed would have."""
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE platform_settings SET value = to_jsonb(CAST(:seconds AS int)) "
                "WHERE key = 'message_wait_seconds'"
            ),
            {"seconds": seconds},
        )


def stored_message_wait(engine: Engine) -> int | None:
    """Read the stored Message wait, or None if it isn't stored."""
    with engine.connect() as connection:
        value: int | None = connection.execute(
            text(
                "SELECT (value #>> '{}')::int FROM platform_settings "
                "WHERE key = 'message_wait_seconds'"
            )
        ).scalar_one_or_none()
    return value


def test_the_migration_reloads_a_message_wait_still_at_the_old_seed(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0065")
    try:
        store_message_wait(engine, message_wait_migration().OLD_MESSAGE_WAIT_SECONDS)
    finally:
        migrate(database_url)

    assert stored_message_wait(engine) is None


def test_the_migration_keeps_a_message_wait_an_admin_changed(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0065")
    try:
        store_message_wait(engine, 9)
    finally:
        migrate(database_url)

    assert stored_message_wait(engine) == 9
