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
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_curiosities import (
    end_current_conversation,
    new_curiosity,
    stored_curiosities,
)
from tests.test_features import switch_for_everyone
from tests.test_moves import reply_to

HOSTING = "going around in circles on where to host my app"
DEPLOY_STEPS = "Did they get the app deployed on the host they picked?"


def hold_plan_steps(client: TestClient, chat_model: ScriptedChatModel) -> None:
    """Send a Message whose Understanding holds Plan steps in mind for later."""
    reply_to(
        client,
        chat_model,
        HOSTING,
        need="Advice",
        lead_move="Suggest",
        next_move="Plan steps",
        next_move_why="once they've picked a host",
    )


def unmade_next_move_seen(chat_model: ScriptedChatModel) -> str:
    """The unmade next Move the newest Curiosity keeping call was shown."""
    asked = chat_model.curiosity_keeping_calls[-1].history[0].text
    after = asked.split("A next Move Zeph had in mind but never made:\n")[1]
    return after.split("\n\n")[0]


def test_an_unmade_next_move_reaches_curiosity_keeping_and_can_become_one(
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

    hold_plan_steps(client, chat_model)
    end_current_conversation(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [new_curiosity(ask=DEPLOY_STEPS, why="Zeph meant to plan the deploy.")],
    )

    assert unmade_next_move_seen(chat_model) == (
        "Plan steps, once they've picked a host."
    )
    assert [row["question"] for row in stored_curiosities(engine)] == [DEPLOY_STEPS]


def test_a_next_move_made_in_a_later_reply_is_not_passed(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    hold_plan_steps(client, chat_model)
    reply_to(
        client,
        chat_model,
        "ok railway it is. what do I do now?",
        need="Advice",
        lead_move="Plan steps",
    )
    end_current_conversation(chat_model, clock, scheduler, seeded_settings, [])

    assert unmade_next_move_seen(chat_model) == "None."


def test_a_conversation_with_no_next_move_passes_none(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    reply_to(client, chat_model, "just saying hi", lead_move="Mirror")
    end_current_conversation(chat_model, clock, scheduler, seeded_settings, [])

    assert unmade_next_move_seen(chat_model) == "None."


def test_with_curiosities_off_no_unmade_next_move_is_passed(
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
    switch_for_everyone(
        client, owner_headers(client, auth_verifier), "curiosities", False
    )

    hold_plan_steps(client, chat_model)
    end_current_conversation(
        chat_model, clock, scheduler, seeded_settings, [new_curiosity(DEPLOY_STEPS)]
    )

    assert chat_model.curiosity_keeping_calls == []
    assert stored_curiosities(engine) == []


def test_with_user_memory_off_no_unmade_next_move_is_passed(
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
    client.patch(
        "/api/me",
        json={"user_memory_enabled": False},
        headers=auth_headers(auth_verifier, "user_maya"),
    )

    hold_plan_steps(client, chat_model)
    end_current_conversation(
        chat_model, clock, scheduler, seeded_settings, [new_curiosity(DEPLOY_STEPS)]
    )

    assert chat_model.curiosity_keeping_calls == []
    assert stored_curiosities(engine) == []


def test_a_fallback_last_understanding_still_passes_the_earlier_next_move(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    hold_plan_steps(client, chat_model)
    chat_model.script_understanding(RuntimeError("model down"))
    chat_model.script("ok")
    send_to_webhook(client, telegram_text_update("ok railway it is"))
    end_current_conversation(chat_model, clock, scheduler, seeded_settings, [])

    assert unmade_next_move_seen(chat_model) == (
        "Plan steps, once they've picked a host."
    )


def test_a_next_move_dropped_before_a_fallback_is_not_passed(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    hold_plan_steps(client, chat_model)
    reply_to(client, chat_model, "honestly I just need to vent", need="Be heard")
    chat_model.script_understanding("not a form")
    chat_model.script("ok")
    send_to_webhook(client, telegram_text_update("anyway"))
    end_current_conversation(chat_model, clock, scheduler, seeded_settings, [])

    assert unmade_next_move_seen(chat_model) == "None."


def test_understandings_store_whether_they_were_the_fallback(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    hold_plan_steps(client, chat_model)
    chat_model.script_understanding("not a form")
    chat_model.script("ok")
    send_to_webhook(client, telegram_text_update("anyway"))

    with engine.connect() as connection:
        stored = connection.execute(
            text("SELECT is_fallback FROM understandings ORDER BY position")
        ).scalars()
        assert list(stored) == [False, True]
