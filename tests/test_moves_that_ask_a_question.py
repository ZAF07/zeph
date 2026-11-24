from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import (
    connect_telegram,
    owner_headers,
)
from tests.test_curiosities import presentation_is_due
from tests.test_moves import how_to_do_it, reply_to, saved_moves

ASK_WHY = {"intensity": "high", "cause_known": False, "mood": "furious"}
RAISE_CURIOSITY = {"bring_up": [{"curiosity": 1, "how": "lead"}]}
UPSET_CAUSE_UNKNOWN = {"intensity": "medium", "cause_known": False, "mood": "upset"}


def saved_asked_why(engine: Engine) -> list[bool]:
    """Whether each saved Reply Plan asked why, oldest first."""
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT asked_why FROM reply_plans ORDER BY position")
        ).all()
    return [row.asked_why for row in rows]


def tick_asks_a_question(
    client: TestClient, admin: dict[str, str], name: str, ticked: bool = True
) -> None:
    """Tick, or untick, a Move's "asks a question" on the admin Moves API."""
    moves = client.get("/api/admin/moves", headers=admin).json()["moves"]
    [move] = [move for move in moves if move["name"] == name]
    response = client.put(
        f"/api/admin/moves/{move['id']}",
        json={**move, "asks_a_question": ticked},
        headers=admin,
    )
    assert response.status_code == 200, response.text


def offered_moves(chat_model: ScriptedChatModel) -> str:
    """The Moves the last Reply Plan was offered, one per line."""
    asked = chat_model.reply_plan_calls[-1].history[0].text
    return asked.split("Moves:\n")[1].split("\n\n")[0]


def test_a_move_that_asks_made_last_reply_is_offered_again_only_the_reply_after(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    tick_asks_a_question(client, owner_headers(client, auth_verifier), "Suggest")

    reply_to(client, chat_model, "bored tonight", lead_move="Suggest")
    reply_to(client, chat_model, "maybe a film")
    after_it = offered_moves(chat_model)
    reply_to(client, chat_model, "or a walk")
    the_reply_after = offered_moves(chat_model)

    assert "- Suggest:" not in after_it
    assert "- Plan steps:" in after_it
    assert "- Suggest:" in the_reply_after


def test_a_move_that_asks_made_as_support_is_not_offered_next_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    tick_asks_a_question(client, owner_headers(client, auth_verifier), "Mirror")

    reply_to(
        client,
        chat_model,
        "should I take the new job?",
        need="Advice",
        lead_move="Reframe",
        support_move="Mirror",
    )
    reply_to(client, chat_model, "the pay is better")

    assert "- Mirror:" not in offered_moves(chat_model)
    assert "- Reframe:" in offered_moves(chat_model)


def test_a_move_that_asks_is_dropped_when_the_reply_asks_why(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    tick_asks_a_question(client, owner_headers(client, auth_verifier), "Suggest")

    instructions = reply_to(
        client, chat_model, "ugh, today", lead_move="Suggest", understanding=ASK_WHY
    )

    assert "you don't know why" in instructions
    assert how_to_do_it("Suggest") not in instructions
    assert saved_moves(engine) == [(None, None)]


def test_a_move_that_asks_is_dropped_when_the_reply_raises_a_curiosity(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    presentation_is_due(client, chat_model, clock, scheduler, seeded_settings)
    tick_asks_a_question(client, owner_headers(client, auth_verifier), "Suggest")

    instructions = reply_to(
        client, chat_model, "hey you", lead_move="Suggest", **RAISE_CURIOSITY
    )

    assert "Ask them this in this reply" in instructions
    assert how_to_do_it("Suggest") not in instructions
    assert saved_moves(engine)[-1] == (None, None)


def test_a_dropped_lead_move_that_asks_does_not_let_the_support_move_up(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    tick_asks_a_question(client, owner_headers(client, auth_verifier), "Suggest")

    instructions = reply_to(
        client,
        chat_model,
        "my landlord won't fix the heating",
        need="Advice",
        lead_move="Suggest",
        support_move="Plan steps",
        understanding=ASK_WHY,
    )

    assert "Lead with:" not in instructions
    assert f"Support it with: Plan steps. {how_to_do_it('Plan steps')}" in (
        instructions
    )
    assert saved_moves(engine) == [(None, "Plan steps")]


def test_a_move_that_doesnt_ask_is_kept_when_the_reply_asks_why(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    instructions = reply_to(
        client, chat_model, "ugh, today", lead_move="Suggest", understanding=ASK_WHY
    )

    assert how_to_do_it("Suggest") in instructions
    assert saved_moves(engine) == [("Suggest", None)]


def test_the_reply_plan_can_ask_why_when_the_mood_does_not_stand_out(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    instructions = reply_to(
        client,
        chat_model,
        "meh, today was a lot",
        understanding=UPSET_CAUSE_UNKNOWN,
        ask_why=True,
    )

    assert "you don't know why" in instructions
    assert saved_asked_why(engine) == [True]


def test_the_reply_plan_never_asks_why_when_the_cause_is_known(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    instructions = reply_to(
        client,
        chat_model,
        "furious, my landlord kept my deposit",
        understanding={**ASK_WHY, "cause_known": True},
        ask_why=True,
    )

    assert "you don't know why" not in instructions
    assert saved_asked_why(engine) == [False]


def test_the_reply_plan_can_rule_out_asking_why_when_the_mood_stands_out(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    instructions = reply_to(
        client, chat_model, "ugh, today", understanding=ASK_WHY, ask_why=False
    )

    assert "you don't know why" not in instructions
    assert saved_asked_why(engine) == [False]


def test_the_reply_plan_prompt_leaves_out_a_check_in_when_the_reply_asks(
    seeded_settings: dict[str, Any],
) -> None:
    prompt = seeded_settings["reply_plan_prompt"]

    assert "when the reply already asks a question" in prompt
