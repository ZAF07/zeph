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
    ScriptedChatModel,
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
    telegram_text_update,
)

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


def test_admins_see_web_search_on_for_everyone_with_no_change_yet(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    features = features_by_key(client, admin)

    assert list(features) == ["web_search"]
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
    unavailable_note = (
        seeded_settings["reply_features_unavailable_note"]
        .replace("{features}", "Web Search")
        .replace("{dashboard_url}", DASHBOARD_URL)
    )

    on = reply_call(client, chat_model, "who wrote Meditations?")
    switch_for_everyone(client, admin, "web_search", on=False)
    off = reply_call(client, chat_model, "can you look up the news?")
    switch_for_everyone(client, admin, "web_search", on=True)
    back_on = reply_call(client, chat_model, "and now?")

    assert web_tool_names(on) == ["web_search", "fetch_page"]
    assert unavailable_note not in on.instructions
    assert web_tool_names(off) == []
    assert web_instructions not in off.instructions
    assert unavailable_note in off.instructions
    assert "Web Search" in unavailable_note
    assert "available on their account" in unavailable_note
    assert f"Dashboard: {DASHBOARD_URL}" in unavailable_note
    assert web_tool_names(back_on) == ["web_search", "fetch_page"]
    assert web_instructions in back_on.instructions
    assert unavailable_note not in back_on.instructions


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

    assert list(user_features_by_key(client, admin, user_id)) == ["web_search"]
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
