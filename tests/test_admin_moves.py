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
from tests.test_admin_needs import MISSING_ID, need_named
from tests.test_moves import STARTER_MOVES, saved_moves, seeded_moves, stored_rule_outs


def list_moves(client: TestClient, admin: dict[str, str]) -> list[dict[str, Any]]:
    """Fetch every Move through the admin API."""
    response = client.get("/api/admin/moves", headers=admin)
    assert response.status_code == 200, response.text
    moves: list[dict[str, Any]] = response.json()["moves"]
    return moves


def move_named(client: TestClient, admin: dict[str, str], name: str) -> dict[str, Any]:
    """Find one Move by name through the admin API."""
    return next(move for move in list_moves(client, admin) if move["name"] == name)


def add_move(
    client: TestClient, admin: dict[str, str], **overrides: Any
) -> dict[str, Any]:
    """Add a Move and return it."""
    body = {
        "name": "Celebrate",
        "when_it_fits": "They are sharing good news.",
        "how_to_do_it": "Be glad with them and name what they did well.",
        "needed_feature": None,
    }
    body.update(overrides)
    response = client.post("/api/admin/moves", json=body, headers=admin)
    assert response.status_code == 201, response.text
    move: dict[str, Any] = response.json()
    return move


def need_body(need: dict[str, Any], ruled_out_move_ids: list[str]) -> dict[str, Any]:
    """A Need's saved text with new ruled-out Moves, as an edit sends it."""
    return {
        "name": need["name"],
        "when_it_fits": need["when_it_fits"],
        "how_to_reply": need["how_to_reply"],
        "ruled_out_move_ids": ruled_out_move_ids,
    }


def test_admin_sees_the_moves_in_order_with_the_feature_each_needs(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    moves = list_moves(client, admin)

    assert [move["name"] for move in moves] == STARTER_MOVES
    assert {move["name"]: move["needed_feature"] for move in moves} == {
        **{name: None for name in STARTER_MOVES},
        "Research": "web_search",
    }
    calm = move_named(client, admin, "Calm")
    assert calm["when_it_fits"] == seeded_moves()["Calm"]["when_it_fits"].strip()
    assert calm["how_to_do_it"] == seeded_moves()["Calm"]["how_to_do_it"].strip()


def test_only_admins_can_manage_moves(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    owner_headers(client, auth_verifier)
    maya = auth_headers(auth_verifier, "user_maya")

    assert client.get("/api/admin/moves", headers=maya).status_code == 403


def test_admin_can_add_edit_and_delete_moves(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    added = add_move(client, admin, name="  Celebrate  ")
    assert added["name"] == "Celebrate"
    assert added["needed_feature"] is None
    assert list_moves(client, admin)[-1]["id"] == added["id"]

    response = client.put(
        f"/api/admin/moves/{added['id']}",
        json={
            "name": "Cheer on",
            "when_it_fits": "Good news.",
            "how_to_do_it": "Cheer them on.",
            "needed_feature": "web_search",
        },
        headers=admin,
    )
    assert response.status_code == 200, response.text
    edited = move_named(client, admin, "Cheer on")
    assert (
        edited["when_it_fits"],
        edited["how_to_do_it"],
        edited["needed_feature"],
    ) == ("Good news.", "Cheer them on.", "web_search")

    response = client.delete(f"/api/admin/moves/{added['id']}", headers=admin)
    assert response.status_code == 204
    assert "Cheer on" not in [move["name"] for move in list_moves(client, admin)]


def test_bad_moves_are_refused(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    calm_id = move_named(client, admin, "Calm")["id"]
    good = {
        "name": "Celebrate",
        "when_it_fits": "Good news.",
        "how_to_do_it": "Cheer.",
        "needed_feature": None,
    }

    for bad in (
        {**good, "name": "  "},
        {**good, "when_it_fits": ""},
        {**good, "how_to_do_it": " "},
        {**good, "name": "x" * 81},
        {**good, "when_it_fits": "x" * 501},
        {**good, "how_to_do_it": "x" * 2001},
        {**good, "needed_feature": "flying"},
    ):
        response = client.post("/api/admin/moves", json=bad, headers=admin)
        assert response.status_code == 422, bad

    response = client.post(
        "/api/admin/moves", json={**good, "name": "plan STEPS"}, headers=admin
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "There is already a Move called “plan STEPS”."

    response = client.put(
        f"/api/admin/moves/{calm_id}", json={**good, "name": "push"}, headers=admin
    )
    assert response.status_code == 409

    response = client.put(
        f"/api/admin/moves/{calm_id}", json={**good, "name": "CALM"}, headers=admin
    )
    assert response.status_code == 200

    for response in (
        client.put(f"/api/admin/moves/{MISSING_ID}", json=good, headers=admin),
        client.delete(f"/api/admin/moves/{MISSING_ID}", headers=admin),
        client.post(
            f"/api/admin/moves/{MISSING_ID}/move",
            json={"direction": "down"},
            headers=admin,
        ),
    ):
        assert response.status_code == 404
        assert response.json()["detail"] == "No such Move"


def test_admin_can_move_a_move_up_or_down(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    ground_id = move_named(client, admin, "Ground")["id"]

    response = client.post(
        f"/api/admin/moves/{ground_id}/move", json={"direction": "up"}, headers=admin
    )

    assert response.status_code == 200, response.text
    assert [move["name"] for move in response.json()["moves"]][:3] == [
        "Ground",
        "Calm",
        "Reframe",
    ]
    last_id = list_moves(client, admin)[-1]["id"]
    client.post(
        f"/api/admin/moves/{last_id}/move", json={"direction": "down"}, headers=admin
    )
    assert list_moves(client, admin)[-1]["id"] == last_id


def test_deleting_a_move_clears_it_from_every_needs_rule_outs(
    client: TestClient, auth_verifier: FakeAuthVerifier, engine: Engine
) -> None:
    admin = owner_headers(client, auth_verifier)
    push_id = move_named(client, admin, "Push")["id"]

    client.delete(f"/api/admin/moves/{push_id}", headers=admin)

    assert all("Push" not in moves for moves in stored_rule_outs(engine).values())
    be_heard = need_named(client, admin, "Be heard")
    assert push_id not in be_heard["ruled_out_move_ids"]
    assert len(be_heard["ruled_out_move_ids"]) == 4


def test_a_needs_ruled_out_moves_are_shown_and_saved(
    client: TestClient, auth_verifier: FakeAuthVerifier, engine: Engine
) -> None:
    admin = owner_headers(client, auth_verifier)
    ids = {move["name"]: move["id"] for move in list_moves(client, admin)}
    advice = need_named(client, admin, "Advice")
    assert advice["ruled_out_move_ids"] == []

    response = client.put(
        f"/api/admin/needs/{advice['id']}",
        json=need_body(advice, [ids["Calm"], ids["Push"]]),
        headers=admin,
    )

    assert response.status_code == 200, response.text
    assert set(response.json()["ruled_out_move_ids"]) == {ids["Calm"], ids["Push"]}
    assert stored_rule_outs(engine)["Advice"] == {"Calm", "Push"}

    response = client.post(
        "/api/admin/needs",
        json={
            "name": "Celebrate",
            "when_it_fits": "Good news.",
            "how_to_reply": "Be glad with them.",
            "ruled_out_move_ids": [ids["Research"]],
        },
        headers=admin,
    )
    assert response.status_code == 201, response.text
    assert stored_rule_outs(engine)["Celebrate"] == {"Research"}

    response = client.put(
        f"/api/admin/needs/{advice['id']}",
        json=need_body(advice, [MISSING_ID]),
        headers=admin,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "No such Move"
    assert stored_rule_outs(engine)["Advice"] == {"Calm", "Push"}


def test_a_changed_rule_out_changes_the_moves_the_next_understanding_is_shown(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    advice = need_named(client, admin, "Advice")
    client.put(
        f"/api/admin/needs/{advice['id']}",
        json=need_body(advice, [move_named(client, admin, "Push")["id"]]),
        headers=admin,
    )
    chat_model.script_understanding(
        understanding_answer(need="Advice", lead_move="Push")
    )
    chat_model.script("ok")

    send_to_webhook(client, telegram_text_update("what should I do?"))

    asked = chat_model.understanding_calls[-1].history[0].text
    assert "- Advice: Calm, Ground, Reframe, Mirror, Suggest, Plan steps, Research" in (
        asked
    )
    assert saved_moves(engine) == [(None, None)]


def test_an_edited_move_reaches_the_next_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    suggest = move_named(client, admin, "Suggest")
    client.put(
        f"/api/admin/moves/{suggest['id']}",
        json={
            "name": "Offer ideas",
            "when_it_fits": "They want ideas.",
            "how_to_do_it": "Give exactly two ideas and stop.",
            "needed_feature": None,
        },
        headers=admin,
    )
    chat_model.script_understanding(
        understanding_answer(need="Advice", lead_move="Offer ideas")
    )
    chat_model.script("try this")

    send_to_webhook(client, telegram_text_update("what should I do?"))

    assert "- Offer ideas: They want ideas." in (
        chat_model.understanding_calls[-1].history[0].text
    )
    reply_call = chat_model.calls[-1]
    assert "Lead with: Offer ideas. Give exactly two ideas and stop." in (
        reply_call.instructions
    )


def test_a_deleted_move_is_not_offered_and_saved_understandings_keep_its_name(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    chat_model.script_understanding(
        understanding_answer(need="Advice", lead_move="Suggest")
    )
    chat_model.script("try this")
    send_to_webhook(client, telegram_text_update("what should I do?"))

    suggest_id = move_named(client, admin, "Suggest")["id"]
    client.delete(f"/api/admin/moves/{suggest_id}", headers=admin)
    chat_model.script_understanding(
        understanding_answer(need="Advice", lead_move="Suggest")
    )
    chat_model.script("hmm")
    send_to_webhook(client, telegram_text_update("and now?"))

    assert "- Suggest:" not in chat_model.understanding_calls[-1].history[0].text
    assert saved_moves(engine) == [("Suggest", None), (None, None)]
