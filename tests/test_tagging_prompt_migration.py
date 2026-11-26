import json
from typing import Any

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import (
    MIGRATIONS_DIR,
    migrate,
    seed_platform_settings,
)
from tests.conftest import SEED_FILE
from tests.test_photo_viewing import stored_setting


def test_an_existing_install_reloads_the_tagging_prompt_that_never_says_he_or_she(
    engine: Engine, database_url: str, seeded_settings: dict[str, Any]
) -> None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.downgrade(config, "0088")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = :old "
                    "WHERE key = 'pattern_tagging_prompt'"
                ),
                {"old": json.dumps("An older tagging prompt.")},
            )
    finally:
        migrate(database_url)
    seed_platform_settings(engine, SEED_FILE)

    prompt = stored_setting(engine, "pattern_tagging_prompt")
    assert prompt == seeded_settings["pattern_tagging_prompt"]
    assert "Never write he, she, him, her, his, hers, himself or herself" in " ".join(
        prompt.split()
    )


def test_the_migration_that_adds_conditions_keeps_a_tagging_prompt_an_admin_edited(
    engine: Engine, database_url: str
) -> None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.downgrade(config, "0109")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = :edited "
                    "WHERE key = 'pattern_tagging_prompt'"
                ),
                {"edited": json.dumps("The Admin's own tagging prompt.")},
            )
    finally:
        migrate(database_url)
    seed_platform_settings(engine, SEED_FILE)

    assert stored_setting(engine, "pattern_tagging_prompt") == (
        "The Admin's own tagging prompt."
    )
