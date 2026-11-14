import json
from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.core.models import ChatLine, ChatRole
from tests.conftest import DASHBOARD_URL
from tests.fakes import FakeAuthVerifier, FakeChatChannel, FakeClock, ScriptedChatModel
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    connect_telegram,
    send_to_webhook,
    telegram_text_update,
)

STRANGER_TELEGRAM_ID = 7770001


def set_platform_setting(engine: Engine, key: str, value: Any) -> None:
    """Change a platform setting the way an Admin would."""
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE platform_settings SET value = CAST(:value AS jsonb) "
                "WHERE key = :key"
            ),
            {"key": key, "value": json.dumps(value)},
        )


def test_connected_user_gets_a_reply_from_the_companion(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("hey, good to hear from you")

    assert send_to_webhook(client, telegram_text_update("hi zeph")) == 200

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey, good to hear from you"
    ]
    assert TELEGRAM_CHAT_ID in chat_channel.typing_shown_in
    [call] = chat_model.calls
    assert call.model == seeded_settings["response_model"]
    assert seeded_settings["persona"] in call.instructions
    assert seeded_settings["response_prompt"] in call.instructions
    assert call.history == [ChatLine(role=ChatRole.USER, text="hi zeph")]


def test_persona_is_read_from_platform_settings(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    set_platform_setting(engine, "persona", "You are Zeph, edited by an Admin.")
    set_platform_setting(engine, "response_model", "deepseek-reasoner")
    chat_model.script("ok")

    send_to_webhook(client, telegram_text_update("hello"))

    [call] = chat_model.calls
    assert "You are Zeph, edited by an Admin." in call.instructions
    assert call.model == "deepseek-reasoner"


def test_reply_with_blank_lines_is_sent_as_several_short_messages(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("oh no\n\nthat sounds like a long day\n\n  \n\nwhat happened?")

    send_to_webhook(client, telegram_text_update("ugh today was rough"))

    assert chat_channel.events == [
        "typing",
        "typing",
        "text: oh no",
        "typing",
        "text: that sounds like a long day",
        "typing",
        "text: what happened?",
    ]


def test_typing_pause_before_each_message_follows_platform_settings(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    set_platform_setting(engine, "typing_seconds_per_character", 0.1)
    set_platform_setting(engine, "min_typing_seconds", 2)
    set_platform_setting(engine, "max_typing_seconds", 5)
    chat_model.script("ok\n\n" + "x" * 30 + "\n\n" + "y" * 200)

    send_to_webhook(client, telegram_text_update("hi"))

    assert clock.slept == [2, 3, 5]


def test_earlier_messages_in_the_conversation_are_given_to_the_model(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("hey!\n\nhow's it going?", "nice, which one?")

    send_to_webhook(client, telegram_text_update("hi"))
    clock.advance(timedelta(minutes=10))
    send_to_webhook(client, telegram_text_update("I started a new book"))

    assert chat_model.calls[1].history == [
        ChatLine(role=ChatRole.USER, text="hi"),
        ChatLine(role=ChatRole.COMPANION, text="hey!"),
        ChatLine(role=ChatRole.COMPANION, text="how's it going?"),
        ChatLine(role=ChatRole.USER, text="I started a new book"),
    ]


def test_message_after_the_quiet_gap_starts_a_new_conversation(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    quiet_gap = timedelta(minutes=seeded_settings["conversation_quiet_gap_minutes"])
    chat_model.script("hey!", "morning!")

    send_to_webhook(client, telegram_text_update("night zeph"))
    clock.advance(quiet_gap + timedelta(minutes=1))
    send_to_webhook(client, telegram_text_update("good morning"))

    assert chat_model.calls[1].history == [
        ChatLine(role=ChatRole.USER, text="good morning")
    ]
    with engine.connect() as connection:
        message_counts = connection.execute(
            text(
                "SELECT count(*) FROM conversation_messages "
                "GROUP BY conversation_id ORDER BY min(sent_at)"
            )
        ).scalars()
        assert list(message_counts) == [2, 2]


def test_message_just_inside_the_quiet_gap_stays_in_the_same_conversation(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    quiet_gap = timedelta(minutes=seeded_settings["conversation_quiet_gap_minutes"])
    chat_model.script("hey!", "still here")

    send_to_webhook(client, telegram_text_update("hi"))
    clock.advance(quiet_gap - timedelta(minutes=1))
    send_to_webhook(client, telegram_text_update("you there?"))

    assert len(chat_model.calls[1].history) == 3


def test_telegram_user_without_a_connection_is_pointed_to_sign_up(
    client: TestClient,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    update = telegram_text_update("hello?", telegram_user_id=STRANGER_TELEGRAM_ID)

    assert send_to_webhook(client, update) == 200

    expected_reply = seeded_settings["unknown_telegram_user_reply"].replace(
        "{dashboard_url}", DASHBOARD_URL
    )
    assert chat_channel.texts_sent_to(STRANGER_TELEGRAM_ID) == [expected_reply]
    assert DASHBOARD_URL in expected_reply
    assert chat_model.calls == []


def test_user_gets_a_fallback_reply_when_the_model_fails(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script(TimeoutError("DeepSeek timed out"))

    assert send_to_webhook(client, telegram_text_update("hi")) == 200

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        seeded_settings["reply_failed_message"]
    ]


def test_user_gets_a_fallback_reply_when_the_model_returns_nothing(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("  \n\n ")

    send_to_webhook(client, telegram_text_update("hi"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        seeded_settings["reply_failed_message"]
    ]
