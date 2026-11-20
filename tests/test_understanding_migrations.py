import json
from typing import Any

import yaml
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import (
    MIGRATIONS_DIR,
    migrate,
    seed_platform_settings,
)
from companion.adapters.postgres.repositories import build_postgres_repositories
from tests.conftest import NEEDS_SEED_FILE, SEED_FILE
from tests.fakes import FakeAuthVerifier, FakeChatChannel, ScriptedChatModel
from tests.telegram_helpers import (
    connect_telegram,
    send_to_webhook,
    telegram_text_update,
)
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
    needs_before = stored_needs(engine)
    downgrade_to(database_url, "0039")
    try:
        assert "Get it done" not in [need["name"] for need in stored_needs(engine)]
    finally:
        migrate(database_url)

    assert stored_needs(engine) == needs_before
    seed_needs: list[dict[str, Any]] = yaml.safe_load(NEEDS_SEED_FILE.read_text())
    [get_it_done] = [need for need in seed_needs if need["name"] == "Get it done"]
    [stored] = [need for need in needs_before if need["name"] == "Get it done"]
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


OLD_UNDERSTANDING_FORM = {
    "need": "Be heard",
    "nuance": "Let them vent.",
    "mood": "furious",
    "intensity": "high",
    "cause_known": False,
    "memory_categories": ["Work"],
    "bring_up": [],
    "left_alone": [],
    "look_up_past": ["boss review"],
    "knowledge": None,
    "threads_touched": [],
    "struggling": True,
    "asked_for_photo": False,
    "lead_move": "Mirror",
    "support_move": "",
    "next_move": "",
    "next_move_why": "",
}


def test_an_existing_install_moves_deciding_to_reply_plans_and_resets_the_prompt(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
    database_url: str,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("hey")
    send_to_webhook(client, telegram_text_update("my boss again"))
    downgrade_to(database_url, "0066")
    try:
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE understandings SET form = :form, need = 'Be heard'"),
                {"form": json.dumps(OLD_UNDERSTANDING_FORM)},
            )
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = :edited "
                    "WHERE key = 'understanding_prompt'"
                ),
                {"edited": json.dumps("An Admin's prompt that picks a Need.")},
            )
    finally:
        migrate(database_url)
    seed_platform_settings(engine, SEED_FILE)

    assert (
        stored_setting(engine, "understanding_prompt")
        == seeded_settings["understanding_prompt"]
    )
    repositories = build_postgres_repositories(engine)
    with engine.connect() as connection:
        conversation_id = connection.execute(
            text("SELECT conversation_id FROM understandings")
        ).scalar_one()
        columns = set(
            connection.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'understandings'"
                )
            ).scalars()
        )
    assert "need" not in columns
    assert "lead_move" not in columns
    [understanding] = repositories.understandings.list_for_conversation(conversation_id)
    assert understanding.form.mood == "furious"
    assert understanding.form.struggling is True
    assert understanding.form.look_up_past == ("boss review",)
    assert understanding.form.means == ""
    assert repositories.reply_plans.list_for_conversation(conversation_id) == []
