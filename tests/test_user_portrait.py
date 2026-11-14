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
    ToolCall,
    understanding_answer,
)
from tests.telegram_helpers import (
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_life_threads import new_thread, thread_keeping_answer
from tests.test_post_conversation import have_conversation, processing_answer

PORTRAIT = "Maya is a designer who just started a new job and loves long walks."
REWRITTEN = "Maya is a designer who loves long walks."
TEACHER_FACT = "Works as a teacher in Leeds"
WALKS_FACT = "Long walks help when they feel low"


def add_fact(content: str) -> dict[str, str]:
    """Build an operation that adds a Memory Item to "Life details"."""
    return {"action": "add", "category": "Life details", "content": content}


def end_conversation_with_portrait(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    portrait: str = PORTRAIT,
    facts: tuple[str, ...] = (TEACHER_FACT, WALKS_FACT),
    threads: list[dict[str, Any]] | None = None,
) -> None:
    """Have a Conversation whose end keeps facts and Threads and writes a Portrait."""
    chat_model.script_thread_keeping(thread_keeping_answer(threads or []))
    chat_model.script_portrait(portrait)
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "Long day at school, a walk helped",
        processing_answer(
            summary="Talked about a long day at school.",
            mood="tired, then lighter",
            offered="Suggested a walk; they said it helped.",
            operations=[add_fact(fact) for fact in facts],
        ),
    )


def portrait_shown(client: TestClient, headers: dict[str, str]) -> Any:
    """Read the User's Portrait through the Dashboard API."""
    response = client.get("/api/user-portrait", headers=headers)
    assert response.status_code == 200
    return response.json()["portrait"]


def memory_item_id(client: TestClient, headers: dict[str, str], content: str) -> str:
    """Find a Memory Item's ID by its content, through the Dashboard API."""
    groups = client.get("/api/memory-items", headers=headers).json()["groups"]
    [item_id] = [
        item["id"]
        for group in groups
        for item in group["items"]
        if item["content"] == content
    ]
    return str(item_id)


def send_message(client: TestClient, chat_model: ScriptedChatModel, text: str) -> None:
    """Send one message the Companion answers."""
    chat_model.script("mm, tell me more")
    send_to_webhook(client, telegram_text_update(text))


def test_a_conversation_end_writes_the_portrait_from_memory_threads_and_summaries(
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

    end_conversation_with_portrait(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        threads=[new_thread()],
    )

    [call] = chat_model.portrait_calls
    given = call.history[0].text
    assert call.model == seeded_settings["portrait_model"]
    assert TEACHER_FACT in given
    assert "Falling-out with Mei" in given
    assert "Talked about a long day at school." in given
    assert "Suggested a walk; they said it helped." in given
    assert portrait_shown(client, headers)["text"] == PORTRAIT


def test_the_portrait_reaches_the_next_understanding_and_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )

    send_message(client, chat_model, "hey, rough morning")

    assert PORTRAIT in chat_model.understanding_calls[-1].history[0].text
    assert PORTRAIT in chat_model.calls[-1].instructions


def test_a_failed_understanding_still_gives_the_reply_the_portrait(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )
    chat_model.script_understanding(RuntimeError("model down"))

    send_message(client, chat_model, "hey, rough morning")

    assert PORTRAIT in chat_model.calls[-1].instructions


def test_the_next_conversation_end_rewrites_the_portrait(
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
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )

    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings, portrait=REWRITTEN
    )

    assert len(chat_model.portrait_calls) == 2
    assert PORTRAIT not in chat_model.portrait_calls[1].history[0].text
    assert portrait_shown(client, headers)["text"] == REWRITTEN


def test_a_failing_portrait_writer_keeps_the_summary_and_the_old_portrait(
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
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )
    chat_model.script_portrait(RuntimeError("model down"))

    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "another day",
        processing_answer(summary="Talked about another day."),
    )
    scheduler.tick()

    summaries = client.get("/api/conversation-summaries", headers=headers).json()
    assert summaries["summaries"][0]["summary"] == "Talked about another day."
    assert portrait_shown(client, headers)["text"] == PORTRAIT
    assert len(chat_model.portrait_calls) == 2


def test_with_user_memory_off_no_portrait_is_written_but_the_saved_one_is_used(
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
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)

    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings, portrait=REWRITTEN
    )
    send_message(client, chat_model, "hey again")

    assert len(chat_model.portrait_calls) == 1
    assert PORTRAIT in chat_model.calls[-1].instructions


def test_deleting_a_memory_item_rewrites_the_portrait_without_it(
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
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )

    item_id = memory_item_id(client, headers, TEACHER_FACT)
    client.delete(f"/api/memory-items/{item_id}", headers=headers)
    chat_model.script_portrait(REWRITTEN)
    scheduler.tick()
    scheduler.tick()

    assert len(chat_model.portrait_calls) == 2
    rewrite_input = chat_model.portrait_calls[1].history[0].text
    assert TEACHER_FACT not in rewrite_input
    assert PORTRAIT not in rewrite_input
    assert WALKS_FACT in rewrite_input
    assert portrait_shown(client, headers)["text"] == REWRITTEN


def test_deleting_a_life_thread_rewrites_the_portrait_without_it(
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
    end_conversation_with_portrait(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        threads=[new_thread()],
    )
    [thread] = client.get("/api/life-threads", headers=headers).json()["threads"]

    client.delete(f"/api/life-threads/{thread['id']}", headers=headers)
    chat_model.script_portrait(REWRITTEN)
    scheduler.tick()

    rewrite_input = chat_model.portrait_calls[-1].history[0].text
    assert "Falling-out with Mei" not in rewrite_input
    assert portrait_shown(client, headers)["text"] == REWRITTEN


def test_deleting_with_user_memory_off_still_rewrites_the_portrait_without_it(
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
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)

    item_id = memory_item_id(client, headers, TEACHER_FACT)
    client.delete(f"/api/memory-items/{item_id}", headers=headers)
    chat_model.script_portrait(REWRITTEN)
    scheduler.tick()

    assert TEACHER_FACT not in chat_model.portrait_calls[-1].history[0].text
    assert portrait_shown(client, headers)["text"] == REWRITTEN


def test_deleting_the_portrait_clears_it_until_a_later_conversation_end_with_memory_on(
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
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )

    deleted = client.delete("/api/user-portrait", headers=headers)
    deleted_again = client.delete("/api/user-portrait", headers=headers)
    send_message(client, chat_model, "hey again")
    reply_after_delete = chat_model.calls[-1].instructions
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings, portrait=REWRITTEN
    )
    shown_while_off = portrait_shown(client, headers)
    client.patch("/api/me", json={"user_memory_enabled": True}, headers=headers)
    chat_model.script_portrait(REWRITTEN)
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "back again",
        processing_answer(),
    )

    assert deleted.status_code == 204
    assert deleted_again.status_code == 404
    assert PORTRAIT not in reply_after_delete
    assert shown_while_off is None
    assert portrait_shown(client, headers)["text"] == REWRITTEN


def test_deleting_a_memory_item_with_no_portrait_writes_none(
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
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )
    client.delete("/api/user-portrait", headers=headers)

    item_id = memory_item_id(client, headers, TEACHER_FACT)
    client.delete(f"/api/memory-items/{item_id}", headers=headers)
    scheduler.tick()

    assert len(chat_model.portrait_calls) == 1
    assert portrait_shown(client, headers) is None


def test_a_portrait_deleted_while_one_is_being_written_stays_deleted(
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
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )

    def delete_portrait() -> None:
        clock.advance(timedelta(seconds=5))
        client.delete("/api/user-portrait", headers=headers)

    chat_model.before_next_portrait = delete_portrait
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings, portrait=REWRITTEN
    )

    assert portrait_shown(client, headers) is None


def test_a_memory_item_deleted_while_the_portrait_is_written_is_rewritten_out(
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

    def delete_teacher_fact() -> None:
        clock.advance(timedelta(seconds=5))
        item_id = memory_item_id(client, headers, TEACHER_FACT)
        client.delete(f"/api/memory-items/{item_id}", headers=headers)
        chat_model.script_portrait(REWRITTEN)

    chat_model.before_next_portrait = delete_teacher_fact
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )

    assert TEACHER_FACT not in chat_model.portrait_calls[-1].history[0].text
    assert portrait_shown(client, headers)["text"] == REWRITTEN


def test_a_user_sees_only_their_own_portrait(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )
    other_headers = auth_headers(auth_verifier, "user_sam")
    client.get("/api/me", headers=other_headers)

    assert portrait_shown(client, other_headers) is None
    assert client.delete("/api/user-portrait", headers=other_headers).status_code == 404


def test_admins_see_only_whether_a_user_has_a_portrait(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )

    users = client.get(
        "/api/admin/users", headers=owner_headers(client, auth_verifier)
    ).json()["users"]

    has_portrait = {user["email"]: user["has_portrait"] for user in users}
    assert has_portrait["user_maya@example.com"] is True
    assert PORTRAIT not in json.dumps(users)


def test_the_summary_records_the_mood_arc_and_what_was_offered(
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
    chat_model.script_understanding(
        understanding_answer(mood="anxious", intensity="high"),
        understanding_answer(mood="calmer", intensity="low"),
    )
    send_message(client, chat_model, "my presentation is tomorrow, freaking out")
    send_message(client, chat_model, "ok a walk sounds good actually")

    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )
    send_message(client, chat_model, "hi")

    processing_input = chat_model.processing_calls[-1].history[0].text
    [summary] = client.get("/api/conversation-summaries", headers=headers).json()[
        "summaries"
    ][:1]
    assert "anxious (high)" in processing_input
    assert "calmer (low)" in processing_input
    assert summary["mood"] == "tired, then lighter"
    assert summary["offered"] == "Suggested a walk; they said it helped."
    assert "Suggested a walk; they said it helped." in chat_model.calls[-1].instructions


def test_forgetting_in_chat_rewrites_the_portrait_without_it(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )
    chat_model.script(ToolCall("list_memories", {}))
    chat_model.script(".")
    send_to_webhook(client, telegram_text_update("what do you remember?"))
    [number] = [
        line.split(".")[0]
        for line in chat_model.calls[-1].tool_results[0].splitlines()
        if TEACHER_FACT in line
    ]

    chat_model.script(
        ToolCall("list_memories", {}),
        ToolCall("forget_memory", {"number": int(number)}),
        "Done, forgotten.",
    )
    send_to_webhook(client, telegram_text_update("forget that I'm a teacher"))
    chat_model.script_portrait(REWRITTEN)
    scheduler.tick()

    assert TEACHER_FACT not in chat_model.portrait_calls[-1].history[0].text
    assert len(chat_model.portrait_calls) == 2


def test_a_failed_rewrite_after_a_deletion_clears_the_portrait(
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
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )

    item_id = memory_item_id(client, headers, TEACHER_FACT)
    client.delete(f"/api/memory-items/{item_id}", headers=headers)
    chat_model.script_portrait(RuntimeError("model down"))
    scheduler.tick()
    scheduler.tick()

    assert portrait_shown(client, headers) is None
    assert len(chat_model.portrait_calls) == 2
