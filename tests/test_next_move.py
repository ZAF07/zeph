from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from tests.fakes import FakeAuthVerifier, FakeChatChannel, ScriptedChatModel
from tests.telegram_helpers import (
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_moves import reply_to


def saved_next_moves(engine: Engine) -> list[tuple[str | None, str | None]]:
    """The next Move and why of every saved Reply Plan, oldest first."""
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT next_move, next_move_why FROM reply_plans ORDER BY position")
        ).all()
    return [(row.next_move, row.next_move_why) for row in rows]


def earlier_reply_plans_seen(chat_model: ScriptedChatModel) -> str:
    """The earlier Reply Plans the newest Reply Plan call was shown."""
    asked = chat_model.reply_plan_calls[-1].history[0].text
    after = asked.split("Earlier Reply Plans in this Conversation")[1]
    return after.split("Earlier messages, across Conversations")[0]


def test_the_next_move_and_why_are_stored_and_shown_to_the_next_reply_plan(
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
        "I'm going around in circles on app hosting",
        need="Advice",
        lead_move="Suggest",
        next_move="research",
        next_move_why="once I know their budget and needs",
    )
    reply_to(
        client,
        chat_model,
        "under SGD 20 a month with managed postgres",
        need="Advice",
        lead_move="Research",
    )

    earlier = earlier_reply_plans_seen(chat_model)
    assert "Research" in earlier
    assert "once I know their budget and needs" in earlier
    assert saved_next_moves(engine) == [
        ("Research", "once I know their budget and needs"),
        (None, None),
    ]


def test_earlier_lead_and_supporting_moves_are_shown_to_later_reply_plans(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    reply_to(
        client,
        chat_model,
        "my boss yelled at me again",
        need="Be heard",
        lead_move="Calm",
        support_move="Mirror",
    )
    reply_to(client, chat_model, "ok I'm a bit calmer", need="Think it through")

    earlier = earlier_reply_plans_seen(chat_model)
    assert "Calm" in earlier
    assert "Mirror" in earlier


def test_a_next_move_the_need_rules_out_now_is_kept_for_later(
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
        "my landlord is ignoring the leak and I'm so fed up",
        need="Be heard",
        lead_move="Mirror",
        next_move="Plan steps",
        next_move_why="once they've let it out",
    )

    assert saved_next_moves(engine) == [("Plan steps", "once they've let it out")]


def test_an_unknown_or_odd_next_move_is_dropped_with_its_why(
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
        next_move="Cheerlead",
        next_move_why="when they're down",
    )
    reply_to(
        client,
        chat_model,
        "it's been three weeks",
        need="Accountability",
        next_move=["Push"],
        next_move_why="if they dodge again",
    )
    reply_to(
        client,
        chat_model,
        "I'll do it tomorrow maybe",
        need="Accountability",
        next_move="Push",
        next_move_why=["if they dodge again"],
    )

    assert saved_next_moves(engine) == [(None, None), (None, None), ("Push", None)]


def test_a_next_move_that_cant_be_made_for_the_user_is_dropped(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    client.put("/api/admin/features/web_search", json={"on": False}, headers=admin)

    reply_to(
        client,
        chat_model,
        "I'm going around in circles on app hosting",
        need="Advice",
        lead_move="Suggest",
        next_move="Research",
        next_move_why="once I know their budget",
    )

    assert saved_next_moves(engine) == [(None, None)]


def test_the_fallback_reply_plan_holds_no_next_move(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_reply_plan('maybe "next_move": "Push" later')
    chat_model.script("tell me more")

    send_to_webhook(client, telegram_text_update("guess what"))

    assert saved_next_moves(engine) == [(None, None)]
