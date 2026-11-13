import logging
from datetime import datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from companion.adapters.postgres.repositories import PostgresCheckInRepository
from companion.core.models import CheckIn
from companion.core.ports import ChatBlockedError, MessageRefusedError
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import TELEGRAM_CHAT_ID, owner_headers
from tests.test_check_in_sending import (
    ONE_DAY,
    recent_check_ins,
    send_answer,
    send_check_ins,
    set_up_user_with_check_ins,
)

RETRY_GAP = timedelta(minutes=15)
BLOCKED_REASON = "User has blocked the Companion on Telegram"


def fail_the_next_save(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the next Check-in save fail as if the database dropped."""
    save = PostgresCheckInRepository.add
    failed = False

    def fail_once(
        repository: PostgresCheckInRepository,
        check_in: CheckIn,
        next_due_at: datetime,
        pause_until_resumed: bool,
    ) -> None:
        nonlocal failed
        if not failed:
            failed = True
            raise ConnectionError("the database dropped")
        save(repository, check_in, next_due_at, pause_until_resumed)

    monkeypatch.setattr(PostgresCheckInRepository, "add", fail_once)


def admin_log(client: TestClient, auth_verifier: FakeAuthVerifier) -> list[Any]:
    """List the Admins' Check-in log for the last week."""
    admin = owner_headers(client, auth_verifier)
    response = client.get("/api/admin/check-ins", params={"days": 7}, headers=admin)
    entries: list[Any] = response.json()["entries"]
    return entries


def ignore_check_ins_up_to_the_threshold(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> dict[str, str]:
    """Send and ignore enough Check-ins that the next is "would you like fewer?"."""
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    threshold = seeded_settings["check_in_ignore_threshold"]
    send_check_ins(chat_model, clock, scheduler, threshold)
    chat_channel.sent.clear()
    return headers


def test_a_failed_save_sends_nothing_and_the_next_tick_tries_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    fail_the_next_save(monkeypatch)
    chat_model.script(send_answer("hey, how's it going?"), send_answer("hi there!"))

    clock.advance(ONE_DAY)
    scheduler.tick()
    assert chat_channel.sent == []
    assert recent_check_ins(client, headers) == []

    clock.advance(timedelta(minutes=1))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hi there!"]
    assert [check_in["outcome"] for check_in in recent_check_ins(client, headers)] == [
        "sent"
    ]


def test_a_refused_check_in_is_taken_back_and_tried_again_15_minutes_later(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_channel.text_send_failures = [MessageRefusedError("Too Many Requests")]
    chat_model.script(send_answer("hey, how's it going?"), send_answer("hi there!"))

    clock.advance(ONE_DAY)
    scheduler.tick()
    assert chat_channel.sent == []
    assert recent_check_ins(client, headers) == []

    clock.advance(RETRY_GAP - timedelta(minutes=1))
    scheduler.tick()
    assert len(chat_model.calls) == 1

    clock.advance(timedelta(minutes=1))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hi there!"]
    [sent] = recent_check_ins(client, headers)
    assert sent["outcome"] == "sent"
    assert sent["decided_at"] == "2026-11-12T09:15:00Z"


def test_a_send_with_an_unknown_result_counts_as_sent_and_is_not_sent_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_channel.text_send_failures = [TimeoutError("Telegram took too long")]
    chat_model.script(send_answer("hey, how's it going?"), send_answer("hi again!"))

    clock.advance(ONE_DAY)
    scheduler.tick()
    [sent] = recent_check_ins(client, headers)
    assert sent["outcome"] == "sent"

    clock.advance(ONE_DAY - timedelta(minutes=1))
    scheduler.tick()
    assert len(chat_model.calls) == 1

    clock.advance(timedelta(minutes=1))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hi again!"]


def test_a_user_who_blocked_the_companion_gets_a_skipped_check_in_and_a_full_gap(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_channel.text_send_failures = [ChatBlockedError("bot was blocked by the user")]
    chat_model.script(send_answer("hey, how's it going?"), send_answer("hi again!"))

    clock.advance(ONE_DAY)
    scheduler.tick()

    [skipped] = recent_check_ins(client, headers)
    assert skipped["outcome"] == "skipped"
    assert skipped["kind"] is None
    [entry] = admin_log(client, auth_verifier)
    assert entry["skip_reason"] == BLOCKED_REASON
    clock.advance(ONE_DAY - timedelta(minutes=1))
    scheduler.tick()
    assert len(chat_model.calls) == 1

    clock.advance(timedelta(minutes=1))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hi again!"]


def test_a_failed_save_of_would_you_like_fewer_sends_nothing_and_tries_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
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
    fail_the_next_save(monkeypatch)

    clock.advance(ONE_DAY)
    scheduler.tick()
    assert chat_channel.sent == []

    clock.advance(timedelta(minutes=1))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        seeded_settings["check_in_fewer_message"]
    ]
    assert client.get("/api/check-ins", headers=headers).json()["paused"] is True


def test_a_refused_would_you_like_fewer_is_taken_back_and_tried_again_later(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
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
    chat_channel.text_send_failures = [MessageRefusedError("Too Many Requests")]
    newest_before = recent_check_ins(client, headers)[0]["id"]

    clock.advance(ONE_DAY)
    scheduler.tick()
    check_ins = client.get("/api/check-ins", headers=headers).json()
    assert check_ins["paused"] is False
    assert check_ins["recent"][0]["id"] == newest_before

    clock.advance(RETRY_GAP - timedelta(minutes=1))
    scheduler.tick()
    assert chat_channel.sent == []

    clock.advance(timedelta(minutes=1))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        seeded_settings["check_in_fewer_message"]
    ]
    assert client.get("/api/check-ins", headers=headers).json()["paused"] is True


def test_would_you_like_fewer_to_a_user_who_blocked_the_companion_is_skipped(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
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
    chat_channel.text_send_failures = [ChatBlockedError("bot was blocked by the user")]

    clock.advance(ONE_DAY)
    scheduler.tick()

    check_ins = client.get("/api/check-ins", headers=headers).json()
    assert check_ins["paused"] is False
    assert check_ins["recent"][0]["outcome"] == "skipped"
    assert admin_log(client, auth_verifier)[0]["skip_reason"] == BLOCKED_REASON
    clock.advance(ONE_DAY - timedelta(minutes=1))
    scheduler.tick()
    assert chat_channel.sent == []

    clock.advance(timedelta(minutes=1))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        seeded_settings["check_in_fewer_message"]
    ]


def test_a_pause_set_while_the_model_decides_survives_a_refused_send(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_model.before_next_reply = lambda: client.put(
        "/api/check-ins/pause", json={"length": "until_resumed"}, headers=headers
    )
    chat_channel.text_send_failures = [MessageRefusedError("Too Many Requests")]
    chat_model.script(send_answer("hey, how's it going?"))

    clock.advance(ONE_DAY)
    scheduler.tick()

    check_ins = client.get("/api/check-ins", headers=headers).json()
    assert check_ins["paused"] is True
    assert check_ins["recent"] == []


def test_a_refused_check_in_whose_undo_fails_is_missed_not_sent_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)

    def fail_undo(*args: object, **kwargs: object) -> None:
        raise ConnectionError("the database dropped")

    monkeypatch.setattr(PostgresCheckInRepository, "undo_add", fail_undo)
    chat_channel.text_send_failures = [MessageRefusedError("Too Many Requests")]
    chat_model.script(send_answer("hey, how's it going?"), send_answer("hi again!"))

    with caplog.at_level(logging.ERROR):
        clock.advance(ONE_DAY)
        scheduler.tick()
    assert "Could not decide on a Check-in" in caplog.text

    clock.advance(ONE_DAY - timedelta(minutes=1))
    scheduler.tick()
    assert chat_channel.sent == []
    assert len(chat_model.calls) == 1
    assert [check_in["outcome"] for check_in in recent_check_ins(client, headers)] == [
        "sent"
    ]
