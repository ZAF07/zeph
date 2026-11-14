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
)
from tests.telegram_helpers import (
    OWNER_AUTH_ID,
    OWNER_TELEGRAM_USER_ID,
    auth_headers,
    connect_owner_telegram,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_life_threads import (
    MEI_STORY,
    end_conversation,
    new_thread,
    start_mei_thread,
    thread_keeping_answer,
    understanding_sees,
)
from tests.test_post_conversation import (
    have_conversation,
    processing_answer,
    quiet_gap,
)
from tests.test_settings_via_chat import reply_call


def life_threads(client: TestClient, headers: dict[str, str]) -> list[dict[str, Any]]:
    """Get the User's Life Threads through the Dashboard API."""
    response = client.get("/api/life-threads", headers=headers)
    assert response.status_code == 200
    threads: list[dict[str, Any]] = response.json()["threads"]
    return threads


def maya_headers(auth_verifier: FakeAuthVerifier) -> dict[str, str]:
    """Build the Dashboard API headers for the User the tests talk as."""
    return auth_headers(auth_verifier, "user_maya")


def test_a_user_sees_their_threads_open_first_with_story_and_when_updated(
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
        "Mei helped me move flat, all sorted now",
        [new_thread(title="Moving flat", story="Moved in March.", is_open=False)],
    )
    clock.advance(timedelta(days=1))
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)

    threads = life_threads(client, maya_headers(auth_verifier))

    assert [
        (thread["title"], thread["story"], thread["is_open"]) for thread in threads
    ] == [
        ("Falling-out with Mei", MEI_STORY, True),
        ("Moving flat", "Moved in March.", False),
    ]
    assert threads[0]["updated_at"] > threads[1]["updated_at"]
    assert set(threads[0]) == {"id", "title", "story", "is_open", "updated_at"}


def test_a_deleted_thread_is_gone_and_never_reminded_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = maya_headers(auth_verifier)
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)
    [thread] = life_threads(client, headers)

    deleted = client.delete(f"/api/life-threads/{thread['id']}", headers=headers)
    deleted_again = client.delete(f"/api/life-threads/{thread['id']}", headers=headers)
    seen = understanding_sees(client, chat_model, "Mei's wedding is next week!")

    assert deleted.status_code == 204
    assert deleted_again.status_code == 404
    assert life_threads(client, headers) == []
    assert "Falling-out with Mei" not in seen
    users = client.get(
        "/api/admin/users", headers=owner_headers(client, auth_verifier)
    ).json()["users"]
    counts = {user["email"]: user["life_thread_count"] for user in users}
    assert counts["user_maya@example.com"] == 0


def test_a_user_cannot_see_or_delete_another_users_thread(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_owner_telegram(client, auth_verifier, chat_channel)
    chat_model.script_thread_keeping(thread_keeping_answer([new_thread()]))
    chat_model.script("mm, I hear you")
    send_to_webhook(
        client,
        telegram_text_update(
            "Mei and I fell out", OWNER_TELEGRAM_USER_ID, username="owner_tg"
        ),
    )
    clock.advance(quiet_gap(seeded_settings) * 2)
    chat_model.script_processing(processing_answer())
    scheduler.tick()
    [owners_thread] = life_threads(client, auth_headers(auth_verifier, OWNER_AUTH_ID))
    connect_telegram(client, auth_verifier, chat_channel)
    headers = maya_headers(auth_verifier)

    deleted = client.delete(f"/api/life-threads/{owners_thread['id']}", headers=headers)

    assert life_threads(client, headers) == []
    assert deleted.status_code == 404
    assert life_threads(client, auth_headers(auth_verifier, OWNER_AUTH_ID)) != []


def test_threads_are_shown_with_user_memory_off(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = maya_headers(auth_verifier)
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)

    [thread] = life_threads(client, headers)

    assert thread["title"] == "Falling-out with Mei"


def test_a_thread_deleted_while_conversation_end_keeps_it_stays_deleted(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = maya_headers(auth_verifier)
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)
    [thread] = life_threads(client, headers)

    def delete_the_thread() -> None:
        client.delete(f"/api/life-threads/{thread['id']}", headers=headers)

    chat_model.before_next_thread_keeping = delete_the_thread
    chat_model.script_thread_keeping(
        thread_keeping_answer([{"thread": 1, "story": "Made up with Mei."}])
    )
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "Mei and I made up",
        processing_answer(summary="Made up with Mei.", mood="relieved"),
    )

    assert life_threads(client, headers) == []


def test_forgetting_a_thread_in_chat(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = maya_headers(auth_verifier)
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)
    listed = reply_call(
        client, chat_model, "what do you remember?", ToolCall("list_memories", {}), "."
    ).tool_results[0]
    [number] = [
        line.split(".")[0]
        for line in listed.splitlines()
        if "Falling-out with Mei" in line
    ]

    call = reply_call(
        client,
        chat_model,
        "forget the thing about my sister",
        ToolCall("list_memories", {}),
        ToolCall("forget_memory", {"number": int(number)}),
        "Done, I've forgotten that.",
    )
    seen = understanding_sees(client, chat_model, "Mei's wedding is next week!")

    assert MEI_STORY in listed
    assert "Falling-out with Mei" in call.tool_results[1]
    assert life_threads(client, headers) == []
    assert "Falling-out with Mei" not in seen
