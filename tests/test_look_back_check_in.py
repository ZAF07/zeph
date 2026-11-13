import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import (
    MIGRATIONS_DIR,
    migrate,
    seed_check_in_kinds,
)
from tests.conftest import CHECK_IN_KINDS_SEED_FILE
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    auth_headers,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_admin_check_ins import list_kinds
from tests.test_check_in_sending import (
    ONE_DAY,
    recent_check_ins,
    send_answer,
    set_up_user_with_check_ins,
)
from tests.test_onboarding import onboarding_answers
from tests.test_send_photo_back import add_shared_photo

LOOK_BACK = "A look back at a photo"
MONSTERA = "A monstera plant in a white pot by a bright window."
MONSTERA_NOTE = "Their first houseplant, bought when they moved into their flat."
BEACH = "Two friends laughing on a windy beach at sunset."
BEACH_NOTE = "A trip with their best friend before she moved abroad."


def look_back_answer(message: str, photo: Any) -> str:
    """Build the Check-in model's JSON answer for a "look back at a photo" send.

    Args:
        message: The Check-in message.
        photo: The Shared Photo's number, as the model names it.

    Returns:
        The JSON answer.
    """
    return json.dumps(
        {"decision": "send", "kind": LOOK_BACK, "message": message, "photo": photo}
    )


def set_up_user_with_shared_photos(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    **overrides: Any,
) -> dict[str, str]:
    """Set up a User due a Check-in a day from now, with two Shared Photos.

    Args:
        client: The backend's test client.
        auth_verifier: The fake auth verifier.
        chat_channel: The fake chat channel.
        **overrides: Onboarding answers to change.

    Returns:
        The User's Dashboard API headers.
    """
    headers = set_up_user_with_check_ins(
        client, auth_verifier, chat_channel, **overrides
    )
    add_shared_photo(
        client,
        headers,
        "monstera-file-id",
        MONSTERA,
        MONSTERA_NOTE,
        sent_at=datetime(2026, 11, 3, 9, tzinfo=UTC),
    )
    add_shared_photo(client, headers, "beach-file-id", BEACH, BEACH_NOTE)
    chat_channel.sent.clear()
    return headers


def test_a_look_back_check_in_sends_the_named_shared_photo_after_its_message(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_shared_photos(client, auth_verifier, chat_channel)
    chat_model.script(look_back_answer("saw this again, how's the monstera?", 2))

    clock.advance(ONE_DAY)
    scheduler.tick()

    assert chat_channel.events == [
        "text: saw this again, how's the monstera?",
        "photo: monstera-file-id",
    ]
    assert [photo.chat_id for photo in chat_channel.sent_photos] == [TELEGRAM_CHAT_ID]
    [line] = chat_model.calls[-1].history
    assert LOOK_BACK in line.text
    assert f"1. 10 Nov 2026: {BEACH} Why it matters: {BEACH_NOTE}" in line.text
    assert f"2. 3 Nov 2026: {MONSTERA} Why it matters: {MONSTERA_NOTE}" in line.text
    assert '"photo"' in line.text
    assert recent_check_ins(client, headers)[0]["kind"] == LOOK_BACK


def test_a_reply_to_a_look_back_check_in_has_the_photo_in_its_history(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_shared_photos(client, auth_verifier, chat_channel)
    chat_model.script(look_back_answer("how's this one doing?", 2))
    clock.advance(ONE_DAY)
    scheduler.tick()

    clock.advance(timedelta(hours=2))
    chat_model.script("so glad it's thriving!")
    send_to_webhook(client, telegram_text_update("it's huge now!"))

    reply_call = chat_model.calls[-1]
    assert [line.text for line in reply_call.history] == [
        "how's this one doing?",
        "[You sent them back their own photo with the send_photo tool. "
        f"It shows: {MONSTERA}]",
        "it's huge now!",
    ]


def test_with_no_shared_photos_the_look_back_kind_is_never_offered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_channel.sent.clear()
    chat_model.script(
        look_back_answer("how's the monstera?", 1),
        send_answer("hey Maya, how's your day?"),
    )

    clock.advance(ONE_DAY)
    scheduler.tick()

    assert chat_channel.sent == []
    [line] = chat_model.calls[-1].history
    assert LOOK_BACK not in line.text
    assert "Shared Photos" not in line.text

    clock.advance(timedelta(minutes=5))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey Maya, how's your day?"]
    assert chat_channel.sent_photos == []


def test_with_user_memory_off_the_look_back_kind_and_photos_are_never_offered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_shared_photos(
        client, auth_verifier, chat_channel, user_memory_enabled=False
    )
    chat_model.script(
        look_back_answer("how's the monstera?", 1),
        send_answer("hey Maya, how's your day?"),
    )

    clock.advance(ONE_DAY)
    scheduler.tick()

    assert chat_channel.sent == []
    [line] = chat_model.calls[-1].history
    assert LOOK_BACK not in line.text
    assert MONSTERA not in line.text

    clock.advance(timedelta(minutes=5))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey Maya, how's your day?"]
    assert chat_channel.sent_photos == []


@pytest.mark.parametrize("photo", [None, 3, 0, "1", True])
def test_a_look_back_answer_without_a_listed_photo_sends_nothing_and_is_tried_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    photo: Any,
) -> None:
    set_up_user_with_shared_photos(client, auth_verifier, chat_channel)
    chat_model.script(
        look_back_answer("how's the monstera?", photo),
        look_back_answer("how's the monstera?", 2),
    )

    clock.advance(ONE_DAY)
    scheduler.tick()
    assert chat_channel.sent == []

    clock.advance(timedelta(minutes=5))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["how's the monstera?"]
    assert [photo.file_id for photo in chat_channel.sent_photos] == ["monstera-file-id"]


def test_a_photo_named_with_another_kind_is_not_sent(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_shared_photos(client, auth_verifier, chat_channel)
    chat_model.script(
        json.dumps(
            {
                "decision": "send",
                "kind": "A casual hello",
                "message": "hey, how are you?",
                "photo": 1,
            }
        )
    )

    clock.advance(ONE_DAY)
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey, how are you?"]
    assert chat_channel.sent_photos == []


def test_a_failed_photo_send_still_sends_the_message_and_logs_the_error(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    headers = set_up_user_with_shared_photos(client, auth_verifier, chat_channel)
    chat_channel.photo_send_failure = RuntimeError("Telegram said no")
    chat_model.script(look_back_answer("how's the monstera?", 2))

    with caplog.at_level(logging.ERROR):
        clock.advance(ONE_DAY)
        scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["how's the monstera?"]
    assert chat_channel.sent_photos == []
    assert "Could not send the Check-in's Shared Photo" in caplog.text
    assert recent_check_ins(client, headers)[0]["outcome"] == "sent"

    clock.advance(timedelta(hours=2))
    chat_model.script("nice!")
    send_to_webhook(client, telegram_text_update("it's huge now!"))
    assert [line.text for line in chat_model.calls[-1].history] == [
        "how's the monstera?",
        "it's huge now!",
    ]


def test_the_users_check_ins_page_lists_the_look_back_kind_only_with_user_memory(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    maya = auth_headers(auth_verifier, "user_maya")
    client.put("/api/onboarding", json=onboarding_answers(), headers=maya)
    assert LOOK_BACK in [
        kind["name"]
        for kind in client.get("/api/check-ins", headers=maya).json()["kinds"]
    ]

    client.patch("/api/me", json={"user_memory_enabled": False}, headers=maya)

    assert LOOK_BACK not in [
        kind["name"]
        for kind in client.get("/api/check-ins", headers=maya).json()["kinds"]
    ]


def test_admin_sees_the_look_back_kind_and_can_edit_and_remove_it(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    [look_back] = [
        kind for kind in list_kinds(client, admin) if kind["sends_shared_photo"]
    ]
    assert look_back["name"] == LOOK_BACK
    assert look_back["allowed_without_user_memory"] is False
    assert [kind["sends_shared_photo"] for kind in list_kinds(client, admin)] == [
        False,
        False,
        False,
        False,
        True,
    ]

    edited = client.put(
        f"/api/admin/check-in-kinds/{look_back['id']}",
        json={
            "name": "Remember this?",
            "description": "A photo you shared, sent back with a word about it.",
            "allowed_without_user_memory": False,
        },
        headers=admin,
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["sends_shared_photo"] is True
    assert edited.json()["name"] == "Remember this?"

    refused = client.put(
        f"/api/admin/check-in-kinds/{look_back['id']}",
        json={
            "name": "Remember this?",
            "description": "A photo you shared.",
            "allowed_without_user_memory": True,
        },
        headers=admin,
    )
    assert refused.status_code == 422
    assert "User Memory" in refused.json()["detail"]

    removed = client.delete(
        f"/api/admin/check-in-kinds/{look_back['id']}", headers=admin
    )
    assert removed.status_code == 204
    assert not any(kind["sends_shared_photo"] for kind in list_kinds(client, admin))


def test_an_edited_look_back_kind_still_sends_its_photo(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_shared_photos(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    [look_back] = [
        kind for kind in list_kinds(client, admin) if kind["sends_shared_photo"]
    ]
    client.put(
        f"/api/admin/check-in-kinds/{look_back['id']}",
        json={
            "name": "Remember this?",
            "description": "A photo you shared, sent back with a word about it.",
            "allowed_without_user_memory": False,
        },
        headers=admin,
    )
    chat_model.script(
        json.dumps(
            {
                "decision": "send",
                "kind": "Remember this?",
                "message": "remember this beach day?",
                "photo": 1,
            }
        )
    )

    clock.advance(ONE_DAY)
    scheduler.tick()

    assert [photo.file_id for photo in chat_channel.sent_photos] == ["beach-file-id"]
    [line] = chat_model.calls[-1].history
    assert "Remember this?" in line.text


def stored_kinds(engine: Engine) -> list[tuple[str, bool, int]]:
    """Read every Check-in Kind's name, photo flag and place straight from the database.

    Args:
        engine: The database engine.

    Returns:
        Each Kind's name, whether it sends a Shared Photo and its sort order.
    """
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT name, sends_shared_photo, sort_order FROM check_in_kinds "
                "ORDER BY sort_order"
            )
        ).all()
    return [(row.name, row.sends_shared_photo, row.sort_order) for row in rows]


def downgrade_to_before_look_back(database_url: str) -> None:
    """Take the database back to before the "look back at a photo" Kind.

    Args:
        database_url: The test database's URL.
    """
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.downgrade(config, "0019")


def test_an_existing_install_gets_the_look_back_kind_last(
    engine: Engine, database_url: str
) -> None:
    downgrade_to_before_look_back(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM check_in_kinds"))
            connection.execute(
                text(
                    "INSERT INTO check_in_kinds (id, name, description, "
                    "allowed_without_user_memory, sort_order) VALUES "
                    "(gen_random_uuid(), 'A hello', 'Hi.', true, 0), "
                    "(gen_random_uuid(), 'A nudge', 'Go on.', true, 3)"
                )
            )
    finally:
        migrate(database_url)

    assert stored_kinds(engine) == [
        ("A hello", False, 0),
        ("A nudge", False, 3),
        (LOOK_BACK, True, 4),
    ]


def test_a_fresh_install_gets_every_kind_from_the_seed_file(
    engine: Engine, database_url: str
) -> None:
    downgrade_to_before_look_back(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM check_in_kinds"))
    finally:
        migrate(database_url)
    seed_check_in_kinds(engine, CHECK_IN_KINDS_SEED_FILE)

    assert [(name, photo) for name, photo, _ in stored_kinds(engine)] == [
        ("A casual hello", False),
        ("A follow-up", False),
        ("A present-moment pause", False),
        ("A thought to reflect on", False),
        (LOOK_BACK, True),
    ]
