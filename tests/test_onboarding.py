from typing import Any

from fastapi.testclient import TestClient

from tests.fakes import FakeAuthVerifier
from tests.telegram_helpers import auth_headers


def onboarding_answers(**overrides: Any) -> dict[str, Any]:
    """Build a valid onboarding request body, with any fields swapped out."""
    answers: dict[str, Any] = {
        "name": "Maya",
        "ai_notice_acknowledged": True,
        "onboarding_reasons": ["Being more present", "Relationships"],
        "onboarding_note": "New job, running on autopilot.",
        "user_memory_enabled": True,
        "country": "SG",
        "time_zone": "Asia/Singapore",
    }
    answers.update(overrides)
    return answers


def test_new_user_has_not_finished_onboarding(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")

    me = client.get("/api/me", headers=headers).json()

    assert me["onboarding_completed_at"] is None
    assert me["ai_notice_acknowledged_at"] is None
    assert me["user_memory_enabled"] is True
    assert me["name"] is None


def test_platform_content_comes_from_seeded_settings(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    seeded_settings: dict[str, Any],
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")

    content = client.get("/api/platform-content", headers=headers).json()

    assert content == {
        "ai_notice": seeded_settings["ai_notice"],
        "ai_notice_short": seeded_settings["ai_notice_short"],
        "user_memory_explanation": seeded_settings["user_memory_explanation"],
        "onboarding_reason_choices": seeded_settings["onboarding_reason_choices"],
        "message_retention_days": seeded_settings["message_retention_days"],
    }


def test_platform_content_needs_sign_in(client: TestClient) -> None:
    assert client.get("/api/platform-content").status_code == 401


def test_completing_onboarding_saves_every_answer(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")

    response = client.put(
        "/api/onboarding",
        json=onboarding_answers(user_memory_enabled=False),
        headers=headers,
    )

    assert response.status_code == 200
    me = client.get("/api/me", headers=headers).json()
    assert me["name"] == "Maya"
    assert me["onboarding_reasons"] == ["Being more present", "Relationships"]
    assert me["onboarding_note"] == "New job, running on autopilot."
    assert me["user_memory_enabled"] is False
    assert me["country"] == "SG"
    assert me["time_zone"] == "Asia/Singapore"
    assert me["ai_notice_acknowledged_at"] == "2026-11-11T09:00:00Z"
    assert me["onboarding_completed_at"] == "2026-11-11T09:00:00Z"
    assert response.json() == me


def test_onboarding_is_refused_without_acknowledging_the_ai_notice(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")

    response = client.put(
        "/api/onboarding",
        json=onboarding_answers(ai_notice_acknowledged=False),
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "The AI notice must be acknowledged."
    me = client.get("/api/me", headers=headers).json()
    assert me["onboarding_completed_at"] is None


def test_onboarding_requires_country_and_time_zone(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    answers = onboarding_answers()
    del answers["country"]
    del answers["time_zone"]

    response = client.put("/api/onboarding", json=answers, headers=headers)

    assert response.status_code == 422


def test_onboarding_rejects_unknown_country_and_time_zone(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")

    bad_country = client.put(
        "/api/onboarding", json=onboarding_answers(country="Singapore"), headers=headers
    )
    bad_time_zone = client.put(
        "/api/onboarding",
        json=onboarding_answers(time_zone="Mars/Base"),
        headers=headers,
    )

    assert bad_country.status_code == 422
    assert bad_country.json()["detail"] == "Country must be a two-letter code."
    assert bad_time_zone.status_code == 422
    assert bad_time_zone.json()["detail"] == "Time zone is not recognised."


def test_onboarding_requires_a_name(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")

    response = client.put(
        "/api/onboarding", json=onboarding_answers(name="   "), headers=headers
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Name is required."


def test_onboarding_reasons_and_note_are_optional(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")

    response = client.put(
        "/api/onboarding",
        json=onboarding_answers(onboarding_reasons=[], onboarding_note="  "),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["onboarding_reasons"] == []
    assert response.json()["onboarding_note"] is None


def test_preferences_can_be_changed_after_onboarding(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    client.put("/api/onboarding", json=onboarding_answers(), headers=headers)

    response = client.patch(
        "/api/me",
        json={
            "name": "May",
            "country": "GB",
            "time_zone": "Europe/London",
            "user_memory_enabled": False,
        },
        headers=headers,
    )

    assert response.status_code == 200
    me = client.get("/api/me", headers=headers).json()
    assert me["name"] == "May"
    assert me["country"] == "GB"
    assert me["time_zone"] == "Europe/London"
    assert me["user_memory_enabled"] is False
    assert me["onboarding_reasons"] == ["Being more present", "Relationships"]


def test_preferences_change_only_the_fields_sent(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    client.put("/api/onboarding", json=onboarding_answers(), headers=headers)

    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)

    me = client.get("/api/me", headers=headers).json()
    assert me["user_memory_enabled"] is False
    assert me["name"] == "Maya"
    assert me["time_zone"] == "Asia/Singapore"


def test_preferences_are_validated(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    client.put("/api/onboarding", json=onboarding_answers(), headers=headers)

    response = client.patch("/api/me", json={"time_zone": "Nowhere"}, headers=headers)

    assert response.status_code == 422
    me = client.get("/api/me", headers=headers).json()
    assert me["time_zone"] == "Asia/Singapore"


def test_one_users_onboarding_does_not_touch_another(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    maya = auth_headers(auth_verifier, "user_maya")
    sam = auth_headers(auth_verifier, "user_sam")
    client.get("/api/me", headers=sam)

    client.put("/api/onboarding", json=onboarding_answers(), headers=maya)

    assert client.get("/api/me", headers=sam).json()["onboarding_completed_at"] is None
