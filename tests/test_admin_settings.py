import re
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from tests.conftest import DASHBOARD_URL
from tests.fakes import (
    ChatModelCall,
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    ScriptedChatModel,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
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
    assert settings["web_search_daily_limit"]["value"] == 10
    assert settings["message_retention_days"]["value"] == 30
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
        {"web_search_daily_limit": -1},
        {"web_search_daily_limit": 1001},
        {"message_retention_days": 0},
        {"message_retention_days": 366},
        {"photo_retry_count": 6},
        {"photo_album_wait_seconds": 0},
        {"photo_album_wait_seconds": 31},
        {"photo_album_max_photos": 0},
        {"photo_album_max_photos": 11},
        {"photo_model": "not-a-model"},
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


def test_the_web_search_daily_limit_can_be_changed(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"web_search_daily_limit": 0}},
        headers=headers,
    )

    settings = response.json()["settings"]
    assert settings["web_search_daily_limit"]["value"] == 0


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
        "Photo viewing",
        "Personal Sticker keeping",
        "Check-ins",
    ]
    service = response["services"][1]
    assert service["prompt_key"] == "response_prompt"
    assert service["model_key"] == "response_model"
    assert response["model_choices"] == ["deepseek-chat", "deepseek-reasoner"]


def test_the_photo_settings_are_editable_with_their_seeded_values(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    seeded_settings: dict[str, Any],
) -> None:
    headers = owner_headers(client, auth_verifier)

    settings = client.get("/api/admin/settings", headers=headers).json()["settings"]

    assert settings["photo_model"]["value"] == "deepseek-chat"
    assert settings["photo_retry_count"]["value"] == 2
    assert settings["photo_album_wait_seconds"]["value"] == 2
    assert settings["photo_album_max_photos"]["value"] == 5
    for key in (
        "photo_description_prompt",
        "photo_not_viewed_note",
        "photo_viewing_off_note",
        "photo_viewing_explanation",
    ):
        assert settings[key]["value"] == seeded_settings[key]
    response = client.get("/api/admin/core-services", headers=headers).json()
    [photo_viewing] = [
        service
        for service in response["services"]
        if service["name"] == "Photo viewing"
    ]
    assert photo_viewing["prompt_key"] == "photo_description_prompt"
    assert photo_viewing["model_key"] == "photo_model"


def test_the_memory_notes_are_editable_with_their_seeded_values(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    seeded_settings: dict[str, Any],
) -> None:
    headers = owner_headers(client, auth_verifier)

    settings = client.get("/api/admin/settings", headers=headers).json()["settings"]

    for key in ("memory_paused_note", "memory_not_available_note"):
        assert settings[key]["value"] == seeded_settings[key]
    assert seeded_settings["memory_paused_note"].startswith("**Memory is paused.**")
    assert seeded_settings["memory_not_available_note"].startswith(
        "**Memory isn’t available on your account.**"
    )


def test_the_photo_description_prompt_asks_for_danger_signs_and_leaves_out_secrets(
    seeded_settings: dict[str, Any],
) -> None:
    prompt = seeded_settings["photo_description_prompt"].lower()

    for danger_sign in ("injuries", "pills", "weapons", "goodbye"):
        assert danger_sign in prompt
    for secret in ("card", "account", "passport", "passwords", "codes", "addresses"):
        assert secret in prompt
    assert "who they are" in prompt


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


def test_the_onboarding_unfinished_reply_can_be_edited_and_is_sent(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
    engine: Engine,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    settings = client.get("/api/admin/settings", headers=admin).json()["settings"]
    assert (
        settings["onboarding_unfinished_reply"]["value"]
        == seeded_settings["onboarding_unfinished_reply"]
    )

    saved = client.patch(
        "/api/admin/settings",
        json={
            "values": {"onboarding_unfinished_reply": "Set up first: {dashboard_url}"}
        },
        headers=admin,
    )
    assert saved.status_code == 200
    user_id = client.get(
        "/api/me", headers=auth_headers(auth_verifier, "user_maya")
    ).json()["id"]
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO connection_tokens "
                "(token, user_id, created_at, expires_at) "
                "VALUES ('OLD1-TOKN', :user_id, :now, :expires_at)"
            ),
            {
                "user_id": user_id,
                "now": clock.now(),
                "expires_at": clock.now() + timedelta(minutes=15),
            },
        )
    send_to_webhook(client, telegram_text_update("/start OLD1-TOKN"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        f"Set up first: {DASHBOARD_URL}"
    ]


def test_the_onboarding_unfinished_reply_must_keep_the_dashboard_link(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"onboarding_unfinished_reply": "Finish setting up first."}},
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "The “Finish onboarding first” reply must include {dashboard_url}, "
        "the link to the Dashboard."
    )


RESPONSE_COMPOSITION_NOTE_GROUPS = {
    "Web search": [
        "web_search_tool_description",
        "page_fetch_tool_description",
        "reply_web_search_instructions",
        "reply_web_search_limit_note",
        "web_result_source_reminder",
    ],
    "Settings in chat": [
        "reply_settings_instructions",
        "reply_delete_data_instructions",
        "reply_data_deletion_cancelled_note",
    ],
    "Memory and Knowledge": ["reply_memory_intro", "reply_knowledge_intro"],
    "Features": ["reply_features_unavailable_note"],
    "Stickers": ["sticker_tool_description"],
}


def core_services_by_name(
    client: TestClient, headers: dict[str, str]
) -> dict[str, Any]:
    """List the core services as Admins see them, by name."""
    response = client.get("/api/admin/core-services", headers=headers).json()
    return {service["name"]: service for service in response["services"]}


def test_response_composition_shows_every_reply_note_in_its_group(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    service = core_services_by_name(client, headers)["Response composition"]

    assert service["extra_prompts"] == []
    assert {
        group["name"]: [prompt["key"] for prompt in group["prompts"]]
        for group in service["extra_prompt_groups"]
    } == RESPONSE_COMPOSITION_NOTE_GROUPS
    assert list(RESPONSE_COMPOSITION_NOTE_GROUPS) == [
        group["name"] for group in service["extra_prompt_groups"]
    ]


def test_reply_notes_carry_a_hint_saying_when_they_are_used(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)
    service = core_services_by_name(client, headers)["Response composition"]

    prompts = {
        prompt["key"]: prompt
        for group in service["extra_prompt_groups"]
        for prompt in group["prompts"]
    }

    assert prompts["reply_memory_intro"]["hint"]
    assert prompts["reply_features_unavailable_note"]["hint"]
    assert prompts["web_search_tool_description"]["hint"] is None
    assert all(prompt["label"] for prompt in prompts.values())


def test_other_core_services_keep_their_extra_prompts_in_a_flat_list(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)
    services = core_services_by_name(client, headers)

    photo_viewing = services["Photo viewing"]
    memory_retrieval = services["Memory retrieval"]

    assert photo_viewing["extra_prompt_groups"] == []
    assert [prompt["key"] for prompt in photo_viewing["extra_prompts"]] == [
        "ask_about_photo_tool_description",
        "send_photo_tool_description",
    ]
    assert memory_retrieval["extra_prompt_groups"] == []
    assert [prompt["key"] for prompt in memory_retrieval["extra_prompts"]] == [
        "shared_photos_memory_description"
    ]


def test_every_reply_note_is_editable_with_its_seeded_value(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    seeded_settings: dict[str, Any],
) -> None:
    headers = owner_headers(client, auth_verifier)
    note_keys = [
        key for keys in RESPONSE_COMPOSITION_NOTE_GROUPS.values() for key in keys
    ]

    settings = client.get("/api/admin/settings", headers=headers).json()["settings"]
    saved = client.patch(
        "/api/admin/settings",
        json={"values": {key: f"{seeded_settings[key]} Edited." for key in note_keys}},
        headers=headers,
    )

    assert {key: settings[key]["value"] for key in note_keys} == {
        key: seeded_settings[key] for key in note_keys
    }
    assert saved.status_code == 200, saved.text
    assert all(
        saved.json()["settings"][key]["value"] == f"{seeded_settings[key]} Edited."
        for key in note_keys
    )


def reply_call(
    client: TestClient, chat_model: ScriptedChatModel, text: str
) -> ChatModelCall:
    """Send a Telegram message and return the reply call the model received."""
    chat_model.calls.clear()
    chat_model.script("ok")
    assert send_to_webhook(client, telegram_text_update(text)) == 200
    [call] = chat_model.calls
    return call


def test_saved_reply_notes_are_used_in_the_next_reply(
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
                "reply_web_search_instructions": "Search only when asked.",
                "web_search_tool_description": "Look things up, edited.",
                "page_fetch_tool_description": "Read one page, edited.",
                "reply_settings_instructions": "Change settings only when asked.",
            }
        },
        headers=headers,
    )

    call = reply_call(client, chat_model, "hello there")

    tool_descriptions = {tool.name: tool.description for tool in call.tools}
    assert "Search only when asked." in call.instructions
    assert "Change settings only when asked." in call.instructions
    assert tool_descriptions["web_search"] == "Look things up, edited."
    assert tool_descriptions["fetch_page"] == "Read one page, edited."


@pytest.mark.parametrize(
    ("note", "missing"),
    [
        (
            "Not available: {features}.",
            "{dashboard_url}, the link to the Dashboard",
        ),
        (
            "Turn things on at {dashboard_url}.",
            "{features}, the names of the Features that don’t work for them",
        ),
    ],
)
def test_the_features_unavailable_note_must_keep_both_placeholders(
    client: TestClient, auth_verifier: FakeAuthVerifier, note: str, missing: str
) -> None:
    headers = owner_headers(client, auth_verifier)

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"reply_features_unavailable_note": note}},
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        f"The Features unavailable note must include {missing}."
    )
