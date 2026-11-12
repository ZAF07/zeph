from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient

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
    connect_telegram,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_onboarding import onboarding_answers

ONE_DAY = timedelta(days=1)


def set_up_user_with_check_ins(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    **overrides: Any,
) -> dict[str, str]:
    """Connect Telegram and onboard with Check-ins on "most days" in Singapore.

    The clock starts at 09:00 UTC (17:00 in Singapore), so the first Check-in
    is due a day later at the same time, outside the seeded quiet hours.
    """
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    answers = onboarding_answers(
        check_ins_enabled=True, check_in_frequency="most_days", **overrides
    )
    assert (
        client.put("/api/onboarding", json=answers, headers=headers).status_code == 200
    )
    return headers


def recent_check_ins(
    client: TestClient, headers: dict[str, str]
) -> list[dict[str, Any]]:
    """List the User's recent Check-ins through the Dashboard API."""
    recent: list[dict[str, Any]] = client.get("/api/check-ins", headers=headers).json()[
        "recent"
    ]
    return recent


def test_a_due_user_gets_a_casual_hello_written_by_the_check_in_model(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)

    chat_model.script("hey Maya, how's your thursday going?")
    clock.advance(ONE_DAY - timedelta(minutes=1))
    scheduler.tick()
    assert chat_channel.sent == []

    clock.advance(timedelta(minutes=1))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey Maya, how's your thursday going?"
    ]
    [call] = chat_model.calls
    assert call.model == seeded_settings["check_in_model"]
    assert seeded_settings["check_in_prompt"] in call.instructions
    assert seeded_settings["persona"] in call.instructions
    [line] = call.history
    assert "A casual hello" in line.text
    assert "Maya" in line.text
    assert "Thursday, 17:00" in line.text
    assert recent_check_ins(client, headers) == [
        {
            "id": recent_check_ins(client, headers)[0]["id"],
            "kind": "A casual hello",
            "sent_at": "2026-11-12T09:00:00Z",
            "status": "sent",
        }
    ]


def test_the_next_check_in_waits_for_the_frequency_gap(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    clock.advance(ONE_DAY)
    chat_model.script("hey, how's it going?", "hi again 👋")
    scheduler.tick()

    clock.advance(ONE_DAY - timedelta(minutes=5))
    scheduler.tick()
    assert len(chat_channel.sent) == 1

    clock.advance(timedelta(minutes=5))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey, how's it going?",
        "hi again 👋",
    ]
    assert [check_in["status"] for check_in in recent_check_ins(client, headers)] == [
        "sent",
        "no_reply",
    ]


def test_no_check_in_is_sent_during_quiet_hours_in_the_users_time_zone(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_check_ins(
        client,
        auth_verifier,
        chat_channel,
        quiet_hours_start="16:00",
        quiet_hours_end="19:00",
    )
    chat_model.script("evening! how was today?")

    clock.advance(ONE_DAY)
    scheduler.tick()
    clock.advance(timedelta(hours=1, minutes=59))
    scheduler.tick()
    assert chat_channel.sent == []

    clock.advance(timedelta(minutes=1))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["evening! how was today?"]


def test_quiet_hours_follow_the_users_own_time_zone(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_check_ins(
        client,
        auth_verifier,
        chat_channel,
        country="US",
        time_zone="America/New_York",
        quiet_hours_start="08:00",
        quiet_hours_end="10:00",
    )

    clock.advance(ONE_DAY)
    chat_model.script("up early? hope you're doing ok")
    scheduler.tick()

    assert clock.now() == datetime(2026, 11, 12, 9, 0, tzinfo=UTC)
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "up early? hope you're doing ok"
    ]
    assert "Thursday, 04:00" in chat_model.calls[0].history[0].text


def test_quiet_hours_can_run_past_midnight(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_check_ins(
        client,
        auth_verifier,
        chat_channel,
        quiet_hours_start="15:00",
        quiet_hours_end="07:30",
    )
    chat_model.script("good morning ☀️")

    clock.advance(ONE_DAY)
    scheduler.tick()
    clock.advance(timedelta(hours=14, minutes=29))
    scheduler.tick()
    assert chat_channel.sent == []

    clock.advance(timedelta(minutes=1))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["good morning ☀️"]


def test_no_check_in_is_sent_with_check_ins_off(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    client.patch("/api/check-ins", json={"enabled": False}, headers=headers)
    chat_model.script("hey, how are you?")

    clock.advance(timedelta(weeks=2))
    scheduler.tick()

    assert chat_channel.sent == []


def test_no_check_in_is_sent_while_paused_and_one_is_sent_once_the_pause_ends(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    client.put("/api/check-ins/pause", json={"length": "week"}, headers=headers)
    chat_model.script("hey, been a little while. how are you?")

    for _ in range(6):
        clock.advance(ONE_DAY)
        scheduler.tick()
    clock.advance(ONE_DAY - timedelta(minutes=1))
    scheduler.tick()
    assert chat_channel.sent == []

    clock.advance(timedelta(minutes=1))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey, been a little while. how are you?"
    ]
    assert client.get("/api/check-ins", headers=headers).json()["frequency"] == (
        "most_days"
    )


def test_no_check_in_is_sent_while_paused_until_resumed(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    client.put(
        "/api/check-ins/pause", json={"length": "until_resumed"}, headers=headers
    )
    chat_model.script("hi! nice to hear from you again")

    clock.advance(timedelta(weeks=4))
    scheduler.tick()
    assert chat_channel.sent == []

    client.delete("/api/check-ins/pause", headers=headers)
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hi! nice to hear from you again"
    ]


def test_no_check_in_is_sent_in_the_middle_of_a_conversation(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    clock.advance(ONE_DAY - timedelta(minutes=10))
    chat_model.script("oh nice!")
    send_to_webhook(client, telegram_text_update("just got back from a run"))
    chat_channel.sent.clear()
    chat_model.script("hey, how's the rest of your day?")

    clock.advance(timedelta(minutes=10))
    scheduler.tick()

    assert chat_channel.sent == []
    quiet_gap = timedelta(minutes=seeded_settings["conversation_quiet_gap_minutes"])
    clock.advance(quiet_gap)
    chat_model.script_processing(
        '{"summary": "Went for a run.", "mood": "good", "memory_operations": []}'
    )
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey, how's the rest of your day?"
    ]


def test_a_failing_check_in_model_sends_nothing_and_tries_again_next_tick(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    clock.advance(ONE_DAY)
    chat_model.script(RuntimeError("model down"), "hey there 🙂")

    scheduler.tick()
    assert chat_channel.sent == []
    assert recent_check_ins(client, headers) == []

    clock.advance(timedelta(minutes=5))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey there 🙂"]


def test_a_reply_to_a_check_in_starts_a_conversation_handled_like_any_other(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    clock.advance(ONE_DAY)
    chat_model.script("hey Maya, how did the presentation go?")
    scheduler.tick()
    chat_channel.sent.clear()

    clock.advance(timedelta(hours=3))
    chat_model.script("that's brilliant, well done!")
    send_to_webhook(client, telegram_text_update("it went really well actually!"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "that's brilliant, well done!"
    ]
    reply_call = chat_model.calls[-1]
    assert [line.text for line in reply_call.history] == [
        "hey Maya, how did the presentation go?",
        "it went really well actually!",
    ]
    assert [line.role for line in reply_call.history] == ["companion", "user"]
    assert len(chat_model.safeguard_calls) == 1
    assert recent_check_ins(client, headers)[0]["status"] == "replied"


def test_only_the_first_message_after_a_check_in_counts_as_its_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    clock.advance(ONE_DAY)
    chat_model.script("hey, how are you?")
    scheduler.tick()
    chat_model.script("glad to hear it")
    send_to_webhook(client, telegram_text_update("good thanks"))

    quiet_gap = timedelta(minutes=seeded_settings["conversation_quiet_gap_minutes"])
    clock.advance(quiet_gap + timedelta(minutes=1))
    chat_model.script_processing(
        '{"summary": "Said hi.", "mood": "fine", "memory_operations": []}'
    )
    scheduler.tick()
    chat_model.script("oh what about?")
    send_to_webhook(client, telegram_text_update("random thought"))

    assert [line.text for line in chat_model.calls[-1].history] == ["random thought"]
