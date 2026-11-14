from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine

from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    ScriptedChatModel,
    understanding_answer,
)
from tests.telegram_helpers import (
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_understanding import FALLBACK_NEED, saved_understandings, seeded_needs

MISSING_ID = "00000000-0000-0000-0000-000000000000"


def list_needs(client: TestClient, admin: dict[str, str]) -> list[dict[str, Any]]:
    """Fetch every Need through the admin API."""
    response = client.get("/api/admin/needs", headers=admin)
    assert response.status_code == 200, response.text
    needs: list[dict[str, Any]] = response.json()["needs"]
    return needs


def need_named(client: TestClient, admin: dict[str, str], name: str) -> dict[str, Any]:
    """Find one Need by name through the admin API."""
    return next(need for need in list_needs(client, admin) if need["name"] == name)


def add_need(
    client: TestClient, admin: dict[str, str], **overrides: Any
) -> dict[str, Any]:
    """Add a Need and return it."""
    body = {
        "name": "Celebrate",
        "when_it_fits": "They are sharing good news.",
        "how_to_reply": "Be glad with them; ask what it means to them.",
    }
    body.update(overrides)
    response = client.post("/api/admin/needs", json=body, headers=admin)
    assert response.status_code == 201, response.text
    need: dict[str, Any] = response.json()
    return need


def test_admin_sees_the_needs_in_order_with_the_fallback_marked(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    needs = list_needs(client, admin)

    assert [need["name"] for need in needs] == list(seeded_needs())
    assert [need["name"] for need in needs if need["is_fallback"]] == [FALLBACK_NEED]
    advice = need_named(client, admin, "Advice")
    assert advice["when_it_fits"] == seeded_needs()["Advice"]["when_it_fits"].strip()
    assert advice["how_to_reply"] == seeded_needs()["Advice"]["how_to_reply"].strip()


def test_only_admins_can_manage_needs(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    owner_headers(client, auth_verifier)
    maya = auth_headers(auth_verifier, "user_maya")

    assert client.get("/api/admin/needs", headers=maya).status_code == 403


def test_admin_can_add_edit_and_delete_needs(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    added = add_need(client, admin, name="  Celebrate  ")
    assert added["name"] == "Celebrate"
    assert added["is_fallback"] is False
    assert list_needs(client, admin)[-1]["id"] == added["id"]

    response = client.put(
        f"/api/admin/needs/{added['id']}",
        json={
            "name": "Share the joy",
            "when_it_fits": "Good news.",
            "how_to_reply": "Cheer them on.",
        },
        headers=admin,
    )
    assert response.status_code == 200, response.text
    edited = need_named(client, admin, "Share the joy")
    assert (edited["when_it_fits"], edited["how_to_reply"]) == (
        "Good news.",
        "Cheer them on.",
    )

    response = client.delete(f"/api/admin/needs/{added['id']}", headers=admin)
    assert response.status_code == 204
    assert "Share the joy" not in [need["name"] for need in list_needs(client, admin)]


def test_bad_needs_are_refused(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    advice_id = need_named(client, admin, "Advice")["id"]
    good = {"name": "Celebrate", "when_it_fits": "Good news.", "how_to_reply": "Cheer."}

    for bad in (
        {**good, "name": "  "},
        {**good, "when_it_fits": ""},
        {**good, "how_to_reply": " "},
        {**good, "name": "x" * 81},
        {**good, "when_it_fits": "x" * 501},
        {**good, "how_to_reply": "x" * 2001},
        {**good, "name": "be HEARD"},
    ):
        response = client.post("/api/admin/needs", json=bad, headers=admin)
        assert response.status_code == 422, bad

    response = client.put(
        f"/api/admin/needs/{advice_id}",
        json={**good, "name": "just chatting"},
        headers=admin,
    )
    assert response.status_code == 422
    assert (
        response.json()["detail"] == "There is already a Need called “just chatting”."
    )

    response = client.put(
        f"/api/admin/needs/{advice_id}",
        json={**good, "name": "ADVICE"},
        headers=admin,
    )
    assert response.status_code == 200

    assert (
        client.put(
            f"/api/admin/needs/{MISSING_ID}", json=good, headers=admin
        ).status_code
        == 404
    )
    assert (
        client.delete(f"/api/admin/needs/{MISSING_ID}", headers=admin).status_code
        == 404
    )


def test_the_fallback_need_can_be_edited_but_not_deleted(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    fallback = need_named(client, admin, FALLBACK_NEED)

    response = client.delete(f"/api/admin/needs/{fallback['id']}", headers=admin)
    assert response.status_code == 409
    assert (
        response.json()["detail"] == "The fallback Need can't be deleted, only edited."
    )

    response = client.put(
        f"/api/admin/needs/{fallback['id']}",
        json={
            "name": "Not sure yet",
            "when_it_fits": "It isn't clear.",
            "how_to_reply": "Ask one short question.",
        },
        headers=admin,
    )
    assert response.status_code == 200, response.text
    assert response.json()["is_fallback"] is True
    assert need_named(client, admin, "Not sure yet")["is_fallback"] is True


def test_admin_can_move_a_need_up_or_down(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    advice_id = need_named(client, admin, "Advice")["id"]

    response = client.post(
        f"/api/admin/needs/{advice_id}/move", json={"direction": "up"}, headers=admin
    )

    assert response.status_code == 200, response.text
    assert [need["name"] for need in response.json()["needs"]][:3] == [
        "Be heard",
        "Advice",
        "Think it through",
    ]
    first_id = list_needs(client, admin)[0]["id"]
    client.post(
        f"/api/admin/needs/{first_id}/move", json={"direction": "up"}, headers=admin
    )
    assert list_needs(client, admin)[0]["id"] == first_id
    assert (
        client.post(
            f"/api/admin/needs/{MISSING_ID}/move",
            json={"direction": "down"},
            headers=admin,
        ).status_code
        == 404
    )


def test_an_edited_how_to_reply_reaches_the_next_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    advice = need_named(client, admin, "Advice")
    client.put(
        f"/api/admin/needs/{advice['id']}",
        json={
            "name": "Advice",
            "when_it_fits": advice["when_it_fits"],
            "how_to_reply": "Give exactly one idea and stop.",
        },
        headers=admin,
    )
    chat_model.script_understanding(understanding_answer(need="Advice"))
    chat_model.script("try this")

    send_to_webhook(client, telegram_text_update("what should I do?"))

    [reply_call] = chat_model.calls
    assert "Give exactly one idea and stop." in reply_call.instructions
    assert seeded_needs()["Advice"]["how_to_reply"].strip() not in (
        reply_call.instructions
    )


def test_a_deleted_need_is_not_offered_and_saved_understandings_keep_its_name(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    chat_model.script_understanding(understanding_answer(need="Advice"))
    chat_model.script("try this")
    send_to_webhook(client, telegram_text_update("what should I do?"))

    advice_id = need_named(client, admin, "Advice")["id"]
    assert (
        client.delete(f"/api/admin/needs/{advice_id}", headers=admin).status_code == 204
    )
    chat_model.script("hmm")
    send_to_webhook(client, telegram_text_update("and now?"))

    asked = chat_model.understanding_calls[-1].history[0].text
    assert "- Advice:" not in asked
    assert "- Be heard:" in asked
    assert [saved["need"] for saved in saved_understandings(engine)][0] == "Advice"
