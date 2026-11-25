from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient

from companion.core.curiosities import DROPPED_TOPICS_FOR_REPLY, DROPPED_TOPICS_HEADER
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
    understanding_answer,
)
from tests.telegram_helpers import connect_telegram, owner_headers
from tests.test_curiosities import (
    PRESENTATION,
    end_current_conversation,
    reply_instructions,
    reply_plan_sees,
)
from tests.test_curiosity_pace_in_replies import raise_first, send, three_are_due
from tests.test_features import switch_for_everyone


def drop_the_presentation(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    """Have Zeph ask about the presentation and the User ask it to drop that."""
    three_are_due(client, chat_model, clock, scheduler, seeded_settings)
    send(client, chat_model, clock, "hey you", **raise_first())
    send(client, chat_model, clock, "pls drop it", curiosity_taken="asked_to_drop")


def test_the_reply_plan_is_shown_the_topics_they_asked_to_drop(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    drop_the_presentation(client, chat_model, clock, scheduler, seeded_settings)

    same_conversation = send(client, chat_model, clock, "so, work")
    end_current_conversation(chat_model, clock, scheduler, seeded_settings, [])
    clock.advance(timedelta(days=30))
    a_month_later = reply_plan_sees(client, chat_model, "hi again")

    for saw in (same_conversation, a_month_later):
        assert f"{DROPPED_TOPICS_HEADER}\n- {PRESENTATION}" in saw


def test_with_nothing_dropped_the_reply_plan_and_reply_are_told_nothing_about_it(
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

    saw = reply_plan_sees(client, chat_model, "hey you")
    instructions = chat_model.calls[-1].instructions

    assert DROPPED_TOPICS_HEADER not in saw
    assert DROPPED_TOPICS_FOR_REPLY not in instructions


def test_the_reply_is_told_the_dropped_topics_among_their_boundaries(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    drop_the_presentation(client, chat_model, clock, scheduler, seeded_settings)

    instructions = reply_instructions(client, chat_model, "so, work")

    told = f"{DROPPED_TOPICS_FOR_REPLY}\n- {PRESENTATION}"
    assert told in instructions
    assert instructions.index(told) < instructions.index(
        "## 2. What they just asked or need right now"
    )


def test_dropped_topics_are_shown_while_struggling_and_with_curiosities_off(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    drop_the_presentation(client, chat_model, clock, scheduler, seeded_settings)

    chat_model.script_understanding(understanding_answer(struggling=True))
    struggling = reply_plan_sees(client, chat_model, "it's all too much")
    switch_for_everyone(
        client, owner_headers(client, auth_verifier), "curiosities", False
    )
    switched_off = reply_plan_sees(client, chat_model, "anyway")

    for saw in (struggling, switched_off):
        assert f"{DROPPED_TOPICS_HEADER}\n- {PRESENTATION}" in saw
