from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient

from tests.fakes import FakeAuthVerifier, FakeClock
from tests.telegram_helpers import auth_headers
from tests.test_onboarding import onboarding_answers


def test_check_ins_are_off_by_default_after_onboarding(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    client.put("/api/onboarding", json=onboarding_answers(), headers=headers)

    check_ins = client.get("/api/check-ins", headers=headers).json()

    assert check_ins == {
        "enabled": False,
        "available": True,
        "frequency": "few_times_a_week",
        "quiet_hours_start": "22:00:00",
        "quiet_hours_end": "07:30:00",
        "paused": False,
        "paused_until": None,
        "recent": [],
        "kinds": check_ins["kinds"],
    }


def test_onboarding_can_turn_check_ins_on_with_frequency_and_quiet_hours(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")

    response = client.put(
        "/api/onboarding",
        json=onboarding_answers(
            check_ins_enabled=True,
            check_in_frequency="most_days",
            quiet_hours_start="21:00",
            quiet_hours_end="08:00",
        ),
        headers=headers,
    )

    assert response.status_code == 200
    check_ins = client.get("/api/check-ins", headers=headers).json()
    assert check_ins["enabled"] is True
    assert check_ins["frequency"] == "most_days"
    assert check_ins["quiet_hours_start"] == "21:00:00"
    assert check_ins["quiet_hours_end"] == "08:00:00"


def onboard_with_check_ins(
    client: TestClient, headers: dict[str, str], **overrides: Any
) -> None:
    """Finish onboarding with Check-ins on, a few times a week, quiet 22:00-07:30."""
    answers = onboarding_answers(check_ins_enabled=True, **overrides)
    assert (
        client.put("/api/onboarding", json=answers, headers=headers).status_code == 200
    )


def test_user_can_change_frequency_and_quiet_hours_or_turn_check_ins_off(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    onboard_with_check_ins(client, headers)

    changed = client.patch(
        "/api/check-ins",
        json={"frequency": "weekly", "quiet_hours_start": "20:30"},
        headers=headers,
    ).json()
    turned_off = client.patch(
        "/api/check-ins", json={"enabled": False}, headers=headers
    ).json()

    assert changed["frequency"] == "weekly"
    assert changed["quiet_hours_start"] == "20:30:00"
    assert changed["quiet_hours_end"] == "07:30:00"
    assert changed["enabled"] is True
    assert turned_off["enabled"] is False
    assert turned_off["frequency"] == "weekly"
    assert client.get("/api/check-ins", headers=headers).json() == turned_off


def test_check_ins_never_show_a_next_check_in_time(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    onboard_with_check_ins(client, headers)

    check_ins = client.get("/api/check-ins", headers=headers).json()
    me = client.get("/api/me", headers=headers).json()

    assert not any("due" in key or "next" in key for key in check_ins)
    assert not any("due" in key or "next" in key for key in me)


def test_bad_check_in_settings_are_refused(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    onboard_with_check_ins(client, headers)

    bad_frequency = client.patch(
        "/api/check-ins", json={"frequency": "hourly"}, headers=headers
    )
    bad_time = client.patch(
        "/api/check-ins", json={"quiet_hours_end": "25:00"}, headers=headers
    )
    bad_pause = client.put(
        "/api/check-ins/pause", json={"length": "forever"}, headers=headers
    )

    assert bad_frequency.status_code == 422
    assert bad_time.status_code == 422
    assert bad_pause.status_code == 422


def test_pausing_keeps_settings_and_a_timed_pause_ends_by_itself(
    client: TestClient, auth_verifier: FakeAuthVerifier, clock: FakeClock
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    onboard_with_check_ins(client, headers, check_in_frequency="most_days")

    paused = client.put(
        "/api/check-ins/pause", json={"length": "day"}, headers=headers
    ).json()
    clock.advance(timedelta(days=1))
    after_a_day = client.get("/api/check-ins", headers=headers).json()

    assert paused["paused"] is True
    assert paused["paused_until"] == "2026-11-12T09:00:00Z"
    assert paused["enabled"] is True
    assert paused["frequency"] == "most_days"
    assert after_a_day["paused"] is False
    assert after_a_day["paused_until"] is None


def test_pause_until_resumed_lasts_until_the_user_resumes(
    client: TestClient, auth_verifier: FakeAuthVerifier, clock: FakeClock
) -> None:
    headers = auth_headers(auth_verifier, "user_maya")
    onboard_with_check_ins(client, headers)

    client.put(
        "/api/check-ins/pause", json={"length": "until_resumed"}, headers=headers
    )
    clock.advance(timedelta(weeks=8))
    still_paused = client.get("/api/check-ins", headers=headers).json()
    resumed = client.delete("/api/check-ins/pause", headers=headers).json()

    assert still_paused["paused"] is True
    assert still_paused["paused_until"] is None
    assert resumed["paused"] is False
    assert resumed["enabled"] is True


def test_check_ins_need_sign_in(client: TestClient) -> None:
    assert client.get("/api/check-ins").status_code == 401
    assert client.patch("/api/check-ins", json={}).status_code == 401
