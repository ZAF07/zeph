from typing import Any

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import (
    MIGRATIONS_DIR,
    migrate,
    seed_platform_settings,
)
from tests.conftest import SEED_FILE
from tests.fakes import FakeAuthVerifier, FakeChatChannel, ScriptedChatModel, ToolCall
from tests.telegram_helpers import TELEGRAM_CHAT_ID, auth_headers, owner_headers
from tests.test_check_in_sending import set_up_user_with_check_ins
from tests.test_photo_viewing import stored_setting
from tests.test_settings_via_chat import reply_call

RELOADED_KEYS = (
    "user_memory_explanation",
    "memory_paused_note",
    "memory_not_available_note",
    "data_deleted_reply",
)


def test_the_consent_explanation_mentions_private_notes_and_delete_my_data(
    seeded_settings: dict[str, Any],
) -> None:
    explanation = seeded_settings["user_memory_explanation"]

    assert "private notes" in explanation
    assert "Delete My Data" in explanation
    assert "Everything I remember is listed" not in explanation


def test_the_memory_off_notes_point_to_delete_my_data(
    seeded_settings: dict[str, Any],
) -> None:
    for key in ("memory_paused_note", "memory_not_available_note"):
        assert "won’t learn anything new" in seeded_settings[key]
        assert "Delete My Data" in seeded_settings[key]


def test_delete_my_data_wording_mentions_private_notes(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    seeded_settings: dict[str, Any],
) -> None:
    maya = auth_headers(auth_verifier, "user_maya")

    content = client.get("/api/platform-content", headers=maya).json()

    assert "private notes" in content["delete_my_data_description"]
    assert "private notes" in seeded_settings["data_deleted_reply"]
    assert "private notes" in seeded_settings["data_deletion_started_note"]


def test_admins_can_edit_the_memory_off_and_delete_my_data_lines(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    maya = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    saved = client.patch(
        "/api/admin/settings",
        json={
            "values": {
                "memory_off_chat_line": "Edited memory-off line.",
                "data_deletion_started_note": 'Edited. Ask for "{word}".',
                "delete_my_data_description": "Edited description.",
                "data_deleted_reply": "Edited deleted reply.",
            }
        },
        headers=admin,
    )
    assert saved.status_code == 200

    chat_channel.sent.clear()
    reply_call(
        client,
        chat_model,
        "stop remembering things",
        ToolCall("turn_user_memory_on_or_off", {"on": False}),
        "Done.",
    )
    started = reply_call(
        client,
        chat_model,
        "delete my data",
        ToolCall("start_deleting_my_data", {}),
        "Sure.",
    )
    content = client.get("/api/platform-content", headers=maya).json()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)[:2] == [
        "Done.",
        "Edited memory-off line.",
    ]
    assert started.tool_results[0].startswith("Edited. Ask for ")
    assert content["delete_my_data_description"] == "Edited description."


def test_the_delete_prompt_must_keep_the_confirmation_word_placeholder(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
) -> None:
    admin = owner_headers(client, auth_verifier)

    saved = client.patch(
        "/api/admin/settings",
        json={"values": {"data_deletion_started_note": "No word here."}},
        headers=admin,
    )

    assert saved.status_code == 422


def test_an_existing_install_reloads_the_reworded_settings(
    engine: Engine,
    database_url: str,
    seeded_settings: dict[str, Any],
) -> None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.downgrade(config, "0033")
    try:
        with engine.begin() as connection:
            for key in RELOADED_KEYS:
                connection.execute(
                    text(
                        "INSERT INTO platform_settings (key, value, updated_at) "
                        "VALUES (:key, '\"The old one.\"', now()) "
                        "ON CONFLICT (key) DO UPDATE SET value = excluded.value"
                    ),
                    {"key": key},
                )
    finally:
        migrate(database_url)

    seed_platform_settings(engine, SEED_FILE)

    for key in RELOADED_KEYS:
        assert stored_setting(engine, key) == seeded_settings[key]
