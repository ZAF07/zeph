from datetime import datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.core.ports import MessageRefusedError
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
from tests.test_check_in_sending import (
    ONE_DAY,
    recent_check_ins,
    send_answer,
    set_up_user_with_check_ins,
    skip_answer,
)
from tests.test_post_conversation import processing_answer, quiet_gap


def change_check_ins(
    client: TestClient, headers: dict[str, str], changes: dict[str, Any]
) -> None:
    """Change the User's Check-in settings on the Dashboard."""
    response = client.patch("/api/check-ins", json=changes, headers=headers)
    assert response.status_code == 200


def pause_check_ins(client: TestClient, headers: dict[str, str], length: str) -> None:
    """Pause the User's Check-ins on the Dashboard."""
    response = client.put(
        "/api/check-ins/pause", json={"length": length}, headers=headers
    )
    assert response.status_code == 200


def chat_until_the_check_in_is_due(
    client: TestClient,
    chat_model: ScriptedChatModel,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    """Send a message five minutes before the first Due Time, then tick at it.

    The Check-in is held back by the open Conversation.
    """
    clock.advance(ONE_DAY - timedelta(minutes=5))
    chat_model.script("oh nice!")
    send_to_webhook(client, telegram_text_update("just got back from a run"))
    chat_channel.sent.clear()
    clock.advance(timedelta(minutes=5))
    scheduler.tick()
    assert chat_channel.sent == []


def test_a_check_in_held_back_by_quiet_hours_keeps_the_next_one_at_the_rhythm(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    change_check_ins(
        client, headers, {"quiet_hours_start": "16:00", "quiet_hours_end": "18:00"}
    )
    chat_model.script(send_answer("evening!"), send_answer("hey again"))

    clock.advance(ONE_DAY)
    scheduler.tick()
    assert chat_channel.sent == []
    clock.advance(timedelta(hours=1))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["evening!"]
    change_check_ins(
        client, headers, {"quiet_hours_start": "22:00", "quiet_hours_end": "07:30"}
    )

    clock.advance(ONE_DAY - timedelta(hours=1, minutes=1))
    scheduler.tick()
    assert len(chat_channel.sent) == 1
    clock.advance(timedelta(minutes=1))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["evening!", "hey again"]


def test_a_check_in_held_back_by_a_conversation_keeps_the_next_one_at_the_rhythm(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_until_the_check_in_is_due(client, chat_model, chat_channel, clock, scheduler)
    chat_model.script(send_answer("how was the rest of the run?"))
    chat_model.script_processing(processing_answer())
    held_back_for = quiet_gap(seeded_settings)
    clock.advance(held_back_for)
    scheduler.tick()
    assert len(chat_channel.sent) == 1

    chat_model.script(send_answer("hey, how's today?"))
    clock.advance(ONE_DAY - held_back_for - timedelta(minutes=1))
    scheduler.tick()
    assert len(chat_channel.sent) == 1
    clock.advance(timedelta(minutes=1))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "how was the rest of the run?",
        "hey, how's today?",
    ]


def test_a_skipped_check_in_does_not_shift_the_rhythm(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_until_the_check_in_is_due(client, chat_model, chat_channel, clock, scheduler)
    chat_model.script(skip_answer("They just talked; give them some space."))
    chat_model.script_processing(processing_answer())
    held_back_for = quiet_gap(seeded_settings)
    clock.advance(held_back_for)
    scheduler.tick()
    assert recent_check_ins(client, headers)[0]["outcome"] == "skipped"

    chat_model.script(send_answer("hey, how's today?"))
    clock.advance(ONE_DAY - held_back_for)
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey, how's today?"]


def test_after_a_long_pause_one_check_in_comes_then_the_normal_rhythm(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    pause_check_ins(client, headers, "week")
    chat_model.script(send_answer("welcome back!"), send_answer("hey, how's today?"))

    for _ in range(8 * 24):
        clock.advance(timedelta(hours=1))
        scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "welcome back!",
        "hey, how's today?",
    ]
    decided = [check_in["decided_at"] for check_in in recent_check_ins(client, headers)]
    assert decided == [
        "2026-11-19T09:00:00Z",
        "2026-11-18T09:00:00Z",
    ]


def test_a_check_in_never_comes_within_half_a_gap_of_the_last_sent_one(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    clock.advance(timedelta(hours=15))
    pause_check_ins(client, headers, "day")
    clock.advance(timedelta(hours=9))
    scheduler.tick()
    chat_model.script(send_answer("morning!"), send_answer("evening!"))
    clock.advance(timedelta(hours=15))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["morning!"]

    clock.advance(timedelta(hours=9))
    scheduler.tick()
    clock.advance(timedelta(hours=2, minutes=59))
    scheduler.tick()
    assert len(chat_channel.sent) == 1
    clock.advance(timedelta(minutes=1))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["morning!", "evening!"]


def test_a_refused_check_in_tried_again_later_keeps_the_rhythm(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_channel.text_send_failures = [MessageRefusedError("Too Many Requests")]
    chat_model.script(
        send_answer("hey!"), send_answer("hey, how's it going?"), send_answer("hi")
    )
    clock.advance(ONE_DAY)
    scheduler.tick()
    clock.advance(timedelta(minutes=15))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey, how's it going?"]

    clock.advance(ONE_DAY - timedelta(minutes=15))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey, how's it going?",
        "hi",
    ]


def test_changing_the_frequency_while_held_back_starts_a_new_rhythm(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    engine: Engine,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    change_check_ins(
        client, headers, {"quiet_hours_start": "16:00", "quiet_hours_end": "18:00"}
    )
    clock.advance(ONE_DAY)
    scheduler.tick()
    assert held_back_due_at(engine) is not None

    clock.advance(timedelta(minutes=30))
    change_check_ins(client, headers, {"frequency": "weekly"})

    assert held_back_due_at(engine) is None


def held_back_due_at(engine: Engine) -> datetime | None:
    """Read the only User's held-back Due Time straight from the database."""
    with engine.connect() as connection:
        due: datetime | None = connection.execute(
            text("SELECT check_in_held_back_due_at FROM users")
        ).scalar_one()
    return due
