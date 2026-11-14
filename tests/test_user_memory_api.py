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
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_onboarding import onboarding_answers
from tests.test_post_conversation import (
    have_conversation,
    memory_contents,
    processing_answer,
)

MISSING_ID = "00000000-0000-0000-0000-000000000000"


def remember(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    summary: str,
    operations: list[dict[str, Any]],
) -> None:
    """Have one processed Conversation with the given summary and operations."""
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "a message",
        processing_answer(summary=summary, mood="calm", operations=operations),
    )


def test_memory_items_are_listed_by_category_in_category_order(
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
    remember(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "Chat.",
        [
            {"action": "add", "category": "What helps", "content": "Swimming"},
            {"action": "add", "category": "Life details", "content": "Lives with Sam"},
            {"action": "add", "category": "What helps", "content": "Walking"},
        ],
    )

    groups = client.get("/api/memory-items", headers=headers).json()["groups"]

    assert [group["category"] for group in groups] == ["Life details", "What helps"]
    [lives_with_sam] = groups[0]["items"]
    assert lives_with_sam["content"] == "Lives with Sam"
    assert lives_with_sam["source"] == "conversation"
    assert lives_with_sam["updated_at"] == clock.now().isoformat().replace(
        "+00:00", "Z"
    )
    assert [item["content"] for item in groups[1]["items"]] == ["Swimming", "Walking"]


def test_a_user_can_delete_one_memory_item(
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
    remember(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "Chat.",
        [
            {"action": "add", "category": "What helps", "content": "Swimming"},
            {"action": "add", "category": "What helps", "content": "Walking"},
        ],
    )
    groups = client.get("/api/memory-items", headers=headers).json()["groups"]
    swimming_id = groups[0]["items"][0]["id"]

    response = client.delete(f"/api/memory-items/{swimming_id}", headers=headers)

    assert response.status_code == 204
    assert memory_contents(client, headers) == {"What helps": ["Walking"]}
    again = client.delete(f"/api/memory-items/{swimming_id}", headers=headers)
    assert again.status_code == 404


def test_a_user_cannot_delete_someone_elses_memory_item(
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
    tom = auth_headers(auth_verifier, "user_tom")
    remember(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "Chat.",
        [{"action": "add", "category": "What helps", "content": "Swimming"}],
    )
    groups = client.get("/api/memory-items", headers=maya).json()["groups"]
    swimming_id = groups[0]["items"][0]["id"]

    response = client.delete(f"/api/memory-items/{swimming_id}", headers=tom)

    assert response.status_code == 404
    assert client.get("/api/memory-items", headers=tom).json() == {"groups": []}
    assert memory_contents(client, maya) == {"What helps": ["Swimming"]}


def test_deleting_all_memory_items_keeps_conversation_summaries(
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
    remember(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "Talked a lot.",
        [
            {"action": "add", "category": "What helps", "content": "Swimming"},
            {"action": "add", "category": "Goals", "content": "Run a 10k"},
        ],
    )

    response = client.delete("/api/memory-items", headers=headers)

    assert response.status_code == 204
    assert client.get("/api/memory-items", headers=headers).json() == {"groups": []}
    summaries = client.get("/api/conversation-summaries", headers=headers).json()
    assert [entry["summary"] for entry in summaries["summaries"]] == ["Talked a lot."]


def test_a_user_can_list_and_delete_conversation_summaries(
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
    tom = auth_headers(auth_verifier, "user_tom")
    remember(client, chat_model, clock, scheduler, seeded_settings, "First.", [])
    remember(client, chat_model, clock, scheduler, seeded_settings, "Second.", [])

    summaries = client.get("/api/conversation-summaries", headers=headers).json()[
        "summaries"
    ]
    assert [(entry["summary"], entry["mood"]) for entry in summaries] == [
        ("Second.", "calm"),
        ("First.", "calm"),
    ]
    first_id = summaries[1]["id"]

    assert (
        client.delete(f"/api/conversation-summaries/{first_id}", headers=tom)
    ).status_code == 404
    response = client.delete(f"/api/conversation-summaries/{first_id}", headers=headers)

    assert response.status_code == 204
    remaining = client.get("/api/conversation-summaries", headers=headers).json()
    assert [entry["summary"] for entry in remaining["summaries"]] == ["Second."]
    missing = client.delete(
        f"/api/conversation-summaries/{MISSING_ID}", headers=headers
    )
    assert missing.status_code == 404


def test_user_memory_routes_need_sign_in(client: TestClient) -> None:
    assert client.get("/api/memory-items").status_code == 401
    assert client.delete("/api/memory-items").status_code == 401
    assert client.delete(f"/api/memory-items/{MISSING_ID}").status_code == 401
    assert client.get("/api/conversation-summaries").status_code == 401
    assert client.delete(f"/api/conversation-summaries/{MISSING_ID}").status_code == 401


def test_onboarding_with_user_memory_on_saves_name_and_reasons_as_memory_items(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")

    client.put("/api/onboarding", json=onboarding_answers(), headers=headers)
    client.put("/api/onboarding", json=onboarding_answers(), headers=headers)

    groups = client.get("/api/memory-items", headers=headers).json()["groups"]
    assert {
        group["category"]: [item["content"] for item in group["items"]]
        for group in groups
    } == {
        "Life details": ["Goes by Maya"],
        "Goals": [
            "Came to Zeph for: Being more present, Relationships",
            "In their own words, what brings them here: New job, running on autopilot.",
        ],
    }
    assert {item["source"] for group in groups for item in group["items"]} == {
        "onboarding"
    }


def test_onboarding_with_user_memory_off_saves_no_memory_items(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")

    client.put(
        "/api/onboarding",
        json=onboarding_answers(user_memory_enabled=False),
        headers=headers,
    )

    assert client.get("/api/memory-items", headers=headers).json() == {"groups": []}


def test_onboarding_with_user_memory_off_by_an_admin_saves_no_memory_items(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    headers = auth_headers(auth_verifier, "user_maya")
    client.put("/api/admin/features/user_memory", json={"on": False}, headers=admin)

    client.put("/api/onboarding", json=onboarding_answers(), headers=headers)

    assert client.get("/api/memory-items", headers=headers).json()["groups"] == []


def test_onboarding_memories_reach_the_first_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    client.put("/api/onboarding", json=onboarding_answers(), headers=headers)
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_understanding(
        understanding_answer(memory_categories=["Life details", "Goals"])
    )
    chat_model.script("hi Maya")

    send_to_webhook(client, telegram_text_update("hello"))

    [reply_call] = chat_model.calls
    assert "Goes by Maya" in reply_call.instructions
    assert "Came to Zeph for: Being more present, Relationships" in (
        reply_call.instructions
    )
