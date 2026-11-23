import importlib
from types import ModuleType

import yaml
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate, seed_platform_settings
from tests.conftest import SEED_FILE
from tests.test_moves_migration import downgrade_to

NEW_WAIT_SETTINGS = (
    "message_wait_finished_seconds",
    "message_wait_trailing_seconds",
    "message_wait_long_text_words",
    "message_wait_trailing_words",
)


def message_wait_migration() -> ModuleType:
    """Load the longer Message wait migration module."""
    return importlib.import_module(
        "companion.adapters.postgres.migrations.versions.0066_longer_message_wait"
    )


def wait_follows_last_text_migration() -> ModuleType:
    """Load the migration that makes the wait follow how the last text reads."""
    return importlib.import_module(
        "companion.adapters.postgres.migrations.versions.0075_wait_follows_last_text"
    )


def remove_new_wait_settings(engine: Engine) -> None:
    """Remove the new wait settings, as on an install from before they existed."""
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM platform_settings WHERE key = ANY(:keys)"),
            {"keys": list(NEW_WAIT_SETTINGS)},
        )


def stored_settings(engine: Engine, keys: tuple[str, ...]) -> dict[str, object]:
    """Read some stored settings' values, by key."""
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT key, value FROM platform_settings WHERE key = ANY(:keys)"),
            {"keys": list(keys)},
        ).all()
    return {key: value for key, value in rows}


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


def test_the_wait_migration_moves_an_unchanged_message_wait_to_six_seconds(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0074")
    try:
        remove_new_wait_settings(engine)
        store_message_wait(
            engine, wait_follows_last_text_migration().OLD_MESSAGE_WAIT_SECONDS
        )
    finally:
        migrate(database_url)
    seed_platform_settings(engine, SEED_FILE)

    assert stored_message_wait(engine) == 6
    assert stored_settings(engine, NEW_WAIT_SETTINGS) == {
        "message_wait_finished_seconds": 2,
        "message_wait_trailing_seconds": 12,
        "message_wait_long_text_words": 15,
        "message_wait_trailing_words": yaml_trailing_words(),
    }


def test_the_wait_migration_keeps_a_message_wait_an_admin_changed(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0074")
    try:
        store_message_wait(engine, 9)
    finally:
        migrate(database_url)
    seed_platform_settings(engine, SEED_FILE)

    assert stored_message_wait(engine) == 9


def yaml_trailing_words() -> list[str]:
    """Read the seeded trailing words."""
    words: list[str] = yaml.safe_load(SEED_FILE.read_text())[
        "message_wait_trailing_words"
    ]
    return words


def remove_wait_cap(engine: Engine) -> None:
    """Remove the wait cap, as on an install from before it existed."""
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM platform_settings WHERE key = 'message_wait_cap_seconds'")
        )


def store_trailing_wait(engine: Engine, seconds: int) -> None:
    """Store the trailing wait, as an Admin would have."""
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE platform_settings SET value = to_jsonb(CAST(:seconds AS int)) "
                "WHERE key = 'message_wait_trailing_seconds'"
            ),
            {"seconds": seconds},
        )


def stored_wait_cap(engine: Engine) -> object:
    """Read the stored wait cap."""
    return stored_settings(engine, ("message_wait_cap_seconds",)).get(
        "message_wait_cap_seconds"
    )


def test_the_cap_migration_adds_a_cap_of_twenty_seconds_and_keeps_the_waits(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0075")
    try:
        remove_wait_cap(engine)
        store_message_wait(engine, 9)
    finally:
        migrate(database_url)
    seed_platform_settings(engine, SEED_FILE)

    assert stored_wait_cap(engine) == 20
    assert stored_message_wait(engine) == 9


def test_the_cap_migration_raises_the_cap_to_an_admins_longer_wait(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0075")
    try:
        remove_wait_cap(engine)
        store_trailing_wait(engine, 25)
    finally:
        migrate(database_url)
    seed_platform_settings(engine, SEED_FILE)

    assert stored_wait_cap(engine) == 25
    assert stored_settings(engine, ("message_wait_trailing_seconds",)) == {
        "message_wait_trailing_seconds": 25
    }
