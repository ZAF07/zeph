import re
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.fakes import FakeAuthVerifier, FakeChatChannel, FakeClock, ScriptedChatModel
from tests.telegram_helpers import (
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)


def test_admin_sees_each_editable_setting_with_its_seeded_value(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    seeded_settings: dict[str, Any],
) -> None:
    headers = owner_headers(client, auth_verifier)

    settings = client.get("/api/admin/settings", headers=headers).json()["settings"]

    assert settings["persona"]["value"] == seeded_settings["persona"]
    assert settings["response_model"]["value"] == seeded_settings["response_model"]
    assert settings["conversation_quiet_gap_minutes"]["value"] == 60
    assert settings["web_search_enabled"]["value"] is True
    assert settings["web_search_daily_limit"]["value"] == 10
    assert settings["persona"]["updated_by"] is None
    assert settings["ai_notice_short"]["value"] == seeded_settings["ai_notice_short"]
    assert "welcome_message" not in settings


def test_saved_settings_record_when_and_by_whom(
    client: TestClient, auth_verifier: FakeAuthVerifier, clock: FakeClock
) -> None:
    headers = owner_headers(client, auth_verifier)
    clock.advance(timedelta(hours=1))

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"persona": "You are Zeph, edited."}},
        headers=headers,
    )

    assert response.status_code == 200
    persona = response.json()["settings"]["persona"]
    assert persona == {
        "value": "You are Zeph, edited.",
        "updated_at": "2026-11-11T10:00:00Z",
        "updated_by": "owner@example.com",
    }
    reloaded = client.get("/api/admin/settings", headers=headers).json()
    assert reloaded["settings"]["persona"] == persona


def test_persona_prompt_and_model_changes_apply_to_the_next_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    client.patch(
        "/api/admin/settings",
        json={
            "values": {
                "persona": "You are Zeph, retuned by an Admin.",
                "response_prompt": "Reply in one short line.",
                "response_model": "deepseek-reasoner",
            }
        },
        headers=headers,
    )
    chat_model.script("hey")

    send_to_webhook(client, telegram_text_update("hi"))

    [call] = chat_model.calls
    assert call.model == "deepseek-reasoner"
    assert "You are Zeph, retuned by an Admin." in call.instructions
    assert "Reply in one short line." in call.instructions


def test_a_shorter_quiet_gap_starts_a_new_conversation_sooner(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    headers = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    client.patch(
        "/api/admin/settings",
        json={"values": {"conversation_quiet_gap_minutes": 10}},
        headers=headers,
    )
    chat_model.script("one", "two")

    send_to_webhook(client, telegram_text_update("first"))
    clock.advance(timedelta(minutes=11))
    send_to_webhook(client, telegram_text_update("second"))

    users = client.get("/api/admin/users", headers=headers).json()["users"]
    [maya] = [user for user in users if user["email"] == "user_maya@example.com"]
    assert maya["conversation_count"] == 2
    assert chat_model.calls[1].history[-1].text == "second"
    assert len(chat_model.calls[1].history) == 1


@pytest.mark.parametrize(
    "values",
    [
        {"welcome_message": "Not editable here."},
        {"no_such_setting": "x"},
        {"persona": "   "},
        {"persona": 42},
        {"conversation_quiet_gap_minutes": 0},
        {"conversation_quiet_gap_minutes": "60"},
        {"conversation_quiet_gap_minutes": True},
        {"response_model": "not-a-model"},
        {"web_search_enabled": "yes"},
        {"web_search_enabled": 1},
        {"web_search_daily_limit": -1},
        {"web_search_daily_limit": 1001},
    ],
)
def test_invalid_setting_changes_are_refused(
    client: TestClient, auth_verifier: FakeAuthVerifier, values: dict[str, Any]
) -> None:
    headers = owner_headers(client, auth_verifier)

    response = client.patch(
        "/api/admin/settings", json={"values": values}, headers=headers
    )

    assert response.status_code == 422


def test_a_refused_value_is_explained_in_plain_words(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"conversation_quiet_gap_minutes": 2}},
        headers=headers,
    )

    assert response.json()["detail"] == (
        "The Conversation quiet gap must be a whole number from 5 to 1440."
    )


def test_web_search_can_be_turned_off_and_its_limit_changed(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"web_search_enabled": False, "web_search_daily_limit": 0}},
        headers=headers,
    )

    settings = response.json()["settings"]
    assert settings["web_search_enabled"]["value"] is False
    assert settings["web_search_daily_limit"]["value"] == 0
    refused = client.patch(
        "/api/admin/settings",
        json={"values": {"web_search_enabled": "off"}},
        headers=headers,
    )
    assert refused.json()["detail"] == "Web search must be on or off."


def test_one_invalid_value_means_nothing_is_saved(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    seeded_settings: dict[str, Any],
) -> None:
    headers = owner_headers(client, auth_verifier)

    client.patch(
        "/api/admin/settings",
        json={"values": {"persona": "New persona", "response_model": "nope"}},
        headers=headers,
    )

    settings = client.get("/api/admin/settings", headers=headers).json()["settings"]
    assert settings["persona"]["value"] == seeded_settings["persona"]


def test_core_services_list_their_prompt_and_model_settings(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    response = client.get("/api/admin/core-services", headers=headers).json()

    assert [service["name"] for service in response["services"]] == [
        "Safeguard",
        "Response composition",
        "Post-conversation processing",
        "Memory retrieval",
        "Check-ins",
    ]
    service = response["services"][1]
    assert service["prompt_key"] == "response_prompt"
    assert service["model_key"] == "response_model"
    assert response["model_choices"] == ["deepseek-chat", "deepseek-reasoner"]


def test_every_admin_endpoint_refuses_users_who_are_not_admins(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    maya = auth_headers(auth_verifier, "user_maya")
    paths = client.get("/openapi.json").json()["paths"]
    admin_routes = [
        (method.upper(), path)
        for path, operations in paths.items()
        if path.startswith("/api/admin")
        for method in operations
    ]

    assert len(admin_routes) >= 5
    for method, path in admin_routes:
        concrete_path = re.sub(
            r"\{[^}]+\}", "00000000-0000-0000-0000-000000000000", path
        )
        response = client.request(method, concrete_path, headers=maya, json={})
        assert response.status_code == 403, (method, path)
