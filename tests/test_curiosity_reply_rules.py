from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate, seed_platform_settings
from companion.core.curiosities import (
    ASK_WHY_FIRST_NOTE,
    MORE_THAN_ONE_QUESTION_NOTE,
)
from companion.main import SEED_FILE
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
    reply_plan_answer,
    understanding_answer,
)
from tests.telegram_helpers import connect_telegram, owner_headers
from tests.test_curiosities import (
    PRESENTATION,
    end_conversation,
    new_curiosity,
    presentation_is_due,
    reply_plan_sees,
    stored_curiosities,
)
from tests.test_model_call_log import newest_call
from tests.test_moves_migration import downgrade_to
from tests.test_needs_treat_curiosities import DESK, RAISE_FIRST, reply_to
from tests.test_older_summaries import set_settings
from tests.test_understanding import saved_reply_plans

RAISE_BOTH = [{"curiosity": 1, "how": "lead"}, {"curiosity": 2, "how": "weave"}]


def two_curiosities_are_due(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    """Save the presentation and desk Curiosities and move on to when both are due."""
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "work is a lot",
        [new_curiosity(), new_curiosity(ask=DESK, not_before=None)],
    )
    clock.advance(timedelta(days=2))


def test_both_rules_start_at_todays_behaviour_with_hints(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
) -> None:
    headers = owner_headers(client, auth_verifier)

    settings = client.get("/api/admin/settings", headers=headers).json()["settings"]

    per_reply = settings["curiosities_per_reply"]
    held = settings["curiosity_held_when_asking_why"]
    assert per_reply["value"] == 1
    assert "Most Curiosities raised per Conversation" in per_reply["hint"]
    assert held["value"] is True
    assert held["hint"]


def test_an_existing_install_gets_both_rules_at_their_starting_values(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0083")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM platform_settings WHERE key IN "
                    "('curiosities_per_reply', 'curiosity_held_when_asking_why')"
                )
            )
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = '\"An edited prompt.\"' "
                    "WHERE key = 'reply_plan_prompt'"
                )
            )
    finally:
        migrate(database_url)
        seed_platform_settings(engine, SEED_FILE)

    with engine.connect() as connection:
        stored = dict(
            connection.execute(
                text(
                    "SELECT key, value FROM platform_settings WHERE key IN "
                    "('curiosities_per_reply', 'curiosity_held_when_asking_why', "
                    "'reply_plan_prompt')"
                )
            ).all()
        )
    assert stored["curiosities_per_reply"] == 1
    assert stored["curiosity_held_when_asking_why"] is True
    assert stored["reply_plan_prompt"] != "An edited prompt."


def test_at_two_per_reply_a_reply_asks_two_curiosities(
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
    two_curiosities_are_due(client, chat_model, clock, scheduler, seeded_settings)
    set_settings(
        client,
        auth_verifier,
        {"curiosities_per_conversation": 2, "curiosities_per_reply": 2},
    )

    instructions = reply_to(
        client, chat_model, need="Think it through", bring_up=RAISE_BOTH
    )

    shape = newest_call(client, owner_headers(client, auth_verifier), "reply_plan")[
        "reply_plan_shape"
    ]
    assert PRESENTATION in instructions
    assert DESK in instructions
    assert MORE_THAN_ONE_QUESTION_NOTE in instructions
    assert [row["state"] for row in stored_curiosities(engine)] == ["raised"] * 2
    assert (shape["curiosities_offered"], shape["curiosity_asked"]) == (2, True)


def test_the_per_conversation_limit_still_caps_the_per_reply_number(
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
    two_curiosities_are_due(client, chat_model, clock, scheduler, seeded_settings)
    set_settings(client, auth_verifier, {"curiosities_per_reply": 2})

    instructions = reply_to(
        client, chat_model, need="Think it through", bring_up=RAISE_BOTH
    )

    assert PRESENTATION in instructions
    assert DESK not in instructions
    assert MORE_THAN_ONE_QUESTION_NOTE not in instructions
    assert [row["state"] for row in stored_curiosities(engine)] == [
        "raised",
        "waiting",
    ]


def test_the_reply_plan_is_told_the_per_reply_number_from_the_setting(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    two_curiosities_are_due(client, chat_model, clock, scheduler, seeded_settings)
    set_settings(
        client,
        auth_verifier,
        {"curiosities_per_conversation": 3, "curiosities_per_reply": 2},
    )
    chat_model.script_reply_plan(reply_plan_answer(need="Think it through"))

    seen = reply_plan_sees(client, chat_model, "hey you")

    prompt = " ".join(seeded_settings["reply_plan_prompt"].split())
    assert "at most 2 in this reply" in seen
    assert "At most one per reply" not in prompt


def test_with_holding_off_a_reply_that_asks_why_also_asks_the_curiosity(
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
    set_settings(client, auth_verifier, {"curiosity_held_when_asking_why": False})
    chat_model.script_understanding(understanding_answer(cause_known=False))

    instructions = reply_to(
        client,
        chat_model,
        need="Think it through",
        bring_up=RAISE_FIRST,
        ask_why=True,
    )

    form = saved_reply_plans(engine)[-1]["form"]
    shape = newest_call(client, owner_headers(client, auth_verifier), "reply_plan")[
        "reply_plan_shape"
    ]
    assert seeded_settings["reply_ask_why_note"].strip() in instructions
    assert PRESENTATION in instructions
    assert ASK_WHY_FIRST_NOTE in instructions
    assert MORE_THAN_ONE_QUESTION_NOTE in instructions
    assert form["curiosity_not_asked_why"] == ""
    assert stored_curiosities(engine)[0]["state"] == "raised"
    assert (shape["curiosities_offered"], shape["curiosity_asked"]) == (1, True)


def test_with_holding_on_the_curiosity_is_dropped_and_stays_due(
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
    chat_model.script_understanding(understanding_answer(cause_known=False))
    reply_to(
        client,
        chat_model,
        need="Think it through",
        bring_up=RAISE_FIRST,
        ask_why=True,
    )
    shape = newest_call(client, owner_headers(client, auth_verifier), "reply_plan")[
        "reply_plan_shape"
    ]
    state_after_asking_why = stored_curiosities(engine)[0]["state"]

    next_instructions = reply_to(
        client, chat_model, need="Think it through", bring_up=RAISE_FIRST
    )

    assert state_after_asking_why == "waiting"
    assert PRESENTATION in next_instructions
    assert (shape["curiosities_offered"], shape["curiosity_asked"]) == (1, False)


def test_no_curiosity_is_offered_while_struggling_whatever_the_rules_say(
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
    two_curiosities_are_due(client, chat_model, clock, scheduler, seeded_settings)
    set_settings(
        client,
        auth_verifier,
        {
            "curiosities_per_conversation": 2,
            "curiosities_per_reply": 2,
            "curiosity_held_when_asking_why": False,
        },
    )
    chat_model.script_understanding(
        understanding_answer(struggling=True, cause_known=False)
    )
    chat_model.script_reply_plan(
        reply_plan_answer(need="Think it through", bring_up=RAISE_BOTH, ask_why=True)
    )

    seen = reply_plan_sees(client, chat_model, "everything is falling apart")

    shape = newest_call(client, owner_headers(client, auth_verifier), "reply_plan")[
        "reply_plan_shape"
    ]
    assert PRESENTATION not in seen
    assert DESK not in seen
    assert [row["state"] for row in stored_curiosities(engine)] == ["waiting"] * 2
    assert (shape["curiosities_offered"], shape["curiosity_asked"]) == (0, False)
