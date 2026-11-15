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

OLD_KNOWLEDGE_INTRO = (
    "Passages from your Knowledge library that may relate to this message. "
    "Most of the time, use none of them."
)


def test_an_existing_install_gets_the_new_knowledge_intro(
    engine: Engine, database_url: str, seeded_settings: dict[str, Any]
) -> None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.downgrade(config, "0037")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = :old "
                    "WHERE key = 'reply_knowledge_intro'"
                ),
                {"old": json.dumps(OLD_KNOWLEDGE_INTRO)},
            )
    finally:
        migrate(database_url)
    seed_platform_settings(engine, SEED_FILE)

    assert (
        stored_setting(engine, "reply_knowledge_intro")
        == seeded_settings["reply_knowledge_intro"]
    )
