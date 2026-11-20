import importlib
from types import ModuleType

from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
from tests.test_moves_migration import downgrade_to


def life_threads_in_mind_migration() -> ModuleType:
    """Load the Life Threads in mind migration module."""
    return importlib.import_module(
        "companion.adapters.postgres.migrations.versions.0072_life_threads_in_mind"
    )


def store_life_threads_per_reply(engine: Engine, count: int) -> None:
    """Store the most Life Threads per reply, as an Admin or the old seed would."""
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE platform_settings SET value = to_jsonb(CAST(:count AS int)) "
                "WHERE key = 'life_threads_per_reply'"
            ),
            {"count": count},
        )


def stored_life_threads_per_reply(engine: Engine) -> int | None:
    """Read the stored most Life Threads per reply, or None if it isn't stored."""
    with engine.connect() as connection:
        value: int | None = connection.execute(
            text(
                "SELECT (value #>> '{}')::int FROM platform_settings "
                "WHERE key = 'life_threads_per_reply'"
            )
        ).scalar_one_or_none()
    return value


def test_the_migration_reloads_a_thread_cap_still_at_the_old_seed(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0071")
    try:
        store_life_threads_per_reply(
            engine, life_threads_in_mind_migration().OLD_LIFE_THREADS_PER_REPLY
        )
    finally:
        migrate(database_url)

    assert stored_life_threads_per_reply(engine) is None


def test_the_migration_keeps_a_thread_cap_an_admin_changed(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0071")
    try:
        store_life_threads_per_reply(engine, 5)
    finally:
        migrate(database_url)

    assert stored_life_threads_per_reply(engine) == 5
