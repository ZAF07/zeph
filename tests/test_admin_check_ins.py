from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient

from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import auth_headers, owner_headers
from tests.test_check_in_sending import (
    ONE_DAY,
    send_answer,
    set_up_user_with_check_ins,
    skip_answer,
)
from tests.test_onboarding import onboarding_answers

MISSING_ID = "00000000-0000-0000-0000-000000000000"


def list_kinds(client: TestClient, admin: dict[str, str]) -> list[dict[str, Any]]:
    """Fetch every Check-in Kind through the admin API."""
    response = client.get("/api/admin/check-in-kinds", headers=admin)
    assert response.status_code == 200, response.text
    kinds: list[dict[str, Any]] = response.json()["kinds"]
    return kinds


def add_kind(
    client: TestClient, admin: dict[str, str], **overrides: Any
) -> dict[str, Any]:
    """Add a Check-in Kind and return it."""
    body = {
        "name": "A gratitude nudge",
        "description": "One small thing that went well today.",
    }
    body.update(overrides)
    response = client.post("/api/admin/check-in-kinds", json=body, headers=admin)
    assert response.status_code == 201, response.text
    kind: dict[str, Any] = response.json()
    return kind


def test_admin_sees_the_check_in_kinds_in_order_with_recent_sends(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_model.script(send_answer("hey, how are you?"))
    clock.advance(ONE_DAY)
    scheduler.tick()
    admin = owner_headers(client, auth_verifier)

    kinds = list_kinds(client, admin)

    assert [(kind["name"], kind["sent_last_30_days"]) for kind in kinds] == [
        ("A casual hello", 1),
        ("A follow-up", 0),
        ("A present-moment pause", 0),
        ("A thought to reflect on", 0),
        ("A look back at a photo", 0),
    ]
    assert not any("allowed_without_user_memory" in kind for kind in kinds)
    assert kinds[0]["description"] == "Just checking how you are."


def test_admin_can_add_edit_and_remove_check_in_kinds(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    added = add_kind(client, admin, name="  A gratitude nudge  ")
    assert added["name"] == "A gratitude nudge"
    assert list_kinds(client, admin)[-1]["id"] == added["id"]

    response = client.put(
        f"/api/admin/check-in-kinds/{added['id']}",
        json={
            "name": "A small win",
            "description": "Ask about one thing that went well.",
        },
        headers=admin,
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "A small win"
    assert "allowed_without_user_memory" not in response.json()

    response = client.delete(f"/api/admin/check-in-kinds/{added['id']}", headers=admin)
    assert response.status_code == 204
    assert "A small win" not in [kind["name"] for kind in list_kinds(client, admin)]


def test_bad_check_in_kinds_are_refused(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    hello_id = list_kinds(client, admin)[0]["id"]

    for body in (
        {"name": " ", "description": "Something"},
        {"name": "Hi", "description": " "},
        {"name": "a casual HELLO", "description": "Taken name"},
    ):
        response = client.post("/api/admin/check-in-kinds", json=body, headers=admin)
        assert response.status_code == 422, body

    response = client.put(
        f"/api/admin/check-in-kinds/{hello_id}",
        json={"name": "A follow-up", "description": "Taken name"},
        headers=admin,
    )
    assert response.status_code == 422
    missing = {"name": "X", "description": "Y"}
    assert (
        client.put(
            f"/api/admin/check-in-kinds/{MISSING_ID}", json=missing, headers=admin
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/admin/check-in-kinds/{MISSING_ID}", headers=admin
        ).status_code
        == 404
    )


def test_the_check_in_log_shows_sends_and_skips_with_reasons_never_message_text(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_model.script(
        send_answer("hey, secret hello text"),
        skip_answer("They said they were heading off on retreat."),
    )
    clock.advance(ONE_DAY)
    scheduler.tick()
    clock.advance(ONE_DAY)
    scheduler.tick()
    admin = owner_headers(client, auth_verifier)

    response = client.get("/api/admin/check-ins", params={"days": 7}, headers=admin)

    assert response.status_code == 200, response.text
    assert "secret hello text" not in response.text
    entries = response.json()["entries"]
    assert [
        {key: value for key, value in entry.items() if key not in ("id", "user_id")}
        for entry in entries
    ] == [
        {
            "decided_at": "2026-11-13T09:00:00Z",
            "user_name": "Maya",
            "user_email": "user_maya@example.com",
            "outcome": "skipped",
            "kind": None,
            "skip_reason": "They said they were heading off on retreat.",
            "status": "skipped",
        },
        {
            "decided_at": "2026-11-12T09:00:00Z",
            "user_name": "Maya",
            "user_email": "user_maya@example.com",
            "outcome": "sent",
            "kind": "A casual hello",
            "skip_reason": None,
            "status": "no_reply",
        },
    ]

    clock.advance(timedelta(days=6, hours=12))
    response = client.get("/api/admin/check-ins", params={"days": 7}, headers=admin)
    assert [entry["outcome"] for entry in response.json()["entries"]] == ["skipped"]


def test_the_users_check_ins_page_lists_the_kinds_that_may_be_sent_to_them(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    maya = auth_headers(auth_verifier, "user_maya")
    client.put("/api/onboarding", json=onboarding_answers(), headers=maya)
    kinds = client.get("/api/check-ins", headers=maya).json()["kinds"]
    assert kinds[0] == {
        "name": "A casual hello",
        "description": "Just checking how you are.",
    }
    assert len(kinds) == 5

    client.patch("/api/me", json={"user_memory_enabled": False}, headers=maya)

    assert client.get("/api/check-ins", headers=maya).json()["kinds"] == kinds


def test_admin_can_set_the_ignore_threshold_and_would_you_like_fewer_message(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    settings = client.get("/api/admin/settings", headers=admin).json()["settings"]
    assert settings["check_in_ignore_threshold"]["value"] == 3
    assert (
        settings["check_in_fewer_message"]["value"]
        == seeded_settings["check_in_fewer_message"]
    )

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"check_in_ignore_threshold": 0}},
        headers=admin,
    )
    assert response.status_code == 422

    response = client.patch(
        "/api/admin/settings",
        json={
            "values": {
                "check_in_ignore_threshold": 5,
                "check_in_fewer_message": "Want fewer of these?",
            }
        },
        headers=admin,
    )
    assert response.status_code == 200
    settings = response.json()["settings"]
    assert settings["check_in_ignore_threshold"]["value"] == 5
    assert settings["check_in_fewer_message"]["value"] == "Want fewer of these?"
