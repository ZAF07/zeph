from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import Engine

from companion.adapters.postgres.repositories import build_postgres_repositories
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
    ToolCall,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    auth_headers,
    owner_headers,
)
from tests.test_check_in_hold_back import due_users_needing_no_model, selects_by_table
from tests.test_check_in_sending import (
    ONE_DAY,
    send_answer,
    set_up_user_with_check_ins,
)
from tests.test_onboarding import onboarding_answers
from tests.test_settings_via_chat import check_ins, reply_call
from tests.test_user_snapshot import add_due_users
from tests.test_web_search import change_settings

SCHEDULE = "/api/admin/check-in-schedule"


def schedule(
    client: TestClient, admin: dict[str, str], **params: Any
) -> dict[str, Any]:
    """Fetch one page of the Check-in Schedule through the admin API."""
    response = client.get(SCHEDULE, params=params, headers=admin)
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


def as_json_time(moment: datetime) -> str:
    """Write a UTC time the way the API sends it."""
    return moment.isoformat().replace("+00:00", "Z")


def only_entry(client: TestClient, admin: dict[str, str]) -> dict[str, Any]:
    """Fetch the Schedule's one row."""
    [entry] = schedule(client, admin)["entries"]
    return entry


def onboard(
    client: TestClient, auth_verifier: FakeAuthVerifier, auth_id: str, **answers: Any
) -> dict[str, str]:
    """Sign up and onboard a User with no Telegram Connection."""
    headers = auth_headers(auth_verifier, auth_id)
    response = client.put(
        "/api/onboarding", json=onboarding_answers(**answers), headers=headers
    )
    assert response.status_code == 200, response.text
    return headers


def test_the_schedule_lists_only_opted_in_users_with_their_due_time_and_settings(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    onboard(client, auth_verifier, "user_sam", name="Sam", check_ins_enabled=False)
    admin = owner_headers(client, auth_verifier)

    page = schedule(client, admin)

    assert page["total"] == 1
    [entry] = page["entries"]
    assert entry["name"] == "Maya"
    assert entry["email"] == "user_maya@example.com"
    assert entry["time_zone"] == "Asia/Singapore"
    assert entry["next_due_at"] == (clock.now() + ONE_DAY).isoformat().replace(
        "+00:00", "Z"
    )
    assert entry["frequency"] == "most_days"
    assert entry["quiet_hours_start"] == "22:00:00"
    assert entry["quiet_hours_end"] == "07:30:00"
    assert entry["paused"] is False
    assert entry["paused_until"] is None
    assert entry["check_ins_work"] is True
    assert entry["held_back"] is None
    assert "message" not in str(entry)


def test_the_schedule_is_searchable_by_name_or_email_and_paged(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    for number in range(3):
        onboard(
            client,
            auth_verifier,
            f"user_{number}",
            name=f"Person {number}",
            check_ins_enabled=True,
        )
    onboard(client, auth_verifier, "user_maya", name="Maya", check_ins_enabled=True)
    admin = owner_headers(client, auth_verifier)

    by_name = schedule(client, admin, search="maya")
    by_email = schedule(client, admin, search="USER_1@EXAMPLE")
    first_page = schedule(client, admin, search="person", page_size=2)
    second_page = schedule(client, admin, search="person", page_size=2, page=2)

    assert [entry["name"] for entry in by_name["entries"]] == ["Maya"]
    assert [entry["name"] for entry in by_email["entries"]] == ["Person 1"]
    assert first_page["total"] == second_page["total"] == 3
    names = [entry["name"] for entry in first_page["entries"] + second_page["entries"]]
    assert sorted(names) == ["Person 0", "Person 1", "Person 2"]
    assert len(first_page["entries"]) == 2


def test_a_user_with_check_ins_off_by_an_admin_shows_the_feature_not_working(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    user_id = schedule(client, admin)["entries"][0]["user_id"]

    response = client.put(
        f"/api/admin/users/{user_id}/features/check_ins",
        json={"switch": "off"},
        headers=admin,
    )
    assert response.status_code == 200, response.text

    assert schedule(client, admin)["entries"][0]["check_ins_work"] is False


def test_non_admins_are_refused_by_the_schedule_endpoints(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    user_id = schedule(client, admin)["entries"][0]["user_id"]

    responses = [
        client.get(SCHEDULE, headers=headers),
        client.patch(
            f"{SCHEDULE}/{user_id}", json={"frequency": "weekly"}, headers=headers
        ),
        client.put(
            f"{SCHEDULE}/{user_id}/pause", json={"length": "day"}, headers=headers
        ),
        client.delete(f"{SCHEDULE}/{user_id}/pause", headers=headers),
    ]

    assert [response.status_code for response in responses] == [403] * 4


def test_the_schedule_says_when_it_was_read_so_due_times_show_from_then(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    clock.advance(timedelta(hours=1))

    assert schedule(client, admin)["now"] == clock.now().isoformat().replace(
        "+00:00", "Z"
    )


def test_a_timed_pause_shows_as_held_back_until_it_ends(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    client.put("/api/check-ins/pause", json={"length": "week"}, headers=headers)
    pause_ends = clock.now() + timedelta(weeks=1)
    admin = owner_headers(client, auth_verifier)
    clock.advance(ONE_DAY)

    scheduler.tick()

    entry = only_entry(client, admin)
    assert entry["paused"] is True
    assert entry["paused_until"] == as_json_time(pause_ends)
    assert entry["held_back"] == {"reason": "paused", "until": as_json_time(pause_ends)}


def test_quiet_hours_show_as_held_back_until_they_end_then_clear_once_sent(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    clock.advance(ONE_DAY + timedelta(hours=6))
    quiet_hours_end = clock.now() + timedelta(hours=8, minutes=30)

    scheduler.tick()
    held_back = only_entry(client, admin)["held_back"]
    clock.advance(quiet_hours_end - clock.now())
    chat_model.script(send_answer("morning!"))
    scheduler.tick()

    assert held_back == {
        "reason": "quiet_hours",
        "until": as_json_time(quiet_hours_end),
    }
    entry = only_entry(client, admin)
    assert entry["held_back"] is None
    assert entry["next_due_at"] == as_json_time(clock.now() + ONE_DAY)


def test_no_telegram_connection_shows_as_held_back_with_no_end(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    onboard(
        client,
        auth_verifier,
        "user_maya",
        check_ins_enabled=True,
        check_in_frequency="most_days",
    )
    admin = owner_headers(client, auth_verifier)
    clock.advance(ONE_DAY)

    scheduler.tick()

    entry = only_entry(client, admin)
    assert entry["held_back"] == {"reason": "no_telegram_connection", "until": None}
    assert entry["next_due_at"] is None


def test_todays_message_limit_used_up_shows_as_held_back_after_the_days_skip(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    engine: Engine,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    change_settings(client, admin, {"daily_message_limit": 1})
    clock.advance(ONE_DAY)
    user_id = UUID(only_entry(client, admin)["user_id"])
    build_postgres_repositories(engine).usage.claim_message(
        user_id, clock.now().date(), 1
    )

    scheduler.tick()
    after_the_skip = only_entry(client, admin)["held_back"]
    clock.advance(timedelta(minutes=1))
    scheduler.tick()

    assert after_the_skip is None
    assert only_entry(client, admin)["held_back"] == {
        "reason": "limit_skip_done_today",
        "until": None,
    }


def test_no_kind_to_send_shows_as_held_back(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    kinds = client.get("/api/admin/check-in-kinds", headers=admin).json()["kinds"]
    for kind in kinds:
        client.delete(f"/api/admin/check-in-kinds/{kind['id']}", headers=admin)
    clock.advance(ONE_DAY)

    scheduler.tick()

    assert only_entry(client, admin)["held_back"] == {
        "reason": "no_kind_to_send",
        "until": None,
    }


def test_schedule_reads_stay_the_same_as_users_grow(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    clock: FakeClock,
    scheduler: FakeScheduler,
    engine: Engine,
) -> None:
    admin = owner_headers(client, auth_verifier)
    change_settings(client, admin, {"daily_message_limit": 1})
    due_users_needing_no_model(engine, clock, add_due_users(engine, clock, 5))
    scheduler.tick()
    with selects_by_table(engine) as reads_for_five:
        assert len(schedule(client, admin)["entries"]) == 5

    due_users_needing_no_model(engine, clock, add_due_users(engine, clock, 15))
    scheduler.tick()
    with selects_by_table(engine) as reads_for_twenty:
        assert len(schedule(client, admin)["entries"]) == 20

    assert reads_for_twenty == reads_for_five


def admin_change(
    client: TestClient,
    admin: dict[str, str],
    user_id: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    """Change a User's Check-in settings as an Admin and return their row."""
    response = client.patch(f"{SCHEDULE}/{user_id}", json=body, headers=admin)
    assert response.status_code == 200, response.text
    entry: dict[str, Any] = response.json()
    return entry


def test_an_admin_changes_a_users_real_frequency_and_quiet_hours_marked_as_theirs(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    user_id = only_entry(client, admin)["user_id"]
    clock.advance(timedelta(hours=1))

    entry = admin_change(
        client,
        admin,
        user_id,
        {"frequency": "weekly", "quiet_hours_start": "21:00"},
    )

    assert entry["frequency"] == "weekly"
    assert entry["next_due_at"] == as_json_time(clock.now() + timedelta(weeks=1))
    assert sorted(entry["changed_by_admin"]) == ["check_in_frequency", "quiet_hours"]
    settings = check_ins(client, headers)
    assert settings["enabled"] is True
    assert settings["frequency"] == "weekly"
    assert settings["quiet_hours_start"] == "21:00:00"
    assert set(settings["changed_by_admin"]) == {"check_in_frequency", "quiet_hours"}


def test_changing_quiet_hours_that_hold_a_check_in_back_decides_it_again_now(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    user_id = only_entry(client, admin)["user_id"]
    clock.advance(ONE_DAY + timedelta(hours=6))
    scheduler.tick()

    entry = admin_change(
        client,
        admin,
        user_id,
        {"quiet_hours_start": "23:30", "quiet_hours_end": "07:30"},
    )
    chat_model.script(send_answer("still up? how was today?"))
    scheduler.tick()

    assert entry["next_due_at"] == as_json_time(clock.now())
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["still up? how was today?"]


def test_an_admin_pauses_and_resumes_a_user(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    user_id = only_entry(client, admin)["user_id"]

    paused = client.put(
        f"{SCHEDULE}/{user_id}/pause", json={"length": "day"}, headers=admin
    )
    settings_while_paused = check_ins(client, headers)
    resumed = client.delete(f"{SCHEDULE}/{user_id}/pause", headers=admin)

    assert paused.status_code == 200, paused.text
    assert paused.json()["paused"] is True
    assert paused.json()["paused_until"] == as_json_time(clock.now() + ONE_DAY)
    assert settings_while_paused["paused"] is True
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["paused"] is False
    settings = check_ins(client, headers)
    assert settings["paused"] is False
    assert list(settings["changed_by_admin"]) == ["check_in_pause"]


def test_the_users_own_dashboard_change_clears_the_admin_mark(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    user_id = only_entry(client, admin)["user_id"]
    admin_change(
        client, admin, user_id, {"frequency": "weekly", "quiet_hours_start": "21:00"}
    )

    response = client.patch(
        "/api/check-ins", json={"frequency": "most_days"}, headers=headers
    )

    assert response.status_code == 200, response.text
    assert list(response.json()["changed_by_admin"]) == ["quiet_hours"]
    assert only_entry(client, admin)["changed_by_admin"] == ["quiet_hours"]


def test_the_users_change_in_chat_swaps_the_admin_mark_for_the_chat_mark(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    user_id = only_entry(client, admin)["user_id"]
    admin_change(client, admin, user_id, {"frequency": "weekly"})

    reply_call(
        client,
        chat_model,
        "check in most days please",
        ToolCall("change_check_in_frequency", {"frequency": "most_days"}),
        "Done: most days.",
    )

    assert check_ins(client, headers)["changed_by_admin"] == {}
    me = client.get("/api/me", headers=headers).json()
    assert list(me["changed_in_chat"]) == ["check_in_frequency"]


def test_an_admin_change_drops_the_chat_mark(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    user_id = only_entry(client, admin)["user_id"]
    reply_call(
        client,
        chat_model,
        "check in once a week",
        ToolCall("change_check_in_frequency", {"frequency": "weekly"}),
        "Done.",
    )

    admin_change(client, admin, user_id, {"frequency": "most_days"})

    me = client.get("/api/me", headers=headers).json()
    assert me["changed_in_chat"] == {}
    assert list(check_ins(client, headers)["changed_by_admin"]) == [
        "check_in_frequency"
    ]


def test_an_admin_can_never_turn_a_users_check_ins_on_or_off(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    sam = onboard(client, auth_verifier, "user_sam", check_ins_enabled=False)
    admin = owner_headers(client, auth_verifier)
    maya_id = only_entry(client, admin)["user_id"]
    sam_id = client.get("/api/me", headers=sam).json()["id"]

    turn_off = client.patch(
        f"{SCHEDULE}/{maya_id}", json={"enabled": False}, headers=admin
    )
    change_sam = client.patch(
        f"{SCHEDULE}/{sam_id}", json={"frequency": "weekly"}, headers=admin
    )
    pause_sam = client.put(
        f"{SCHEDULE}/{sam_id}/pause", json={"length": "week"}, headers=admin
    )
    missing = client.patch(
        f"{SCHEDULE}/00000000-0000-0000-0000-000000000000",
        json={"frequency": "weekly"},
        headers=admin,
    )

    assert turn_off.status_code == 422
    assert only_entry(client, admin)["user_id"] == maya_id
    assert change_sam.status_code == 409
    assert pause_sam.status_code == 409
    assert check_ins(client, sam)["enabled"] is False
    assert check_ins(client, sam)["paused"] is False
    assert missing.status_code == 404


def test_a_settings_change_that_moves_the_due_time_clears_the_old_reason(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    user_id = only_entry(client, admin)["user_id"]
    clock.advance(ONE_DAY + timedelta(hours=6))
    scheduler.tick()

    entry = admin_change(client, admin, user_id, {"frequency": "weekly"})

    assert entry["next_due_at"] == as_json_time(clock.now() + timedelta(weeks=1))
    assert entry["held_back"] is None
    assert only_entry(client, admin)["held_back"] is None


def test_a_settings_change_that_keeps_the_due_time_keeps_the_reason(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    onboard(
        client,
        auth_verifier,
        "user_maya",
        check_ins_enabled=True,
        check_in_frequency="most_days",
    )
    admin = owner_headers(client, auth_verifier)
    user_id = only_entry(client, admin)["user_id"]
    clock.advance(ONE_DAY)
    scheduler.tick()

    entry = admin_change(client, admin, user_id, {"quiet_hours_start": "21:00"})

    assert entry["held_back"] == {"reason": "no_telegram_connection", "until": None}
