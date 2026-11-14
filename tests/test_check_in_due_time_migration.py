from datetime import UTC, datetime
from uuid import UUID, uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import MIGRATIONS_DIR, migrate
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import User


def add_user_with_no_due_time(engine: Engine, check_ins_enabled: bool) -> UUID:
    """Add a User with Check-ins on or off and no next due time.

    Args:
        engine: The test database.
        check_ins_enabled: Whether their Check-ins are on.

    Returns:
        The User's ID.
    """
    user = build_postgres_repositories(engine).users.add(
        User(
            id=uuid4(),
            auth_id=f"user_{uuid4()}",
            email=None,
            created_at=datetime(2026, 11, 1, tzinfo=UTC),
        )
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE users SET check_ins_enabled = :enabled, "
                "check_in_next_due_at = NULL WHERE id = :id"
            ),
            {"enabled": check_ins_enabled, "id": user.id},
        )
    return user.id


def next_due_at(engine: Engine, user_id: UUID) -> datetime | None:
    """Read a User's next due time straight from the database."""
    with engine.connect() as connection:
        due: datetime | None = connection.execute(
            text("SELECT check_in_next_due_at FROM users WHERE id = :id"),
            {"id": user_id},
        ).scalar()
    return due


def test_users_with_check_ins_on_and_no_due_time_become_due(
    engine: Engine, database_url: str
) -> None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.downgrade(config, "0023")
    try:
        on_id = add_user_with_no_due_time(engine, check_ins_enabled=True)
        off_id = add_user_with_no_due_time(engine, check_ins_enabled=False)
    finally:
        migrate(database_url)

    assert next_due_at(engine, on_id) is not None
    assert next_due_at(engine, off_id) is None
