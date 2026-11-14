from datetime import timedelta
from typing import Any

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import MIGRATIONS_DIR, migrate
from tests.conftest import DASHBOARD_URL
from tests.fakes import (
    ChatModelCall,
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeEmbedder,
    FakeScheduler,
    ScriptedChatModel,
    ToolCall,
)
from tests.knowledge_helpers import upload_document
from tests.telegram_helpers import (
    OWNER_TELEGRAM_USER_ID,
    TELEGRAM_CHAT_ID,
    auth_headers,
    connect_owner_telegram,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_reply_to_sticker_update,
    telegram_sticker_update,
    telegram_text_update,
)
from tests.test_check_in_sending import send_answer, set_up_user_with_check_ins
from tests.test_knowledge import BREATH_PASSAGES
from tests.test_memory_retrieval import remember_some_things
from tests.test_post_conversation import memory_contents, quiet_gap
from tests.test_settings_via_chat import SETTINGS_TOOLS
from tests.test_settings_via_chat import reply_call as chat_reply_call
from tests.test_sticker_adding import WAVE
from tests.test_stickers import import_calm_creatures, list_stickers, save_note

WEB_TOOLS = ("web_search", "fetch_page")


def reply_call(
    client: TestClient, chat_model: ScriptedChatModel, text: str
) -> ChatModelCall:
    """Send a Telegram message and return the reply call the model received."""
    chat_model.calls.clear()
    chat_model.script("ok")
    assert send_to_webhook(client, telegram_text_update(text)) == 200
    [call] = chat_model.calls
    return call


def owner_reply_call(
    client: TestClient, chat_model: ScriptedChatModel, text: str
) -> ChatModelCall:
    """Send a Telegram message as the owner and return the reply call."""
    chat_model.calls.clear()
    chat_model.script("ok")
    update = telegram_text_update(text, OWNER_TELEGRAM_USER_ID, username="owner_tg")
    assert send_to_webhook(client, update) == 200
    [call] = chat_model.calls
    return call


def web_tool_names(call: ChatModelCall) -> list[str]:
    """List the web tools a reply call was offered."""
    return [tool.name for tool in call.tools if tool.name in WEB_TOOLS]


USER_MEMORY_IN_REPLY_NOTE = (
    "learning new things about them (you still remember and use everything "
    "you already know about them)"
)


def unavailable_note(seeded_settings: dict[str, Any], names: str) -> str:
    """Write the seeded not-available note for the given Features' names."""
    note: str = seeded_settings["reply_features_unavailable_note"]
    return note.replace("{features}", names).replace("{dashboard_url}", DASHBOARD_URL)


def switch_for_everyone(
    client: TestClient, admin: dict[str, str], feature: str, on: bool
) -> dict[str, Any]:
    """Turn a Feature on or off for everyone as an Admin."""
    response = client.put(
        f"/api/admin/features/{feature}", json={"on": on}, headers=admin
    )
    assert response.status_code == 200, response.text
    switch: dict[str, Any] = response.json()
    return switch


def features_by_key(client: TestClient, admin: dict[str, str]) -> dict[str, Any]:
    """List the Features' switches for everyone, by Feature."""
    response = client.get("/api/admin/features", headers=admin)
    assert response.status_code == 200, response.text
    return {feature["feature"]: feature for feature in response.json()["features"]}


def test_admins_see_every_feature_with_its_default_and_no_change_yet(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    features = features_by_key(client, admin)

    assert list(features) == [
        "web_search",
        "stickers",
        "knowledge",
        "check_ins",
        "user_memory",
        "settings_in_chat",
        "photo_viewing",
        "personal_stickers",
    ]
    for key, feature in features.items():
        assert feature["name"]
        assert feature["description"]
        assert feature["on"] is (key != "personal_stickers")
        assert feature["changed_by_email"] is None
        assert feature["changed_at"] is None
    assert features["stickers"]["name"] == "Stickers"
    assert features["knowledge"]["name"] == "Knowledge"
    web_search = features["web_search"]
    assert web_search["name"] == "Web Search"
    assert web_search["description"]
    assert web_search["on"] is True
    assert web_search["changed_by_email"] is None
    assert web_search["changed_at"] is None


def test_turning_web_search_off_and_on_records_who_and_when(
    client: TestClient, auth_verifier: FakeAuthVerifier, clock: FakeClock
) -> None:
    admin = owner_headers(client, auth_verifier)
    clock.advance(timedelta(hours=1))

    turned_off = switch_for_everyone(client, admin, "web_search", on=False)
    clock.advance(timedelta(hours=1))
    switch_for_everyone(client, admin, "web_search", on=True)

    assert turned_off["on"] is False
    assert turned_off["changed_by_email"] == "owner@example.com"
    assert turned_off["changed_at"] == "2026-11-11T10:00:00Z"
    web_search = features_by_key(client, admin)["web_search"]
    assert web_search["on"] is True
    assert web_search["changed_by_email"] == "owner@example.com"
    assert web_search["changed_at"] == "2026-11-11T11:00:00Z"


def test_only_admins_can_see_or_change_features(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    maya = auth_headers(auth_verifier, "user_maya")

    listed = client.get("/api/admin/features", headers=maya)
    changed = client.put(
        "/api/admin/features/web_search", json={"on": False}, headers=maya
    )

    assert listed.status_code == 403
    assert changed.status_code == 403
    assert features_by_key(client, admin)["web_search"]["on"] is True


def test_an_unknown_feature_or_value_is_refused(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    unknown = client.put(
        "/api/admin/features/telepathy", json={"on": False}, headers=admin
    )
    not_on_or_off = client.put(
        "/api/admin/features/web_search", json={"on": "off"}, headers=admin
    )

    assert unknown.status_code == 422
    assert not_on_or_off.status_code == 422


def test_with_web_search_off_replies_get_no_web_tools_and_the_unavailable_note(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    web_instructions = seeded_settings["reply_web_search_instructions"]
    note = unavailable_note(seeded_settings, "Web Search")

    on = reply_call(client, chat_model, "who wrote Meditations?")
    switch_for_everyone(client, admin, "web_search", on=False)
    off = reply_call(client, chat_model, "can you look up the news?")
    switch_for_everyone(client, admin, "web_search", on=True)
    back_on = reply_call(client, chat_model, "and now?")

    assert web_tool_names(on) == ["web_search", "fetch_page"]
    assert note not in on.instructions
    assert web_tool_names(off) == []
    assert web_instructions not in off.instructions
    assert note in off.instructions
    assert "Web Search" in note
    assert "available on their account" in note
    assert f"Dashboard: {DASHBOARD_URL}" in note
    assert web_tool_names(back_on) == ["web_search", "fetch_page"]
    assert web_instructions in back_on.instructions
    assert note not in back_on.instructions


def test_the_web_search_switch_is_no_longer_a_platform_setting(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    settings = client.get("/api/admin/settings", headers=admin).json()["settings"]
    refused = client.patch(
        "/api/admin/settings",
        json={"values": {"web_search_enabled": False}},
        headers=admin,
    )

    assert "web_search_enabled" not in settings
    assert "web_search_daily_limit" in settings
    assert refused.status_code == 422


def test_the_migration_keeps_an_existing_installs_web_search_switch(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    engine: Engine,
    database_url: str,
) -> None:
    admin = owner_headers(client, auth_verifier)
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.downgrade(config, "0014")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = 'false', "
                    "updated_at = '2026-11-01T08:00:00Z', "
                    "updated_by = (SELECT id FROM users WHERE email = :email) "
                    "WHERE key = 'web_search_enabled'"
                ),
                {"email": "owner@example.com"},
            )
    finally:
        migrate(database_url)

    web_search = features_by_key(client, admin)["web_search"]
    settings = client.get("/api/admin/settings", headers=admin).json()["settings"]

    assert web_search["on"] is False
    assert web_search["changed_by_email"] == "owner@example.com"
    assert web_search["changed_at"] == "2026-11-01T08:00:00Z"
    assert "web_search_enabled" not in settings


def maya_id(client: TestClient, auth_verifier: FakeAuthVerifier) -> str:
    """Sign Maya up if she isn't yet and return her User ID."""
    headers = auth_headers(auth_verifier, "user_maya")
    user_id: str = client.get("/api/me", headers=headers).json()["id"]
    return user_id


def switch_for_user(
    client: TestClient,
    admin: dict[str, str],
    user_id: str,
    feature: str,
    switch: str,
) -> dict[str, Any]:
    """Set a Feature to default, on or off for one User as an Admin."""
    response = client.put(
        f"/api/admin/users/{user_id}/features/{feature}",
        json={"switch": switch},
        headers=admin,
    )
    assert response.status_code == 200, response.text
    status: dict[str, Any] = response.json()
    return status


def user_features_by_key(
    client: TestClient, admin: dict[str, str], user_id: str
) -> dict[str, Any]:
    """List a User's Feature statuses, by Feature."""
    response = client.get(f"/api/admin/users/{user_id}/features", headers=admin)
    assert response.status_code == 200, response.text
    return {feature["feature"]: feature for feature in response.json()["features"]}


def user_switch_rows(engine: Engine, user_id: str) -> int:
    """Count the per-User switches stored for a User."""
    with engine.connect() as connection:
        count: int = connection.execute(
            text("SELECT count(*) FROM user_feature_switches WHERE user_id = :id"),
            {"id": user_id},
        ).scalar_one()
    return count


def test_a_user_with_no_switch_of_their_own_follows_the_switch_for_everyone(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    user_id = maya_id(client, auth_verifier)

    on = user_features_by_key(client, admin, user_id)["web_search"]
    switch_for_everyone(client, admin, "web_search", on=False)
    off = user_features_by_key(client, admin, user_id)["web_search"]

    assert list(user_features_by_key(client, admin, user_id)) == [
        "web_search",
        "stickers",
        "knowledge",
        "check_ins",
        "user_memory",
        "settings_in_chat",
        "photo_viewing",
        "personal_stickers",
    ]
    assert on["name"] == "Web Search"
    assert on["switch"] == "default"
    assert on["works"] is True
    assert on["reason"] == "on_for_everyone"
    assert on["changed_by_email"] is None
    assert on["changed_at"] is None
    assert off["switch"] == "default"
    assert off["works"] is False
    assert off["reason"] == "off_for_everyone"


def test_off_for_one_user_stops_web_search_for_that_user_only(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    clock.advance(timedelta(hours=1))

    status = switch_for_user(client, admin, user_id, "web_search", "off")
    maya_call = reply_call(client, chat_model, "look up the news?")
    owner_call = owner_reply_call(client, chat_model, "look up the news?")

    assert status["switch"] == "off"
    assert status["works"] is False
    assert status["reason"] == "off_for_user"
    assert status["changed_by_email"] == "owner@example.com"
    assert status["changed_at"] == "2026-11-11T10:00:00Z"
    assert web_tool_names(maya_call) == []
    assert "Web Search" in maya_call.instructions
    assert web_tool_names(owner_call) == ["web_search", "fetch_page"]
    assert features_by_key(client, admin)["web_search"]["on"] is True


def test_on_for_one_user_gives_them_web_search_while_it_is_off_for_everyone(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    switch_for_everyone(client, admin, "web_search", on=False)

    status = switch_for_user(client, admin, user_id, "web_search", "on")
    maya_call = reply_call(client, chat_model, "look up the news?")
    owner_call = owner_reply_call(client, chat_model, "look up the news?")

    assert status["switch"] == "on"
    assert status["works"] is True
    assert status["reason"] == "on_for_user"
    assert web_tool_names(maya_call) == ["web_search", "fetch_page"]
    assert web_tool_names(owner_call) == []


def test_setting_a_user_back_to_default_follows_everyone_and_forgets_the_change(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    switch_for_user(client, admin, user_id, "web_search", "off")

    status = switch_for_user(client, admin, user_id, "web_search", "default")
    call = reply_call(client, chat_model, "look up the news?")

    assert status["switch"] == "default"
    assert status["works"] is True
    assert status["reason"] == "on_for_everyone"
    assert status["changed_by_email"] is None
    assert status["changed_at"] is None
    assert web_tool_names(call) == ["web_search", "fetch_page"]
    assert user_switch_rows(engine, user_id) == 0


def test_only_admins_can_see_or_change_a_users_features(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    user_id = maya_id(client, auth_verifier)
    maya = auth_headers(auth_verifier, "user_maya")

    listed = client.get(f"/api/admin/users/{user_id}/features", headers=maya)
    changed = client.put(
        f"/api/admin/users/{user_id}/features/web_search",
        json={"switch": "on"},
        headers=maya,
    )

    assert listed.status_code == 403
    assert changed.status_code == 403
    assert user_features_by_key(client, admin, user_id)["web_search"]["switch"] == (
        "default"
    )


def test_an_unknown_user_feature_or_switch_is_refused(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    user_id = maya_id(client, auth_verifier)
    nobody = "00000000-0000-0000-0000-000000000000"

    no_user_list = client.get(f"/api/admin/users/{nobody}/features", headers=admin)
    no_user_set = client.put(
        f"/api/admin/users/{nobody}/features/web_search",
        json={"switch": "on"},
        headers=admin,
    )
    unknown_feature = client.put(
        f"/api/admin/users/{user_id}/features/telepathy",
        json={"switch": "on"},
        headers=admin,
    )
    unknown_switch = client.put(
        f"/api/admin/users/{user_id}/features/web_search",
        json={"switch": "maybe"},
        headers=admin,
    )

    assert no_user_list.status_code == 404
    assert no_user_set.status_code == 404
    assert unknown_feature.status_code == 422
    assert unknown_switch.status_code == 422


def test_delete_my_data_keeps_a_users_switches(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    user_id = maya_id(client, auth_verifier)
    switch_for_user(client, admin, user_id, "web_search", "off")

    response = client.delete(
        "/api/me/data", headers=auth_headers(auth_verifier, "user_maya")
    )

    assert response.status_code == 204
    assert user_features_by_key(client, admin, user_id)["web_search"]["switch"] == (
        "off"
    )


def test_delete_my_data_in_chat_keeps_a_users_switches(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    switch_for_user(client, admin, user_id, "web_search", "off")
    word = seeded_settings["data_deletion_confirmation_word"]
    chat_model.script(ToolCall("start_deleting_my_data", {}), "Reply to confirm.")
    assert send_to_webhook(client, telegram_text_update("delete my data")) == 200
    chat_channel.sent.clear()

    assert send_to_webhook(client, telegram_text_update(word)) == 200

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        seeded_settings["data_deleted_reply"]
    ]
    assert user_features_by_key(client, admin, user_id)["web_search"]["switch"] == (
        "off"
    )


def test_account_deletion_removes_a_users_switches(
    client: TestClient, auth_verifier: FakeAuthVerifier, engine: Engine
) -> None:
    admin = owner_headers(client, auth_verifier)
    user_id = maya_id(client, auth_verifier)
    switch_for_user(client, admin, user_id, "web_search", "off")

    response = client.delete(
        "/api/me", headers=auth_headers(auth_verifier, "user_maya")
    )

    assert response.status_code == 204
    assert user_switch_rows(engine, user_id) == 0


def sticker_tool_names(call: ChatModelCall) -> list[str]:
    """List the sticker tools a reply call was offered."""
    return [tool.name for tool in call.tools if tool.name == "send_sticker"]


def add_seedling_with_a_note(
    client: TestClient, admin: dict[str, str], chat_channel: FakeChatChannel
) -> None:
    """Fill the Sticker Library and give the seedling sticker a note."""
    [seedling, _] = import_calm_creatures(client, admin, chat_channel)
    save_note(client, admin, seedling["id"], "Celebrating a small step forward")


def test_with_stickers_off_replies_get_no_sticker_tool_and_send_no_sticker(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    note = unavailable_note(seeded_settings, "Stickers")
    add_seedling_with_a_note(client, admin, chat_channel)
    connect_telegram(client, auth_verifier, chat_channel)

    on = reply_call(client, chat_model, "I went for my first run!")
    switch_for_everyone(client, admin, "stickers", on=False)
    off = reply_call(client, chat_model, "and again today!")
    switch_for_everyone(client, admin, "stickers", on=True)
    back_on = reply_call(client, chat_model, "and tomorrow too")

    assert sticker_tool_names(on) == ["send_sticker"]
    assert note not in on.instructions
    assert sticker_tool_names(off) == []
    assert note in off.instructions
    assert chat_channel.sent_stickers == []
    assert sticker_tool_names(back_on) == ["send_sticker"]
    assert note not in back_on.instructions


def test_with_stickers_off_for_one_user_their_stickers_still_read_as_emoji(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    add_seedling_with_a_note(client, admin, chat_channel)
    connect_telegram(client, auth_verifier, chat_channel)
    switch_for_user(client, admin, maya_id(client, auth_verifier), "stickers", "off")
    chat_model.script("haha")

    assert send_to_webhook(client, telegram_sticker_update("😂")) == 200
    [maya_call] = chat_model.calls
    owner_call = owner_reply_call(client, chat_model, "I went for my first run!")

    assert maya_call.history[-1].text == "[sticker: 😂]"
    assert sticker_tool_names(maya_call) == []
    assert unavailable_note(seeded_settings, "Stickers") in maya_call.instructions
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["haha"]
    assert sticker_tool_names(owner_call) == ["send_sticker"]


def test_with_stickers_off_admins_still_add_stickers_in_chat(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    switch_for_everyone(client, admin, "stickers", on=False)

    update = telegram_reply_to_sticker_update(
        "add this", WAVE, telegram_user_id=OWNER_TELEGRAM_USER_ID
    )
    assert send_to_webhook(client, update) == 200

    [sticker] = list_stickers(client, admin)
    assert sticker["emoji"] == "🌊"


def upload_breath_passage(client: TestClient, admin: dict[str, str]) -> None:
    """Upload one Knowledge document about the breath."""
    response = upload_document(
        client,
        admin,
        "breath.md",
        BREATH_PASSAGES[0].encode(),
        title="On the breath",
        source="Owner’s summary",
        tradition="Mindfulness",
    )
    assert response.status_code == 201, response.text


def test_with_knowledge_off_no_passages_go_into_the_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    embedder: FakeEmbedder,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    upload_breath_passage(client, admin)
    connect_telegram(client, auth_verifier, chat_channel)
    intro = seeded_settings["reply_knowledge_intro"]
    note = unavailable_note(seeded_settings, "Knowledge")

    on = reply_call(client, chat_model, "the breath helps me")
    switch_for_everyone(client, admin, "knowledge", on=False)
    searches_before = len(embedder.queries)
    off = reply_call(client, chat_model, "the breath helps me")
    searches_while_off = len(embedder.queries) - searches_before
    switch_for_everyone(client, admin, "knowledge", on=True)
    back_on = reply_call(client, chat_model, "the breath helps me")

    assert BREATH_PASSAGES[0] in on.instructions
    assert note not in on.instructions
    assert BREATH_PASSAGES[0] not in off.instructions
    assert intro not in off.instructions
    assert searches_while_off == 0
    assert note in off.instructions
    assert BREATH_PASSAGES[0] in back_on.instructions
    assert note not in back_on.instructions


def test_with_knowledge_off_for_one_user_others_still_get_passages(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    upload_breath_passage(client, admin)
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)

    status = switch_for_user(client, admin, user_id, "knowledge", "off")
    maya_call = reply_call(client, chat_model, "the breath helps me")
    owner_call = owner_reply_call(client, chat_model, "the breath helps me")

    assert status["works"] is False
    assert status["reason"] == "off_for_user"
    assert BREATH_PASSAGES[0] not in maya_call.instructions
    assert BREATH_PASSAGES[0] in owner_call.instructions


def test_user_memory_and_check_ins_say_when_the_user_turned_them_off(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    maya = auth_headers(auth_verifier, "user_maya")

    client.patch("/api/me", json={"user_memory_enabled": False}, headers=maya)
    features = user_features_by_key(client, admin, user_id)
    call = reply_call(client, chat_model, "hello")

    assert features["user_memory"]["name"] == "User Memory"
    assert features["user_memory"]["switch"] == "default"
    assert features["user_memory"]["works"] is False
    assert features["user_memory"]["reason"] == "turned_off_by_user"
    assert features["check_ins"]["name"] == "Check-ins"
    assert features["check_ins"]["works"] is False
    assert features["check_ins"]["reason"] == "turned_off_by_user"
    assert unavailable_note(seeded_settings, "User Memory") not in call.instructions
    assert unavailable_note(seeded_settings, "Check-ins") not in call.instructions


def test_off_for_the_user_comes_before_the_users_own_switch(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    user_id = maya_id(client, auth_verifier)
    maya = auth_headers(auth_verifier, "user_maya")
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=maya)

    switch_for_everyone(client, admin, "user_memory", on=False)
    off_for_everyone = user_features_by_key(client, admin, user_id)["user_memory"]
    switch_for_user(client, admin, user_id, "user_memory", "off")
    off_for_user = user_features_by_key(client, admin, user_id)["user_memory"]

    assert off_for_everyone["reason"] == "off_for_everyone"
    assert off_for_user["reason"] == "off_for_user"


def test_with_user_memory_off_by_an_admin_memory_is_still_used_and_the_choice_is_kept(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    maya = auth_headers(auth_verifier, "user_maya")
    remember_some_things(client, chat_model, clock, scheduler, seeded_settings)
    note = unavailable_note(seeded_settings, USER_MEMORY_IN_REPLY_NOTE)

    switch_for_user(client, admin, user_id, "user_memory", "off")
    chat_model.understanding_calls.clear()
    off = reply_call(client, chat_model, "my sister called")
    understandings_while_off = list(chat_model.understanding_calls)
    me_while_off = client.get("/api/me", headers=maya).json()
    memories_while_off = memory_contents(client, maya)
    switch_for_user(client, admin, user_id, "user_memory", "default")
    back_on = reply_call(client, chat_model, "my sister called")

    assert len(understandings_while_off) == 1
    assert "Talked about work and family." in off.instructions
    assert note in off.instructions
    assert unavailable_note(seeded_settings, "User Memory") not in off.instructions
    assert me_while_off["user_memory_enabled"] is True
    assert me_while_off["user_memory_available"] is False
    assert "Sister Jo" in memories_while_off["Relationships"]
    assert "Talked about work and family." in back_on.instructions
    assert note not in back_on.instructions
    assert client.get("/api/me", headers=maya).json()["user_memory_available"]


def test_with_user_memory_off_by_an_admin_memories_can_still_be_deleted(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    maya = auth_headers(auth_verifier, "user_maya")
    remember_some_things(client, chat_model, clock, scheduler, seeded_settings)
    switch_for_everyone(client, admin, "user_memory", on=False)

    summaries = client.get("/api/conversation-summaries", headers=maya).json()
    deleted_items = client.delete("/api/memory-items", headers=maya)
    deleted_summary = client.delete(
        f"/api/conversation-summaries/{summaries['summaries'][0]['id']}",
        headers=maya,
    )

    assert deleted_items.status_code == 204
    assert deleted_summary.status_code == 204
    assert memory_contents(client, maya) == {}


def test_a_user_cant_change_a_switch_an_admin_turned_off(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    maya = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    switch_for_everyone(client, admin, "user_memory", on=False)
    switch_for_everyone(client, admin, "check_ins", on=False)

    memory_change = client.patch(
        "/api/me", json={"user_memory_enabled": False}, headers=maya
    )
    check_ins_change = client.patch(
        "/api/check-ins", json={"enabled": False}, headers=maya
    )
    name_change = client.patch("/api/me", json={"name": "May"}, headers=maya)
    check_ins = client.get("/api/check-ins", headers=maya).json()

    assert memory_change.status_code == 403
    assert check_ins_change.status_code == 403
    assert name_change.status_code == 200
    assert name_change.json()["user_memory_enabled"] is True
    assert check_ins["enabled"] is True
    assert check_ins["available"] is False


def test_turning_user_memory_on_in_chat_is_refused_when_an_admin_turned_it_off(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    maya = auth_headers(auth_verifier, "user_maya")
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=maya)
    switch_for_everyone(client, admin, "user_memory", on=False)
    call = chat_reply_call(
        client,
        chat_model,
        "please remember things again",
        ToolCall("turn_user_memory_on_or_off", {"on": True}),
        "It isn't available on your account.",
    )

    [tool_result] = call.tool_results
    assert "isn't available on their account" in tool_result
    assert client.get("/api/me", headers=maya).json()["user_memory_enabled"] is False


def test_with_user_memory_off_by_an_admin_conversation_end_keeps_nothing(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    maya = auth_headers(auth_verifier, "user_maya")
    switch_for_everyone(client, admin, "user_memory", on=False)

    chat_model.script("sounds lovely")
    send_to_webhook(client, telegram_text_update("I swim every morning"))
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    scheduler.tick()

    assert chat_model.processing_calls == []
    summaries = client.get("/api/conversation-summaries", headers=maya).json()
    assert summaries["summaries"] == []
    assert memory_contents(client, maya) == {}


def test_with_check_ins_off_by_an_admin_none_are_sent_until_it_is_back_on(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    admin = owner_headers(client, auth_verifier)
    maya = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    switch_for_user(client, admin, user_id, "check_ins", "off")
    chat_model.script(send_answer("hey Maya, how's it going?"))

    clock.advance(timedelta(days=2))
    scheduler.tick()
    sent_while_off = list(chat_channel.sent)
    calls_while_off = list(chat_model.calls)
    check_ins_while_off = client.get("/api/check-ins", headers=maya).json()
    home_while_off = client.get("/api/home", headers=maya).json()["check_ins"]
    switch_for_user(client, admin, user_id, "check_ins", "default")
    scheduler.tick()

    assert sent_while_off == []
    assert calls_while_off == []
    assert home_while_off["enabled"] is True
    assert home_while_off["available"] is False
    assert check_ins_while_off["enabled"] is True
    assert check_ins_while_off["recent"] == []
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey Maya, how's it going?"]


def test_with_user_memory_off_by_an_admin_check_ins_still_use_existing_memory(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    admin = owner_headers(client, auth_verifier)
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    switch_for_everyone(client, admin, "user_memory", on=False)
    chat_model.script(send_answer("hey Maya, how's your day going?"))

    clock.advance(timedelta(days=1))
    scheduler.tick()

    [line] = chat_model.calls[-1].history
    assert "A casual hello" in line.text
    assert "A follow-up" in line.text
    assert "New job, running on autopilot." in line.text
    assert "User Memory is off" not in line.text


def settings_tool_names(call: ChatModelCall) -> list[str]:
    """List the settings tools a reply call was offered."""
    return [tool.name for tool in call.tools if tool.name in SETTINGS_TOOLS]


def test_with_settings_in_chat_off_only_delete_my_data_is_offered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    settings_instructions = seeded_settings["reply_settings_instructions"]
    delete_only_instructions = seeded_settings["reply_delete_data_instructions"]
    note = unavailable_note(seeded_settings, "Settings in Chat")

    on = reply_call(client, chat_model, "hi")
    switch_for_everyone(client, admin, "settings_in_chat", on=False)
    off = reply_call(client, chat_model, "can you pause my check-ins for a week?")
    switch_for_everyone(client, admin, "settings_in_chat", on=True)
    back_on = reply_call(client, chat_model, "hi again")

    assert settings_tool_names(on) == SETTINGS_TOOLS
    assert settings_instructions in on.instructions
    assert note not in on.instructions
    assert settings_tool_names(off) == ["start_deleting_my_data"]
    assert settings_instructions not in off.instructions
    assert delete_only_instructions in off.instructions
    assert note in off.instructions
    assert DASHBOARD_URL in off.instructions
    assert settings_tool_names(back_on) == SETTINGS_TOOLS
    assert settings_instructions in back_on.instructions
    assert note not in back_on.instructions


def test_with_settings_in_chat_off_for_one_user_delete_my_data_still_works(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    connect_telegram(client, auth_verifier, chat_channel)
    switch_for_user(
        client, admin, maya_id(client, auth_verifier), "settings_in_chat", "off"
    )
    word = seeded_settings["data_deletion_confirmation_word"]

    owner_call = owner_reply_call(client, chat_model, "hi")
    asked = chat_reply_call(
        client,
        chat_model,
        "delete my data",
        ToolCall("start_deleting_my_data", {}),
        "Reply to confirm.",
    )
    chat_channel.sent.clear()
    assert send_to_webhook(client, telegram_text_update(word)) == 200

    assert settings_tool_names(owner_call) == SETTINGS_TOOLS
    assert settings_tool_names(asked) == ["start_deleting_my_data"]
    [asked_result] = asked.tool_results
    assert f'"{word}"' in asked_result
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        seeded_settings["data_deleted_reply"]
    ]
