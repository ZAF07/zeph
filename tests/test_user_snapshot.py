import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event

from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.admin_users import UserNotFoundError
from companion.core.features import FeatureService
from companion.core.models import (
    CheckInSettings,
    Feature,
    TelegramConnection,
    User,
    UserFeatureSwitch,
    UserRole,
)
from companion.core.user_snapshot import UserSnapshotLoader
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_check_in_sending import set_up_user_with_check_ins, skip_answer

SNAPSHOT_TABLES = ("users", "feature_switches", "user_feature_switches")


@contextmanager
def reads_by_table(engine: Engine) -> Iterator[dict[str, int]]:
    """Count the SELECT statements whose main table is a User or switch table.

    A table only joined in, like `users` for who changed a switch, isn't
    counted.

    Args:
        engine: The database engine the app uses.

    Yields:
        The counts by table name, filled in while the block runs.
    """
    counts = dict.fromkeys(SNAPSHOT_TABLES, 0)

    def count(
        connection: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        if not statement.lstrip().upper().startswith("SELECT"):
            return
        for table in SNAPSHOT_TABLES:
            if re.search(rf"\bFROM {table}\b", statement):
                counts[table] += 1

    event.listen(engine, "before_cursor_execute", count)
    try:
        yield counts
    finally:
        event.remove(engine, "before_cursor_execute", count)


def add_due_users(engine: Engine, clock: FakeClock, how_many: int) -> list[User]:
    """Add onboarded Users with Telegram and Check-ins on, each due right now.

    Args:
        engine: The test database.
        clock: Tells the current time.
        how_many: How many Users to add.

    Returns:
        The Users added.
    """
    repositories = build_postgres_repositories(engine)
    now = clock.now()
    added = []
    for number in range(how_many):
        user = repositories.users.add(
            User(
                id=uuid4(),
                auth_id=f"user_due_{number}_{uuid4()}",
                email=None,
                created_at=now,
            )
        )
        repositories.users.update(
            replace(
                user,
                name=f"Due {number}",
                onboarding_completed_at=now,
                check_ins=CheckInSettings(enabled=True, next_due_at=now),
            )
        )
        telegram_user_id = 900_000 + number + 10 * how_many
        repositories.telegram_connections.save(
            TelegramConnection(
                user_id=user.id,
                telegram_user_id=telegram_user_id,
                telegram_chat_id=telegram_user_id,
                telegram_username=None,
                connected_at=now,
            )
        )
        added.append(user)
    return added


def test_a_reply_reads_the_user_and_their_switches_once(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_model.script("hey, good to hear from you")

    with reads_by_table(engine) as reads:
        send_to_webhook(client, telegram_text_update("hi Zeph"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)[-1] == (
        "hey, good to hear from you"
    )
    assert reads == {"users": 1, "feature_switches": 1, "user_feature_switches": 1}


def test_a_check_in_tick_reads_users_and_switches_the_same_for_many_due_users(
    client: TestClient,
    engine: Engine,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    add_due_users(engine, clock, 1)
    chat_model.script(skip_answer("not now"))
    with reads_by_table(engine) as reads_for_one:
        scheduler.tick()

    clock.advance(timedelta(minutes=1))
    add_due_users(engine, clock, 5)
    chat_model.script(*[skip_answer("not now")] * 5)
    with reads_by_table(engine) as reads_for_five:
        scheduler.tick()

    assert len(chat_model.calls) == 6
    assert reads_for_five == reads_for_one
    assert reads_for_one["feature_switches"] == 1
    assert reads_for_one["user_feature_switches"] == 1


def test_a_check_in_tick_with_no_due_users_reads_no_switches(
    client: TestClient,
    engine: Engine,
    scheduler: FakeScheduler,
) -> None:
    with reads_by_table(engine) as reads:
        scheduler.tick()

    assert reads["feature_switches"] == 0
    assert reads["user_feature_switches"] == 0


def test_snapshots_hold_the_same_feature_statuses_as_the_feature_service(
    engine: Engine, clock: FakeClock
) -> None:
    repositories = build_postgres_repositories(engine)
    maya, sam = add_due_users(engine, clock, 2)
    admin = repositories.users.update(replace(sam, role=UserRole.ADMIN))
    features = FeatureService(repositories, clock, "http://dashboard.test")
    features.set_for_everyone(Feature.STICKERS, False, admin)
    features.set_for_user(maya.id, Feature.WEB_SEARCH, UserFeatureSwitch.OFF, admin)
    repositories.users.update(replace(maya, time_zone="Asia/Singapore"))
    loader = UserSnapshotLoader(repositories, clock)

    snapshots = loader.load_many([sam.id, uuid4(), maya.id])

    assert [snapshot.user.id for snapshot in snapshots] == [sam.id, maya.id]
    for snapshot in snapshots:
        assert list(snapshot.features) == features.statuses_for(snapshot.user.id)
    maya_snapshot = snapshots[1]
    assert not maya_snapshot.works(Feature.WEB_SEARCH)
    assert not maya_snapshot.works(Feature.STICKERS)
    assert maya_snapshot.unavailable_features[:2] == [
        Feature.WEB_SEARCH,
        Feature.STICKERS,
    ]
    assert maya_snapshot.local_now.utcoffset() == timedelta(hours=8)
    assert maya_snapshot.today == (clock.now() + timedelta(hours=8)).date()
    assert loader.load(maya.id) == maya_snapshot
    with pytest.raises(UserNotFoundError):
        loader.load(uuid4())
