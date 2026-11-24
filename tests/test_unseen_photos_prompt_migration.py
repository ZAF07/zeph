from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
from tests.fakes import FakeAuthVerifier, FakeChatChannel, ScriptedChatModel
from tests.telegram_helpers import (
    connect_telegram,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_chat_message_ids_migration import stored_response_prompt
from tests.test_moves_migration import downgrade_to
from tests.test_replied_to_texts_migration import saved_messages


def test_the_migration_reloads_the_response_prompt_from_the_seed(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0077")
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


def test_the_migration_keeps_the_users_messages(
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
    downgrade_to(database_url, "0077")

    migrate(database_url)

    assert saved_messages(engine) == messages_before
