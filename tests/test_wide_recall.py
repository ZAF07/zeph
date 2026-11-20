from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient

from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeEmbedder,
    FakeScheduler,
    ScriptedChatModel,
    reply_plan_answer,
    understanding_answer,
)
from tests.telegram_helpers import connect_telegram
from tests.test_life_threads import (
    MEI_STORY,
    end_conversation,
    new_thread,
    reply_instructions,
    reply_plan_sees,
    start_mei_thread,
)
from tests.test_older_summaries import set_settings

KNEE_STORY = "Knee pain during long runs."


def start_threads_naming_mei(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    count: int,
) -> None:
    """Have a Conversation whose end starts some open Threads that name Mei."""
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "so much going on with Mei",
        [
            new_thread(title=f"Mei story {number}", story=f"Story {number}.")
            for number in range(1, count + 1)
        ],
    )
    clock.advance(timedelta(days=3))


def test_a_thread_reminded_by_message_2_is_still_in_mind_at_message_20(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)
    clock.advance(timedelta(days=30))

    reply_plan_sees(client, chat_model, "hey there")
    reply_plan_sees(client, chat_model, "Mei's wedding is next week")
    for number in range(3, 20):
        reply_plan_sees(client, chat_model, f"the weather is grey, take {number}")
    seen_at_20 = reply_plan_sees(client, chat_model, "anyway, back to work")

    assert "[1] Falling-out with Mei (open" in seen_at_20
    assert MEI_STORY in seen_at_20


def test_a_thread_in_mind_still_follows_the_hold_back_rules(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)
    clock.advance(timedelta(days=30))

    chat_model.script_reply_plan(
        reply_plan_answer(bring_up=[{"thread": 1, "how": "lead"}], threads_touched=[1])
    )
    reply_plan_sees(client, chat_model, "Mei's wedding is next week")
    set_settings(client, auth_verifier, {"life_threads_texts_to_search": 1})
    seen_later = reply_plan_sees(client, chat_model, "the weather is grey")

    assert (
        "Don't bring it up: you already brought it up in this Conversation."
        in seen_later
    )


def test_recall_searches_on_what_the_understanding_says_they_mean(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "training is going badly",
        [new_thread(title="Marathon training", story=KNEE_STORY, people=())],
    )
    clock.advance(timedelta(days=3))

    chat_model.script_understanding(
        understanding_answer(means="Their knee pain is back during long runs.")
    )
    seen = reply_plan_sees(client, chat_model, "ugh, not again")

    assert "Marathon training" in seen


def test_recall_searches_the_admin_set_number_of_their_recent_texts(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    embedder: FakeEmbedder,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    set_settings(client, auth_verifier, {"life_threads_texts_to_search": 4})
    for number in range(1, 6):
        reply_plan_sees(client, chat_model, f"text number {number}")

    meaning = "They want to talk about something heavy."
    chat_model.script_understanding(understanding_answer(means=meaning))
    reply_plan_sees(client, chat_model, "text number 6")
    search = next(query for query in embedder.queries if meaning in query)

    assert all(f"text number {number}" in search for number in range(3, 7))
    assert "text number 2" not in search


def test_more_than_3_threads_past_the_bar_reach_the_reply_plan(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_threads_naming_mei(
        client, chat_model, clock, scheduler, seeded_settings, count=5
    )

    seen = reply_plan_sees(client, chat_model, "Mei again")

    assert all(f"[{number}] Mei story" in seen for number in range(1, 6))


def test_the_admin_set_cap_limits_the_threads_one_search_brings_to_mind(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_threads_naming_mei(
        client, chat_model, clock, scheduler, seeded_settings, count=5
    )
    set_settings(client, auth_verifier, {"life_threads_per_reply": 4})

    seen = reply_plan_sees(client, chat_model, "Mei again")

    assert "[4] Mei story" in seen
    assert "[5]" not in seen


def test_only_threads_the_reply_plan_picks_reach_the_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_threads_naming_mei(
        client, chat_model, clock, scheduler, seeded_settings, count=3
    )

    chat_model.script_reply_plan(reply_plan_answer(threads_touched=[2]))
    instructions = reply_instructions(client, chat_model, "Mei again")

    assert "Story 2." in instructions
    assert "Story 1." not in instructions
    assert "Story 3." not in instructions


def test_a_failed_reply_plan_gives_the_reply_no_threads(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)
    clock.advance(timedelta(days=30))

    chat_model.script_reply_plan(RuntimeError("model is down"))
    instructions = reply_instructions(client, chat_model, "Mei's wedding is soon")

    assert MEI_STORY not in instructions
    assert "Bring up" not in instructions
    assert chat_channel.texts_sent_to(5551001)[-1] == "mm, tell me more"


def test_the_cap_limits_the_threads_in_mind_at_once_keeping_this_messages_first(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "so much going on",
        [
            new_thread(title="Mei story", story="Story Mei.", people=("Mei",)),
            new_thread(title="Tom story", story="Story Tom.", people=("Tom",)),
            new_thread(title="Sam story", story="Story Sam.", people=("Sam",)),
        ],
    )
    clock.advance(timedelta(days=3))
    set_settings(
        client,
        auth_verifier,
        {"life_threads_per_reply": 2, "life_threads_texts_to_search": 1},
    )

    reply_plan_sees(client, chat_model, "Mei called")
    reply_plan_sees(client, chat_model, "Tom called")
    seen = reply_plan_sees(client, chat_model, "Sam called")

    assert "[1] Sam story" in seen
    assert "[2] Mei story" in seen
    assert "Tom story" not in seen
