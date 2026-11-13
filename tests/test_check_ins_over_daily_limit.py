from datetime import date, timedelta
from typing import Any
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import Engine

from companion.adapters.postgres.repositories import build_postgres_repositories
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import TELEGRAM_CHAT_ID, owner_headers
from tests.test_check_in_send_failures import (
    admin_log,
    ignore_check_ins_up_to_the_threshold,
)
from tests.test_check_in_sending import (
    ONE_DAY,
    recent_check_ins,
    send_answer,
    send_check_ins,
    set_up_user_with_check_ins,
)
from tests.test_post_conversation import have_conversation, processing_answer
from tests.test_usage_limits import set_message_limit, usage_rows

LIMIT_SKIP_REASON = "User had used up today's Daily Message Limit"


def message_before_the_check_in(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    message_limit: int,
) -> None:
    """Set the message limit, send one message, then wait until the Check-in is due.

    The message is sent two hours before the first Check-in is due, and its
    Conversation has ended by the time the Check-in is due.
    """
    set_message_limit(client, owner_headers(client, auth_verifier), message_limit)
    clock.advance(ONE_DAY - timedelta(hours=2))
    have_conversation(
        client, chat_model, clock, scheduler, seeded_settings, "hi", processing_answer()
    )
    clock.advance(timedelta(minutes=59))


def test_a_user_who_used_up_the_limit_gets_one_limit_skip_and_stays_due(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    message_before_the_check_in(
        client, auth_verifier, chat_model, clock, scheduler, seeded_settings, 1
    )
    chat_channel.sent.clear()
    model_calls = len(chat_model.calls)

    scheduler.tick()
    clock.advance(timedelta(hours=1))
    scheduler.tick()
    clock.advance(timedelta(hours=3, minutes=59))
    scheduler.tick()

    assert chat_channel.sent == []
    assert len(chat_model.calls) == model_calls
    [skipped] = recent_check_ins(client, headers)
    assert skipped == {
        "id": skipped["id"],
        "outcome": "skipped",
        "kind": None,
        "decided_at": skipped["decided_at"],
        "status": "skipped",
        "skipped_for_daily_limit": True,
    }
    [logged] = admin_log(client, auth_verifier)
    assert logged["skip_reason"] == LIMIT_SKIP_REASON

    chat_model.script(send_answer("morning! how did you sleep?"))
    clock.advance(timedelta(hours=10))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "morning! how did you sleep?"
    ]


def test_a_user_one_message_below_the_limit_gets_check_ins_as_normal(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    message_before_the_check_in(
        client, auth_verifier, chat_model, clock, scheduler, seeded_settings, 2
    )
    chat_channel.sent.clear()
    chat_model.script(send_answer("hey, how's the evening going?"))

    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey, how's the evening going?"
    ]
    assert recent_check_ins(client, headers)[0]["skipped_for_daily_limit"] is False
    [row] = usage_rows(client, owner_headers(client, auth_verifier))
    assert row["message_count"] == 1


def test_a_user_at_the_ignore_threshold_over_the_limit_is_asked_about_fewer_next_day(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    headers = ignore_check_ins_up_to_the_threshold(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    set_message_limit(client, owner_headers(client, auth_verifier), 1)
    user_id = UUID(admin_log(client, auth_verifier)[0]["user_id"])
    build_postgres_repositories(engine).usage.claim_message(
        user_id, date(2026, 11, 15), 1
    )

    clock.advance(ONE_DAY)
    scheduler.tick()

    assert chat_channel.sent == []
    assert recent_check_ins(client, headers)[0]["skipped_for_daily_limit"] is True

    clock.advance(ONE_DAY)
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        seeded_settings["check_in_fewer_message"]
    ]


def test_a_limit_skip_does_not_count_toward_the_ignore_threshold(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    threshold = seeded_settings["check_in_ignore_threshold"]
    send_check_ins(chat_model, clock, scheduler, threshold - 1)
    set_message_limit(client, owner_headers(client, auth_verifier), 1)
    user_id = UUID(admin_log(client, auth_verifier)[0]["user_id"])
    limit_day = date(2026, 11, 12) + timedelta(days=threshold - 1)
    build_postgres_repositories(engine).usage.claim_message(user_id, limit_day, 1)
    clock.advance(ONE_DAY)
    scheduler.tick()
    chat_channel.sent.clear()

    chat_model.script(send_answer("hey, hope today's gentler"))
    clock.advance(ONE_DAY)
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey, hope today's gentler"]
