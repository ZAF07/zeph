from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient

from companion.core.models import WebSearchResult
from tests.fakes import (
    TOKENS_IN_PER_CALL,
    TOKENS_OUT_PER_CALL,
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    FakeWebSearch,
    ScriptedChatModel,
    ToolCall,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_check_in_sending import (
    ONE_DAY,
    send_answer,
    set_up_user_with_check_ins,
)
from tests.test_safeguard import use_simple_crisis_reply
from tests.test_web_search import change_settings

LIMIT_REPLY = "I'm wiped for today, talk tomorrow?"


def send_text(client: TestClient, text: str) -> None:
    """Send the connected User's Telegram message to the webhook."""
    assert send_to_webhook(client, telegram_text_update(text)) == 200


def usage_rows(
    client: TestClient, admin: dict[str, str], days: int = 7
) -> list[dict[str, Any]]:
    """Fetch the usage rows through the admin API."""
    response = client.get(f"/api/admin/usage?days={days}", headers=admin)
    assert response.status_code == 200, response.text
    rows: list[dict[str, Any]] = response.json()["rows"]
    return rows


def set_message_limit(client: TestClient, admin: dict[str, str], limit: int) -> None:
    """Set the daily message limit and the limit-reached wording."""
    change_settings(
        client,
        admin,
        {"daily_message_limit": limit, "daily_limit_reply": LIMIT_REPLY},
    )


def test_under_the_daily_limit_the_companion_replies(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    set_message_limit(client, admin, 2)
    chat_model.script("hey you", "still here")

    send_text(client, "hi")
    send_text(client, "how are you?")

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey you", "still here"]


def test_over_the_daily_limit_the_user_gets_the_limit_reply_and_nothing_is_composed(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    set_message_limit(client, admin, 1)
    chat_model.script("hey you")
    send_text(client, "hi")
    chat_model.calls.clear()

    send_text(client, "one more thing")

    assert chat_model.calls == []
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey you", LIMIT_REPLY]


def test_the_seeded_limit_reply_is_in_character_and_the_limit_is_generous(
    seeded_settings: dict[str, Any],
) -> None:
    assert seeded_settings["daily_message_limit"] == 200
    assert "tomorrow" in seeded_settings["daily_limit_reply"]


def test_the_safeguard_runs_first_so_a_crisis_over_the_limit_gets_the_crisis_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    use_simple_crisis_reply(client, admin)
    connect_telegram(client, auth_verifier, chat_channel)
    set_message_limit(client, admin, 1)
    chat_model.script("hey you")
    send_text(client, "hi")
    chat_model.safeguard_calls.clear()
    chat_model.script_safeguard("suicide_or_self_harm")

    send_text(client, "I don't want to be here anymore")

    assert len(chat_model.safeguard_calls) == 1
    hey, crisis_reply = chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)
    assert crisis_reply.startswith("I'm an AI. Please reach out:")
    assert LIMIT_REPLY not in chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)


def test_a_crisis_does_not_count_toward_the_daily_limit(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    use_simple_crisis_reply(client, admin)
    connect_telegram(client, auth_verifier, chat_channel)
    set_message_limit(client, admin, 1)
    chat_model.script_safeguard("abuse")
    send_text(client, "he hit me again")
    chat_model.script("I'm here")

    send_text(client, "thanks for that")

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)[-1] == "I'm here"
    [row] = usage_rows(client, admin)
    assert row["message_count"] == 1


def test_the_limit_starts_again_on_the_users_next_day(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    set_message_limit(client, admin, 1)
    chat_model.script("hey you", "morning!")
    send_text(client, "hi")
    send_text(client, "still there?")

    clock.advance(timedelta(days=1))
    send_text(client, "good morning")

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey you",
        LIMIT_REPLY,
        "morning!",
    ]


def test_messages_tokens_and_web_searches_are_recorded_per_user_per_day(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    web_search: FakeWebSearch,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    web_search.results = [
        WebSearchResult(title="Seneca", url="https://example.com", content="Anger.")
    ]
    chat_model.script(
        ToolCall("web_search", {"query": "Seneca on anger"}), "Seneca said a lot"
    )
    send_text(client, "what did Seneca say about anger?")
    chat_model.script("sure")
    send_text(client, "nice")
    model_calls = len(chat_model.call_order)

    [row] = usage_rows(client, admin)

    assert row["day"] == "2026-11-11"
    assert row["user_email"] == "user_maya@example.com"
    assert row["message_count"] == 2
    assert row["web_search_count"] == 1
    assert row["tokens_in"] == model_calls * TOKENS_IN_PER_CALL
    assert row["tokens_out"] == model_calls * TOKENS_OUT_PER_CALL


def test_check_in_tokens_count_toward_the_users_usage(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_model.script(send_answer("hey, how are you?"))
    clock.advance(ONE_DAY)
    scheduler.tick()
    admin = owner_headers(client, auth_verifier)

    [row] = usage_rows(client, admin)

    assert row["message_count"] == 0
    assert row["tokens_in"] == TOKENS_IN_PER_CALL
    assert row["tokens_out"] == TOKENS_OUT_PER_CALL


def test_usage_lists_only_the_chosen_period_newest_day_first_with_the_limits(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    set_message_limit(client, admin, 50)
    chat_model.script("hey", "hey again", "and again")
    send_text(client, "hi")
    clock.advance(timedelta(days=3))
    send_text(client, "hi")
    clock.advance(timedelta(days=1))
    send_text(client, "hi")

    response = client.get("/api/admin/usage?days=3", headers=admin)

    assert response.status_code == 200, response.text
    body = response.json()
    assert [row["day"] for row in body["rows"]] == ["2026-11-15", "2026-11-14"]
    assert body["daily_message_limit"] == 50
    assert body["web_search_daily_limit"] == 10
    assert [row["day"] for row in usage_rows(client, admin, days=1)] == ["2026-11-15"]


def test_only_admins_can_see_usage(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")

    response = client.get("/api/admin/usage", headers=headers)

    assert response.status_code == 403


def test_admins_can_set_the_daily_message_limit_within_its_range(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    too_high = client.patch(
        "/api/admin/settings",
        json={"values": {"daily_message_limit": 100_001}},
        headers=admin,
    )
    blank_reply = client.patch(
        "/api/admin/settings",
        json={"values": {"daily_limit_reply": "  "}},
        headers=admin,
    )
    set_message_limit(client, admin, 60)

    assert too_high.status_code == 422
    assert blank_reply.status_code == 422
    settings = client.get("/api/admin/settings", headers=admin).json()["settings"]
    assert settings["daily_message_limit"]["value"] == 60
    assert settings["daily_limit_reply"]["value"] == LIMIT_REPLY
