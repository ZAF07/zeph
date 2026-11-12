from typing import Any

from fastapi.testclient import TestClient
from langgraph.checkpoint.postgres import PostgresSaver
from sqlalchemy import Engine, text

from tests.conftest import DASHBOARD_URL
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import (
    OWNER_AUTH_ID,
    TELEGRAM_USER_ID,
    auth_headers,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_check_in_sending import (
    recent_check_ins,
    send_check_ins,
    set_up_user_with_check_ins,
)
from tests.test_message_retention import has_checkpoints
from tests.test_post_conversation import (
    have_conversation,
    memory_contents,
    processing_answer,
)

USER_DATA_TABLES = (
    "conversations",
    "conversation_summaries",
    "memory_items",
    "check_ins",
    "connection_tokens",
    "telegram_connections",
)


def set_up_user_with_every_kind_of_data(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> tuple[dict[str, str], str]:
    """Give a User messages, User Memory, a Check-in and a Telegram Connection.

    Returns:
        Their Dashboard API headers and their User ID.
    """
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "I started a new job in design",
        processing_answer(
            summary="Shared that they started a new job.",
            operations=[
                {"action": "add", "category": "Life details", "content": "Designer"}
            ],
        ),
    )
    send_check_ins(chat_model, clock, scheduler, count=1)
    chat_model.script("thanks for checking in")
    send_to_webhook(client, telegram_text_update("doing well, thanks"))
    user_id: str = client.get("/api/me", headers=headers).json()["id"]
    return headers, user_id


def rows_per_table(engine: Engine, user_id: str) -> dict[str, int]:
    """Count a User's rows in each table that holds their data."""
    with engine.connect() as connection:
        return {
            table: connection.execute(
                text(f"SELECT count(*) FROM {table} WHERE user_id = :user_id"),  # noqa: S608
                {"user_id": user_id},
            ).scalar_one()
            for table in USER_DATA_TABLES
        }


def message_count(engine: Engine) -> int:
    """Count every saved message."""
    with engine.connect() as connection:
        count: int = connection.execute(
            text("SELECT count(*) FROM conversation_messages")
        ).scalar_one()
    return count


def assert_treated_as_unknown_telegram_user(
    client: TestClient,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    """Check a message from the User's Telegram gets the unknown-user reply."""
    chat_channel.sent.clear()
    model_calls_before = len(chat_model.calls)

    send_to_webhook(client, telegram_text_update("hello again"))

    expected_reply = seeded_settings["unknown_telegram_user_reply"].replace(
        "{dashboard_url}", DASHBOARD_URL
    )
    assert chat_channel.texts_sent_to(TELEGRAM_USER_ID) == [expected_reply]
    assert len(chat_model.calls) == model_calls_before


def test_delete_my_data_removes_every_kind_of_data_but_keeps_the_account(
    client: TestClient,
    engine: Engine,
    checkpointer: PostgresSaver,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    headers, user_id = set_up_user_with_every_kind_of_data(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    assert all(count > 0 for count in rows_per_table(engine, user_id).values())
    assert has_checkpoints(checkpointer, user_id)

    response = client.delete("/api/me/data", headers=headers)

    assert response.status_code == 204
    assert rows_per_table(engine, user_id) == dict.fromkeys(USER_DATA_TABLES, 0)
    assert message_count(engine) == 0
    assert not has_checkpoints(checkpointer, user_id)
    assert memory_contents(client, headers) == {}
    summaries = client.get("/api/conversation-summaries", headers=headers).json()
    assert summaries == {"summaries": []}
    assert recent_check_ins(client, headers) == []
    connection = client.get("/api/telegram-connection", headers=headers).json()
    assert connection == {"connection": None, "latest_token": None}
    me = client.get("/api/me", headers=headers).json()
    assert me["name"] == "Maya"
    assert me["onboarding_completed_at"] is not None
    assert auth_verifier.deleted_accounts == []
    assert_treated_as_unknown_telegram_user(
        client, chat_channel, chat_model, seeded_settings
    )


def test_delete_my_data_leaves_other_users_alone(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    _, user_id = set_up_user_with_every_kind_of_data(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    before = rows_per_table(engine, user_id)

    response = client.delete(
        "/api/me/data", headers=owner_headers(client, auth_verifier)
    )

    assert response.status_code == 204
    assert rows_per_table(engine, user_id) == before


def test_delete_account_removes_the_user_and_their_auth_account(
    client: TestClient,
    engine: Engine,
    checkpointer: PostgresSaver,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    headers, user_id = set_up_user_with_every_kind_of_data(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )

    response = client.delete("/api/me", headers=headers)

    assert response.status_code == 204
    assert auth_verifier.deleted_accounts == ["user_maya"]
    with engine.connect() as connection:
        users_left = connection.execute(
            text("SELECT count(*) FROM users WHERE id = :user_id"),
            {"user_id": user_id},
        ).scalar_one()
    assert users_left == 0
    assert rows_per_table(engine, user_id) == dict.fromkeys(USER_DATA_TABLES, 0)
    assert message_count(engine) == 0
    assert not has_checkpoints(checkpointer, user_id)
    assert client.get("/api/me", headers=headers).status_code == 401
    assert_treated_as_unknown_telegram_user(
        client, chat_channel, chat_model, seeded_settings
    )


def test_the_last_admin_cannot_delete_their_account(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    response = client.delete("/api/me", headers=headers)

    assert response.status_code == 409
    assert "only Admin" in response.json()["detail"]
    assert auth_verifier.deleted_accounts == []
    assert client.get("/api/me", headers=headers).json()["role"] == "admin"


def test_an_admin_can_delete_their_account_while_another_admin_remains(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    owner = owner_headers(client, auth_verifier)
    maya = auth_headers(auth_verifier, "user_maya")
    maya_id = client.get("/api/me", headers=maya).json()["id"]
    promoted = client.put(
        f"/api/admin/users/{maya_id}/role", json={"role": "admin"}, headers=owner
    )
    assert promoted.status_code == 200

    response = client.delete("/api/me", headers=owner)

    assert response.status_code == 204
    assert auth_verifier.deleted_accounts == [OWNER_AUTH_ID]
    assert client.get("/api/me", headers=maya).json()["role"] == "admin"


def test_deleting_needs_sign_in(client: TestClient) -> None:
    assert client.delete("/api/me/data").status_code == 401
    assert client.delete("/api/me").status_code == 401
