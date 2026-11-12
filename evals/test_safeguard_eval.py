from typing import Any

import pytest
from fastapi.testclient import TestClient

from evals.cases import CASES_DIR, SafeguardCase, load_safeguard_cases
from evals.report import EvalReport, SafeguardResult
from tests.fakes import FakeAuthVerifier, FakeChatChannel
from tests.telegram_helpers import (
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)

pytestmark = pytest.mark.eval

SAFEGUARD_CASES = load_safeguard_cases(CASES_DIR / "safeguard.yaml")


def safeguard_events(client: TestClient, admin: dict[str, str]) -> list[Any]:
    """Fetch the Safeguard Events, newest first, through the admin API.

    Args:
        client: The backend's test client.
        admin: An Admin's Dashboard API headers.

    Returns:
        The events as the API gives them.
    """
    response = client.get("/api/admin/safeguard-events", headers=admin)
    assert response.status_code == 200, response.text
    events: list[Any] = response.json()["events"]
    return events


@pytest.mark.parametrize(
    "case", SAFEGUARD_CASES, ids=[case.id for case in SAFEGUARD_CASES]
)
def test_the_safeguard_catches_every_real_crisis(
    case: SafeguardCase,
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    eval_report: EvalReport,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    for earlier_message in case.earlier:
        assert send_to_webhook(client, telegram_text_update(earlier_message)) == 200
    events_before = len(safeguard_events(client, admin))

    assert send_to_webhook(client, telegram_text_update(case.message)) == 200

    events = safeguard_events(client, admin)
    risk_type = events[0]["risk_type"] if len(events) > events_before else None
    eval_report.safeguard.append(SafeguardResult(case, risk_type))
    if case.is_crisis:
        assert risk_type is not None, f"Missed {case.kind}: {case.message}"
