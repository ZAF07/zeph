from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine

from companion.core.curiosities import ASKED_CHECK_PROMPT
from companion.core.models import CuriosityState
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import connect_telegram, owner_headers
from tests.test_curiosities import (
    PRESENTATION,
    bring_up_curiosity,
    presentation_is_due,
    reply_plan_sees,
    stored_curiosities,
)
from tests.test_curiosity_pace_in_replies import (
    DESK,
    raise_first,
    reactions,
    send,
    three_are_due,
)
from tests.test_curiosity_reply_rules import RAISE_BOTH, two_curiosities_are_due
from tests.test_explorations import talk
from tests.test_model_call_log import newest_call
from tests.test_needs_treat_curiosities import reply_to
from tests.test_older_summaries import set_settings
from tests.test_prediction_follow_up import (
    ASK_FIRST,
    FOLLOW_UP,
    share_and_end,
    waiting,
)


def test_a_picked_curiosity_the_reply_never_asked_stays_waiting_and_is_offered_again(
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

    bring_up_curiosity(chat_model, 1)
    chat_model.script_asked_check("no")
    reply_plan_sees(client, chat_model, "hey you")
    [curiosity] = stored_curiosities(engine)
    next_message = reply_plan_sees(client, chat_model, "busy day today")

    assert curiosity["state"] == "waiting"
    assert curiosity["raised_at"] is None
    assert curiosity["raised_conversation_id"] is None
    assert f"[1] {PRESENTATION}" in next_message
    assert "raised 0 of at most 1 in this Conversation" in next_message
    assert "was meant to ask" not in next_message


def test_the_asked_check_reads_the_question_and_the_reply_as_sent(
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

    bring_up_curiosity(chat_model, 1)
    chat_model.script("hey!\n\nhow did the presentation go in the end?")
    reply_plan_sees(client, chat_model, "hey you")

    [check] = chat_model.asked_check_calls
    [curiosity] = stored_curiosities(engine)
    assert check.instructions == ASKED_CHECK_PROMPT
    assert check.thinking is False
    assert check.model == seeded_settings["check_in_model"]
    assert check.history[0].text == (
        f"What the reply was meant to ask: {PRESENTATION}\n\n"
        "The reply:\nhey!\nhow did the presentation go in the end?"
    )
    assert chat_model.call_order[-3:] == ["reply", "claim_check", "asked_check"]
    assert curiosity["state"] == "raised"


def test_a_reply_that_picked_no_curiosity_makes_no_asked_check(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    presentation_is_due(client, chat_model, clock, scheduler, seeded_settings)

    reply_plan_sees(client, chat_model, "hey you")

    assert chat_model.asked_check_calls == []


def test_a_failed_asked_check_counts_as_asked_so_it_is_never_asked_twice(
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

    bring_up_curiosity(chat_model, 1)
    chat_model.script_asked_check(RuntimeError("model down"))
    reply_plan_sees(client, chat_model, "hey you")

    [curiosity] = stored_curiosities(engine)
    assert curiosity["state"] == "raised"


def test_of_two_picked_only_the_one_the_reply_asked_is_marked_raised(
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

    chat_model.script_asked_check("no", "yes")
    reply_to(client, chat_model, need="Think it through", bring_up=RAISE_BOTH)

    states = {row["question"]: row["state"] for row in stored_curiosities(engine)}
    assert states == {PRESENTATION: "waiting", DESK: "raised"}


def test_the_model_call_log_says_whether_the_curiosity_was_really_asked(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    presentation_is_due(client, chat_model, clock, scheduler, seeded_settings)
    headers = owner_headers(client, auth_verifier)

    bring_up_curiosity(chat_model, 1)
    chat_model.script_asked_check("no")
    reply_plan_sees(client, chat_model, "hey you")
    left_out = newest_call(client, headers, "reply_plan")["reply_plan_shape"]
    asked_check = newest_call(client, headers, "curiosity_asked_check")
    clock.advance(timedelta(minutes=1))
    bring_up_curiosity(chat_model, 1)
    reply_plan_sees(client, chat_model, "so anyway")
    asked = newest_call(client, headers, "reply_plan")["reply_plan_shape"]

    assert left_out["curiosities_offered"] == 1
    assert left_out["curiosity_asked"] is False
    assert asked_check["step"] == "curiosity_asked_check"
    assert asked["curiosity_asked"] is True


def test_an_unasked_curiosity_never_counts_as_a_brush_off(
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

    chat_model.script_asked_check("no")
    send(client, chat_model, clock, "hey you", **raise_first())
    next_saw = send(client, chat_model, clock, "meh", curiosity_taken="brushed_off")

    assert set(reactions(engine).values()) == {None}
    assert "was meant to ask" not in next_saw
    assert f"[1] {PRESENTATION}" in next_saw


def test_a_prediction_follow_up_picked_but_not_asked_is_still_waiting(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = share_and_end(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    [follow_up] = waiting(client.engine, user_id)
    clock.advance(timedelta(days=8))

    chat_model.script_asked_check("no")
    talk(client, chat_model, clock, "hello", **ASK_FIRST)
    [still_waiting] = waiting(client.engine, user_id)
    offered_again = talk(client, chat_model, clock, "anyway")
    talk(client, chat_model, clock, "what's new", **ASK_FIRST)

    assert still_waiting.id == follow_up.id
    assert still_waiting.state == CuriosityState.WAITING
    assert still_waiting.raised_at is None
    assert FOLLOW_UP in offered_again
    assert waiting(client.engine, user_id) == []
