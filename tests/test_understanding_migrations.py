import json
from typing import Any

import yaml
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import (
    MIGRATIONS_DIR,
    migrate,
    seed_platform_settings,
)
from tests.conftest import NEEDS_SEED_FILE, SEED_FILE
from tests.test_photo_viewing import stored_setting

OLD_UNDERSTANDING_PROMPT = "Pick a Need. Answer with JSON only."


def downgrade_to(database_url: str, revision: str) -> None:
    """Move the test database back to an earlier migration."""
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.downgrade(config, revision)


def stored_needs(engine: Engine) -> list[dict[str, Any]]:
    """Every stored Need, in the order they are shown."""
    with engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(
                text(
                    "SELECT name, when_it_fits, how_to_reply, is_fallback "
                    "FROM needs ORDER BY sort_order"
                )
            ).mappings()
        ]


def test_an_existing_install_gets_the_new_understanding_prompt(
    engine: Engine, database_url: str, seeded_settings: dict[str, Any]
) -> None:
    downgrade_to(database_url, "0038")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = :old "
                    "WHERE key = 'understanding_prompt'"
                ),
                {"old": json.dumps(OLD_UNDERSTANDING_PROMPT)},
            )
    finally:
        migrate(database_url)
    seed_platform_settings(engine, SEED_FILE)

    assert (
        stored_setting(engine, "understanding_prompt")
        == seeded_settings["understanding_prompt"]
    )


def test_an_existing_install_gets_get_it_done_just_before_the_fallback(
    engine: Engine, database_url: str
) -> None:
    seeded = stored_needs(engine)
    downgrade_to(database_url, "0039")
    try:
        assert "Get it done" not in [need["name"] for need in stored_needs(engine)]
    finally:
        migrate(database_url)

    assert stored_needs(engine) == seeded
    seed: list[dict[str, Any]] = yaml.safe_load(NEEDS_SEED_FILE.read_text())
    [get_it_done] = [need for need in seed if need["name"] == "Get it done"]
    [stored] = [need for need in seeded if need["name"] == "Get it done"]
    assert stored["when_it_fits"] == get_it_done["when_it_fits"]
    assert stored["how_to_reply"] == get_it_done["how_to_reply"]


def test_get_it_done_is_not_added_twice(engine: Engine, database_url: str) -> None:
    downgrade_to(database_url, "0039")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO needs (id, name, when_it_fits, how_to_reply, "
                    "sort_order, is_fallback) VALUES (gen_random_uuid(), "
                    "'get it done', 'An Admin made it.', 'Their way.', 99, false)"
                )
            )
    finally:
        migrate(database_url)

    names = [need["name"].lower() for need in stored_needs(engine)]
    assert names.count("get it done") == 1
