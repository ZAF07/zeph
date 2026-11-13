import json
from datetime import timedelta
from typing import Any

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import (
    MIGRATIONS_DIR,
    migrate,
    seed_platform_settings,
)
from companion.core.models import StickerImage
from companion.core.ports import ChatTool
from tests.conftest import SEED_FILE
from tests.fakes import (
    ChatModelCall,
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
    SentSticker,
    ToolCall,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    auth_headers,
    connect_owner_telegram,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_sticker_update,
    telegram_text_update,
)
from tests.test_features import (
    features_by_key,
    maya_id,
    reply_call,
    switch_for_everyone,
    switch_for_user,
    unavailable_note,
    user_features_by_key,
)
from tests.test_message_retention import retention
from tests.test_post_conversation import processing_answer, quiet_gap
from tests.test_stickers import import_calm_creatures, save_note
from tests.test_stickers import reply_call as sticker_reply_call

LAUGHING_NOTE = "For laughing along at a small mishap."
HUG_NOTE = "For sending warmth when a day went well."


def keeping_answer(*picks: tuple[int, str]) -> str:
    """Build the JSON the Personal Sticker keeping model answers with."""
    return json.dumps(
        {
            "stickers_to_keep": [
                {"sticker": number, "note": note} for number, note in picks
            ]
        }
    )


def turn_personal_stickers_on(client: TestClient, admin: dict[str, str]) -> None:
    """Turn Personal Stickers on for everyone as an Admin."""
    switch_for_everyone(client, admin, "personal_stickers", on=True)


def chat(
    client: TestClient, chat_model: ScriptedChatModel, *updates: dict[str, Any]
) -> None:
    """Send each Telegram update and let the Companion answer it."""
    for update in updates:
        chat_model.script("ok")
        assert send_to_webhook(client, update) == 200


def end_conversation(
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    keeping: str | None = None,
) -> None:
    """Let the quiet gap pass and run the tick that ends the Conversation."""
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(processing_answer())
    if keeping is not None:
        chat_model.script_sticker_keeping(keeping)
    scheduler.tick()


def personal_stickers(
    client: TestClient, headers: dict[str, str]
) -> list[dict[str, Any]]:
    """List the User's Personal Stickers through the Dashboard API."""
    response = client.get("/api/personal-stickers", headers=headers)
    assert response.status_code == 200, response.text
    stickers: list[dict[str, Any]] = response.json()["stickers"]
    return stickers


def maya_headers(auth_verifier: FakeAuthVerifier) -> dict[str, str]:
    """Maya's Dashboard API headers."""
    return auth_headers(auth_verifier, "user_maya")


def test_personal_stickers_is_a_feature_off_for_everyone_to_start(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)

    feature = features_by_key(client, admin)["personal_stickers"]
    status = user_features_by_key(client, admin, user_id)["personal_stickers"]
    call = reply_call(client, chat_model, "hello")

    assert feature["name"] == "Personal Stickers"
    assert feature["description"]
    assert feature["on"] is False
    assert feature["changed_at"] is None
    assert status["works"] is False
    assert status["reason"] == "off_for_everyone"
    assert "Personal Stickers" not in call.instructions
    assert (
        unavailable_note(seeded_settings, "Personal Stickers") not in call.instructions
    )


def test_personal_stickers_works_only_when_stickers_works(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    user_id = maya_id(client, auth_verifier)

    switch_for_everyone(client, admin, "personal_stickers", on=True)
    on = user_features_by_key(client, admin, user_id)["personal_stickers"]
    switch_for_user(client, admin, user_id, "stickers", "off")
    without_stickers = user_features_by_key(client, admin, user_id)
    switch_for_user(client, admin, user_id, "personal_stickers", "off")
    both_off = user_features_by_key(client, admin, user_id)["personal_stickers"]

    assert on["works"] is True
    assert on["reason"] == "on_for_everyone"
    assert without_stickers["stickers"]["works"] is False
    assert without_stickers["personal_stickers"]["works"] is False
    assert without_stickers["personal_stickers"]["reason"] == "stickers_off"
    assert both_off["reason"] == "off_for_user"


def test_stickers_with_a_clear_meaning_are_kept_with_a_note_when_a_conversation_ends(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    turn_personal_stickers_on(client, owner_headers(client, auth_verifier))
    connect_telegram(client, auth_verifier, chat_channel)
    chat(
        client,
        chat_model,
        telegram_text_update("I dropped my toast butter side down"),
        telegram_sticker_update("😂", "laugh"),
        telegram_sticker_update("🫠", "melt"),
    )

    end_conversation(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        keeping_answer((1, LAUGHING_NOTE)),
    )

    [keeping_call] = chat_model.sticker_keeping_calls
    given = keeping_call.history[-1].text
    assert "[1] 😂" in given
    assert "[2] 🫠" in given
    assert "Person: I dropped my toast butter side down" in given
    assert "Person: [sticker 1: 😂]" in given
    [kept] = personal_stickers(client, maya_headers(auth_verifier))
    assert kept["emoji"] == "😂"
    assert kept["note"] == LAUGHING_NOTE
    assert kept["has_image"] is True
    assert "file_id" not in kept


def test_stickers_are_kept_with_user_memory_off(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    turn_personal_stickers_on(client, owner_headers(client, auth_verifier))
    connect_telegram(client, auth_verifier, chat_channel)
    maya = maya_headers(auth_verifier)
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=maya)
    chat(client, chat_model, telegram_sticker_update("😂", "laugh"))

    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    chat_model.script_sticker_keeping(keeping_answer((1, LAUGHING_NOTE)))
    scheduler.tick()

    assert chat_model.processing_calls == []
    assert [s["note"] for s in personal_stickers(client, maya)] == [LAUGHING_NOTE]


def test_picks_that_cannot_be_used_are_skipped(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    turn_personal_stickers_on(client, owner_headers(client, auth_verifier))
    connect_telegram(client, auth_verifier, chat_channel)
    chat(client, chat_model, telegram_sticker_update("😂", "laugh"))
    answer = json.dumps(
        {
            "stickers_to_keep": [
                {"sticker": 7, "note": "No such sticker"},
                {"sticker": 1, "note": "  "},
                {"sticker": True, "note": "Not a number"},
                "not a pick",
            ]
        }
    )

    end_conversation(chat_model, clock, scheduler, seeded_settings, answer)

    assert personal_stickers(client, maya_headers(auth_verifier)) == []


def test_sending_a_kept_sticker_again_can_sharpen_its_note(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    turn_personal_stickers_on(client, owner_headers(client, auth_verifier))
    connect_telegram(client, auth_verifier, chat_channel)
    chat(client, chat_model, telegram_sticker_update("😂", "laugh"))
    end_conversation(
        chat_model, clock, scheduler, seeded_settings, keeping_answer((1, "Laughing"))
    )
    chat(client, chat_model, telegram_sticker_update("😂", "laugh"))

    sharper = "For laughing along when a plan goes comically wrong."
    end_conversation(
        chat_model, clock, scheduler, seeded_settings, keeping_answer((1, sharper))
    )

    given = chat_model.sticker_keeping_calls[-1].history[-1].text
    assert "[1] 😂 (kept already: Laughing)" in given
    [kept] = personal_stickers(client, maya_headers(auth_verifier))
    assert kept["note"] == sharper


def test_no_keeping_call_when_the_user_sent_no_stickers(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    turn_personal_stickers_on(client, owner_headers(client, auth_verifier))
    connect_telegram(client, auth_verifier, chat_channel)
    chat(client, chat_model, telegram_text_update("hi"))

    end_conversation(chat_model, clock, scheduler, seeded_settings)

    assert chat_model.sticker_keeping_calls == []
    assert len(chat_model.processing_calls) == 1


def test_a_sticker_also_in_the_sticker_library_is_still_kept_as_theirs(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    import_calm_creatures(client, admin, chat_channel)
    turn_personal_stickers_on(client, admin)
    connect_telegram(client, auth_verifier, chat_channel)
    chat(client, chat_model, telegram_sticker_update("🌱", "seedling"))

    end_conversation(
        chat_model, clock, scheduler, seeded_settings, keeping_answer((1, HUG_NOTE))
    )

    [kept] = personal_stickers(client, maya_headers(auth_verifier))
    assert kept["emoji"] == "🌱"
    assert kept["note"] == HUG_NOTE


def test_over_the_limit_the_sticker_used_longest_ago_is_dropped(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    turn_personal_stickers_on(client, admin)
    response = client.patch(
        "/api/admin/settings",
        json={"values": {"personal_stickers_limit": 2}},
        headers=admin,
    )
    assert response.status_code == 200, response.text
    connect_telegram(client, auth_verifier, chat_channel)
    chat(
        client,
        chat_model,
        telegram_sticker_update("😂", "laugh"),
        telegram_sticker_update("🤗", "hug"),
    )
    end_conversation(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        keeping_answer((1, LAUGHING_NOTE), (2, HUG_NOTE)),
    )
    chat(client, chat_model, telegram_sticker_update("😂", "laugh"))
    end_conversation(chat_model, clock, scheduler, seeded_settings, keeping_answer())
    chat(client, chat_model, telegram_sticker_update("🌙", "moon"))

    end_conversation(
        chat_model, clock, scheduler, seeded_settings, keeping_answer((1, "Good night"))
    )

    kept = personal_stickers(client, maya_headers(auth_verifier))
    assert sorted(sticker["emoji"] for sticker in kept) == sorted(["😂", "🌙"])


def test_with_personal_stickers_off_nothing_is_kept_and_nothing_is_deleted(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    turn_personal_stickers_on(client, admin)
    connect_telegram(client, auth_verifier, chat_channel)
    chat(client, chat_model, telegram_sticker_update("😂", "laugh"))
    end_conversation(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        keeping_answer((1, LAUGHING_NOTE)),
    )

    switch_for_everyone(client, admin, "personal_stickers", on=False)
    chat(client, chat_model, telegram_sticker_update("🤗", "hug"))
    end_conversation(chat_model, clock, scheduler, seeded_settings)

    assert len(chat_model.sticker_keeping_calls) == 1
    assert [
        s["note"] for s in personal_stickers(client, maya_headers(auth_verifier))
    ] == [LAUGHING_NOTE]


def test_with_stickers_off_for_the_user_nothing_is_kept(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    turn_personal_stickers_on(client, admin)
    connect_telegram(client, auth_verifier, chat_channel)
    switch_for_user(client, admin, maya_id(client, auth_verifier), "stickers", "off")
    chat(client, chat_model, telegram_sticker_update("😂", "laugh"))

    end_conversation(chat_model, clock, scheduler, seeded_settings)

    assert chat_model.sticker_keeping_calls == []
    assert personal_stickers(client, maya_headers(auth_verifier)) == []


def keep_laugh_and_seedling(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    """Have Maya send 😂, then 🌱, and keep both as her Personal Stickers."""
    chat(client, chat_model, telegram_sticker_update("😂", "laugh"))
    clock.advance(timedelta(minutes=1))
    chat(client, chat_model, telegram_sticker_update("🌱", "seedling"))
    end_conversation(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        keeping_answer((1, LAUGHING_NOTE), (2, HUG_NOTE)),
    )


def sticker_tool(call: ChatModelCall) -> ChatTool:
    """Find the sticker tool a reply call was offered."""
    [tool] = [tool for tool in call.tools if tool.name == "send_sticker"]
    return tool


def test_replies_list_the_users_own_stickers_first_as_theirs(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    [seedling, moon] = import_calm_creatures(client, admin, chat_channel)
    save_note(client, admin, seedling["id"], "Celebrating a small step forward")
    save_note(client, admin, moon["id"], "Saying good night")
    turn_personal_stickers_on(client, admin)
    connect_telegram(client, auth_verifier, chat_channel)
    keep_laugh_and_seedling(client, chat_model, clock, scheduler, seeded_settings)

    call = sticker_reply_call(
        client,
        chat_model,
        telegram_text_update("my cat knocked my coffee over lol"),
        ToolCall("send_sticker", {"number": 2}),
        "classic cat",
    )

    description = sticker_tool(call).description
    assert description.startswith(seeded_settings["sticker_tool_description"])
    listed = description.split("\n\n")[-1].splitlines()
    assert listed == [
        f"1. 🌱 (theirs) {HUG_NOTE}",
        f"2. 😂 (theirs) {LAUGHING_NOTE}",
        "3. 🌙 Saying good night",
    ]
    assert chat_channel.sent_stickers == [
        SentSticker(chat_id=TELEGRAM_CHAT_ID, file_id="file-laugh")
    ]
    kept = personal_stickers(client, maya_headers(auth_verifier))
    assert [sticker["emoji"] for sticker in kept] == ["😂", "🌱"]


def test_with_personal_stickers_off_replies_offer_only_library_stickers(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    [_, moon] = import_calm_creatures(client, admin, chat_channel)
    save_note(client, admin, moon["id"], "Saying good night")
    turn_personal_stickers_on(client, admin)
    connect_telegram(client, auth_verifier, chat_channel)
    keep_laugh_and_seedling(client, chat_model, clock, scheduler, seeded_settings)

    switch_for_everyone(client, admin, "personal_stickers", on=False)
    call = sticker_reply_call(
        client, chat_model, telegram_text_update("night!"), "sleep well"
    )

    listed = sticker_tool(call).description.split("\n\n")[-1].splitlines()
    assert listed == ["1. 🌙 Saying good night"]
    assert len(personal_stickers(client, maya_headers(auth_verifier))) == 2


def test_a_reply_can_be_just_one_of_the_users_own_stickers(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    turn_personal_stickers_on(client, owner_headers(client, auth_verifier))
    connect_telegram(client, auth_verifier, chat_channel)
    chat(client, chat_model, telegram_sticker_update("😂", "laugh"))
    end_conversation(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        keeping_answer((1, LAUGHING_NOTE)),
    )
    chat_channel.sent.clear()

    call = sticker_reply_call(
        client,
        chat_model,
        telegram_text_update("tripped over my own feet again"),
        ToolCall("send_sticker", {"number": 1}),
        ToolCall("send_sticker", {"number": 1}),
        "",
    )

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == []
    assert chat_channel.sent_stickers == [
        SentSticker(chat_id=TELEGRAM_CHAT_ID, file_id="file-laugh")
    ]
    assert "already" in call.tool_results[1]
    next_call = sticker_reply_call(
        client, chat_model, telegram_text_update("haha"), "ok"
    )
    assert next_call.history[-2].text == "[sticker: 😂]"


def test_the_crisis_reply_never_includes_one_of_the_users_own_stickers(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    turn_personal_stickers_on(client, owner_headers(client, auth_verifier))
    connect_telegram(client, auth_verifier, chat_channel)
    keep_laugh_and_seedling(client, chat_model, clock, scheduler, seeded_settings)
    chat_model.calls.clear()
    chat_model.script_safeguard("suicide_or_self_harm")

    assert send_to_webhook(client, telegram_text_update("I want to end it")) == 200

    assert chat_model.calls == []
    assert chat_channel.sent_stickers == []


def test_users_see_their_personal_stickers_with_images_and_remove_them(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    turn_personal_stickers_on(client, admin)
    connect_telegram(client, auth_verifier, chat_channel)
    keep_laugh_and_seedling(client, chat_model, clock, scheduler, seeded_settings)
    maya = maya_headers(auth_verifier)
    chat_channel.sticker_images["file-laugh"] = StickerImage(
        content=b"webp-bytes", media_type="image/webp"
    )
    [seedling, laugh] = personal_stickers(client, maya)

    image = client.get(f"/api/personal-stickers/{laugh['id']}/image", headers=maya)
    no_image = client.get(
        f"/api/personal-stickers/{seedling['id']}/image", headers=maya
    )
    others = client.get(f"/api/personal-stickers/{laugh['id']}/image", headers=admin)
    switch_for_everyone(client, admin, "personal_stickers", on=False)
    removed = client.delete(f"/api/personal-stickers/{seedling['id']}", headers=maya)
    again = client.delete(f"/api/personal-stickers/{seedling['id']}", headers=maya)

    assert image.status_code == 200
    assert image.content == b"webp-bytes"
    assert image.headers["content-type"] == "image/webp"
    assert no_image.status_code == 404
    assert others.status_code == 404
    assert removed.status_code == 204
    assert again.status_code == 404
    assert [s["emoji"] for s in personal_stickers(client, maya)] == ["😂"]


def test_users_are_told_whether_personal_stickers_works_for_them(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    user_id = maya_id(client, auth_verifier)
    maya = maya_headers(auth_verifier)

    off = client.get("/api/me", headers=maya).json()
    turn_personal_stickers_on(client, admin)
    on = client.get("/api/me", headers=maya).json()
    switch_for_user(client, admin, user_id, "stickers", "off")
    without_stickers = client.get("/api/me", headers=maya).json()

    assert off["personal_stickers_available"] is False
    assert on["personal_stickers_available"] is True
    assert without_stickers["personal_stickers_available"] is False


def test_admins_see_only_how_many_personal_stickers_a_user_has(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    turn_personal_stickers_on(client, admin)
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    before = client.get(f"/api/admin/users/{user_id}/features", headers=admin)
    keep_laugh_and_seedling(client, chat_model, clock, scheduler, seeded_settings)

    after = client.get(f"/api/admin/users/{user_id}/features", headers=admin)

    assert before.json()["personal_sticker_count"] == 0
    assert after.json()["personal_sticker_count"] == 2
    assert LAUGHING_NOTE not in after.text


def test_message_retention_keeps_personal_stickers(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    turn_personal_stickers_on(client, owner_headers(client, auth_verifier))
    connect_telegram(client, auth_verifier, chat_channel)
    keep_laugh_and_seedling(client, chat_model, clock, scheduler, seeded_settings)

    clock.advance(retention(seeded_settings) + timedelta(days=1))
    scheduler.tick()

    assert len(personal_stickers(client, maya_headers(auth_verifier))) == 2


def stored_sticker_tool_description(engine: Engine) -> str:
    """Read the stored sticker tool description."""
    with engine.connect() as connection:
        description: str = connection.execute(
            text(
                "SELECT value FROM platform_settings "
                "WHERE key = 'sticker_tool_description'"
            )
        ).scalar_one()
    return description


def test_an_existing_install_loads_the_new_sticker_tool_description(
    engine: Engine, database_url: str, seeded_settings: dict[str, Any]
) -> None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.downgrade(config, "0021")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO platform_settings (key, value, updated_at) "
                    "VALUES ('sticker_tool_description', '\"The old text.\"', now())"
                )
            )
        assert stored_sticker_tool_description(engine) == "The old text."
    finally:
        migrate(database_url)

    seed_platform_settings(engine, SEED_FILE)

    description = stored_sticker_tool_description(engine)
    assert description == seeded_settings["sticker_tool_description"]
    assert "(theirs)" in description


def test_only_sticker_messages_keep_a_sticker(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    chat(
        client,
        chat_model,
        telegram_text_update("hi"),
        telegram_sticker_update("😂", "laugh"),
    )

    with engine.connect() as connection:
        stickers = connection.execute(
            text(
                "SELECT direction, sticker->>'file_unique_id' "
                "FROM conversation_messages "
                "WHERE sticker IS NOT NULL ORDER BY position"
            )
        ).all()
    assert [tuple(row) for row in stickers] == [("incoming", "laugh")]
