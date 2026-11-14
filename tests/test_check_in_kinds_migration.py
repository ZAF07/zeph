from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect

from companion.adapters.postgres.database import MIGRATIONS_DIR, migrate


def check_in_kind_columns(engine: Engine) -> list[str]:
    """List the columns of the Check-in Kinds table.

    Args:
        engine: The database engine.

    Returns:
        The column names.
    """
    return [column["name"] for column in inspect(engine).get_columns("check_in_kinds")]


def test_check_in_kinds_no_longer_store_allowed_without_user_memory(
    engine: Engine, database_url: str
) -> None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.downgrade(config, "0022")
    try:
        columns_before = check_in_kind_columns(engine)
    finally:
        migrate(database_url)

    assert "allowed_without_user_memory" in columns_before
    assert "allowed_without_user_memory" not in check_in_kind_columns(engine)
