from datetime import timedelta
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import (
    MIGRATIONS_DIR,
    migrate,
    seed_platform_settings,
)
from companion.adapters.postgres.repositories import build_postgres_repositories
from tests.conftest import SEED_FILE
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakePhotoViewer,
    FakeScheduler,
    FakeTimer,
    ScriptedChatModel,
    ToolCall,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_photo_update,
)
from tests.test_check_in_sending import ONE_DAY, send_answer
from tests.test_features import (
    maya_id,
    switch_for_everyone,
    switch_for_user,
    user_features_by_key,
)
from tests.test_look_back_check_in import (
    LOOK_BACK,
    MONSTERA,
    look_back_answer,
    set_up_user_with_shared_photos,
)
from tests.test_photos import (
    CAT,
    ask_about_photo_tools,
    send_album,
    send_photo_and_reply,
)
from tests.test_post_conversation import quiet_gap
from tests.test_safeguard import use_simple_crisis_reply
from tests.test_send_photo_back import (
    CAT_NOTE,
    connect_maya_with_a_shared_cat,
    send_photo_tools,
)
from tests.test_settings_via_chat import me, reply_call
from tests.test_shared_photos import keep_the_cat, shared_photos

OFF_CASES = ["by_the_user", "by_an_admin_for_the_user", "for_everyone"]


def turn_photo_viewing_off(
    client: TestClient, auth_verifier: FakeAuthVerifier, how: str
) -> None:
    """Turn Photo Viewing off for Maya, by her own switch or an Admin's."""
    if how == "by_the_user":
        maya = auth_headers(auth_verifier, "user_maya")
        response = client.patch(
            "/api/me", json={"photo_viewing_enabled": False}, headers=maya
        )
        assert response.status_code == 200, response.text
        return
    admin = owner_headers(client, auth_verifier)
    if how == "for_everyone":
        switch_for_everyone(client, admin, "photo_viewing", on=False)
        return
    switch_for_user(
        client, admin, maya_id(client, auth_verifier), "photo_viewing", "off"
    )


def not_looked_at(seeded_settings: dict[str, Any], name: str = "photo") -> str:
    """The marker the reply reads for a photo it didn't look at."""
    return f"[{name} you didn't look at. {seeded_settings['photo_viewing_off_note']}]"


def saved_photo_messages(engine: Engine) -> list[Any]:
    """List the only User's saved messages that came with photos, oldest first."""
    repositories = build_postgres_repositories(engine)
    [user] = [overview.user for overview in repositories.users.list_overviews()]
    conversation = repositories.conversations.get_latest_for_user(user.id)
    assert conversation is not None
    return [
        message
        for message in repositories.conversations.list_messages(conversation.id)
        if message.photos
    ]


@pytest.mark.parametrize("how", OFF_CASES)
def test_with_photo_viewing_off_the_reply_gets_only_the_caption_and_the_off_note(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    seeded_settings: dict[str, Any],
    how: str,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    turn_photo_viewing_off(client, auth_verifier, how)
    photo_viewer.script(CAT)

    newest_message = send_photo_and_reply(
        client, chat_model, telegram_photo_update("meet Biscuit")
    )

    assert newest_message == f"{not_looked_at(seeded_settings)} meet Biscuit"
    assert CAT not in chat_model.calls[-1].instructions
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["what a sleepy cat"]


@pytest.mark.parametrize("how", OFF_CASES)
def test_with_photo_viewing_off_the_safeguard_still_reads_the_description(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    how: str,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    turn_photo_viewing_off(client, auth_verifier, how)
    photo_viewer.script(CAT)

    send_photo_and_reply(client, chat_model, telegram_photo_update("meet Biscuit"))

    safeguard_line = chat_model.safeguard_calls[-1].history[-1].text
    assert safeguard_line.endswith(f"[photo: {CAT}] meet Biscuit")
    assert len(photo_viewer.calls) == 1


def test_with_photo_viewing_off_the_saved_message_keeps_no_description(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    engine: Engine,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    turn_photo_viewing_off(client, auth_verifier, "by_the_user")
    photo_viewer.script(CAT)

    send_photo_and_reply(client, chat_model, telegram_photo_update("meet Biscuit"))

    [message] = saved_photo_messages(engine)
    assert message.content == f"{not_looked_at(seeded_settings)} meet Biscuit"
    [photo] = message.photos
    assert photo.viewed is False
    assert photo.description == ""
    assert photo.caption == "meet Biscuit"


def test_with_photo_viewing_off_an_album_marks_every_photo_as_not_looked_at(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    timer: FakeTimer,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    turn_photo_viewing_off(client, auth_verifier, "by_the_user")
    photo_viewer.script(CAT, CAT)

    newest_message = send_album(client, timer, chat_model, photo_count=2)

    assert newest_message == (
        f"{not_looked_at(seeded_settings, 'photo 1')} "
        f"{not_looked_at(seeded_settings, 'photo 2')} our trip"
    )
    assert CAT in chat_model.safeguard_calls[-1].history[-1].text


@pytest.mark.parametrize("how", ["by_the_user", "for_everyone"])
def test_a_worrying_photo_with_no_caption_gets_the_crisis_reply_with_photo_viewing_off(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    how: str,
) -> None:
    use_simple_crisis_reply(client, owner_headers(client, auth_verifier))
    connect_telegram(client, auth_verifier, chat_channel)
    turn_photo_viewing_off(client, auth_verifier, how)
    goodbye_note = "A handwritten note: 'I'm sorry. Goodbye.' beside a pile of pills."
    photo_viewer.script(goodbye_note)
    chat_model.script_safeguard("suicide_or_self_harm")

    assert send_to_webhook(client, telegram_photo_update()) == 200

    assert goodbye_note in chat_model.safeguard_calls[-1].history[-1].text
    [crisis_reply] = chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)
    assert crisis_reply.startswith("I'm an AI. Please reach out:")
    assert chat_model.calls == []


def test_with_photo_viewing_off_ask_about_photo_is_not_offered_even_for_earlier_photos(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    photo_viewer.script(CAT, CAT)
    send_photo_and_reply(client, chat_model, telegram_photo_update("meet Biscuit"))
    turn_photo_viewing_off(client, auth_verifier, "by_the_user")
    send_photo_and_reply(
        client, chat_model, telegram_photo_update(file_unique_id="photo-2")
    )

    call = reply_call(client, chat_model, "what colour is the pot?", "no idea")

    assert ask_about_photo_tools(call) == []


def test_shared_photos_are_not_used_while_photo_viewing_is_off_and_come_back_on(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = connect_maya_with_a_shared_cat(client, auth_verifier, chat_channel)
    client.patch("/api/me", json={"photo_viewing_enabled": False}, headers=headers)
    chat_model.script_retrieval("Shared Photos")

    off = reply_call(client, chat_model, "Miso!", "hi")

    assert CAT not in off.instructions
    assert send_photo_tools(off) == []
    assert all(
        "Shared Photos" not in call.history[-1].text
        for call in chat_model.retrieval_calls
    )
    assert [photo["description"] for photo in shared_photos(client, headers)] == [CAT]

    client.patch("/api/me", json={"photo_viewing_enabled": True}, headers=headers)
    chat_model.script_retrieval("Shared Photos")

    on = reply_call(client, chat_model, "Miso!", "hi")

    assert CAT in on.instructions
    assert len(send_photo_tools(on)) == 1


def test_with_photo_viewing_off_conversation_end_keeps_no_photos(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    photo_viewer.script(CAT)
    send_photo_and_reply(client, chat_model, telegram_photo_update("this is Miso"))
    client.patch("/api/me", json={"photo_viewing_enabled": False}, headers=headers)

    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(keep_the_cat())
    scheduler.tick()

    assert shared_photos(client, headers) == []
    assert CAT_NOTE not in str(shared_photos(client, headers))


def test_with_photo_viewing_off_check_ins_never_offer_the_look_back_kind(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_shared_photos(client, auth_verifier, chat_channel)
    client.patch("/api/me", json={"photo_viewing_enabled": False}, headers=headers)
    chat_model.script(
        look_back_answer("how's the monstera?", 1),
        send_answer("hey Maya, how's your day?"),
    )

    clock.advance(ONE_DAY)
    scheduler.tick()

    assert chat_channel.sent == []
    [line] = chat_model.calls[-1].history
    assert LOOK_BACK not in line.text
    assert MONSTERA not in line.text

    clock.advance(timedelta(minutes=5))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey Maya, how's your day?"]
    assert chat_channel.sent_photos == []


def test_the_user_switches_photo_viewing_on_the_dashboard(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    maya = auth_headers(auth_verifier, "user_maya")

    before = me(client, maya)
    response = client.patch(
        "/api/me", json={"photo_viewing_enabled": False}, headers=maya
    )

    assert before["photo_viewing_enabled"] is True
    assert before["photo_viewing_available"] is True
    assert response.status_code == 200
    assert response.json()["photo_viewing_enabled"] is False
    assert me(client, maya)["photo_viewing_enabled"] is False


def test_the_dashboard_gets_the_admin_managed_photo_viewing_explanation(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    seeded_settings: dict[str, Any],
) -> None:
    maya = auth_headers(auth_verifier, "user_maya")
    admin = owner_headers(client, auth_verifier)

    seeded = client.get("/api/platform-content", headers=maya).json()
    client.patch(
        "/api/admin/settings",
        json={"values": {"photo_viewing_explanation": "Edited explanation."}},
        headers=admin,
    )
    edited = client.get("/api/platform-content", headers=maya).json()

    assert (
        seeded["photo_viewing_explanation"]
        == (seeded_settings["photo_viewing_explanation"])
    )
    assert " ".join(seeded["photo_viewing_explanation"].split()).startswith(
        "When off, Zeph won't look at or remember your photos. Every photo is "
        "still checked for safety"
    )
    assert edited["photo_viewing_explanation"] == "Edited explanation."


@pytest.mark.parametrize("how", ["by_an_admin_for_the_user", "for_everyone"])
def test_with_the_admin_side_off_the_switch_is_not_available_and_kept(
    client: TestClient, auth_verifier: FakeAuthVerifier, how: str
) -> None:
    maya = auth_headers(auth_verifier, "user_maya")
    turn_photo_viewing_off(client, auth_verifier, how)

    response = client.patch(
        "/api/me", json={"photo_viewing_enabled": False}, headers=maya
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not available on your account"
    assert me(client, maya)["photo_viewing_enabled"] is True
    assert me(client, maya)["photo_viewing_available"] is False


def test_photo_viewing_shows_on_the_features_page_and_per_user_panel(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    user_id = maya_id(client, auth_verifier)
    maya = auth_headers(auth_verifier, "user_maya")

    features = client.get("/api/admin/features", headers=admin).json()["features"]
    client.patch("/api/me", json={"photo_viewing_enabled": False}, headers=maya)
    status = user_features_by_key(client, admin, user_id)["photo_viewing"]

    [photo_viewing] = [f for f in features if f["feature"] == "photo_viewing"]
    assert photo_viewing["name"] == "Photo Viewing"
    assert photo_viewing["on"] is True
    assert "safety" in photo_viewing["description"]
    assert status["works"] is False
    assert status["reason"] == "turned_off_by_user"


def test_turning_photo_viewing_off_and_on_in_chat(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    maya = auth_headers(auth_verifier, "user_maya")

    off = reply_call(
        client,
        chat_model,
        "stop looking at my photos",
        ToolCall("turn_photo_viewing_on_or_off", {"on": False}),
        "Okay, I won't look at your photos.",
    )
    assert me(client, maya)["photo_viewing_enabled"] is False
    assert "safety" in off.tool_results[0]
    assert "photo_viewing" in me(client, maya)["changed_in_chat"]

    reply_call(
        client,
        chat_model,
        "you can look at my photos again",
        ToolCall("turn_photo_viewing_on_or_off", {"on": True}),
        "Great, send away.",
    )
    assert me(client, maya)["photo_viewing_enabled"] is True


def test_turning_photo_viewing_in_chat_while_the_admin_side_is_off_changes_nothing(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    maya = auth_headers(auth_verifier, "user_maya")
    turn_photo_viewing_off(client, auth_verifier, "for_everyone")

    call = reply_call(
        client,
        chat_model,
        "stop looking at my photos",
        ToolCall("turn_photo_viewing_on_or_off", {"on": False}),
        "It isn't available.",
    )

    assert "isn't available" in call.tool_results[0]
    assert me(client, maya)["photo_viewing_enabled"] is True


def test_with_settings_in_chat_off_the_photo_viewing_tool_is_not_offered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    switch_for_everyone(
        client, owner_headers(client, auth_verifier), "settings_in_chat", on=False
    )

    call = reply_call(client, chat_model, "stop looking at my photos", "ok")

    assert "turn_photo_viewing_on_or_off" not in [tool.name for tool in call.tools]


def stored_setting(engine: Engine, key: str) -> Any:
    """Read one stored platform setting."""
    with engine.connect() as connection:
        return connection.execute(
            text("SELECT value FROM platform_settings WHERE key = :key"),
            {"key": key},
        ).scalar_one()


def test_an_existing_install_keeps_photo_viewing_on_and_reloads_settings_instructions(
    engine: Engine,
    database_url: str,
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    seeded_settings: dict[str, Any],
) -> None:
    maya = auth_headers(auth_verifier, "user_maya")
    me(client, maya)
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.downgrade(config, "0020")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO platform_settings (key, value, updated_at) "
                    "VALUES ('reply_settings_instructions', '\"The old one.\"', "
                    "now()) ON CONFLICT (key) DO UPDATE SET value = excluded.value"
                )
            )
    finally:
        migrate(database_url)

    seed_platform_settings(engine, SEED_FILE)

    assert me(client, maya)["photo_viewing_enabled"] is True
    instructions = stored_setting(engine, "reply_settings_instructions")
    assert instructions == seeded_settings["reply_settings_instructions"]
    assert "photos" in instructions
