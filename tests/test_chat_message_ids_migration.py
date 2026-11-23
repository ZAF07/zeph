from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
from tests.fakes import FakeAuthVerifier, FakeChatChannel, ScriptedChatModel
from tests.telegram_helpers import (
    connect_telegram,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_moves_migration import downgrade_to
from tests.test_replied_to_texts_migration import saved_messages


def stored_response_prompt(engine: Engine) -> str | None:
    """Read the stored response prompt, or None if it isn't stored."""
    with engine.connect() as connection:
        prompt: str | None = connection.execute(
            text(
                "SELECT value #>> '{}' FROM platform_settings "
                "WHERE key = 'response_prompt'"
            )
        ).scalar_one_or_none()
    return prompt


def test_the_migration_adds_the_column_and_keeps_existing_messages_as_they_were(
    client: TestClient,
    engine: Engine,
    database_url: str,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("oh no")
    send_to_webhook(client, telegram_text_update("rough day"))
    messages_before = saved_messages(engine)
    downgrade_to(database_url, "0076")

    migrate(database_url)

    assert saved_messages(engine) == messages_before
    with engine.connect() as connection:
        chat_message_ids = connection.execute(
            text("SELECT chat_message_id FROM conversation_messages")
        ).scalars()
        assert set(chat_message_ids) == {None}


def test_the_migration_reloads_the_response_prompt_from_the_seed(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0076")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = to_jsonb('old prompt'::text) "
                    "WHERE key = 'response_prompt'"
                )
            )
    finally:
        migrate(database_url)

    assert stored_response_prompt(engine) is None


def test_a_users_text_keeps_its_chat_message_id(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("oh no")

    send_to_webhook(client, telegram_text_update("rough day", message_id=101))

    with engine.connect() as connection:
        chat_message_ids = connection.execute(
            text(
                "SELECT direction, chat_message_id FROM conversation_messages "
                "ORDER BY position"
            )
        ).all()
    assert [tuple(row) for row in chat_message_ids][-2:] == [
        ("incoming", 101),
        ("outgoing", None),
    ]
