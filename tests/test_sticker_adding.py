from typing import Any

from fastapi.testclient import TestClient

from companion.core.models import ChannelSticker
from tests.conftest import DASHBOARD_URL
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeTimer,
    ScriptedChatModel,
    SentReaction,
    ToolCall,
)
from tests.telegram_helpers import (
    OWNER_TELEGRAM_USER_ID,
    TELEGRAM_CHAT_ID,
    connect_owner_telegram,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_reply_to_sticker_update,
    telegram_sticker_update,
    telegram_text_update,
)
from tests.test_stickers import list_stickers, save_note

ADDING_TOOL = "start_adding_stickers"
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
WAVE = ChannelSticker(
    file_id="file-wave",
    file_unique_id="wave",
    emoji="🌊",
    set_name="CalmCreatures",
    preview_file_id="thumb-wave",
)


def owner_text(text: str) -> dict[str, Any]:
    """Build a text message from the initial Admin's Telegram account."""
    return telegram_text_update(text, OWNER_TELEGRAM_USER_ID, username="owner_tg")


def owner_sticker(
    emoji: str, file_unique_id: str, set_name: str | None = "CalmCreatures"
) -> dict[str, Any]:
    """Build a sticker message from the initial Admin's Telegram account."""
    update = telegram_sticker_update(
        emoji, file_unique_id, OWNER_TELEGRAM_USER_ID, set_name=set_name
    )
    update["message"]["message_id"] = 40
    return update


def start_adding(
    client: TestClient,
    chat_model: ScriptedChatModel,
    chat_channel: FakeChatChannel,
    choice: str,
) -> list[str]:
    """Ask the Companion, as the Admin, to start adding stickers.

    Returns:
        What the tool told the model back.
    """
    chat_model.calls.clear()
    chat_model.script(ToolCall(ADDING_TOOL, {"choice": choice}), "Send them over 👍")
    assert send_to_webhook(client, owner_text("I want to add some stickers")) == 200
    [call] = chat_model.calls
    chat_channel.sent.clear()
    chat_channel.events.clear()
    chat_model.calls.clear()
    chat_model.safeguard_calls.clear()
    return call.tool_results


def summary(seeded_settings: dict[str, Any], added: str) -> str:
    """Write the summary the Admin gets after adding stickers."""
    template: str = seeded_settings["sticker_adding_summary_reply"]
    return template.replace("{added}", added).replace("{dashboard_url}", DASHBOARD_URL)


def test_an_admins_sticker_outside_adding_mode_is_answered_like_any_users(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    chat_model.script("haha love it")

    assert send_to_webhook(client, owner_sticker("😂", "laugh")) == 200

    [call] = chat_model.calls
    assert call.history[-1].text == "[sticker: 😂]"
    assert chat_channel.texts_sent_to(OWNER_TELEGRAM_USER_ID) == ["haha love it"]
    assert list_stickers(client, admin) == []


def test_only_admins_are_offered_the_adding_tool(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_owner_telegram(client, auth_verifier, chat_channel)
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("Sure", "Sure")

    send_to_webhook(client, owner_text("I want to add some stickers"))
    send_to_webhook(client, telegram_text_update("I want to add some stickers"))

    admin_call, user_call = chat_model.calls
    assert ADDING_TOOL in [tool.name for tool in admin_call.tools]
    assert ADDING_TOOL not in [tool.name for tool in user_call.tools]


def test_in_single_mode_each_sticker_is_added_with_a_reaction_and_no_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    [tool_result] = start_adding(client, chat_model, chat_channel, "single_stickers")
    assert "single" in tool_result

    assert send_to_webhook(client, owner_sticker("🌊", "wave")) == 200
    assert send_to_webhook(client, owner_sticker("🌙", "moon")) == 200

    assert [sticker["emoji"] for sticker in list_stickers(client, admin)] == [
        "🌊",
        "🌙",
    ]
    assert chat_channel.reactions == [
        SentReaction(OWNER_TELEGRAM_USER_ID, 40, "👍"),
        SentReaction(OWNER_TELEGRAM_USER_ID, 40, "👍"),
    ]
    assert chat_channel.sent == []
    assert chat_model.calls == []
    assert chat_model.safeguard_calls == []


def test_a_message_that_isnt_a_sticker_ends_adding_mode_with_a_summary_first(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_owner_telegram(client, auth_verifier, chat_channel)
    start_adding(client, chat_model, chat_channel, "single_stickers")
    send_to_webhook(client, owner_sticker("🌊", "wave"))
    send_to_webhook(client, owner_sticker("🌙", "moon"))
    send_to_webhook(client, owner_sticker("🌙", "moon"))
    chat_model.script("Lovely ones!")

    assert send_to_webhook(client, owner_text("that's all")) == 200

    assert chat_channel.texts_sent_to(OWNER_TELEGRAM_USER_ID) == [
        summary(seeded_settings, "Added 2 stickers (1 was already there)."),
        "Lovely ones!",
    ]
    [call] = chat_model.calls
    assert [line.text for line in call.history[-2:]] == [
        summary(seeded_settings, "Added 2 stickers (1 was already there)."),
        "that's all",
    ]

    chat_model.script("ha")
    send_to_webhook(client, owner_sticker("😂", "laugh"))
    assert chat_model.calls[-1].history[-1].text == "[sticker: 😂]"


def test_in_whole_sets_mode_a_sticker_adds_its_set_once_and_keeps_notes(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    chat_channel.sticker_sets["CalmCreatures"] = [SEEDLING]
    import_response = client.post(
        "/api/admin/stickers/import",
        json={"set_name": "CalmCreatures"},
        headers=admin,
    )
    assert import_response.status_code == 201
    [seedling] = list_stickers(client, admin)
    save_note(client, admin, seedling["id"], "A small step forward")
    chat_channel.sticker_sets["CalmCreatures"] = [SEEDLING, MOON, WAVE]
    start_adding(client, chat_model, chat_channel, "whole_sets")

    send_to_webhook(client, owner_sticker("🌊", "wave"))
    send_to_webhook(client, owner_sticker("🌙", "moon"))
    send_to_webhook(client, owner_sticker("🐸", "frog", set_name=None))
    chat_model.script("Nice")
    send_to_webhook(client, owner_text("done"))

    stickers = {sticker["emoji"]: sticker for sticker in list_stickers(client, admin)}
    assert sorted(stickers) == ["🌊", "🌙", "🌱", "🐸"]
    assert stickers["🌱"]["note"] == "A small step forward"
    assert stickers["🌊"]["note"] == ""
    assert len(chat_channel.reactions) == 3
    assert chat_channel.texts_sent_to(OWNER_TELEGRAM_USER_ID)[0] == summary(
        seeded_settings, "Added 3 stickers from 1 set (1 was already there)."
    )


def test_in_whole_sets_mode_a_set_that_cant_be_found_adds_the_sticker_alone(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    start_adding(client, chat_model, chat_channel, "whole_sets")

    send_to_webhook(client, owner_sticker("🌊", "wave", set_name="GoneSet"))

    assert [sticker["emoji"] for sticker in list_stickers(client, admin)] == ["🌊"]


def test_adding_mode_ends_after_the_quiet_gap_with_a_summary(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
    seeded_settings: dict[str, Any],
) -> None:
    connect_owner_telegram(client, auth_verifier, chat_channel)
    start_adding(client, chat_model, chat_channel, "single_stickers")
    send_to_webhook(client, owner_sticker("🌊", "wave"))
    gap_seconds = seeded_settings["sticker_adding_quiet_gap_minutes"] * 60
    assert timer.waits[-1][1] == gap_seconds

    timer.run_waiting()

    assert chat_channel.texts_sent_to(OWNER_TELEGRAM_USER_ID) == [
        summary(seeded_settings, "Added 1 sticker.")
    ]
    chat_model.script("ha")
    send_to_webhook(client, owner_sticker("😂", "laugh"))
    assert chat_model.calls[-1].history[-1].text == "[sticker: 😂]"


def test_adding_mode_with_nothing_sent_ends_quietly(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
) -> None:
    connect_owner_telegram(client, auth_verifier, chat_channel)
    start_adding(client, chat_model, chat_channel, "single_stickers")

    timer.run_waiting()

    assert chat_channel.sent == []


def test_an_admin_replying_add_this_to_a_sticker_adds_it(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    update = telegram_reply_to_sticker_update("Add this!", WAVE, OWNER_TELEGRAM_USER_ID)

    assert send_to_webhook(client, update) == 200

    assert [sticker["emoji"] for sticker in list_stickers(client, admin)] == ["🌊"]
    assert chat_channel.texts_sent_to(OWNER_TELEGRAM_USER_ID) == [
        summary(seeded_settings, "Added 1 sticker.")
    ]
    assert chat_model.calls == []


def test_an_admin_replying_add_this_set_to_a_sticker_adds_its_set(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    chat_channel.sticker_sets["CalmCreatures"] = [SEEDLING, MOON, WAVE]
    update = telegram_reply_to_sticker_update(
        "add this set", WAVE, OWNER_TELEGRAM_USER_ID
    )

    assert send_to_webhook(client, update) == 200

    assert len(list_stickers(client, admin)) == 3
    assert chat_channel.texts_sent_to(OWNER_TELEGRAM_USER_ID) == [
        summary(seeded_settings, "Added 3 stickers from 1 set.")
    ]


def test_add_this_for_a_sticker_already_there_says_so_without_the_note_reminder(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    connect_owner_telegram(client, auth_verifier, chat_channel)
    update = telegram_reply_to_sticker_update("add this", WAVE, OWNER_TELEGRAM_USER_ID)
    send_to_webhook(client, update)
    chat_channel.sent.clear()

    send_to_webhook(client, update)

    assert chat_channel.texts_sent_to(OWNER_TELEGRAM_USER_ID) == [
        "Added 0 stickers (1 was already there)."
    ]


def test_add_this_from_a_user_who_isnt_an_admin_is_just_chat(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("Add it where? 😄")

    send_to_webhook(client, telegram_reply_to_sticker_update("add this", WAVE))

    assert chat_model.calls[-1].history[-1].text == "add this"
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["Add it where? 😄"]
    assert list_stickers(client, owner_headers(client, auth_verifier)) == []


def test_other_replies_to_a_sticker_are_just_chat_for_admins(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    chat_model.script("Right?")

    send_to_webhook(
        client,
        telegram_reply_to_sticker_update(
            "this one is so cute", WAVE, OWNER_TELEGRAM_USER_ID
        ),
    )

    assert chat_model.calls[-1].history[-1].text == "this one is so cute"
    assert list_stickers(client, admin) == []


def test_admins_set_how_long_the_quiet_gap_is(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    response = client.patch(
        "/api/admin/settings",
        json={"values": {"sticker_adding_quiet_gap_minutes": 2}},
        headers=admin,
    )
    assert response.status_code == 200, response.text
    start_adding(client, chat_model, chat_channel, "whole_sets")

    send_to_webhook(client, owner_sticker("🌊", "wave"))

    assert timer.waits[-1][1] == 120


def test_an_unknown_choice_starts_nothing(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_owner_telegram(client, auth_verifier, chat_channel)
    [tool_result] = start_adding(client, chat_model, chat_channel, "some")
    assert "Nothing started" in tool_result
    chat_model.script("ha")

    send_to_webhook(client, owner_sticker("😂", "laugh"))

    assert chat_model.calls[-1].history[-1].text == "[sticker: 😂]"
