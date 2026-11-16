from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import CheckIn, CheckInOutcome, Conversation, Feature, User
from companion.core.ports import MessageRefusedError
from tests.conftest import INITIAL_ADMIN_EMAIL
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_check_in_hold_back import (
    due_users_needing_no_model,
    maya_id,
    next_due_at,
    selects_by_table,
)
from tests.test_check_in_schedule import SCHEDULE, onboard, only_entry, schedule
from tests.test_check_in_sending import (
    ONE_DAY,
    send_answer,
    send_check_ins,
    set_up_user_with_check_ins,
    skip_answer,
)
from tests.test_post_conversation import quiet_gap
from tests.test_usage_limits import set_message_limit
from tests.test_user_snapshot import add_due_users
from tests.test_web_search import change_settings

CHECK_IN_NOW = f"{SCHEDULE}/check-in-now"


def check_in_now(
    client: TestClient, admin: dict[str, str], user_ids: list[UUID]
) -> dict[str, str]:
    """Ask for a Check in Now through the admin API.

    Returns:
        Each User's result, by User ID.
    """
    response = client.post(
        CHECK_IN_NOW,
        json={"user_ids": [str(user_id) for user_id in user_ids]},
        headers=admin,
    )
    assert response.status_code == 200, response.text
    return {item["user_id"]: item["result"] for item in response.json()["results"]}


def newest_log_entry(client: TestClient, admin: dict[str, str]) -> dict[str, Any]:
    """Fetch the newest Check-in Log entry through the admin API."""
    response = client.get("/api/admin/check-ins", headers=admin)
    assert response.status_code == 200, response.text
    entry: dict[str, Any] = response.json()["entries"][0]
    return entry


def requested_maya(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    **overrides: Any,
) -> tuple[dict[str, str], dict[str, str], UUID]:
    """Set Maya up with Check-ins on and sign in the Admin.

    Returns:
        Maya's headers, the Admin's headers and Maya's ID.
    """
    headers = set_up_user_with_check_ins(
        client, auth_verifier, chat_channel, **overrides
    )
    return headers, owner_headers(client, auth_verifier), maya_id(client, headers)


def test_each_selected_user_gets_their_result_and_only_requested_ones_wait(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    _, admin, maya = requested_maya(client, auth_verifier, chat_channel)
    sam = maya_id(
        client,
        onboard(client, auth_verifier, "user_sam", name="Sam", check_ins_enabled=True),
    )
    lee = maya_id(
        client,
        onboard(client, auth_verifier, "user_lee", name="Lee", check_ins_enabled=False),
    )

    results = check_in_now(client, admin, [maya, sam, lee])

    assert results == {
        str(maya): "requested",
        str(sam): "no_telegram_connection",
        str(lee): "not_opted_in",
    }
    waiting = {
        entry["name"]: entry["check_in_now_waiting"]
        for entry in schedule(client, admin)["entries"]
    }
    assert waiting == {"Maya": True, "Sam": False}


def test_a_paused_user_gets_the_check_in_on_the_next_tick_and_stays_paused(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    engine: Engine,
) -> None:
    headers, admin, maya = requested_maya(client, auth_verifier, chat_channel)
    client.put("/api/check-ins/pause", json={"length": "week"}, headers=headers)
    pause_ends = clock.now() + timedelta(weeks=1)
    clock.advance(timedelta(hours=1))

    check_in_now(client, admin, [maya])
    chat_model.script(send_answer("hey Maya, thinking of you"))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey Maya, thinking of you"]
    entry = newest_log_entry(client, admin)
    assert entry["outcome"] == "sent"
    assert entry["requested_by"] == INITIAL_ADMIN_EMAIL
    assert next_due_at(engine, maya) == clock.now() + ONE_DAY
    settings = client.get("/api/check-ins", headers=headers).json()
    assert settings["paused"] is True
    assert settings["paused_until"] == pause_ends.isoformat().replace("+00:00", "Z")
    assert settings["frequency"] == "most_days"
    assert only_entry(client, admin)["check_in_now_waiting"] is False


def test_quiet_hours_and_the_half_gap_do_not_hold_a_check_in_now_back(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    _, admin, maya = requested_maya(client, auth_verifier, chat_channel)
    chat_model.script(send_answer("first one"))
    clock.advance(ONE_DAY)
    scheduler.tick()
    clock.advance(timedelta(hours=6))

    check_in_now(client, admin, [maya])
    chat_model.script(send_answer("late one, in quiet hours"))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "first one",
        "late one, in quiet hours",
    ]


def test_the_check_ins_feature_off_for_the_user_does_not_hold_it_back(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    _, admin, maya = requested_maya(client, auth_verifier, chat_channel)
    response = client.put(
        f"/api/admin/users/{maya}/features/check_ins",
        json={"switch": "off"},
        headers=admin,
    )
    assert response.status_code == 200, response.text
    clock.advance(ONE_DAY)
    scheduler.tick()
    assert chat_channel.sent == []

    check_in_now(client, admin, [maya])
    chat_model.script(send_answer("hey, an Admin asked me to say hi"))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey, an Admin asked me to say hi"
    ]


def test_todays_message_limit_used_up_does_not_skip_it(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    engine: Engine,
) -> None:
    _, admin, maya = requested_maya(client, auth_verifier, chat_channel)
    set_message_limit(client, admin, 1)
    build_postgres_repositories(engine).usage.claim_message(maya, clock.now().date(), 1)

    check_in_now(client, admin, [maya])
    chat_model.script(send_answer("hey, how's it going?"))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey, how's it going?"]
    assert newest_log_entry(client, admin)["outcome"] == "sent"


def test_past_the_ignore_threshold_it_asks_the_model_not_about_fewer(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    _, admin, maya = requested_maya(client, auth_verifier, chat_channel)
    send_check_ins(
        chat_model, clock, scheduler, seeded_settings["check_in_ignore_threshold"]
    )
    clock.advance(timedelta(hours=1))

    check_in_now(client, admin, [maya])
    chat_model.script(send_answer("hey, no pressure to reply"))
    scheduler.tick()

    sent = chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)
    assert sent[-1] == "hey, no pressure to reply"
    assert seeded_settings["check_in_fewer_message"] not in sent


def test_the_check_in_model_can_still_skip_and_the_skip_names_the_admin(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    engine: Engine,
) -> None:
    _, admin, maya = requested_maya(client, auth_verifier, chat_channel)
    clock.advance(timedelta(hours=2))

    check_in_now(client, admin, [maya])
    chat_model.script(skip_answer("They asked for some space"))
    scheduler.tick()

    assert chat_channel.sent == []
    entry = newest_log_entry(client, admin)
    assert entry["outcome"] == "skipped"
    assert entry["skip_reason"] == "They asked for some space"
    assert entry["requested_by"] == INITIAL_ADMIN_EMAIL
    assert next_due_at(engine, maya) == clock.now() + ONE_DAY
    assert only_entry(client, admin)["check_in_now_waiting"] is False


def test_a_user_who_lost_their_telegram_connection_is_held_back_and_still_waits(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    scheduler: FakeScheduler,
    engine: Engine,
) -> None:
    _, admin, maya = requested_maya(client, auth_verifier, chat_channel)
    check_in_now(client, admin, [maya])
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM telegram_connections WHERE user_id = :id"), {"id": maya}
        )

    scheduler.tick()

    assert chat_channel.sent == []
    assert chat_model.calls == []
    entry = only_entry(client, admin)
    assert entry["check_in_now_waiting"] is True
    assert entry["held_back"]["reason"] == "no_telegram_connection"


def test_mid_conversation_it_waits_then_goes_out_as_the_admins_check_in(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    _, admin, maya = requested_maya(client, auth_verifier, chat_channel)
    clock.advance(timedelta(hours=1))
    chat_model.script("oh nice!")
    send_to_webhook(client, telegram_text_update("just got back from a run"))
    chat_channel.sent.clear()

    check_in_now(client, admin, [maya])
    scheduler.tick()
    assert chat_channel.sent == []
    assert only_entry(client, admin)["check_in_now_waiting"] is True

    clock.advance(quiet_gap(seeded_settings))
    chat_model.script_processing(
        '{"summary": "Went for a run.", "mood": "good", "memory_operations": []}'
    )
    chat_model.script(send_answer("hey, how was the rest of the run?"))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey, how was the rest of the run?"
    ]
    assert newest_log_entry(client, admin)["requested_by"] == INITIAL_ADMIN_EMAIL


def test_a_refused_send_keeps_the_check_in_now_waiting(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    _, admin, maya = requested_maya(client, auth_verifier, chat_channel)
    check_in_now(client, admin, [maya])
    chat_channel.text_send_failures.append(MessageRefusedError("Too many requests"))
    chat_model.script(send_answer("hey there"))

    scheduler.tick()

    assert only_entry(client, admin)["check_in_now_waiting"] is True


def test_turning_check_ins_off_drops_a_waiting_check_in_now(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    scheduler: FakeScheduler,
) -> None:
    headers, admin, maya = requested_maya(client, auth_verifier, chat_channel)
    check_in_now(client, admin, [maya])

    client.patch("/api/check-ins", json={"enabled": False}, headers=headers)
    client.patch("/api/check-ins", json={"enabled": True}, headers=headers)
    scheduler.tick()

    assert chat_channel.sent == []
    assert chat_model.calls == []


def test_an_unknown_user_is_not_found_and_nothing_is_requested(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    _, admin, maya = requested_maya(client, auth_verifier, chat_channel)

    response = client.post(
        CHECK_IN_NOW,
        json={"user_ids": [str(maya), str(uuid4())]},
        headers=admin,
    )

    assert response.status_code == 404
    assert only_entry(client, admin)["check_in_now_waiting"] is False


def test_non_admins_are_refused_check_in_now(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    headers, admin, maya = requested_maya(client, auth_verifier, chat_channel)

    response = client.post(
        CHECK_IN_NOW, json={"user_ids": [str(maya)]}, headers=headers
    )

    assert response.status_code == 403
    assert only_entry(client, admin)["check_in_now_waiting"] is False


def requested_users_needing_no_model(
    engine: Engine, clock: FakeClock, users: list[User], admin_id: UUID
) -> None:
    """Ask for a Check in Now for each User, held back so no model is needed.

    Every User has the Check-ins Feature off for them, is not due, and is
    either mid-Conversation or has no Telegram Connection, in turns.

    Args:
        engine: The test database.
        clock: Tells the current time.
        users: Users from `add_due_users`.
        admin_id: The Admin who asks.
    """
    repositories = build_postgres_repositories(engine)
    now = clock.now()
    for number, user in enumerate(users):
        repositories.feature_switches.save_for_user(
            user.id, Feature.CHECK_INS, on=False, changed_at=now, changed_by=admin_id
        )
        if number % 2 == 0:
            repositories.conversations.add(
                Conversation(
                    id=uuid4(),
                    user_id=user.id,
                    started_at=now - timedelta(minutes=5),
                    last_message_at=now - timedelta(minutes=1),
                )
            )
        else:
            with engine.begin() as connection:
                connection.execute(
                    text("DELETE FROM telegram_connections WHERE user_id = :id"),
                    {"id": user.id},
                )
    repositories.check_ins.request_check_ins_now(
        [user.id for user in users], admin_id, now
    )


def test_tick_reads_stay_the_same_as_due_and_requested_users_grow(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    engine: Engine,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    admin = owner_headers(client, auth_verifier)
    admin_id = maya_id(client, admin)
    change_settings(client, admin, {"daily_message_limit": 1})

    def add_users(how_many: int) -> None:
        added = add_due_users(engine, clock, 2 * how_many)
        due_users_needing_no_model(engine, clock, added[:how_many])
        requested_users_needing_no_model(engine, clock, added[how_many:], admin_id)

    add_users(5)
    with selects_by_table(engine) as reads_for_five:
        scheduler.tick()
    clock.advance(timedelta(minutes=1))
    add_users(15)
    with selects_by_table(engine) as reads_for_fifteen:
        scheduler.tick()

    assert chat_model.calls == []
    assert reads_for_fifteen == reads_for_five
    with engine.connect() as connection:
        held_back_requests = connection.execute(
            text(
                "SELECT count(*) FROM users WHERE check_in_now_requested_at "
                "IS NOT NULL AND check_in_held_back_reason IN "
                "('waiting_to_be_woven_in', 'no_telegram_connection')"
            )
        ).scalar()
    assert held_back_requests == 5 + 15


def test_a_check_in_now_asked_while_a_scheduled_one_is_decided_still_waits(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
    engine: Engine,
) -> None:
    _, admin, maya = requested_maya(client, auth_verifier, chat_channel)
    check_in_now(client, admin, [maya])

    build_postgres_repositories(engine).check_ins.add(
        CheckIn(
            id=uuid4(),
            user_id=maya,
            outcome=CheckInOutcome.SKIPPED,
            decided_at=clock.now(),
            skip_reason="decided from a read before the request",
        ),
        clock.now() + ONE_DAY,
        pause_until_resumed=False,
    )

    assert only_entry(client, admin)["check_in_now_waiting"] is True


def test_a_user_who_has_not_finished_onboarding_is_refused(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    engine: Engine,
) -> None:
    _, admin, maya = requested_maya(client, auth_verifier, chat_channel)
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE users SET onboarding_completed_at = NULL WHERE id = :id"),
            {"id": maya},
        )

    assert check_in_now(client, admin, [maya]) == {str(maya): "not_opted_in"}
