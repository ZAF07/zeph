from typing import Any

from fastapi.testclient import TestClient

from companion.core.typing_keeper import TYPING_WAIT_PREFIX
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeTimer,
    ScriptedChatModel,
    ToolCall,
)
from tests.telegram_helpers import (
    connect_telegram,
    owner_headers,
    post_to_webhook,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_safeguard import use_simple_crisis_reply
from tests.test_settings_via_chat import reply_call
from tests.test_usage_limits import LIMIT_REPLY, set_message_limit
from tests.test_web_search import change_settings


def typing_waits(timer: FakeTimer) -> list[float]:
    """List how long each typing wait was, oldest first."""
    return [
        seconds for key, seconds in timer.waits if key.startswith(TYPING_WAIT_PREFIX)
    ]


def assert_no_typing_after_the_last_message(
    chat_channel: FakeChatChannel, timer: FakeTimer
) -> None:
    """End any typing wait left and check typing doesn't show again."""
    events_before = list(chat_channel.events)
    timer.end_typing_waits()
    assert chat_channel.events == events_before
    assert chat_channel.events[-1] != "typing"


def test_a_slow_reply_shows_typing_again_at_each_interval_until_the_first_part(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_channel.events.clear()
    chat_model.script("oh hi\n\nhow was your day?")

    def two_intervals_pass() -> None:
        timer.end_typing_waits()
        timer.end_typing_waits()

    chat_model.before_next_reply = two_intervals_pass
    send_to_webhook(client, telegram_text_update("hey"))

    assert chat_channel.events == [
        "typing",
        "typing",
        "typing",
        "typing",
        "text: oh hi",
        "typing",
        "text: how was your day?",
    ]
    assert_no_typing_after_the_last_message(chat_channel, timer)


def test_typing_shows_again_while_a_text_is_slow_to_check_and_while_waiting(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_channel.events.clear()
    chat_model.before_next_safeguard = timer.end_typing_waits

    post_to_webhook(client, telegram_text_update("hey"))
    timer.end_typing_waits()

    assert chat_channel.events == ["typing", "typing", "typing"]


def test_the_interval_is_the_admins_typing_repeat_setting(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
    seeded_settings: dict[str, Any],
) -> None:
    assert seeded_settings["typing_repeat_seconds"] == 4
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    change_settings(client, admin, {"typing_repeat_seconds": 3})
    chat_model.script("hi")
    chat_model.before_next_reply = timer.end_typing_waits

    send_to_webhook(client, telegram_text_update("hey"))

    assert len(typing_waits(timer)) >= 2
    assert set(typing_waits(timer)) == {3}


def test_typing_stops_when_the_crisis_reply_is_sent(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
) -> None:
    admin = owner_headers(client, auth_verifier)
    use_simple_crisis_reply(client, admin)
    connect_telegram(client, auth_verifier, chat_channel)
    chat_channel.events.clear()
    chat_model.script_safeguard("suicide_or_self_harm")
    chat_model.before_next_safeguard = timer.end_typing_waits

    post_to_webhook(client, telegram_text_update("i don't want to be here anymore"))

    assert chat_channel.events[:2] == ["typing", "typing"]
    assert chat_channel.events[2].startswith("text: I'm an AI.")
    assert_no_typing_after_the_last_message(chat_channel, timer)


def test_typing_stops_when_the_limit_reply_is_sent(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    set_message_limit(client, admin, 1)
    chat_model.script("hey you")
    send_to_webhook(client, telegram_text_update("hi"))
    chat_channel.events.clear()

    post_to_webhook(client, telegram_text_update("one more thing"))
    timer.end_typing_waits()
    timer.end_message_waits()

    assert chat_channel.events == ["typing", "typing", f"text: {LIMIT_REPLY}"]
    assert_no_typing_after_the_last_message(chat_channel, timer)


def test_typing_stops_when_deleting_data_is_confirmed(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    word = seeded_settings["data_deletion_confirmation_word"]
    reply_call(
        client,
        chat_model,
        "please delete all my data",
        ToolCall("start_deleting_my_data", {}),
        f"Reply {word} to confirm.",
    )
    chat_channel.events.clear()

    post_to_webhook(client, telegram_text_update(word))
    timer.end_typing_waits()
    timer.end_message_waits()

    assert chat_channel.events == [
        "typing",
        "typing",
        f"text: {seeded_settings['data_deleted_reply']}",
    ]
    assert_no_typing_after_the_last_message(chat_channel, timer)


def test_typing_stops_when_the_reply_fails(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_channel.events.clear()
    chat_model.script(RuntimeError("model down"))
    chat_model.before_next_reply = timer.end_typing_waits

    send_to_webhook(client, telegram_text_update("hey"))

    assert chat_channel.events == [
        "typing",
        "typing",
        f"text: {seeded_settings['reply_failed_message']}",
    ]
    assert_no_typing_after_the_last_message(chat_channel, timer)
