import logging
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from langgraph.checkpoint.postgres import PostgresSaver
from sqlalchemy import Engine, text

from companion.adapters.clerk.accounts import ClerkAccounts
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.user_data import UserDataService
from tests.conftest import DASHBOARD_URL
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeConversationEngine,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import (
    OWNER_AUTH_ID,
    TELEGRAM_USER_ID,
    auth_headers,
    owner_headers,
    send_to_webhook,
    telegram_photo_update,
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
    "shared_photos",
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

    Their User Memory holds a Memory Item, a Conversation Summary and a
    Shared Photo.

    Returns:
        Their Dashboard API headers and their User ID.
    """
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_model.script("what a lovely desk")
    send_to_webhook(client, telegram_photo_update(caption="my new desk"))
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
            photos_to_keep=[{"photo": 1, "note": "Their desk at the new job"}],
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
    photos = client.get("/api/shared-photos", headers=headers).json()
    assert photos == {"photos": []}
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


def pending_auth_account_deletions(engine: Engine) -> list[tuple[str, ...]]:
    """List every row of the Clerk accounts still to delete, as plain values."""
    with engine.connect() as connection:
        return [
            tuple(str(value) for value in row)
            for row in connection.execute(
                text("SELECT * FROM pending_auth_account_deletions ORDER BY auth_id")
            )
        ]


def count_users_with_auth_id(engine: Engine, auth_id: str) -> int:
    """Count the Users signed in with an auth provider account."""
    with engine.connect() as connection:
        count: int = connection.execute(
            text("SELECT count(*) FROM users WHERE auth_id = :auth_id"),
            {"auth_id": auth_id},
        ).scalar_one()
    return count


def delete_account_while_auth_provider_fails(
    client: TestClient, auth_verifier: FakeAuthVerifier, auth_id: str
) -> dict[str, str]:
    """Sign a User in, then delete their account while their auth delete fails.

    Returns:
        Their Dashboard API headers.
    """
    headers = auth_headers(auth_verifier, auth_id)
    client.get("/api/me", headers=headers)
    auth_verifier.failing_deletes.add(auth_id)
    client.delete("/api/me", headers=headers)
    return headers


def test_a_failed_auth_account_delete_still_deletes_the_users_data(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    clock: FakeClock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    client.get("/api/me", headers=headers)
    auth_verifier.failing_deletes.add("user_maya")

    with caplog.at_level(logging.ERROR):
        response = client.delete("/api/me", headers=headers)

    assert response.status_code == 204
    assert count_users_with_auth_id(engine, "user_maya") == 0
    assert auth_verifier.deleted_accounts == []
    assert pending_auth_account_deletions(engine) == [("user_maya", str(clock.now()))]
    assert "Could not delete an account at the auth provider" in caplog.text


def test_a_successful_delete_leaves_no_auth_account_to_retry(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    client.get("/api/me", headers=headers)

    client.delete("/api/me", headers=headers)

    assert pending_auth_account_deletions(engine) == []


def test_a_later_tick_deletes_the_auth_account_once_the_provider_works(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    scheduler: FakeScheduler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    headers = delete_account_while_auth_provider_fails(
        client, auth_verifier, "user_maya"
    )

    with caplog.at_level(logging.ERROR):
        scheduler.tick()
    assert len(pending_auth_account_deletions(engine)) == 1
    assert caplog.text.count("Could not delete an account at the auth provider") == 2

    auth_verifier.failing_deletes.clear()
    scheduler.tick()

    assert auth_verifier.deleted_accounts == ["user_maya"]
    assert pending_auth_account_deletions(engine) == []
    assert client.get("/api/me", headers=headers).status_code == 401


def test_one_failing_retry_does_not_stop_the_others(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    scheduler: FakeScheduler,
) -> None:
    for auth_id in ("user_ana", "user_maya"):
        delete_account_while_auth_provider_fails(client, auth_verifier, auth_id)
    auth_verifier.failing_deletes = {"user_ana"}

    scheduler.tick()

    assert auth_verifier.deleted_accounts == ["user_maya"]
    assert [row[0] for row in pending_auth_account_deletions(engine)] == ["user_ana"]


def test_the_retry_also_deletes_a_user_made_by_signing_in_again(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    scheduler: FakeScheduler,
) -> None:
    headers = delete_account_while_auth_provider_fails(
        client, auth_verifier, "user_maya"
    )
    assert client.get("/api/me", headers=headers).status_code == 200
    assert count_users_with_auth_id(engine, "user_maya") == 1

    auth_verifier.failing_deletes.clear()
    scheduler.tick()

    assert count_users_with_auth_id(engine, "user_maya") == 0
    assert pending_auth_account_deletions(engine) == []
    assert client.get("/api/me", headers=headers).status_code == 401


def test_an_account_already_gone_from_clerk_on_retry_counts_as_deleted(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    clock: FakeClock,
) -> None:
    client.get("/api/me", headers=auth_headers(auth_verifier, "user_maya"))
    clerk_answers = iter([500, 404])
    clerk = ClerkAccounts(
        "sk_test_123",
        http_client=httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(next(clerk_answers), json={})
            )
        ),
    )
    repositories = build_postgres_repositories(engine)
    user_data = UserDataService(repositories, FakeConversationEngine(), clerk, clock)
    user = repositories.users.get_by_auth_id("user_maya")
    assert user is not None

    user_data.delete_account(user)
    assert len(pending_auth_account_deletions(engine)) == 1
    user_data.delete_pending_auth_accounts()

    assert pending_auth_account_deletions(engine) == []


def test_deleting_an_account_twice_at_once_is_harmless(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    client.get("/api/me", headers=auth_headers(auth_verifier, "user_maya"))
    users = build_postgres_repositories(engine).users
    user = users.get_by_auth_id("user_maya")
    assert user is not None

    first = users.delete_unless_last_admin(user.id, datetime(2026, 11, 11, tzinfo=UTC))
    second = users.delete_unless_last_admin(user.id, datetime(2026, 11, 11, tzinfo=UTC))

    assert (first, second) == (True, True)
    assert len(pending_auth_account_deletions(engine)) == 1


def test_deleting_needs_sign_in(client: TestClient) -> None:
    assert client.delete("/api/me/data").status_code == 401
    assert client.delete("/api/me").status_code == 401
