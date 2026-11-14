from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import yaml
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, exists, select
from sqlalchemy.dialects.postgresql import insert

from companion.adapters.postgres.tables import (
    check_in_kinds,
    helplines,
    memory_categories,
    needs,
    platform_settings,
)

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


def seed_helplines(engine: Engine, seed_file: Path) -> None:
    """Load the seed Helplines and international fallback on first run.

    Nothing is loaded once any Helpline exists, so a Helpline an Admin removed
    never comes back.

    Args:
        engine: The database engine.
        seed_file: YAML file with `countries` (country code to a list of
            Helplines) and one `international_fallback`.
    """
    seed = yaml.safe_load(seed_file.read_text())
    fallback = seed["international_fallback"]
    rows = [
        {
            "id": uuid4(),
            "country": None,
            "name": fallback["name"],
            "number": str(fallback["number"]),
            "hours": fallback.get("hours"),
            "sort_order": 0,
        }
    ]
    for country, country_helplines in seed["countries"].items():
        rows.extend(
            {
                "id": uuid4(),
                "country": country,
                "name": helpline["name"],
                "number": str(helpline["number"]),
                "hours": helpline.get("hours"),
                "sort_order": sort_order,
            }
            for sort_order, helpline in enumerate(country_helplines)
        )
    with engine.begin() as connection:
        if connection.execute(select(exists().select_from(helplines))).scalar():
            return
        connection.execute(insert(helplines).values(rows))


def seed_memory_categories(engine: Engine, seed_file: Path) -> None:
    """Load the starting Memory Categories on first run.

    Nothing is loaded once any Memory Category exists, so Admin changes are
    never overwritten.

    Args:
        engine: The database engine.
        seed_file: YAML file listing categories with `name`, `description`
            and `always_include`, in the order to show them.
    """
    seed = yaml.safe_load(seed_file.read_text())
    rows = [
        {
            "id": uuid4(),
            "name": category["name"],
            "description": category["description"],
            "always_include": category["always_include"],
            "archived": False,
            "sort_order": sort_order,
        }
        for sort_order, category in enumerate(seed)
    ]
    with engine.begin() as connection:
        if connection.execute(select(exists().select_from(memory_categories))).scalar():
            return
        connection.execute(insert(memory_categories).values(rows))


def seed_check_in_kinds(engine: Engine, seed_file: Path) -> None:
    """Load the starting Check-in Kinds on first run.

    Nothing is loaded once any Check-in Kind exists, so Admin changes are
    never overwritten.

    Args:
        engine: The database engine.
        seed_file: YAML file listing Kinds with `name`, `description` and
            an optional `sends_shared_photo`, in the order to show them.
    """
    seed = yaml.safe_load(seed_file.read_text())
    rows = [
        {
            "id": uuid4(),
            "name": kind["name"],
            "description": kind["description"],
            "sort_order": sort_order,
            "sends_shared_photo": kind.get("sends_shared_photo", False),
        }
        for sort_order, kind in enumerate(seed)
    ]
    with engine.begin() as connection:
        if connection.execute(select(exists().select_from(check_in_kinds))).scalar():
            return
        connection.execute(insert(check_in_kinds).values(rows))


def seed_needs(engine: Engine, seed_file: Path) -> None:
    """Load the starting Needs on first run.

    Nothing is loaded once any Need exists, so Admin changes are never
    overwritten.

    Args:
        engine: The database engine.
        seed_file: YAML file listing Needs with `name`, `when_it_fits`,
            `how_to_reply` and an optional `fallback`, in the order to show
            them.
    """
    seed = yaml.safe_load(seed_file.read_text())
    rows = [
        {
            "id": uuid4(),
            "name": need["name"],
            "when_it_fits": need["when_it_fits"],
            "how_to_reply": need["how_to_reply"],
            "sort_order": sort_order,
            "is_fallback": need.get("fallback", False),
        }
        for sort_order, need in enumerate(seed)
    ]
    with engine.begin() as connection:
        if connection.execute(select(exists().select_from(needs))).scalar():
            return
        connection.execute(insert(needs).values(rows))
