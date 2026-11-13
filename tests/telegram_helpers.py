from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text

from companion.core.models import ChannelSticker
from tests.conftest import INITIAL_ADMIN_EMAIL, WEBHOOK_SECRET, CompanionTestClient
from tests.fakes import FakeAuthVerifier, FakeChatChannel

TELEGRAM_USER_ID = 5551001
TELEGRAM_CHAT_ID = 5551001
OWNER_TELEGRAM_USER_ID = 5552002
OWNER_AUTH_ID = INITIAL_ADMIN_EMAIL.split("@")[0]


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


def telegram_message_update(
    content: dict[str, Any],
    telegram_user_id: int = TELEGRAM_USER_ID,
    username: str = "maya_l",
) -> dict[str, Any]:
    """Build a Telegram webhook update for a private message with any content."""
    update = telegram_text_update("", telegram_user_id, username)
    del update["message"]["text"]
    update["message"].update(content)
    return update


def telegram_photo_update(
    caption: str | None = None,
    file_unique_id: str = "photo-cat",
    album_id: str | None = None,
    message_id: int = 10,
) -> dict[str, Any]:
    """Build a Telegram webhook update for a photo, in a small and a large size.

    A photo with an album id is one of several sent together.
    """
    content: dict[str, Any] = {
        "photo": [
            {
                "file_id": f"small-{file_unique_id}",
                "file_unique_id": f"small-{file_unique_id}",
                "width": 90,
                "height": 60,
            },
            {
                "file_id": f"file-{file_unique_id}",
                "file_unique_id": file_unique_id,
                "width": 1280,
                "height": 853,
            },
        ]
    }
    if caption is not None:
        content["caption"] = caption
    if album_id is not None:
        content["media_group_id"] = album_id
    update = telegram_message_update(content)
    update["message"]["message_id"] = message_id
    return update


def telegram_album_video_update(
    caption: str | None = None, album_id: str = "album-1", message_id: int = 10
) -> dict[str, Any]:
    """Build a Telegram webhook update for a video sent in an album."""
    content: dict[str, Any] = {
        "video": {"file_id": "file-video", "file_unique_id": "video"},
        "media_group_id": album_id,
    }
    if caption is not None:
        content["caption"] = caption
    update = telegram_message_update(content)
    update["message"]["message_id"] = message_id
    return update


def telegram_file_update(
    mime_type: str, file_size: int = 250_000, file_unique_id: str = "file-1"
) -> dict[str, Any]:
    """Build a Telegram webhook update for a file sent as a document."""
    return telegram_message_update(
        {
            "document": {
                "file_id": f"file-{file_unique_id}",
                "file_unique_id": file_unique_id,
                "mime_type": mime_type,
                "file_size": file_size,
            }
        }
    )


def telegram_sticker_update(
    emoji: str | None = "😂",
    file_unique_id: str = "sticker-laugh",
    telegram_user_id: int = TELEGRAM_USER_ID,
    set_name: str | None = "CalmCreatures",
) -> dict[str, Any]:
    """Build a Telegram webhook update for a sticker message."""
    sticker: dict[str, Any] = {
        "file_id": f"file-{file_unique_id}",
        "file_unique_id": file_unique_id,
        "type": "regular",
        "width": 512,
        "height": 512,
        "is_animated": False,
        "is_video": False,
        "thumbnail": {"file_id": f"thumb-{file_unique_id}", "width": 128},
    }
    if emoji is not None:
        sticker["emoji"] = emoji
    if set_name is not None:
        sticker["set_name"] = set_name
    return telegram_message_update({"sticker": sticker}, telegram_user_id)


def telegram_reply_to_sticker_update(
    text: str,
    sticker: ChannelSticker,
    telegram_user_id: int = TELEGRAM_USER_ID,
) -> dict[str, Any]:
    """Build a Telegram webhook update for a text replying to a sticker message."""
    replied_sticker: dict[str, Any] = {
        "file_id": sticker.file_id,
        "file_unique_id": sticker.file_unique_id,
        "type": "regular",
        "is_animated": False,
        "is_video": False,
    }
    if sticker.emoji is not None:
        replied_sticker["emoji"] = sticker.emoji
    if sticker.set_name is not None:
        replied_sticker["set_name"] = sticker.set_name
    if sticker.preview_file_id is not None:
        replied_sticker["thumbnail"] = {"file_id": sticker.preview_file_id}
    update = telegram_text_update(text, telegram_user_id)
    update["message"]["reply_to_message"] = {
        "message_id": 9,
        "date": 1762851500,
        "chat": {"id": telegram_user_id, "type": "private"},
        "sticker": replied_sticker,
    }
    return update


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


def onboarding_answers(**overrides: Any) -> dict[str, Any]:
    """Build a valid onboarding request body, with any fields swapped out."""
    answers: dict[str, Any] = {
        "name": "Maya",
        "ai_notice_acknowledged": True,
        "onboarding_reasons": ["Being more present", "Relationships"],
        "onboarding_note": "New job, running on autopilot.",
        "user_memory_enabled": True,
        "country": "SG",
        "time_zone": "Asia/Singapore",
    }
    answers.update(overrides)
    return answers


def mark_onboarded(client: TestClient, headers: dict[str, str]) -> None:
    """Mark the User as onboarded unless they already are.

    Only the onboarding times are set, so the User's name, answers and
    Memory Items stay as they were. Tests of onboarding itself use the API.
    """
    assert isinstance(client, CompanionTestClient)
    user_id = client.get("/api/me", headers=headers).json()["id"]
    with client.engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE users SET onboarding_completed_at = now(), "
                "ai_notice_acknowledged_at = now() "
                "WHERE id = :user_id AND onboarding_completed_at IS NULL"
            ),
            {"user_id": user_id},
        )


def create_connection_token(client: TestClient, headers: dict[str, str]) -> str:
    """Mark the User onboarded, then ask for a connection token and return it."""
    mark_onboarded(client, headers)
    response = client.post("/api/telegram-connection/tokens", headers=headers)
    assert response.status_code == 201
    token: str = response.json()["token"]
    return token


def connect_telegram(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    """Sign up a User, make their Telegram Connection and forget the welcome."""
    headers = auth_headers(auth_verifier, "user_maya")
    token = create_connection_token(client, headers)
    assert send_to_webhook(client, telegram_text_update(f"/start {token}")) == 200
    chat_channel.sent.clear()
    chat_channel.events.clear()


def connect_owner_telegram(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> dict[str, str]:
    """Connect the initial Admin's Telegram account and return their headers."""
    headers = owner_headers(client, auth_verifier)
    token = create_connection_token(client, headers)
    update = telegram_text_update(
        f"/start {token}", OWNER_TELEGRAM_USER_ID, username="owner_tg"
    )
    assert send_to_webhook(client, update) == 200
    chat_channel.sent.clear()
    chat_channel.events.clear()
    return headers


def owner_headers(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> dict[str, str]:
    """Sign in as the initial Admin and return their Dashboard API headers."""
    headers = auth_headers(auth_verifier, OWNER_AUTH_ID)
    assert client.get("/api/me", headers=headers).json()["role"] == "admin"
    return headers
