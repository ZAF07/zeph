from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import BOT_USERNAME
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
    ToolCall,
)
from tests.telegram_helpers import (
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_admin_memory_categories import category_named, edit_category
from tests.test_check_in_sending import (
    ONE_DAY,
    send_answer,
    set_up_user_with_check_ins,
    skip_answer,
)
from tests.test_onboarding import onboarding_answers
from tests.test_post_conversation import have_conversation, processing_answer
from tests.test_settings_via_chat import reply_call


def get_home(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    """Fetch the User's Dashboard home through the API."""
    response = client.get("/api/home", headers=headers)
    assert response.status_code == 200, response.text
    home: dict[str, Any] = response.json()
    return home


def iso(clock: FakeClock) -> str:
    """Write the clock's time as the API sends it."""
    return clock.now().isoformat().replace("+00:00", "Z")


def test_a_new_user_sees_telegram_not_connected_and_nothing_remembered(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")

    home = get_home(client, headers)

    assert home["telegram_connection"] is None
    assert home["last_conversation_at"] is None
    assert home["check_ins"]["enabled"] is False
    assert home["check_ins"]["last_sent"] is None
    assert home["goals"] == []
    assert home["recently_remembered"] == []


def test_home_shows_the_telegram_connection_and_last_conversation(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    clock.advance(timedelta(hours=2))
    chat_model.script("mm, I hear you")
    send_to_webhook(client, telegram_text_update("long day"))

    home = get_home(client, headers)

    assert home["telegram_connection"]["telegram_username"] == "maya_l"
    assert home["last_conversation_at"] == iso(clock)
    assert home["telegram_chat_url"] == f"https://t.me/{BOT_USERNAME}"


def test_home_shows_goals_and_the_newest_memory_items_with_their_category(
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
    client.put(
        "/api/onboarding",
        json=onboarding_answers(onboarding_note=None),
        headers=headers,
    )
    clock.advance(timedelta(hours=1))
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "a message",
        processing_answer(
            operations=[
                {"action": "add", "category": "What helps", "content": "Swimming"},
                {"action": "add", "category": "Goals", "content": "Phone-free dinners"},
                {"action": "add", "category": "Relationships", "content": "Sister Jo"},
            ]
        ),
    )

    home = get_home(client, headers)

    assert [item["content"] for item in home["goals"]] == [
        "Phone-free dinners",
        "Came to Zeph for: Being more present, Relationships",
    ]
    assert [
        (item["content"], item["category"]) for item in home["recently_remembered"]
    ] == [
        ("Swimming", "What helps"),
        ("Phone-free dinners", "Goals"),
        ("Sister Jo", "Relationships"),
    ]
    assert home["recently_remembered"][0]["updated_at"] == iso(clock)


def test_with_memory_on_home_and_me_have_no_memory_note(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    client.put("/api/onboarding", json=onboarding_answers(), headers=headers)

    home = get_home(client, headers)

    assert home["memory_note"] == ""
    assert client.get("/api/me", headers=headers).json()["memory_note"] == ""


def test_with_user_memory_paused_home_shows_memories_with_the_paused_note(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    seeded_settings: dict[str, Any],
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    client.put("/api/onboarding", json=onboarding_answers(), headers=headers)
    me = client.patch(
        "/api/me", json={"user_memory_enabled": False}, headers=headers
    ).json()

    home = get_home(client, headers)

    assert home["goals"] != []
    assert home["recently_remembered"] != []
    assert home["memory_note"] == seeded_settings["memory_paused_note"]
    assert me["memory_note"] == seeded_settings["memory_paused_note"]


def test_with_user_memory_off_by_an_admin_home_shows_the_not_available_note(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    headers = auth_headers(auth_verifier, "user_maya")
    client.put("/api/onboarding", json=onboarding_answers(), headers=headers)
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)
    client.put("/api/admin/features/user_memory", json={"on": False}, headers=admin)

    home = get_home(client, headers)

    assert home["recently_remembered"] != []
    assert home["memory_note"] == seeded_settings["memory_not_available_note"]
    assert (
        client.get("/api/me", headers=headers).json()["memory_note"]
        == seeded_settings["memory_not_available_note"]
    )


def test_with_only_the_admins_switch_off_home_shows_the_not_available_note(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    headers = auth_headers(auth_verifier, "user_maya")
    client.put("/api/onboarding", json=onboarding_answers(), headers=headers)
    client.put("/api/admin/features/user_memory", json={"on": False}, headers=admin)

    home = get_home(client, headers)

    assert client.get("/api/me", headers=headers).json()["user_memory_enabled"]
    assert home["goals"] != []
    assert home["recently_remembered"] != []
    assert home["memory_note"] == seeded_settings["memory_not_available_note"]


def test_an_edited_memory_note_is_shown_as_set(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
) -> None:
    admin = owner_headers(client, auth_verifier)
    headers = auth_headers(auth_verifier, "user_maya")
    client.put("/api/onboarding", json=onboarding_answers(), headers=headers)
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)
    saved = client.patch(
        "/api/admin/settings",
        json={"values": {"memory_paused_note": "**Paused.** Edited."}},
        headers=admin,
    )

    assert saved.status_code == 200, saved.text
    assert get_home(client, headers)["memory_note"] == "**Paused.** Edited."


def test_goals_follow_the_goals_category_when_an_admin_renames_it(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    headers = auth_headers(auth_verifier, "user_maya")
    client.put(
        "/api/onboarding",
        json=onboarding_answers(onboarding_note=None),
        headers=headers,
    )

    edit_category(client, admin, category_named(client, admin, "Goals"), name="Aims")

    [goal] = get_home(client, headers)["goals"]
    assert goal["content"] == "Came to Zeph for: Being more present, Relationships"


def test_home_shows_the_last_check_in_sent_and_never_a_next_time(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_model.script(send_answer("hey Maya"))
    clock.advance(ONE_DAY)
    scheduler.tick()
    sent_at = iso(clock)
    chat_model.script(skip_answer("she's busy"))
    clock.advance(ONE_DAY)
    scheduler.tick()

    check_ins = get_home(client, headers)["check_ins"]

    assert check_ins["enabled"] is True
    assert check_ins["frequency"] == "most_days"
    assert check_ins["paused"] is False
    assert check_ins["last_sent"]["kind"] == "A casual hello"
    assert check_ins["last_sent"]["decided_at"] == sent_at
    assert check_ins["last_sent"]["status"] == "no_reply"
    assert not any("next" in key for key in check_ins)


def test_home_shows_when_check_ins_are_paused_until(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    client.put("/api/check-ins/pause", json={"length": "week"}, headers=headers)

    check_ins = get_home(client, headers)["check_ins"]

    assert check_ins["paused"] is True
    assert check_ins["paused_until"] == (clock.now() + timedelta(weeks=1)).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
    assert check_ins["pause_changed_in_chat_at"] is None


def test_home_says_when_check_ins_were_paused_in_chat(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    paused_at = iso(clock)
    reply_call(
        client,
        chat_model,
        "give me a week off from check-ins",
        ToolCall("pause_check_ins", {"length": "week"}),
        "Done.",
    )

    check_ins = get_home(client, headers)["check_ins"]

    assert check_ins["paused"] is True
    assert check_ins["pause_changed_in_chat_at"] == paused_at


def test_home_needs_a_signed_in_user(client: TestClient) -> None:
    assert client.get("/api/home").status_code == 401
