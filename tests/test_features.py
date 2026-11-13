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
)
from tests.telegram_helpers import (
    auth_headers,
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
