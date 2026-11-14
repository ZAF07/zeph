import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import Engine, event, text

from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import (
    CheckIn,
    CheckInOutcome,
    Conversation,
    NextDueTimeChange,
    User,
)
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    auth_headers,
    create_connection_token,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_check_in_sending import (
    ONE_DAY,
    send_answer,
    set_up_user_with_check_ins,
)
from tests.test_features import switch_for_everyone
from tests.test_onboarding import onboarding_answers
from tests.test_user_snapshot import add_due_users, reads_by_table
from tests.test_web_search import change_settings


@contextmanager
def selects_by_table(engine: Engine) -> Iterator[dict[str, int]]:
    """Count every SELECT statement by its main table while the block runs.

    Args:
        engine: The database engine the app uses.

    Yields:
        The counts by table name, filled in while the block runs.
    """
    counts: dict[str, int] = {}

    def count(
        connection: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        found = re.search(r"\bFROM (\w+)", statement)
        if statement.lstrip().upper().startswith("SELECT") and found:
            counts[found.group(1)] = counts.get(found.group(1), 0) + 1

    event.listen(engine, "before_cursor_execute", count)
    try:
        yield counts
    finally:
        event.remove(engine, "before_cursor_execute", count)


def next_due_at(engine: Engine, user_id: UUID) -> datetime | None:
    """Read a User's next due time straight from the database.

    Args:
        engine: The test database.
        user_id: The User.

    Returns:
        Their next due time; None for none.
    """
    with engine.connect() as connection:
        due: datetime | None = connection.execute(
            text("SELECT check_in_next_due_at FROM users WHERE id = :id"),
            {"id": user_id},
        ).scalar()
    return due


def maya_id(client: TestClient, headers: dict[str, str]) -> UUID:
    """Read the signed-in User's ID."""
    return UUID(client.get("/api/me", headers=headers).json()["id"])


def due_users_needing_no_model(
    engine: Engine, clock: FakeClock, users: list[User]
) -> None:
    """Make each due User need no model call, in turns of five ways.

    Held back by Quiet Hours, mid-Conversation or no Telegram Connection;
    over the Daily Message Limit (set to 1); or ignored three Check-ins.

    Args:
        engine: The test database.
        clock: Tells the current time.
        users: Due Users from `add_due_users`.
    """
    repositories = build_postgres_repositories(engine)
    now = clock.now()
    for number, user in enumerate(users):
        reason = number % 5
        if reason == 0:
            quiet_now = (now - timedelta(hours=1)).time()
            stored = repositories.users.get(user.id)
            assert stored is not None
            repositories.users.update(
                replace(
                    stored,
                    check_ins=replace(
                        stored.check_ins,
                        quiet_hours_start=quiet_now,
                        quiet_hours_end=(now + timedelta(hours=1)).time(),
                    ),
                )
            )
        elif reason == 1:
            repositories.conversations.add(
                Conversation(
                    id=uuid4(),
                    user_id=user.id,
                    started_at=now - timedelta(minutes=5),
                    last_message_at=now - timedelta(minutes=1),
                )
            )
        elif reason == 2:
            with engine.begin() as connection:
                connection.execute(
                    text("DELETE FROM telegram_connections WHERE user_id = :id"),
                    {"id": user.id},
                )
        elif reason == 3:
            repositories.usage.claim_message(user.id, now.date(), 1)
        else:
            for days_ago in (3, 2, 1):
                repositories.check_ins.add(
                    CheckIn(
                        id=uuid4(),
                        user_id=user.id,
                        outcome=CheckInOutcome.SENT,
                        decided_at=now - timedelta(days=days_ago),
                        message="hey",
                    ),
                    now,
                    pause_until_resumed=False,
                )


def test_reads_per_tick_stay_the_same_as_due_users_grow(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    engine: Engine,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    change_settings(
        client, owner_headers(client, auth_verifier), {"daily_message_limit": 1}
    )
    due_users_needing_no_model(engine, clock, add_due_users(engine, clock, 5))
    with selects_by_table(engine) as reads_for_five:
        scheduler.tick()

    clock.advance(timedelta(minutes=1))
    due_users_needing_no_model(engine, clock, add_due_users(engine, clock, 15))
    with selects_by_table(engine) as reads_for_fifteen:
        scheduler.tick()

    assert chat_model.calls == []
    assert len(chat_channel.sent) == 1 + 3
    assert reads_for_fifteen == reads_for_five


def test_a_user_in_quiet_hours_is_due_again_when_they_end_and_not_reloaded_before(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    engine: Engine,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    clock.advance(ONE_DAY + timedelta(hours=6))
    chat_model.script(send_answer("morning! sleep ok?"))

    scheduler.tick()
    quiet_hours_end = next_due_at(engine, maya_id(client, headers))
    clock.advance(timedelta(minutes=10))
    with reads_by_table(engine) as reads_while_quiet:
        scheduler.tick()

    assert chat_channel.sent == []
    assert quiet_hours_end is not None
    assert quiet_hours_end == clock.now() - timedelta(minutes=10) + timedelta(
        hours=8, minutes=30
    )
    assert reads_while_quiet["feature_switches"] == 0

    clock.advance(quiet_hours_end - clock.now())
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["morning! sleep ok?"]


def test_a_user_paused_until_resumed_has_no_due_time_until_they_resume(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    engine: Engine,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    user_id = maya_id(client, headers)
    client.put(
        "/api/check-ins/pause", json={"length": "until_resumed"}, headers=headers
    )
    clock.advance(ONE_DAY)
    scheduler.tick()
    due_while_paused = next_due_at(engine, user_id)

    clock.advance(timedelta(hours=2))
    client.delete("/api/check-ins/pause", headers=headers)
    due_after_resuming = next_due_at(engine, user_id)
    chat_model.script(send_answer("welcome back 👋"))
    scheduler.tick()

    assert due_while_paused is None
    assert due_after_resuming == clock.now()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["welcome back 👋"]


def test_a_user_held_back_to_the_end_of_a_timed_pause_gets_one_when_resuming_early(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    engine: Engine,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    user_id = maya_id(client, headers)
    clock.advance(ONE_DAY - timedelta(hours=1))
    client.put("/api/check-ins/pause", json={"length": "week"}, headers=headers)
    pause_end = clock.now() + timedelta(weeks=1)
    clock.advance(timedelta(hours=1))
    scheduler.tick()
    due_while_paused = next_due_at(engine, user_id)

    clock.advance(timedelta(days=2))
    client.delete("/api/check-ins/pause", headers=headers)
    chat_model.script(send_answer("hey, back already?"))
    scheduler.tick()

    assert due_while_paused == pause_end
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey, back already?"]


def test_a_user_with_no_telegram_connection_gets_a_due_time_once_they_connect(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    engine: Engine,
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    answers = onboarding_answers(check_ins_enabled=True, check_in_frequency="most_days")
    assert (
        client.put("/api/onboarding", json=answers, headers=headers).status_code == 200
    )
    user_id = maya_id(client, headers)
    clock.advance(ONE_DAY)
    scheduler.tick()
    due_before_connecting = next_due_at(engine, user_id)

    clock.advance(timedelta(hours=1))
    token = create_connection_token(client, headers)
    assert send_to_webhook(client, telegram_text_update(f"/start {token}")) == 200
    due_after_connecting = next_due_at(engine, user_id)
    chat_channel.sent.clear()
    chat_model.script(send_answer("hi Maya, glad you're here"))
    scheduler.tick()

    assert due_before_connecting is None
    assert due_after_connecting == clock.now()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hi Maya, glad you're here"]


def test_connecting_telegram_keeps_a_due_time_already_set(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
    engine: Engine,
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    answers = onboarding_answers(check_ins_enabled=True, check_in_frequency="most_days")
    client.put("/api/onboarding", json=answers, headers=headers)
    user_id = maya_id(client, headers)
    due_after_onboarding = next_due_at(engine, user_id)

    token = create_connection_token(client, headers)
    send_to_webhook(client, telegram_text_update(f"/start {token}"))

    assert due_after_onboarding == clock.now() + ONE_DAY
    assert next_due_at(engine, user_id) == due_after_onboarding


def test_users_with_check_ins_off_by_an_admin_are_not_loaded_and_stay_due(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    engine: Engine,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    switch_for_everyone(client, admin, "check_ins", on=False)
    clock.advance(ONE_DAY * 3)
    with reads_by_table(engine) as reads_while_off:
        scheduler.tick()
    due_while_off = next_due_at(engine, maya_id(client, headers))

    switch_for_everyone(client, admin, "check_ins", on=True)
    chat_model.script(send_answer("hey, it's been a while"))
    scheduler.tick()

    assert reads_while_off["feature_switches"] == 0
    assert due_while_off is not None
    assert due_while_off < clock.now()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey, it's been a while"]


def test_a_user_who_resumes_while_a_tick_holds_them_back_stays_due(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
    engine: Engine,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    user_id = maya_id(client, headers)
    client.put(
        "/api/check-ins/pause", json={"length": "until_resumed"}, headers=headers
    )
    clock.advance(ONE_DAY + timedelta(minutes=1))
    due_as_the_tick_read_it = next_due_at(engine, user_id)

    client.delete("/api/check-ins/pause", headers=headers)
    build_postgres_repositories(engine).check_ins.save_next_due_times(
        [
            NextDueTimeChange(
                user_id=user_id, read_as=due_as_the_tick_read_it, becomes=None
            )
        ]
    )

    assert next_due_at(engine, user_id) == clock.now()


def test_a_user_who_connects_telegram_while_a_tick_holds_them_back_stays_due(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    clock: FakeClock,
    engine: Engine,
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    answers = onboarding_answers(check_ins_enabled=True, check_in_frequency="most_days")
    client.put("/api/onboarding", json=answers, headers=headers)
    user_id = maya_id(client, headers)
    clock.advance(ONE_DAY + timedelta(minutes=1))
    due_as_the_tick_read_it = next_due_at(engine, user_id)

    token = create_connection_token(client, headers)
    send_to_webhook(client, telegram_text_update(f"/start {token}"))
    build_postgres_repositories(engine).check_ins.save_next_due_times(
        [
            NextDueTimeChange(
                user_id=user_id, read_as=due_as_the_tick_read_it, becomes=None
            )
        ]
    )

    assert next_due_at(engine, user_id) == clock.now()


def test_changing_quiet_hours_while_held_back_by_them_is_due_again_now(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    clock.advance(ONE_DAY + timedelta(hours=6))
    scheduler.tick()

    client.patch(
        "/api/check-ins",
        json={"quiet_hours_start": "23:30", "quiet_hours_end": "07:30"},
        headers=headers,
    )
    chat_model.script(send_answer("still up? how was today?"))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["still up? how was today?"]


def test_changing_time_zone_while_held_back_by_quiet_hours_is_due_again_now(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    clock.advance(ONE_DAY + timedelta(hours=6))
    scheduler.tick()

    client.patch("/api/me", json={"time_zone": "Europe/London"}, headers=headers)
    chat_model.script(send_answer("good afternoon from Zeph!"))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["good afternoon from Zeph!"]
