from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
    reply_plan_answer,
)
from tests.telegram_helpers import auth_headers, connect_telegram, owner_headers
from tests.test_admin_needs import need_named
from tests.test_curiosities import (
    PRESENTATION,
    end_conversation,
    end_current_conversation,
    new_curiosity,
    reply_instructions,
    reply_plan_sees,
    stored_curiosities,
)
from tests.test_model_call_log import newest_call
from tests.test_moves_migration import downgrade_to
from tests.test_needs_treat_curiosities import set_treatment
from tests.test_older_summaries import set_settings

DESK = "Did the new desk arrive?"
CAT = "How is the cat?"
NONE_OFFERED = "in this reply):\nNone."
GET_CURIOUS_LINE = "- Get curious:"
A_MINUTE = timedelta(minutes=1)


def three_are_due(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    """Save three Curiosities in one Conversation and move on to when all are due."""
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "work is a lot",
        [
            new_curiosity(),
            new_curiosity(ask=DESK, not_before=None),
            new_curiosity(ask=CAT, not_before=None),
        ],
    )
    clock.advance(timedelta(days=2))


def send(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    message: str,
    **plan: Any,
) -> str:
    """Send a message a minute after the last; return what its Reply Plan saw."""
    clock.advance(A_MINUTE)
    chat_model.script_reply_plan(reply_plan_answer(**plan))
    return reply_plan_sees(client, chat_model, message)


def reactions(engine: Engine) -> dict[str, str | None]:
    """How the User took each saved Curiosity, by question."""
    return {row["question"]: row["reaction"] for row in stored_curiosities(engine)}


def raise_first(need: str = "Ask more") -> dict[str, Any]:
    """A Reply Plan that asks the first Curiosity offered, under a Need."""
    return {"need": need, "bring_up": [{"curiosity": 1, "how": "weave"}]}


def brush_off_two(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    """Have the User brush off two Curiosities in a row in one Conversation."""
    three_are_due(client, chat_model, clock, scheduler, seeded_settings)
    set_settings(
        client,
        auth_verifier,
        {"curiosities_per_conversation": 5, "curiosity_replies_between": 1},
    )
    send(client, chat_model, clock, "hey you", **raise_first())
    send(client, chat_model, clock, "meh", curiosity_taken="brushed_off")
    send(client, chat_model, clock, "anyway", **raise_first())
    send(client, chat_model, clock, "whatever", curiosity_taken="brushed_off")


def test_an_admin_can_set_a_need_to_test_the_water_and_the_reply_plan_is_told(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)

    set_treatment(client, admin, "Advice", "test_the_water")

    saw = reply_plan_sees(client, chat_model, "hey")
    assert need_named(client, admin, "Advice")["curiosities"] == "test_the_water"
    assert need_named(client, admin, "Just chatting")["curiosities"] == (
        "test_the_water"
    )
    assert (
        "- Just chatting: test the water: one light opener in a Conversation at most"
    ) in saw


def test_under_test_the_water_the_opener_is_asked_lightly(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    three_are_due(client, chat_model, clock, scheduler, seeded_settings)
    chat_model.script_reply_plan(reply_plan_answer(**raise_first("Just chatting")))

    instructions = reply_instructions(client, chat_model, "hey you")

    assert "Ask them this lightly, in passing, as something they can let go" in (
        instructions
    )
    assert f"- {PRESENTATION}" in instructions


def test_under_test_the_water_none_is_asked_once_they_let_the_opener_pass(
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
    three_are_due(client, chat_model, clock, scheduler, seeded_settings)
    set_settings(
        client,
        auth_verifier,
        {"curiosities_per_conversation": 5, "curiosity_replies_between": 1},
    )
    send(client, chat_model, clock, "hey you", **raise_first("Just chatting"))
    after_opener = send(client, chat_model, clock, "meh", curiosity_taken="brushed_off")

    saw = send(client, chat_model, clock, "so anyway", **raise_first("Just chatting"))

    shape = newest_call(client, owner_headers(client, auth_verifier), "reply_plan")[
        "reply_plan_shape"
    ]
    assert f"was meant to ask: {PRESENTATION} If Zeph's messages did ask it" in (
        after_opener
    )
    assert reactions(engine)[PRESENTATION] == "brushed_off"
    assert f"[1] {DESK}" in saw
    assert (shape["curiosities_offered"], shape["curiosity_asked"]) == (0, False)
    assert {row["question"]: row["state"] for row in stored_curiosities(engine)}[
        DESK
    ] == "waiting"


def test_under_test_the_water_none_more_is_asked_even_after_an_engaged_opener(
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
    three_are_due(client, chat_model, clock, scheduler, seeded_settings)
    set_settings(
        client,
        auth_verifier,
        {"curiosities_per_conversation": 5, "curiosity_replies_between": 1},
    )
    send(client, chat_model, clock, "hey you", **raise_first("Just chatting"))
    send(client, chat_model, clock, "it went great!", curiosity_taken="engaged")

    send(client, chat_model, clock, "so anyway", **raise_first("Just chatting"))

    states = {row["question"]: row["state"] for row in stored_curiosities(engine)}
    assert reactions(engine)[PRESENTATION] == "engaged"
    assert states[DESK] == "waiting"


def test_no_curiosity_is_offered_until_the_set_number_of_replies_has_passed(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    three_are_due(client, chat_model, clock, scheduler, seeded_settings)
    set_settings(client, auth_verifier, {"curiosities_per_conversation": 5})
    send(client, chat_model, clock, "hey you", **raise_first())

    waiting = [
        send(client, chat_model, clock, text) for text in ("one", "two", "three")
    ]
    fourth = send(client, chat_model, clock, "four")

    assert all(NONE_OFFERED in saw for saw in waiting)
    assert f"[1] {DESK}" in fourth


@pytest.mark.parametrize(
    ("directness", "replies_between"), [("gentle", 4), ("balanced", 3), ("direct", 2)]
)
def test_directness_sets_the_fewest_replies_between_curiosities(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    directness: str,
    replies_between: int,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    maya = auth_headers(auth_verifier, "user_maya")
    client.patch("/api/me", json={"directness": directness}, headers=maya)
    three_are_due(client, chat_model, clock, scheduler, seeded_settings)
    set_settings(client, auth_verifier, {"curiosities_per_conversation": 5})
    send(client, chat_model, clock, "hey you", **raise_first())

    waiting = [
        send(client, chat_model, clock, f"reply {number}")
        for number in range(replies_between)
    ]
    after = send(client, chat_model, clock, "and one more")

    assert all(NONE_OFFERED in saw for saw in waiting)
    assert f"[1] {DESK}" in after


def test_a_direct_users_spacing_still_doubles_after_brush_offs(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    maya = auth_headers(auth_verifier, "user_maya")
    client.patch("/api/me", json={"directness": "direct"}, headers=maya)
    three_are_due(client, chat_model, clock, scheduler, seeded_settings)
    set_settings(client, auth_verifier, {"curiosities_per_conversation": 5})
    send(client, chat_model, clock, "hey you", **raise_first())
    send(client, chat_model, clock, "meh", curiosity_taken="brushed_off")
    send(client, chat_model, clock, "hm")
    send(client, chat_model, clock, "anyway", **raise_first())
    send(client, chat_model, clock, "whatever", curiosity_taken="brushed_off")
    end_current_conversation(chat_model, clock, scheduler, seeded_settings, [])
    clock.advance(timedelta(hours=12))

    waiting = [
        send(client, chat_model, clock, text) for text in ("one", "two", "three")
    ]
    fourth = send(client, chat_model, clock, "four")

    assert all(NONE_OFFERED in saw for saw in waiting)
    assert f"[1] {CAT}" in fourth


def test_the_replies_between_curiosities_count_across_conversations(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    three_are_due(client, chat_model, clock, scheduler, seeded_settings)
    send(client, chat_model, clock, "hey you", **raise_first())
    end_current_conversation(chat_model, clock, scheduler, seeded_settings, [])
    clock.advance(timedelta(hours=12))

    next_conversation = send(client, chat_model, clock, "morning!")

    assert "raised 0 of at most 1 in this Conversation" in next_conversation
    assert NONE_OFFERED in next_conversation


def test_follow_ups_stop_at_their_cap_and_use_none_of_the_curiosity_limit(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    three_are_due(client, chat_model, clock, scheduler, seeded_settings)
    set_settings(client, auth_verifier, {"follow_ups_per_conversation": 1})

    first = send(client, chat_model, clock, "went hiking", lead_move="Get curious")
    send(client, chat_model, clock, "it was steep")
    after_cap = send(client, chat_model, clock, "and muddy")

    assert GET_CURIOUS_LINE in first
    assert GET_CURIOUS_LINE not in after_cap
    assert "raised 0 of at most 1 in this Conversation" in after_cap
    assert f"[1] {PRESENTATION}" in after_cap


def test_after_brush_offs_in_a_row_none_is_offered_for_the_rest_of_the_conversation(
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
    brush_off_two(client, auth_verifier, chat_model, clock, scheduler, seeded_settings)

    later = [send(client, chat_model, clock, text) for text in ("a", "b", "c", "d")]

    assert list(reactions(engine).values()).count("brushed_off") == 2
    assert all(NONE_OFFERED in saw for saw in later)


def test_after_backing_off_the_spacing_is_doubled_in_the_next_conversation(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    brush_off_two(client, auth_verifier, chat_model, clock, scheduler, seeded_settings)
    end_current_conversation(chat_model, clock, scheduler, seeded_settings, [])
    clock.advance(timedelta(hours=12))

    first = send(client, chat_model, clock, "morning!")
    second = send(client, chat_model, clock, "slept badly")

    assert NONE_OFFERED in first
    assert f"[1] {CAT}" in second


def test_the_doubled_spacing_ends_after_the_set_days(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    brush_off_two(client, auth_verifier, chat_model, clock, scheduler, seeded_settings)
    end_current_conversation(chat_model, clock, scheduler, seeded_settings, [])
    clock.advance(timedelta(days=4))

    first = send(client, chat_model, clock, "morning!")

    assert f"[1] {CAT}" in first


def test_one_engaged_answer_returns_the_spacing_to_normal(
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
    brush_off_two(client, auth_verifier, chat_model, clock, scheduler, seeded_settings)
    end_current_conversation(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [{"curiosity": 2, "reaction": "engaged"}],
    )
    clock.advance(timedelta(hours=12))

    first = send(client, chat_model, clock, "morning!")

    assert list(reactions(engine).values()).count("engaged") == 1
    assert f"[1] {CAT}" in first


def test_a_curiosity_they_asked_to_drop_is_always_shown_to_the_keeping_step(
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
    three_are_due(client, chat_model, clock, scheduler, seeded_settings)
    send(client, chat_model, clock, "hey you", **raise_first())
    send(client, chat_model, clock, "pls drop it", curiosity_taken="asked_to_drop")
    end_current_conversation(chat_model, clock, scheduler, seeded_settings, [])
    clock.advance(timedelta(days=1))

    end_conversation(
        client, chat_model, clock, scheduler, seeded_settings, "hi again", []
    )

    keeper_saw = chat_model.curiosity_keeping_calls[-1].history[0].text
    assert reactions(engine)[PRESENTATION] == "asked_to_drop"
    assert (
        "They asked Zeph to drop these; never ask about them again unless they "
        f"bring it up:\n- {PRESENTATION}"
    ) in keeper_saw


def test_a_reaction_is_read_only_when_the_last_reply_asked_a_curiosity(
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
    three_are_due(client, chat_model, clock, scheduler, seeded_settings)

    saw = send(client, chat_model, clock, "hey you", curiosity_taken="brushed_off")

    assert "was meant to ask" not in saw
    assert set(reactions(engine).values()) == {None}


def test_the_migration_moves_just_chatting_to_test_the_water(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    engine: Engine,
    database_url: str,
) -> None:
    owner_headers(client, auth_verifier)
    downgrade_to(database_url, "0080")
    try:
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE needs SET curiosities = 'never' WHERE name = 'Advice'")
            )
            connection.execute(
                text(
                    "INSERT INTO platform_settings (key, value, updated_at) VALUES "
                    "('reply_plan_prompt', '\"An old prompt.\"', now()) "
                    "ON CONFLICT (key) DO UPDATE SET value = excluded.value"
                )
            )
    finally:
        migrate(database_url)

    with engine.begin() as connection:
        treatments = dict(
            connection.execute(text("SELECT name, curiosities FROM needs")).all()
        )
        prompt = connection.execute(
            text("SELECT value FROM platform_settings WHERE key = 'reply_plan_prompt'")
        ).all()
        connection.execute(
            text(
                "UPDATE needs SET curiosities = 'only_if_it_fits' WHERE name = 'Advice'"
            )
        )
    assert treatments["Just chatting"] == "test_the_water"
    assert treatments["Advice"] == "never"
    assert prompt == []
