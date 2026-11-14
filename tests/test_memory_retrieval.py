from typing import Any

from fastapi.testclient import TestClient

from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
    understanding_answer,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    auth_headers,
    connect_telegram,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_post_conversation import have_conversation, processing_answer

REMEMBERED = [
    {"action": "add", "category": "Life details", "content": "Works in design"},
    {"action": "add", "category": "Relationships", "content": "Sister Jo"},
    {"action": "add", "category": "Preferences", "content": "Likes Stoicism"},
    {"action": "add", "category": "Challenges", "content": "Catastrophises"},
]


def remember_some_things(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    """Have one processed Conversation that leaves a Memory Item per category."""
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "lots on my mind",
        processing_answer(
            summary="Talked about work and family.",
            mood="tired",
            operations=REMEMBERED,
        ),
    )
    chat_model.calls.clear()
    chat_model.understanding_calls.clear()


def test_reply_gets_picked_and_always_include_memories_and_recent_summaries(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    remember_some_things(client, chat_model, clock, scheduler, seeded_settings)
    chat_model.script_understanding(
        understanding_answer(memory_categories=["Relationships"])
    )
    chat_model.script("aw, Jo")

    send_to_webhook(client, telegram_text_update("my sister called"))

    [understanding_call] = chat_model.understanding_calls
    asked = understanding_call.history[0].text
    assert "my sister called" in asked
    assert "- Relationships:" in asked
    assert "- Life details:" in asked
    assert "- Preferences:" not in asked
    [reply_call] = chat_model.calls
    assert "Sister Jo" in reply_call.instructions
    assert "Likes Stoicism" in reply_call.instructions
    assert "Catastrophises" in reply_call.instructions
    assert "Works in design" not in reply_call.instructions
    assert "Talked about work and family." in reply_call.instructions
    assert "tired" in reply_call.instructions
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)[-1] == "aw, Jo"


def test_only_the_newest_conversation_summaries_reach_the_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    for number in range(1, 5):
        have_conversation(
            client,
            chat_model,
            clock,
            scheduler,
            seeded_settings,
            f"chat {number}",
            processing_answer(summary=f"Summary number {number}."),
        )
    chat_model.calls.clear()
    chat_model.script("hey")

    send_to_webhook(client, telegram_text_update("hi again"))

    [reply_call] = chat_model.calls
    assert seeded_settings["recent_conversation_summaries"] == 3
    assert "Summary number 1." not in reply_call.instructions
    for number in (2, 3, 4):
        assert f"Summary number {number}." in reply_call.instructions


def test_with_user_memory_off_replies_still_use_existing_memory(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    remember_some_things(client, chat_model, clock, scheduler, seeded_settings)
    headers = auth_headers(auth_verifier, "user_maya")
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)
    chat_model.script_understanding(
        understanding_answer(memory_categories=["Relationships"])
    )
    chat_model.script("aw, Jo")

    send_to_webhook(client, telegram_text_update("my sister called"))

    assert len(chat_model.understanding_calls) == 1
    [reply_call] = chat_model.calls
    assert "Sister Jo" in reply_call.instructions
    assert "Likes Stoicism" in reply_call.instructions
    assert "Talked about work and family." in reply_call.instructions


def test_reply_still_gets_always_include_memories_when_the_understanding_fails(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    remember_some_things(client, chat_model, clock, scheduler, seeded_settings)
    chat_model.script_understanding(TimeoutError("DeepSeek timed out"))
    chat_model.script("hey")

    send_to_webhook(client, telegram_text_update("my sister called"))

    [reply_call] = chat_model.calls
    assert "Likes Stoicism" in reply_call.instructions
    assert "Sister Jo" not in reply_call.instructions
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)[-1] == "hey"


def test_a_new_user_with_nothing_remembered_is_offered_no_memory_categories(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("hey")

    send_to_webhook(client, telegram_text_update("hello"))

    [understanding_call] = chat_model.understanding_calls
    assert "Memory Categories with something saved:\nNone yet." in (
        understanding_call.history[0].text
    )
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey"]
