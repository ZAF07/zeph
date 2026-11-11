from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import BOT_USERNAME, DASHBOARD_URL
from tests.fakes import FakeAuthVerifier, FakeChatChannel, FakeClock
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    auth_headers,
    create_connection_token,
    send_to_webhook,
    telegram_text_update,
)


def test_start_with_valid_token_connects_telegram_and_sends_welcome(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    seeded_settings: dict[str, Any],
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")

    created = client.post("/api/telegram-connection/tokens", headers=headers)
    assert created.status_code == 201
    token = created.json()["token"]
    assert (
        created.json()["deep_link_url"] == f"https://t.me/{BOT_USERNAME}?start={token}"
    )
    assert created.json()["status"] == "active"

    assert send_to_webhook(client, telegram_text_update(f"/start {token}")) == 200

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        seeded_settings["welcome_message"]
    ]
    status = client.get("/api/telegram-connection", headers=headers).json()
    assert status["connection"]["telegram_username"] == "maya_l"
    assert status["latest_token"]["status"] == "used"


def test_expired_token_gets_reply_pointing_back_to_dashboard(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
    seeded_settings: dict[str, Any],
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    token = create_connection_token(client, headers)

    clock.advance(timedelta(minutes=15))
    send_to_webhook(client, telegram_text_update(f"/start {token}"))

    expected_reply = seeded_settings["connection_token_invalid_reply"].replace(
        "{dashboard_url}", DASHBOARD_URL
    )
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [expected_reply]
    status = client.get("/api/telegram-connection", headers=headers).json()
    assert status["connection"] is None
    assert status["latest_token"]["status"] == "expired"


def test_already_used_token_gets_reply_pointing_back_to_dashboard(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    seeded_settings: dict[str, Any],
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    token = create_connection_token(client, headers)
    send_to_webhook(client, telegram_text_update(f"/start {token}"))

    other_telegram_user = 5552002
    send_to_webhook(
        client, telegram_text_update(f"/start {token}", other_telegram_user, "sam")
    )

    expected_reply = seeded_settings["connection_token_invalid_reply"].replace(
        "{dashboard_url}", DASHBOARD_URL
    )
    assert chat_channel.texts_sent_to(other_telegram_user) == [expected_reply]
    status = client.get("/api/telegram-connection", headers=headers).json()
    assert status["connection"]["telegram_username"] == "maya_l"


def test_telegram_account_connected_to_one_user_cannot_connect_to_another(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    seeded_settings: dict[str, Any],
) -> None:
    maya_headers = auth_headers(auth_verifier, "user_maya")
    send_to_webhook(
        client,
        telegram_text_update(f"/start {create_connection_token(client, maya_headers)}"),
    )

    sam_headers = auth_headers(auth_verifier, "user_sam")
    sam_token = create_connection_token(client, sam_headers)
    send_to_webhook(client, telegram_text_update(f"/start {sam_token}"))

    expected_reply = seeded_settings["telegram_connected_elsewhere_reply"].replace(
        "{dashboard_url}", DASHBOARD_URL
    )
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)[-1] == expected_reply
    sam_status = client.get("/api/telegram-connection", headers=sam_headers).json()
    assert sam_status["connection"] is None
    assert sam_status["latest_token"]["status"] == "connected_elsewhere"
    maya_status = client.get("/api/telegram-connection", headers=maya_headers).json()
    assert maya_status["connection"]["telegram_username"] == "maya_l"


def test_webhook_rejects_requests_without_the_right_secret(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    token = create_connection_token(client, auth_headers(auth_verifier, "user_maya"))
    update = telegram_text_update(f"/start {token}")

    missing = client.post("/telegram/webhook", json=update)
    wrong = client.post(
        "/telegram/webhook",
        json=update,
        headers={"X-Telegram-Bot-Api-Secret-Token": "not-the-secret"},
    )

    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert chat_channel.sent == []


def test_dashboard_api_rejects_requests_without_a_valid_token(
    client: TestClient,
) -> None:
    missing = client.get("/api/telegram-connection")
    wrong = client.get(
        "/api/telegram-connection", headers={"Authorization": "Bearer nope"}
    )

    assert missing.status_code == 401
    assert wrong.status_code == 401


def test_first_dashboard_request_creates_the_user(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")

    first = client.get("/api/me", headers=headers).json()
    second = client.get("/api/me", headers=headers).json()

    assert first["email"] == "user_maya@example.com"
    assert first["id"] == second["id"]


def test_repeated_start_from_the_connected_account_gets_the_welcome_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    seeded_settings: dict[str, Any],
) -> None:
    token = create_connection_token(client, auth_headers(auth_verifier, "user_maya"))
    update = telegram_text_update(f"/start {token}")

    send_to_webhook(client, update)
    send_to_webhook(client, update)

    welcome = seeded_settings["welcome_message"]
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [welcome, welcome]


def test_start_without_a_known_token_gets_reply_pointing_back_to_dashboard(
    client: TestClient,
    chat_channel: FakeChatChannel,
    seeded_settings: dict[str, Any],
) -> None:
    send_to_webhook(client, telegram_text_update("/start"))
    send_to_webhook(client, telegram_text_update("/start NOPE-NOPE"))

    expected_reply = seeded_settings["connection_token_invalid_reply"].replace(
        "{dashboard_url}", DASHBOARD_URL
    )
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        expected_reply,
        expected_reply,
    ]
