from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import WEBHOOK_SECRET
from tests.fakes import FakeAuthVerifier

TELEGRAM_USER_ID = 5551001
TELEGRAM_CHAT_ID = 5551001


def telegram_text_update(
    text: str,
    telegram_user_id: int = TELEGRAM_USER_ID,
    username: str = "maya_l",
) -> dict[str, Any]:
    """Build a Telegram webhook update for a private text message."""
    return {
        "update_id": 1,
        "message": {
            "message_id": 10,
            "date": 1762851600,
            "from": {"id": telegram_user_id, "is_bot": False, "username": username},
            "chat": {"id": telegram_user_id, "type": "private"},
            "text": text,
        },
    }


def send_to_webhook(client: TestClient, update: dict[str, Any]) -> int:
    """Post an update to the webhook with the right secret and return the status."""
    response = client.post(
        "/telegram/webhook",
        json=update,
        headers={"X-Telegram-Bot-Api-Secret-Token": WEBHOOK_SECRET},
    )
    return response.status_code


def auth_headers(auth_verifier: FakeAuthVerifier, auth_id: str) -> dict[str, str]:
    """Build Dashboard API headers for an account."""
    token = auth_verifier.token_for(auth_id, f"{auth_id}@example.com")
    return {"Authorization": f"Bearer {token}"}


def create_connection_token(client: TestClient, headers: dict[str, str]) -> str:
    """Ask the Dashboard API for a connection token and return it."""
    response = client.post("/api/telegram-connection/tokens", headers=headers)
    assert response.status_code == 201
    token: str = response.json()["token"]
    return token
