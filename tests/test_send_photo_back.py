import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from companion.core.photos import sent_shared_photo_text
from tests.conftest import CompanionTestClient
from tests.fakes import (
    ChatModelCall,
    FakeAuthVerifier,
    FakeChatChannel,
    ScriptedChatModel,
    SentPhoto,
    ToolCall,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    auth_headers,
    connect_owner_telegram,
    connect_telegram,
    telegram_text_update,
)
from tests.test_stickers import import_calm_creatures, reply_call, save_note
from tests.test_web_search import change_settings

CAT = "A ginger cat asleep on a sunny windowsill next to a small cactus."
CAT_NOTE = "Miso is their cat, who keeps them company when they work from home."
GARDEN = "A small balcony garden with tomato plants in clay pots."
GARDEN_NOTE = "They grew these tomatoes from seed during a hard winter."
OWNERS_DOG = "A black dog running on a beach at sunset."


def add_shared_photo(
    client: TestClient,
    headers: dict[str, str],
    file_id: str,
    description: str,
    note: str,
    sent_at: datetime = datetime(2026, 11, 10, 9, tzinfo=UTC),
) -> str:
    """Keep a Shared Photo for the signed-in User, as memory processing would.

    Returns:
        The Shared Photo's ID.
    """
    assert isinstance(client, CompanionTestClient)
    user_id = client.get("/api/me", headers=headers).json()["id"]
    photo_id = str(uuid4())
    with client.engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO shared_photos (id, user_id, file_id, file_unique_id, "
                "description, note, caption, sent_at) VALUES (:id, :user_id, "
                ":file_id, :file_id, :description, :note, '', :sent_at)"
            ),
            {
                "id": photo_id,
                "user_id": user_id,
                "file_id": file_id,
                "description": description,
                "note": note,
                "sent_at": sent_at,
            },
        )
    return photo_id


def connect_maya_with_a_shared_cat(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> dict[str, str]:
    """Connect Maya and give her one Shared Photo, of her cat.

    Returns:
        Her Dashboard API headers.
    """
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    add_shared_photo(client, headers, "file-cat", CAT, CAT_NOTE)
    return headers


def send_photo_tools(call: ChatModelCall) -> list[Any]:
    """The send_photo tools offered to a reply call."""
    return [tool for tool in call.tools if tool.name == "send_photo"]


def test_a_relevant_shared_photo_reaches_the_reply_and_can_be_sent_back(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_maya_with_a_shared_cat(client, auth_verifier, chat_channel)
    chat_model.script_retrieval("Shared Photos")

    call = reply_call(
        client,
        chat_model,
        telegram_text_update("Miso knocked my plant over again"),
        ToolCall("send_photo", {"photo": 1}),
        "classic Miso, remember this sleepy face?",
    )

    [retrieval_call] = chat_model.retrieval_calls
    group_description = seeded_settings["shared_photos_memory_description"]
    assert f"- Shared Photos: {group_description}" in retrieval_call.history[0].text
    assert CAT in call.instructions
    assert CAT_NOTE in call.instructions
    [tool] = send_photo_tools(call)
    assert tool.description.startswith(seeded_settings["send_photo_tool_description"])
    assert f"1. {CAT}" in tool.description
    assert chat_channel.events[-2:] == [
        "text: classic Miso, remember this sleepy face?",
        "photo: file-cat",
    ]
    next_call = reply_call(
        client, chat_model, telegram_text_update("haha yes"), "so cute"
    )
    assert [line.text for line in next_call.history[-3:]] == [
        "classic Miso, remember this sleepy face?",
        sent_shared_photo_text(CAT),
        "haha yes",
    ]


def test_shared_photos_not_picked_for_the_message_are_not_shown_or_offered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_maya_with_a_shared_cat(client, auth_verifier, chat_channel)

    call = reply_call(client, chat_model, telegram_text_update("long day"), "aw")

    assert CAT not in call.instructions
    assert send_photo_tools(call) == []


def test_a_reply_sends_at_most_one_shared_photo_after_the_text_and_before_a_sticker(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    [seedling, _] = import_calm_creatures(client, admin, chat_channel)
    save_note(client, admin, seedling["id"], "Celebrating growth")
    headers = connect_maya_with_a_shared_cat(client, auth_verifier, chat_channel)
    add_shared_photo(
        client,
        headers,
        "file-garden",
        GARDEN,
        GARDEN_NOTE,
        sent_at=datetime(2026, 11, 12, 9, tzinfo=UTC),
    )
    chat_model.script_retrieval("Shared Photos")

    call = reply_call(
        client,
        chat_model,
        telegram_text_update("first tomato of the year!"),
        ToolCall("send_photo", {"photo": 2}),
        ToolCall("send_photo", {"photo": 1}),
        ToolCall("send_sticker", {"number": 1}),
        "look how far they've come",
    )

    [tool] = send_photo_tools(call)
    assert f"1. {GARDEN}" in tool.description
    assert f"2. {CAT}" in tool.description
    assert "already" in call.tool_results[1]
    assert chat_channel.sent_photos == [
        SentPhoto(chat_id=TELEGRAM_CHAT_ID, file_id="file-cat")
    ]
    assert chat_channel.events[-3:] == [
        "text: look how far they've come",
        "photo: file-cat",
        "sticker: file-seedling",
    ]


def test_another_users_shared_photo_is_never_shown_or_sent(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    owners_photo_id = add_shared_photo(
        client, admin, "file-owners-dog", OWNERS_DOG, "Their dog."
    )
    connect_maya_with_a_shared_cat(client, auth_verifier, chat_channel)
    chat_model.script_retrieval("Shared Photos")

    call = reply_call(
        client,
        chat_model,
        telegram_text_update("I miss the beach"),
        ToolCall("send_photo", {"photo": 2}),
        ToolCall("send_photo", {"photo": owners_photo_id}),
        ToolCall("send_photo", {"photo": "file-owners-dog"}),
        "me too",
    )

    assert OWNERS_DOG not in call.instructions
    [tool] = send_photo_tools(call)
    assert OWNERS_DOG not in tool.description
    assert all("no shared photo" in result.lower() for result in call.tool_results)
    assert chat_channel.sent_photos == []


def test_with_user_memory_off_no_shared_photos_are_shown_and_the_tool_is_not_offered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = connect_maya_with_a_shared_cat(client, auth_verifier, chat_channel)
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)
    chat_model.script_retrieval("Shared Photos")

    call = reply_call(client, chat_model, telegram_text_update("Miso!"), "hi")

    assert chat_model.retrieval_calls == []
    assert CAT not in call.instructions
    assert send_photo_tools(call) == []


def test_when_telegram_refuses_the_photo_the_text_still_goes_out_and_it_is_logged(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    caplog: pytest.LogCaptureFixture,
) -> None:
    connect_maya_with_a_shared_cat(client, auth_verifier, chat_channel)
    chat_model.script_retrieval("Shared Photos")
    chat_channel.photo_send_failure = RuntimeError("Bad Request: wrong file id")

    with caplog.at_level(logging.ERROR):
        reply_call(
            client,
            chat_model,
            telegram_text_update("Miso is asleep again"),
            ToolCall("send_photo", {"photo": 1}),
            "she's a pro",
        )

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)[-1] == "she's a pro"
    assert chat_channel.sent_photos == []
    assert "Could not send a Shared Photo" in caplog.text
    next_call = reply_call(client, chat_model, telegram_text_update("lol"), "ha")
    assert sent_shared_photo_text(CAT) not in [line.text for line in next_call.history]


def test_the_tool_description_says_to_use_it_rarely_and_never_when_struggling(
    seeded_settings: dict[str, Any],
) -> None:
    description = seeded_settings["send_photo_tool_description"].lower()

    assert "rarely" in description
    assert "struggling" in description


def test_edited_send_photo_settings_are_used_and_show_on_the_prompts_page(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    connect_maya_with_a_shared_cat(client, auth_verifier, chat_channel)
    edited_tool = "Send one back only on happy anniversaries."
    edited_group = "Photos of pets and plants they love."
    change_settings(
        client,
        admin,
        {
            "send_photo_tool_description": edited_tool,
            "shared_photos_memory_description": edited_group,
        },
    )
    chat_model.script_retrieval("Shared Photos")

    call = reply_call(client, chat_model, telegram_text_update("Miso!"), "hi")

    [tool] = send_photo_tools(call)
    assert tool.description.startswith(edited_tool)
    assert f"- Shared Photos: {edited_group}" in (
        chat_model.retrieval_calls[0].history[0].text
    )
    services = client.get("/api/admin/core-services", headers=admin).json()
    extra_prompts = {
        service["name"]: [prompt["key"] for prompt in service["extra_prompts"]]
        for service in services["services"]
    }
    assert "send_photo_tool_description" in extra_prompts["Photo viewing"]
    assert "shared_photos_memory_description" in extra_prompts["Memory retrieval"]
