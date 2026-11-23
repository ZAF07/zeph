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


def saved_messages(engine: Engine) -> list[tuple[str, str]]:
    """The saved messages' direction and content, in the order saved."""
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT direction, content FROM conversation_messages ORDER BY position"
            )
        ).all()
    return [(row.direction, row.content) for row in rows]


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
    downgrade_to(database_url, "0073")

    migrate(database_url)

    assert saved_messages(engine) == messages_before
    with engine.connect() as connection:
        replied_to = connection.execute(
            text("SELECT replied_to FROM conversation_messages")
        ).scalars()
        assert set(replied_to) == {None}
