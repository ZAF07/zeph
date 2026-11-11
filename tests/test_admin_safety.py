from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import seed_helplines
from tests.conftest import HELPLINES_SEED_FILE
from tests.fakes import FakeAuthVerifier, FakeChatChannel, FakeClock, ScriptedChatModel
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)


def list_helplines(client: TestClient, admin: dict[str, str]) -> dict[str, Any]:
    """Fetch the Helplines page data."""
    response = client.get("/api/admin/helplines", headers=admin)
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    return body


def helpline_names(client: TestClient, admin: dict[str, str]) -> list[str]:
    """List every country Helpline's name, in display order."""
    return [helpline["name"] for helpline in list_helplines(client, admin)["helplines"]]


def add_helpline(
    client: TestClient, admin: dict[str, str], **overrides: Any
) -> dict[str, Any]:
    """Add a Helpline and return it."""
    body = {"country": "GB", "name": "Samaritans", "number": "116 123", "hours": None}
    body.update(overrides)
    response = client.post("/api/admin/helplines", json=body, headers=admin)
    assert response.status_code == 201, response.text
    helpline: dict[str, Any] = response.json()
    return helpline


def test_singapore_helplines_and_the_international_fallback_are_seeded(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    body = list_helplines(client, admin)

    assert [
        (helpline["country"], helpline["name"], helpline["number"], helpline["hours"])
        for helpline in body["helplines"]
    ] == [
        ("SG", "Samaritans of Singapore (SOS)", "1767", "24 hours"),
        ("SG", "IMH Mental Health Helpline", "6389 2222", "24 hours"),
        ("SG", "Emergency ambulance (SCDF)", "995", "24 hours"),
    ]
    fallback = body["international_fallback"]
    assert (fallback["name"], fallback["number"]) == (
        "Find A Helpline",
        "findahelpline.com",
    )


def test_seeding_happens_only_on_first_run(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    for helpline in list_helplines(client, admin)["helplines"]:
        client.delete(f"/api/admin/helplines/{helpline['id']}", headers=admin)

    seed_helplines(engine, HELPLINES_SEED_FILE)

    assert list_helplines(client, admin)["helplines"] == []


def test_an_added_helpline_is_used_in_the_next_crisis_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    add_helpline(client, admin, hours="24/7")
    connect_telegram(client, auth_verifier, chat_channel)
    client.patch(
        "/api/me",
        json={"country": "GB"},
        headers=auth_headers(auth_verifier, "user_maya"),
    )
    chat_model.script_safeguard("suicide_or_self_harm")

    send_to_webhook(client, telegram_text_update("i can't go on"))

    [crisis_reply] = chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)
    assert "Samaritans: 116 123 (24/7)" in crisis_reply
    assert "findahelpline.com" not in crisis_reply


def test_a_new_helpline_goes_last_in_its_country(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    added = add_helpline(client, admin, country="SG", name="CHAT", number="6493 6500")

    assert added["country"] == "SG"
    assert helpline_names(client, admin)[-1] == "CHAT"


def test_helplines_can_be_edited(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    added = add_helpline(client, admin)

    response = client.put(
        f"/api/admin/helplines/{added['id']}",
        json={
            "country": "GB",
            "name": "Samaritans UK",
            "number": "116 123",
            "hours": "24 hours",
        },
        headers=admin,
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Samaritans UK"
    assert response.json()["hours"] == "24 hours"
    assert "Samaritans UK" in helpline_names(client, admin)


def test_helplines_can_be_removed(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    added = add_helpline(client, admin)

    response = client.delete(f"/api/admin/helplines/{added['id']}", headers=admin)

    assert response.status_code == 204
    assert "Samaritans" not in helpline_names(client, admin)


def test_helplines_move_up_and_down_within_their_country(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    emergency = list_helplines(client, admin)["helplines"][2]

    response = client.post(
        f"/api/admin/helplines/{emergency['id']}/move",
        json={"direction": "up"},
        headers=admin,
    )

    assert response.status_code == 200
    assert [helpline["name"] for helpline in response.json()["helplines"]] == [
        "Samaritans of Singapore (SOS)",
        "Emergency ambulance (SCDF)",
        "IMH Mental Health Helpline",
    ]
    client.post(
        f"/api/admin/helplines/{emergency['id']}/move",
        json={"direction": "down"},
        headers=admin,
    )
    assert helpline_names(client, admin)[-1] == "Emergency ambulance (SCDF)"


def test_moving_the_first_helpline_up_changes_nothing(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    before = helpline_names(client, admin)
    first = list_helplines(client, admin)["helplines"][0]

    client.post(
        f"/api/admin/helplines/{first['id']}/move",
        json={"direction": "up"},
        headers=admin,
    )

    assert helpline_names(client, admin) == before


def test_the_international_fallback_can_be_edited_and_is_used(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)

    response = client.put(
        "/api/admin/helplines/international-fallback",
        json={"name": "IASP crisis centres", "number": "iasp.info", "hours": None},
        headers=admin,
    )
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_safeguard("abuse")
    send_to_webhook(client, telegram_text_update("help me"))

    assert response.status_code == 200
    assert list_helplines(client, admin)["international_fallback"]["name"] == (
        "IASP crisis centres"
    )
    [crisis_reply] = chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)
    assert "IASP crisis centres: iasp.info" in crisis_reply


def test_the_international_fallback_cannot_be_removed(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    fallback = list_helplines(client, admin)["international_fallback"]

    response = client.delete(f"/api/admin/helplines/{fallback['id']}", headers=admin)

    assert response.status_code == 409
    assert (
        list_helplines(client, admin)["international_fallback"]["id"] == fallback["id"]
    )


@pytest.mark.parametrize(
    ("changes", "detail"),
    [
        ({"country": "Singapore"}, "Country must be a two-letter code."),
        ({"name": "  "}, "A Helpline needs a name."),
        ({"number": ""}, "A Helpline needs a number."),
    ],
)
def test_invalid_helplines_are_refused_in_plain_words(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    changes: dict[str, Any],
    detail: str,
) -> None:
    admin = owner_headers(client, auth_verifier)
    body = {"country": "GB", "name": "Samaritans", "number": "116 123", "hours": None}
    body.update(changes)

    response = client.post("/api/admin/helplines", json=body, headers=admin)

    assert response.status_code == 422
    assert response.json()["detail"] == detail


def test_editing_or_removing_an_unknown_helpline_is_not_found(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    missing = "/api/admin/helplines/00000000-0000-0000-0000-000000000000"
    body = {"country": "GB", "name": "x", "number": "1", "hours": None}

    assert client.put(missing, json=body, headers=admin).status_code == 404
    assert client.delete(missing, headers=admin).status_code == 404
    assert (
        client.post(
            f"{missing}/move", json={"direction": "up"}, headers=admin
        ).status_code
        == 404
    )


def test_the_crisis_reply_wording_is_an_admin_setting(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)

    settings = client.get("/api/admin/settings", headers=admin).json()["settings"]

    assert settings["crisis_reply"]["value"] == seeded_settings["crisis_reply"]
    assert "{helplines}" in seeded_settings["crisis_reply"]


def test_crisis_reply_wording_must_keep_the_helplines_placeholder(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"crisis_reply": "I'm an AI. Please get help."}},
        headers=admin,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "The Crisis Reply must include {helplines}, where the Helplines go."
    )


def test_safeguard_is_listed_as_a_core_service(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    services = client.get("/api/admin/core-services", headers=admin).json()["services"]

    [safeguard] = [service for service in services if service["name"] == "Safeguard"]
    assert safeguard["prompt_key"] == "safeguard_prompt"
    assert safeguard["model_key"] == "safeguard_model"
    assert services[0]["name"] == "Safeguard"


def crisis(client: TestClient, chat_model: ScriptedChatModel, risk_type: str) -> None:
    """Send a message the Safeguard flags with the given risk type."""
    chat_model.script_safeguard(risk_type)
    send_to_webhook(client, telegram_text_update("message"))


def test_safeguard_events_are_newest_first_and_filter_by_risk_type_and_period(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    crisis(client, chat_model, "abuse")
    clock.advance(timedelta(days=10))
    crisis(client, chat_model, "suicide_or_self_harm")
    clock.advance(timedelta(days=8))
    crisis(client, chat_model, "abuse")

    def risk_types(query: str) -> list[str]:
        response = client.get(f"/api/admin/safeguard-events{query}", headers=admin)
        assert response.status_code == 200
        return [event["risk_type"] for event in response.json()["events"]]

    assert risk_types("") == ["abuse", "suicide_or_self_harm", "abuse"]
    assert risk_types("?risk_type=abuse") == ["abuse", "abuse"]
    assert risk_types("?days=7") == ["abuse"]
    assert risk_types("?days=30&risk_type=suicide_or_self_harm") == [
        "suicide_or_self_harm"
    ]


def test_safeguard_events_name_the_user(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    client.patch(
        "/api/me",
        json={"name": "Maya"},
        headers=auth_headers(auth_verifier, "user_maya"),
    )
    crisis(client, chat_model, "abuse")

    [event] = client.get("/api/admin/safeguard-events", headers=admin).json()["events"]

    with engine.connect() as connection:
        maya_id = connection.execute(
            text("SELECT id FROM users WHERE auth_id = 'user_maya'")
        ).scalar_one()
    assert event["user_id"] == str(maya_id)
    assert event["user_name"] == "Maya"


def test_safeguard_event_filters_are_checked(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    assert (
        client.get(
            "/api/admin/safeguard-events?risk_type=none", headers=admin
        ).status_code
        == 422
    )
    assert (
        client.get("/api/admin/safeguard-events?days=0", headers=admin).status_code
        == 422
    )
