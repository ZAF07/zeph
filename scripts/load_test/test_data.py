"""Make and remove the load test's Users and their data in the stack's database."""

from dataclasses import replace
from datetime import datetime, time, timedelta
from uuid import uuid4

from sqlalchemy import Engine, text

from companion.core.models import (
    CheckInFrequency,
    CheckInSettings,
    Conversation,
    ConversationMessage,
    MessageDirection,
    MessageKind,
    TelegramConnection,
    User,
    UserRole,
)
from companion.core.ports import Repositories

TEST_AUTH_ID_PREFIX = "load-test-"
ADMIN_AUTH_ID = f"{TEST_AUTH_ID_PREFIX}admin"
CHAT_TELEGRAM_IDS_FROM = 9_100_000_000
CHECK_IN_TELEGRAM_IDS_FROM = 9_200_000_000
CONVERSATION_TELEGRAM_IDS_FROM = 9_300_000_000
TIME_ZONE = "UTC"
ENDED_CONVERSATION_LINES = (
    (MessageDirection.INCOMING, "work has been a lot this week"),
    (MessageDirection.OUTGOING, "that sounds heavy. what's been the hardest part?"),
    (MessageDirection.INCOMING, "my manager keeps moving deadlines"),
    (MessageDirection.OUTGOING, "that would wear anyone down."),
)


def add_onboarded_user(
    repositories: Repositories, auth_id: str, telegram_id: int, now: datetime
) -> User:
    """Save an onboarded User with a Telegram Connection.

    Args:
        repositories: Where to save them.
        auth_id: Their auth ID, starting with "load-test-".
        telegram_id: Their Telegram account and chat ID.
        now: When they signed up and onboarded.

    Returns:
        The saved User.
    """
    user = repositories.users.add(
        User(id=uuid4(), auth_id=auth_id, email=None, created_at=now)
    )
    user = repositories.users.update(
        replace(
            user,
            name=f"Tester {telegram_id % 100_000}",
            country="SG",
            time_zone=TIME_ZONE,
            ai_notice_acknowledged_at=now,
            onboarding_completed_at=now,
        )
    )
    repositories.telegram_connections.save(
        TelegramConnection(
            user_id=user.id,
            telegram_user_id=telegram_id,
            telegram_chat_id=telegram_id,
            telegram_username=None,
            connected_at=now,
        )
    )
    return user


def create_chat_users(
    repositories: Repositories, count: int, now: datetime
) -> list[int]:
    """Make the Users who chat during the load test.

    Args:
        repositories: Where to save them.
        count: How many.
        now: The time now.

    Returns:
        Their Telegram chat IDs, which the script posts texts from.
    """
    chat_ids = [CHAT_TELEGRAM_IDS_FROM + number for number in range(count)]
    for number, chat_id in enumerate(chat_ids):
        add_onboarded_user(
            repositories, f"{TEST_AUTH_ID_PREFIX}chat-{number}", chat_id, now
        )
    return chat_ids


def create_admin(repositories: Repositories, now: datetime) -> str:
    """Make the Admin whose Dashboard API pages the script times.

    Args:
        repositories: Where to save them.
        now: The time now.

    Returns:
        The bearer token that signs in as them with the load-test sign-in.
    """
    repositories.users.add(
        User(
            id=uuid4(),
            auth_id=ADMIN_AUTH_ID,
            email=None,
            created_at=now,
            role=UserRole.ADMIN,
        )
    )
    return ADMIN_AUTH_ID


def create_due_check_in_users(
    repositories: Repositories, count: int, now: datetime
) -> None:
    """Make Users whose Check-in is due now, outside their quiet hours.

    Args:
        repositories: Where to save them.
        count: How many.
        now: The time now, in UTC.
    """
    quiet_hours_start = (now + timedelta(hours=2)).time().replace(microsecond=0)
    quiet_hours_end = (now + timedelta(hours=3)).time().replace(microsecond=0)
    for number in range(count):
        user = add_onboarded_user(
            repositories,
            f"{TEST_AUTH_ID_PREFIX}check-in-{number}",
            CHECK_IN_TELEGRAM_IDS_FROM + number,
            now,
        )
        repositories.users.update(
            replace(
                user,
                check_ins=CheckInSettings(
                    enabled=True,
                    frequency=CheckInFrequency.MOST_DAYS,
                    quiet_hours_start=time(
                        quiet_hours_start.hour, quiet_hours_start.minute
                    ),
                    quiet_hours_end=time(quiet_hours_end.hour, quiet_hours_end.minute),
                    next_due_at=now - timedelta(minutes=1),
                ),
            )
        )


def create_ended_conversations(
    repositories: Repositories, count: int, now: datetime, quiet_gap: timedelta
) -> None:
    """Make Users each with a short Conversation that has been quiet too long.

    The next tick ends each one and runs the Conversation-end steps on it.

    Args:
        repositories: Where to save them.
        count: How many.
        now: The time now.
        quiet_gap: The quiet gap after which a Conversation ends.
    """
    started_at = now - quiet_gap - timedelta(minutes=10)
    for number in range(count):
        user = add_onboarded_user(
            repositories,
            f"{TEST_AUTH_ID_PREFIX}conversation-{number}",
            CONVERSATION_TELEGRAM_IDS_FROM + number,
            now,
        )
        conversation = Conversation(
            id=uuid4(),
            user_id=user.id,
            started_at=started_at,
            last_message_at=started_at,
        )
        repositories.conversations.add(conversation)
        for minute, (direction, content) in enumerate(ENDED_CONVERSATION_LINES):
            repositories.conversations.add_message(
                ConversationMessage(
                    id=uuid4(),
                    conversation_id=conversation.id,
                    direction=direction,
                    kind=MessageKind.TEXT,
                    content=content,
                    sent_at=started_at + timedelta(minutes=minute),
                )
            )


def delete_test_users(engine: Engine) -> None:
    """Delete every load-test User and, through the database, all their data.

    Run before and after each load test, so a normal backend on this
    database never makes real model calls or sends for test Users.

    Args:
        engine: The stack's database.
    """
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM users WHERE auth_id LIKE :prefix"),
            {"prefix": f"{TEST_AUTH_ID_PREFIX}%"},
        )
