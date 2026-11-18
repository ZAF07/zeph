from typing import Any

import yaml
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from tests.conftest import MOVES_SEED_FILE
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    ScriptedChatModel,
    understanding_answer,
)
from tests.telegram_helpers import (
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_understanding import how_to_reply, seeded_needs

STARTER_MOVES = [
    "Calm",
    "Ground",
    "Reframe",
    "Mirror",
    "Suggest",
    "Plan steps",
    "Push",
    "Research",
    "Get curious",
]


def seeded_moves() -> dict[str, dict[str, Any]]:
    """The seeded Moves, by name."""
    moves: list[dict[str, Any]] = yaml.safe_load(MOVES_SEED_FILE.read_text())
    return {move["name"]: move for move in moves}


def how_to_do_it(move: str) -> str:
    """The seeded "how to do it" of a Move."""
    guidance: str = seeded_moves()[move]["how_to_do_it"]
    return guidance.strip()


def when_it_fits(move: str) -> str:
    """The seeded "when it fits" of a Move."""
    wording: str = seeded_moves()[move]["when_it_fits"]
    return wording.strip()


def saved_moves(engine: Engine) -> list[tuple[str | None, str | None]]:
    """The lead and supporting Moves of every saved Understanding, oldest first."""
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT lead_move, support_move FROM understandings ORDER BY position")
        ).all()
    return [(row.lead_move, row.support_move) for row in rows]


def stored_rule_outs(engine: Engine) -> dict[str, set[str]]:
    """Each stored Need's ruled-out Moves, by name."""
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT needs.name AS need, moves.name AS move FROM needs "
                "JOIN need_ruled_out_moves ON need_ruled_out_moves.need_id = needs.id "
                "JOIN moves ON moves.id = need_ruled_out_moves.move_id"
            )
        ).all()
    rule_outs: dict[str, set[str]] = {}
    for row in rows:
        rule_outs.setdefault(row.need, set()).add(row.move)
    return rule_outs


def reply_to(
    client: TestClient,
    chat_model: ScriptedChatModel,
    message: str,
    **answer: Any,
) -> str:
    """Send a Message whose Understanding answers with the given form fields.

    Returns:
        The reply call's instructions.
    """
    chat_model.script_understanding(understanding_answer(**answer))
    chat_model.script("ok")
    send_to_webhook(client, telegram_text_update(message))
    return chat_model.calls[-1].instructions


def test_a_fresh_install_has_the_starter_moves_and_rule_outs_in_order(
    engine: Engine,
) -> None:
    with engine.connect() as connection:
        names = connection.execute(
            text("SELECT name FROM moves ORDER BY sort_order")
        ).scalars()
        assert list(names) == STARTER_MOVES

    rule_outs = stored_rule_outs(engine)
    assert rule_outs["Be heard"] == {
        "Reframe",
        "Suggest",
        "Plan steps",
        "Push",
        "Research",
    }
    assert rule_outs["Think it through"] == {"Suggest", "Research"}
    assert rule_outs["Just chatting"] == {
        "Calm",
        "Ground",
        "Reframe",
        "Mirror",
        "Plan steps",
        "Push",
    }
    assert rule_outs["Get it done"] == set(STARTER_MOVES)
    assert rule_outs["Ask more"] == set(STARTER_MOVES)
    assert "Advice" not in rule_outs
    assert "Accountability" not in rule_outs


def test_a_fresh_install_has_get_curious_asking_a_question(engine: Engine) -> None:
    with engine.connect() as connection:
        asks_a_question_by_name = dict(
            connection.execute(text("SELECT name, asks_a_question FROM moves")).all()
        )

    assert asks_a_question_by_name == {
        **{name: False for name in STARTER_MOVES},
        "Get curious": True,
    }


def test_the_understanding_is_shown_the_moves_and_which_each_need_allows(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    reply_to(client, chat_model, "hello there")

    asked = chat_model.understanding_calls[-1].history[0].text
    for name, move in seeded_moves().items():
        assert f"- {name}: {move['when_it_fits'].strip()}" in asked
    allowed = asked.split("Moves each Need allows:")[1]
    assert "- Be heard: Calm, Ground, Mirror, Get curious\n" in allowed
    assert (
        "- Think it through: Calm, Ground, Reframe, Mirror, Plan steps, Push, "
        "Get curious\n"
    ) in allowed
    assert f"- Advice: {', '.join(STARTER_MOVES)}\n" in allowed
    assert "- Get it done: none\n" in allowed
    assert "- Ask more: none\n" in allowed
    assert "- Just chatting: Suggest, Research, Get curious\n" in allowed


def test_get_curious_is_offered_under_just_chatting_and_not_under_ask_more(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    chatting = reply_to(
        client,
        chat_model,
        "5 hours sleep only",
        need="Just chatting",
        lead_move="Get curious",
    )
    unclear = reply_to(
        client, chat_model, "hmm", need="Ask more", lead_move="Get curious"
    )

    assert how_to_do_it("Get curious") in chatting
    assert how_to_do_it("Get curious") not in unclear
    assert saved_moves(engine) == [("Get curious", None), (None, None)]


def test_the_picked_moves_how_to_do_it_follows_the_needs_how_to_reply(
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
        "still hunting for hosting under 20 SGD with managed postgres",
        need="Accountability",
        lead_move="Research",
        support_move="Suggest",
    )

    need_at = instructions.index(how_to_reply("Accountability").strip())
    lead_at = instructions.index(how_to_do_it("Research"))
    support_at = instructions.index(how_to_do_it("Suggest"))
    assert need_at < lead_at < support_at
    assert how_to_do_it("Push") not in instructions
    assert saved_moves(engine) == [("Research", "Suggest")]


def test_move_names_are_read_in_any_case(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    reply_to(
        client,
        chat_model,
        "I keep putting off the launch",
        need="Accountability",
        lead_move="plan steps",
    )

    assert saved_moves(engine) == [("Plan steps", None)]


def test_being_heard_is_never_given_a_move_it_rules_out(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    ruled_out = seeded_needs()["Be heard"]["ruled_out_moves"]
    assert set(ruled_out) == {"Push", "Suggest", "Plan steps", "Research", "Reframe"}

    for move in ruled_out:
        instructions = reply_to(
            client,
            chat_model,
            "my boss yelled at me again",
            need="Be heard",
            lead_move=move,
            support_move=move,
        )
        assert how_to_do_it(move) not in instructions

    assert saved_moves(engine) == [(None, None)] * len(ruled_out)


def test_an_unknown_or_odd_move_is_dropped_and_the_other_kept(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    reply_to(
        client,
        chat_model,
        "my boss yelled at me",
        need="Be heard",
        lead_move="Cheerlead",
        support_move="Mirror",
    )
    reply_to(
        client,
        chat_model,
        "he does it every week",
        need="Be heard",
        lead_move="Calm",
        support_move=["Ground"],
    )
    reply_to(
        client,
        chat_model,
        "and I just take it",
        need="Be heard",
        lead_move="Mirror",
        support_move="Mirror",
    )

    assert saved_moves(engine) == [
        ("Mirror", None),
        ("Calm", None),
        ("Mirror", None),
    ]


def test_an_unknown_need_falls_back_with_only_the_moves_the_fallback_allows(
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
        "guess what",
        need="Cheerleading",
        lead_move="Push",
    )

    assert how_to_do_it("Push") not in instructions
    assert saved_moves(engine) == [(None, None)]


def test_the_fallback_understanding_has_no_moves(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_understanding('I think they want "lead_move": "Push"')
    chat_model.script("tell me more")

    send_to_webhook(client, telegram_text_update("guess what"))

    for move in STARTER_MOVES:
        assert how_to_do_it(move) not in chat_model.calls[-1].instructions
    assert saved_moves(engine) == [(None, None)]


def test_with_web_search_off_research_is_never_offered_and_the_reply_says_so(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    client.put("/api/admin/features/web_search", json={"on": False}, headers=admin)

    instructions = reply_to(
        client,
        chat_model,
        "find me hosting under 20 SGD with managed postgres",
        need="Advice",
        lead_move="Research",
        support_move="Suggest",
    )

    asked = chat_model.understanding_calls[-1].history[0].text
    assert "- Research:" not in asked
    assert (
        "- Advice: Calm, Ground, Reframe, Mirror, Suggest, Plan steps, Push, "
        "Get curious\n"
    ) in asked
    assert how_to_do_it("Research") not in instructions
    assert how_to_do_it("Suggest") in instructions
    assert "these aren't available on this person's account" in instructions.lower()
    assert "Web Search" in instructions
    assert seeded_settings["reply_web_search_instructions"] not in instructions
    assert saved_moves(engine) == [("Suggest", None)]


def test_with_the_web_search_limit_used_up_research_is_never_offered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    client.patch(
        "/api/admin/settings",
        json={"values": {"web_search_daily_limit": 0}},
        headers=admin,
    )

    instructions = reply_to(
        client,
        chat_model,
        "find me hosting under 20 SGD with managed postgres",
        need="Advice",
        lead_move="Research",
    )

    assert "- Research:" not in chat_model.understanding_calls[-1].history[0].text
    assert how_to_do_it("Research") not in instructions
    assert seeded_settings["reply_web_search_limit_note"] in instructions
    assert saved_moves(engine) == [(None, None)]


def test_a_move_needing_a_feature_that_works_is_offered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    reply_to(
        client,
        chat_model,
        "find me hosting under 20 SGD with managed postgres",
        need="Advice",
        lead_move="Research",
    )

    assert "- Research:" in chat_model.understanding_calls[-1].history[0].text
    assert saved_moves(engine) == [("Research", None)]
