from datetime import UTC, datetime
from pathlib import Path

import yaml
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine
from sqlalchemy.dialects.postgresql import insert

from companion.adapters.postgres.tables import platform_settings

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def migrate(database_url: str) -> None:
    """Bring the database schema up to date.

    Args:
        database_url: SQLAlchemy URL of the database.
    """
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, "head")


def seed_platform_settings(engine: Engine, seed_file: Path) -> None:
    """Load seed platform settings, keeping any value already in the database.

    Only keys that are missing get added, so Admin edits are never overwritten
    and settings added by later releases still appear on existing installs.

    Args:
        engine: The database engine.
        seed_file: YAML file mapping setting keys to their starting values.
    """
    seed_values = yaml.safe_load(seed_file.read_text())
    now = datetime.now(UTC)
    rows = [
        {"key": key, "value": value, "updated_at": now}
        for key, value in seed_values.items()
    ]
    with engine.begin() as connection:
        connection.execute(
            insert(platform_settings).values(rows).on_conflict_do_nothing()
        )
