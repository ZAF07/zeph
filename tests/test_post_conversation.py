import json
from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient

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
    send_to_webhook,
    telegram_text_update,
)
from tests.test_onboarding import onboarding_answers


def processing_answer(
    summary: str = "Talked about a new job.",
    mood: str = "excited",
    operations: list[dict[str, Any]] | None = None,
    photos_to_keep: list[dict[str, Any]] | None = None,
) -> str:
    """Build the JSON the post-conversation processing model answers with."""
    return json.dumps(
        {
            "summary": summary,
            "mood": mood,
            "memory_operations": operations or [],
            "photos_to_keep": photos_to_keep or [],
        }
    )


def quiet_gap(seeded_settings: dict[str, Any]) -> timedelta:
    """The seeded quiet gap after which a Conversation ends."""
    return timedelta(minutes=seeded_settings["conversation_quiet_gap_minutes"])


def memory_contents(
    client: TestClient, headers: dict[str, str]
) -> dict[str, list[str]]:
    """List the User's Memory Items through the Dashboard API, by category."""
    groups = client.get("/api/memory-items", headers=headers).json()["groups"]
    return {
        group["category"]: [item["content"] for item in group["items"]]
        for group in groups
    }


def test_conversation_ends_after_the_quiet_gap_and_is_processed_once(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    chat_model.script("oh nice, congrats!")
    send_to_webhook(client, telegram_text_update("I started a new job in design"))

    clock.advance(quiet_gap(seeded_settings) - timedelta(minutes=1))
    scheduler.tick()
    assert chat_model.processing_calls == []

    clock.advance(timedelta(minutes=2))
    chat_model.script_processing(
        processing_answer(
            summary="Shared that they started a new job in design.",
            mood="excited, a bit nervous",
            operations=[
                {
                    "action": "add",
                    "category": "Life details",
                    "content": "Started a new job in design",
                }
            ],
        )
    )
    scheduler.tick()
    scheduler.tick()

    assert len(chat_model.processing_calls) == 1
    [summary] = client.get("/api/conversation-summaries", headers=headers).json()[
        "summaries"
    ]
    assert summary["summary"] == "Shared that they started a new job in design."
    assert summary["mood"] == "excited, a bit nervous"
    assert memory_contents(client, headers) == {
        "Life details": ["Started a new job in design"]
    }


def have_conversation(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    text: str,
    answer: str | Exception,
) -> None:
    """Send one message, let the quiet gap pass and run a tick to process it."""
    chat_model.script("mm, I hear you")
    send_to_webhook(client, telegram_text_update(text))
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(answer)
    scheduler.tick()


def test_a_changed_fact_updates_the_old_memory_item_instead_of_adding_one(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    add_teacher = {
        "action": "add",
        "category": "Life details",
        "content": "Works as a teacher",
    }
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "I teach year 5",
        processing_answer(operations=[add_teacher]),
    )

    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "I quit teaching, I'm in product design now",
        processing_answer(
            operations=[
                {"action": "update", "item": 1, "content": "Works in product design"}
            ]
        ),
    )

    assert memory_contents(client, headers) == {
        "Life details": ["Works in product design"]
    }
    second_call = chat_model.processing_calls[1].history[0].text
    assert "[1] (Life details) Works as a teacher" in second_call
    assert "Person: I quit teaching, I'm in product design now" in second_call


def test_with_user_memory_off_nothing_is_saved_and_chat_still_works(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "I swim every morning",
        processing_answer(
            operations=[{"action": "add", "category": "What helps", "content": "Swims"}]
        ),
    )
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)

    chat_model.script("sounds lovely")
    send_to_webhook(client, telegram_text_update("I went to the beach today"))
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    scheduler.tick()

    assert chat_channel.texts_sent_to(5551001)[-1] == "sounds lovely"
    assert len(chat_model.processing_calls) == 1
    summaries = client.get("/api/conversation-summaries", headers=headers).json()
    assert len(summaries["summaries"]) == 1
    assert memory_contents(client, headers) == {"What helps": ["Swims"]}


def test_a_message_after_a_conversation_ended_starts_a_new_one(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "hi",
        processing_answer(summary="Said hi."),
    )

    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "back again",
        processing_answer(summary="Came back."),
    )

    assert chat_model.calls[1].history[-1].text == "back again"
    assert len(chat_model.calls[1].history) == 1
    summaries = client.get("/api/conversation-summaries", headers=headers).json()
    assert [entry["summary"] for entry in summaries["summaries"]] == [
        "Came back.",
        "Said hi.",
    ]


def test_processing_that_fails_is_tried_again_on_the_next_tick(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "hi",
        TimeoutError("DeepSeek timed out"),
    )
    assert client.get("/api/conversation-summaries", headers=headers).json() == {
        "summaries": []
    }

    chat_model.script_processing(processing_answer(summary="Said hi."))
    scheduler.tick()

    summaries = client.get("/api/conversation-summaries", headers=headers).json()
    assert [entry["summary"] for entry in summaries["summaries"]] == ["Said hi."]


def test_an_unreadable_answer_is_asked_again_once(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    chat_model.script_processing("Sorry, I can't do that.")

    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "hi",
        "```json\n" + processing_answer(summary="Said hi.") + "\n```",
    )

    assert len(chat_model.processing_calls) == 2
    summaries = client.get("/api/conversation-summaries", headers=headers).json()
    assert [entry["summary"] for entry in summaries["summaries"]] == ["Said hi."]


def test_operations_that_cannot_be_applied_are_skipped(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "my sister Jo is moving abroad, and I hate mornings",
        processing_answer(
            operations=[
                {"action": "add", "category": "Relationships", "content": "Sister Jo"},
                {"action": "add", "category": "relationships", "content": "sister jo"},
                {"action": "add", "category": "Hobbies", "content": "Unknown kind"},
                {"action": "add", "category": "Preferences", "content": " "},
                {"action": "update", "item": 7, "content": "No such item"},
                {"action": "remove", "item": "1"},
                "not an operation",
                {
                    "action": "add",
                    "category": "Preferences",
                    "content": "Not a morning person",
                },
            ]
        ),
    )

    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "actually forget about Jo",
        processing_answer(operations=[{"action": "remove", "item": 1}]),
    )

    assert memory_contents(client, headers) == {"Preferences": ["Not a morning person"]}


def test_an_updated_onboarding_memory_survives_answering_onboarding_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    client.put("/api/onboarding", json=onboarding_answers(), headers=headers)
    connect_telegram(client, auth_verifier, chat_channel)
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "call me May, actually",
        processing_answer(
            operations=[{"action": "update", "item": 1, "content": "Goes by May"}]
        ),
    )

    client.put("/api/onboarding", json=onboarding_answers(), headers=headers)

    assert memory_contents(client, headers)["Life details"] == [
        "Goes by May",
        "Goes by Maya",
    ]
