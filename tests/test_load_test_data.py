from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import User, UserRole
from scripts.load_test.test_data import (
    ADMIN_AUTH_ID,
    create_admin,
    create_chat_users,
    create_due_check_in_users,
    create_ended_conversations,
    delete_test_users,
)
from tests.fakes import FakeChatChannel, FakeClock, ScriptedChatModel
from tests.telegram_helpers import send_to_webhook, telegram_text_update


def test_chat_users_are_onboarded_and_get_replies_on_telegram(
    client: TestClient,
    engine: Engine,
    clock: FakeClock,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    repositories = build_postgres_repositories(engine)

    chat_ids = create_chat_users(repositories, 3, clock.now())

    assert len(set(chat_ids)) == 3
    chat_model.script("hey, good to hear from you")
    send_to_webhook(client, telegram_text_update("hi", telegram_user_id=chat_ids[1]))
    assert chat_channel.texts_sent_to(chat_ids[1]) == ["hey, good to hear from you"]


def test_the_admin_signs_in_with_its_auth_id(engine: Engine, clock: FakeClock) -> None:
    repositories = build_postgres_repositories(engine)

    token = create_admin(repositories, clock.now())

    assert token == ADMIN_AUTH_ID
    admin = repositories.users.get_by_auth_id(ADMIN_AUTH_ID)
    assert admin is not None
    assert admin.role == UserRole.ADMIN


def test_check_in_users_are_due_now_and_reachable(
    engine: Engine, clock: FakeClock
) -> None:
    repositories = build_postgres_repositories(engine)

    create_due_check_in_users(repositories, 4, clock.now())

    due = repositories.check_ins.list_due_users(clock.now())
    assert len(due) == 4
    for user in due:
        assert repositories.telegram_connections.get_by_user(user.id) is not None


def test_conversations_are_left_quiet_long_enough_to_end(
    engine: Engine, clock: FakeClock
) -> None:
    repositories = build_postgres_repositories(engine)
    quiet_gap = timedelta(minutes=15)

    create_ended_conversations(repositories, 5, clock.now(), quiet_gap)

    repositories.conversations.end_quiet(
        quiet_since=clock.now() - quiet_gap, ended_at=clock.now()
    )
    ended = repositories.conversations.list_ended_unprocessed()
    assert len(ended) == 5
    for conversation in ended:
        assert len(repositories.conversations.list_messages(conversation.id)) == 4


def test_only_load_test_users_are_deleted(engine: Engine, clock: FakeClock) -> None:
    repositories = build_postgres_repositories(engine)
    real_user = repositories.users.add(
        User(id=uuid4(), auth_id="user_maya", email=None, created_at=clock.now())
    )
    create_chat_users(repositories, 2, clock.now())
    create_admin(repositories, clock.now())
    create_due_check_in_users(repositories, 2, clock.now())
    create_ended_conversations(repositories, 2, clock.now(), timedelta(minutes=15))

    delete_test_users(engine)

    with engine.begin() as connection:
        auth_ids = connection.execute(text("SELECT auth_id FROM users")).scalars()
        assert list(auth_ids) == [real_user.auth_id]
