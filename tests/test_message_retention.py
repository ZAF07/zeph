from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

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
from tests.test_post_conversation import (
    have_conversation,
    memory_contents,
    processing_answer,
)

ONE_DAY = timedelta(days=1)
ONE_MINUTE = timedelta(minutes=1)


def message_contents(engine: Engine) -> list[str]:
    """Every saved message's text, oldest first."""
    with engine.connect() as connection:
        return list(
            connection.execute(
                text("SELECT content FROM conversation_messages ORDER BY position")
            ).scalars()
        )


def retention(seeded_settings: dict[str, Any]) -> timedelta:
    """The seeded time raw messages are kept for."""
    return timedelta(days=seeded_settings["message_retention_days"])


def test_a_tick_deletes_messages_older_than_the_retention_period(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    sent_at = clock.now()
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "I started a new job in design",
        processing_answer(
            summary="Shared that they started a new job.",
            operations=[
                {"action": "add", "category": "Life details", "content": "Designer"}
            ],
        ),
    )

    clock.advance(sent_at + retention(seeded_settings) - ONE_MINUTE - clock.now())
    scheduler.tick()
    assert message_contents(engine) == [
        "I started a new job in design",
        "mm, I hear you",
    ]

    clock.advance(2 * ONE_MINUTE)
    scheduler.tick()

    assert message_contents(engine) == []
    summaries = client.get("/api/conversation-summaries", headers=headers).json()
    assert [entry["summary"] for entry in summaries["summaries"]] == [
        "Shared that they started a new job."
    ]
    assert memory_contents(client, headers) == {"Life details": ["Designer"]}


def test_newer_messages_stay_when_older_ones_are_deleted(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("hey!")
    send_to_webhook(client, telegram_text_update("an old message"))
    clock.advance(retention(seeded_settings) - ONE_DAY)
    chat_model.script("hello again!")
    send_to_webhook(client, telegram_text_update("a newer message"))

    clock.advance(2 * ONE_DAY)
    chat_model.script_processing(processing_answer(), processing_answer())
    scheduler.tick()

    assert message_contents(engine) == ["a newer message", "hello again!"]


def test_the_companion_still_replies_after_its_saved_state_is_cleared(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("hey!")
    send_to_webhook(client, telegram_text_update("an old message"))
    clock.advance(retention(seeded_settings) + ONE_DAY)
    chat_model.script_processing(processing_answer())
    scheduler.tick()
    chat_channel.sent.clear()

    chat_model.script("good to hear from you")
    send_to_webhook(client, telegram_text_update("back again"))

    assert [message.text for message in chat_channel.sent] == ["good to hear from you"]
    assert message_contents(engine) == ["back again", "good to hear from you"]


def test_an_admin_can_shorten_the_retention_period(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("hey!")
    send_to_webhook(client, telegram_text_update("a week-old message"))

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"message_retention_days": 7}},
        headers=admin,
    )
    clock.advance(7 * ONE_DAY + ONE_MINUTE)
    chat_model.script_processing(processing_answer())
    scheduler.tick()

    assert response.status_code == 200
    assert response.json()["settings"]["message_retention_days"]["value"] == 7
    assert message_contents(engine) == []
