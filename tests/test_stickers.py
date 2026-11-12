from typing import Any

from fastapi.testclient import TestClient

from companion.core.models import ChannelSticker, StickerImage
from tests.conftest import DASHBOARD_URL
from tests.fakes import (
    ChatModelCall,
    FakeAuthVerifier,
    FakeChatChannel,
    ScriptedChatModel,
    SentSticker,
    ToolCall,
)
from tests.telegram_helpers import (
    OWNER_TELEGRAM_USER_ID,
    TELEGRAM_CHAT_ID,
    auth_headers,
    connect_owner_telegram,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_message_update,
    telegram_sticker_update,
    telegram_text_update,
)

SEEDLING = ChannelSticker(
    file_id="file-seedling",
    file_unique_id="seedling",
    emoji="🌱",
    set_name="CalmCreatures",
    preview_file_id="thumb-seedling",
)
MOON = ChannelSticker(
    file_id="file-moon",
    file_unique_id="moon",
    emoji="🌙",
    set_name="CalmCreatures",
    preview_file_id=None,
)


def list_stickers(client: TestClient, admin: dict[str, str]) -> list[dict[str, Any]]:
    """List the Sticker Library as an Admin."""
    response = client.get("/api/admin/stickers", headers=admin)
    assert response.status_code == 200, response.text
    stickers: list[dict[str, Any]] = response.json()["stickers"]
    return stickers


def import_calm_creatures(
    client: TestClient, admin: dict[str, str], chat_channel: FakeChatChannel
) -> list[dict[str, Any]]:
    """Import the CalmCreatures set as an Admin and return the library."""
    chat_channel.sticker_sets["CalmCreatures"] = [SEEDLING, MOON]
    response = client.post(
        "/api/admin/stickers/import",
        json={"set_name": "CalmCreatures"},
        headers=admin,
    )
    assert response.status_code == 201, response.text
    return list_stickers(client, admin)


def save_note(
    client: TestClient, admin: dict[str, str], sticker_id: str, note: str
) -> dict[str, Any]:
    """Save a sticker's "when to use" note as an Admin."""
    response = client.put(
        f"/api/admin/stickers/{sticker_id}", json={"note": note}, headers=admin
    )
    assert response.status_code == 200, response.text
    sticker: dict[str, Any] = response.json()
    return sticker


def reply_call(
    client: TestClient,
    chat_model: ScriptedChatModel,
    update: dict[str, Any],
    *script: str | ToolCall,
) -> ChatModelCall:
    """Send a Telegram update and return the reply call the model received."""
    chat_model.calls.clear()
    chat_model.script(*script)
    assert send_to_webhook(client, update) == 200
    [call] = chat_model.calls
    return call


def test_an_admin_sending_a_sticker_adds_it_to_the_sticker_library(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)

    update = telegram_sticker_update(
        "🌊", "wave", telegram_user_id=OWNER_TELEGRAM_USER_ID
    )
    assert send_to_webhook(client, update) == 200

    [sticker] = list_stickers(client, admin)
    assert sticker["emoji"] == "🌊"
    assert sticker["note"] == ""
    assert sticker["set_name"] == "CalmCreatures"
    assert sticker["has_image"] is True
    assert chat_channel.texts_sent_to(OWNER_TELEGRAM_USER_ID) == [
        seeded_settings["sticker_added_reply"].replace("{dashboard_url}", DASHBOARD_URL)
    ]
    assert chat_model.calls == []


def test_an_admin_sending_a_sticker_already_in_the_library_does_not_add_it_twice(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    update = telegram_sticker_update(
        "🌊", "wave", telegram_user_id=OWNER_TELEGRAM_USER_ID
    )
    assert send_to_webhook(client, update) == 200
    chat_channel.sent.clear()

    assert send_to_webhook(client, update) == 200

    assert len(list_stickers(client, admin)) == 1
    assert chat_channel.texts_sent_to(OWNER_TELEGRAM_USER_ID) == [
        seeded_settings["sticker_already_in_library_reply"]
    ]


def test_a_users_sticker_reaches_the_companion_as_its_emoji_and_is_not_added(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    call = reply_call(client, chat_model, telegram_sticker_update("😂"), "haha")

    assert call.history[-1].text == "[sticker: 😂]"
    assert chat_model.safeguard_calls[-1].history[-1].text.endswith("[sticker: 😂]")
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["haha"]
    assert list_stickers(client, owner_headers(client, auth_verifier)) == []


def test_a_sticker_without_an_emoji_still_reaches_the_companion(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    call = reply_call(client, chat_model, telegram_sticker_update(None), "nice")

    assert call.history[-1].text == "[sticker]"


def test_voice_notes_and_photos_get_the_unsupported_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    voice = telegram_message_update({"voice": {"file_id": "v1", "duration": 3}})
    photo = telegram_message_update({"photo": [{"file_id": "p1", "width": 90}]})

    assert send_to_webhook(client, voice) == 200
    assert send_to_webhook(client, photo) == 200

    unsupported_reply = seeded_settings["unsupported_message_reply"]
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        unsupported_reply,
        unsupported_reply,
    ]
    assert chat_model.calls == []
    assert chat_model.safeguard_calls == []


def test_a_photo_caption_is_checked_and_answered_like_a_message(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    photo = telegram_message_update(
        {"photo": [{"file_id": "p1", "width": 90}], "caption": "my new plant"}
    )

    call = reply_call(client, chat_model, photo, "oh I can't see photos yet")

    assert call.history[-1].text == "[photo] my new plant"
    assert (
        chat_model.safeguard_calls[-1].history[-1].text.endswith("[photo] my new plant")
    )


def test_admins_add_a_sticker_set_by_name_without_notes(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    chat_channel.sticker_sets["CalmCreatures"] = [SEEDLING, MOON]

    response = client.post(
        "/api/admin/stickers/import",
        json={"set_name": " CalmCreatures "},
        headers=admin,
    )

    assert response.status_code == 201
    assert response.json() == {"added_count": 2}
    stickers = list_stickers(client, admin)
    assert [(s["emoji"], s["note"], s["has_image"]) for s in stickers] == [
        ("🌱", "", True),
        ("🌙", "", False),
    ]


def test_importing_a_set_again_skips_stickers_already_in_the_library(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    [seedling, _] = import_calm_creatures(client, admin, chat_channel)
    save_note(client, admin, seedling["id"], "Celebrating a small step")

    response = client.post(
        "/api/admin/stickers/import",
        json={"set_name": "CalmCreatures"},
        headers=admin,
    )

    assert response.json() == {"added_count": 0}
    notes = [sticker["note"] for sticker in list_stickers(client, admin)]
    assert notes == ["Celebrating a small step", ""]


def test_an_unknown_or_blank_sticker_set_name_is_refused(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)

    unknown = client.post(
        "/api/admin/stickers/import", json={"set_name": "NoSuchSet"}, headers=admin
    )
    blank = client.post(
        "/api/admin/stickers/import", json={"set_name": "  "}, headers=admin
    )

    assert unknown.status_code == 404
    assert "NoSuchSet" in unknown.json()["detail"]
    assert blank.status_code == 422


def test_admins_edit_the_when_to_use_note_and_remove_stickers(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    [seedling, moon] = import_calm_creatures(client, admin, chat_channel)

    saved = save_note(client, admin, seedling["id"], "  Celebrating a small step ")
    removed = client.delete(f"/api/admin/stickers/{moon['id']}", headers=admin)

    assert saved["note"] == "Celebrating a small step"
    assert removed.status_code == 204
    assert [s["id"] for s in list_stickers(client, admin)] == [seedling["id"]]
    missing = client.delete(f"/api/admin/stickers/{moon['id']}", headers=admin)
    assert missing.status_code == 404
    missing_note = client.put(
        f"/api/admin/stickers/{moon['id']}", json={"note": "x"}, headers=admin
    )
    assert missing_note.status_code == 404


def test_admins_see_a_stickers_image(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    [seedling, moon] = import_calm_creatures(client, admin, chat_channel)
    chat_channel.sticker_images["thumb-seedling"] = StickerImage(
        content=b"webp-bytes", media_type="image/webp"
    )

    image = client.get(f"/api/admin/stickers/{seedling['id']}/image", headers=admin)
    no_image = client.get(f"/api/admin/stickers/{moon['id']}/image", headers=admin)

    assert image.status_code == 200
    assert image.content == b"webp-bytes"
    assert image.headers["content-type"] == "image/webp"
    assert no_image.status_code == 404


def test_only_admins_can_use_the_sticker_library(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
) -> None:
    user = auth_headers(auth_verifier, "user_maya")

    assert client.get("/api/admin/stickers", headers=user).status_code == 403
    imported = client.post(
        "/api/admin/stickers/import", json={"set_name": "CalmCreatures"}, headers=user
    )
    assert imported.status_code == 403


def test_a_reply_can_include_one_sticker_from_the_library(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    [seedling, _] = import_calm_creatures(client, admin, chat_channel)
    save_note(client, admin, seedling["id"], "Celebrating a small step forward")
    connect_telegram(client, auth_verifier, chat_channel)

    call = reply_call(
        client,
        chat_model,
        telegram_text_update("I went for my first run today!"),
        ToolCall("send_sticker", {"number": 1}),
        "that's brilliant",
    )

    [tool] = [tool for tool in call.tools if tool.name == "send_sticker"]
    assert "1. 🌱 Celebrating a small step forward" in tool.description
    assert "🌙" not in tool.description
    assert chat_channel.events == [
        "typing",
        "typing",
        "text: that's brilliant",
        "sticker: file-seedling",
    ]
    next_call = reply_call(
        client, chat_model, telegram_text_update("thanks"), "anytime"
    )
    assert [line.text for line in next_call.history[-3:]] == [
        "that's brilliant",
        "[sticker: 🌱]",
        "thanks",
    ]
    assert len(chat_channel.sent_stickers) == 1


def test_a_reply_sends_at_most_one_sticker(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    [seedling, moon] = import_calm_creatures(client, admin, chat_channel)
    save_note(client, admin, seedling["id"], "A small step forward")
    save_note(client, admin, moon["id"], "Good night")
    connect_telegram(client, auth_verifier, chat_channel)

    call = reply_call(
        client,
        chat_model,
        telegram_text_update("ran today, off to bed now"),
        ToolCall("send_sticker", {"number": 2}),
        ToolCall("send_sticker", {"number": 1}),
        ToolCall("send_sticker", {"number": 9}),
        "sleep well",
    )

    assert chat_channel.sent_stickers == [
        SentSticker(chat_id=TELEGRAM_CHAT_ID, file_id="file-moon")
    ]
    assert "already" in call.tool_results[1]


def test_a_reply_can_be_just_a_sticker(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    [seedling, _] = import_calm_creatures(client, admin, chat_channel)
    save_note(client, admin, seedling["id"], "A small step forward")
    connect_telegram(client, auth_verifier, chat_channel)

    reply_call(
        client,
        chat_model,
        telegram_text_update("did it!"),
        ToolCall("send_sticker", {"number": 1}),
        "",
    )

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == []
    assert chat_channel.sent_stickers == [
        SentSticker(chat_id=TELEGRAM_CHAT_ID, file_id="file-seedling")
    ]


def test_no_sticker_tool_is_offered_when_no_sticker_has_a_note(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    import_calm_creatures(client, admin, chat_channel)
    connect_telegram(client, auth_verifier, chat_channel)

    call = reply_call(client, chat_model, telegram_text_update("hi"), "hey")

    assert [tool.name for tool in call.tools if tool.name == "send_sticker"] == []


def test_the_crisis_reply_never_includes_a_sticker(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    [seedling, _] = import_calm_creatures(client, admin, chat_channel)
    save_note(client, admin, seedling["id"], "Any time at all")
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_safeguard("suicide_or_self_harm")

    assert send_to_webhook(client, telegram_text_update("I want to end it")) == 200

    assert chat_model.calls == []
    assert chat_channel.sent_stickers == []
    assert len(chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)) == 1


def test_telegram_not_answering_is_a_clear_error_and_images_fall_back(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    [seedling, _] = import_calm_creatures(client, admin, chat_channel)
    chat_channel.sticker_lookup_failure = TimeoutError("Telegram timed out")

    imported = client.post(
        "/api/admin/stickers/import",
        json={"set_name": "CalmCreatures"},
        headers=admin,
    )
    image = client.get(f"/api/admin/stickers/{seedling['id']}/image", headers=admin)

    assert imported.status_code == 502
    assert imported.json()["detail"] == "Telegram didn’t respond. Please try again."
    assert image.status_code == 404


def test_service_messages_are_ignored(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    pinned = telegram_message_update({"pinned_message": {"message_id": 3}})

    assert send_to_webhook(client, pinned) == 200

    assert chat_channel.sent == []
    assert chat_model.safeguard_calls == []
