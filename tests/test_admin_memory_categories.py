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


def list_categories(client: TestClient, admin: dict[str, str]) -> list[dict[str, Any]]:
    """Fetch every Memory Category through the admin API."""
    response = client.get("/api/admin/memory-categories", headers=admin)
    assert response.status_code == 200, response.text
    categories: list[dict[str, Any]] = response.json()["categories"]
    return categories


def category_named(
    client: TestClient, admin: dict[str, str], name: str
) -> dict[str, Any]:
    """Find one Memory Category by name."""
    [category] = [
        category
        for category in list_categories(client, admin)
        if category["name"] == name
    ]
    return category


def add_category(
    client: TestClient, admin: dict[str, str], **overrides: Any
) -> dict[str, Any]:
    """Add a Memory Category and return it."""
    body = {"name": "Work", "description": "Job, colleagues, career goals"}
    body.update(overrides)
    response = client.post("/api/admin/memory-categories", json=body, headers=admin)
    assert response.status_code == 201, response.text
    category: dict[str, Any] = response.json()
    return category


def edit_category(
    client: TestClient, admin: dict[str, str], category: dict[str, Any], **changes: Any
) -> dict[str, Any]:
    """Save changes to a Memory Category's name, description or always include."""
    body = {
        "name": category["name"],
        "description": category["description"],
        "always_include": category["always_include"],
    }
    body.update(changes)
    response = client.put(
        f"/api/admin/memory-categories/{category['id']}", json=body, headers=admin
    )
    assert response.status_code == 200, response.text
    edited: dict[str, Any] = response.json()
    return edited


def archive(client: TestClient, admin: dict[str, str], category_id: str) -> None:
    """Archive a Memory Category."""
    response = client.post(
        f"/api/admin/memory-categories/{category_id}/archive", headers=admin
    )
    assert response.status_code == 200, response.text
    assert response.json()["archived"] is True


def test_the_starter_categories_are_listed_in_order_with_item_counts(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "my sister Jo and my partner Sam",
        processing_answer(
            operations=[
                {"action": "add", "category": "Relationships", "content": "Sister Jo"},
                {"action": "add", "category": "Relationships", "content": "Sam"},
            ]
        ),
    )

    categories = list_categories(client, admin)

    assert [
        (category["name"], category["always_include"], category["archived"])
        for category in categories
    ] == [
        ("Life details", False, False),
        ("Relationships", False, False),
        ("Goals", False, False),
        ("Values & beliefs", True, False),
        ("Challenges", True, False),
        ("Preferences", True, False),
        ("What helps", False, False),
    ]
    item_counts = {category["name"]: category["item_count"] for category in categories}
    assert item_counts["Relationships"] == 2
    assert item_counts["Goals"] == 0
    assert all(category["description"] for category in categories)


def test_a_new_category_is_used_by_the_next_processing_and_retrieval(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")

    work = add_category(client, admin, name="  Work ")

    assert (work["name"], work["always_include"], work["archived"]) == (
        "Work",
        False,
        False,
    )
    assert list_categories(client, admin)[-1]["name"] == "Work"
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "my manager keeps changing the deadline",
        processing_answer(
            operations=[
                {
                    "action": "add",
                    "category": "Work",
                    "content": "Manager moves deadlines",
                }
            ]
        ),
    )
    assert "- Work: Job, colleagues, career goals" in (
        chat_model.processing_calls[-1].history[0].text
    )
    assert memory_contents(client, headers) == {"Work": ["Manager moves deadlines"]}

    chat_model.calls.clear()
    chat_model.script_retrieval("Work")
    chat_model.script("ugh, again?")
    send_to_webhook(client, telegram_text_update("deadline moved AGAIN"))

    assert "- Work:" in chat_model.retrieval_calls[-1].history[0].text
    assert "Manager moves deadlines" in chat_model.calls[-1].instructions


def test_an_archived_category_keeps_its_items_but_gets_no_new_ones(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "swimming really helps me",
        processing_answer(
            operations=[
                {"action": "add", "category": "What helps", "content": "Swimming"}
            ]
        ),
    )

    archive(client, admin, category_named(client, admin, "What helps")["id"])

    archived = category_named(client, admin, "What helps")
    assert (archived["archived"], archived["item_count"]) == (True, 1)
    assert memory_contents(client, headers) == {"What helps": ["Swimming"]}
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "walking helps too",
        processing_answer(
            operations=[
                {"action": "add", "category": "What helps", "content": "Walking"}
            ]
        ),
    )
    assert "- What helps:" not in chat_model.processing_calls[-1].history[0].text
    assert memory_contents(client, headers) == {"What helps": ["Swimming"]}

    chat_model.calls.clear()
    chat_model.script("mm")
    send_to_webhook(client, telegram_text_update("long day"))
    assert chat_model.retrieval_calls == []
    assert "Swimming" not in chat_model.calls[-1].instructions


def test_a_restored_category_gets_new_items_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    what_helps = category_named(client, admin, "What helps")
    archive(client, admin, what_helps["id"])

    response = client.post(
        f"/api/admin/memory-categories/{what_helps['id']}/restore", headers=admin
    )

    assert response.status_code == 200, response.text
    assert response.json()["archived"] is False
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "walking helps",
        processing_answer(
            operations=[
                {"action": "add", "category": "What helps", "content": "Walking"}
            ]
        ),
    )
    assert memory_contents(client, headers) == {"What helps": ["Walking"]}


def test_admins_can_rename_describe_and_toggle_always_include(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "swimming really helps me",
        processing_answer(
            operations=[
                {"action": "add", "category": "What helps", "content": "Swimming"}
            ]
        ),
    )

    edited = edit_category(
        client,
        admin,
        category_named(client, admin, "What helps"),
        name="What steadies them",
        description="Practices that calm them down",
        always_include=True,
    )

    assert (edited["name"], edited["description"], edited["always_include"]) == (
        "What steadies them",
        "Practices that calm them down",
        True,
    )
    assert category_named(client, admin, "What steadies them")["item_count"] == 1
    chat_model.calls.clear()
    chat_model.script("mm")
    send_to_webhook(client, telegram_text_update("long day"))
    assert chat_model.retrieval_calls == []
    reply_instructions = chat_model.calls[-1].instructions
    assert "What steadies them:\n- Swimming" in reply_instructions


def test_renaming_an_onboarding_category_keeps_onboarding_memories_working(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    edit_category(client, admin, category_named(client, admin, "Goals"), name="Aims")
    headers = auth_headers(auth_verifier, "user_maya")

    client.put("/api/onboarding", json=onboarding_answers(), headers=headers)

    assert set(memory_contents(client, headers)) == {"Life details", "Aims"}


def test_category_names_must_be_filled_in_and_unique(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    goals = category_named(client, admin, "Goals")

    blank_name = client.post(
        "/api/admin/memory-categories",
        json={"name": " ", "description": "Something"},
        headers=admin,
    )
    blank_description = client.post(
        "/api/admin/memory-categories",
        json={"name": "Work", "description": ""},
        headers=admin,
    )
    taken_name = client.post(
        "/api/admin/memory-categories",
        json={"name": "goals", "description": "Something"},
        headers=admin,
    )
    renamed_to_taken = client.put(
        f"/api/admin/memory-categories/{goals['id']}",
        json={"name": "Challenges", "description": "x", "always_include": False},
        headers=admin,
    )
    kept_own_name = client.put(
        f"/api/admin/memory-categories/{goals['id']}",
        json={"name": "GOALS", "description": "x", "always_include": False},
        headers=admin,
    )

    assert blank_name.status_code == 422
    assert blank_name.json()["detail"] == "A Memory Category needs a name."
    assert blank_description.status_code == 422
    assert blank_description.json()["detail"] == (
        "A Memory Category needs a description."
    )
    assert taken_name.status_code == 422
    assert taken_name.json()["detail"] == "There is already a category called Goals."
    assert renamed_to_taken.status_code == 422
    assert kept_own_name.status_code == 200
    assert len(list_categories(client, admin)) == 7


def test_categories_can_never_be_deleted(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    goals = category_named(client, admin, "Goals")

    response = client.delete(
        f"/api/admin/memory-categories/{goals['id']}", headers=admin
    )

    assert response.status_code == 405
    assert category_named(client, admin, "Goals") == goals


def test_changing_a_missing_category_is_not_found(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    base = f"/api/admin/memory-categories/{MISSING_ID}"
    edit = {"name": "x", "description": "x", "always_include": False}

    assert client.put(base, json=edit, headers=admin).status_code == 404
    assert client.post(f"{base}/archive", headers=admin).status_code == 404
    assert client.post(f"{base}/restore", headers=admin).status_code == 404


def test_only_admins_can_manage_categories(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    owner_headers(client, auth_verifier)
    maya = auth_headers(auth_verifier, "user_maya")
    client.get("/api/me", headers=maya)

    listed = client.get("/api/admin/memory-categories", headers=maya)
    added = client.post(
        "/api/admin/memory-categories",
        json={"name": "Work", "description": "Job"},
        headers=maya,
    )

    assert listed.status_code == 403
    assert added.status_code == 403
