from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.eval_repositories import PostgresEvalCaseRepository
from companion.core.evals.case_seed import add_seed_cases
from companion.core.evals.cases import InvalidEvalCaseError
from companion.core.evals.models import EvalCase, EvalName
from tests.eval_run_helpers import (
    CRISIS_CASE,
    FALSE_ALARM_CASE,
    SETTINGS_CASE,
    add_cases,
    open_run,
    start_run,
)
from tests.fakes import FakeAuthVerifier, FakeClock
from tests.telegram_helpers import auth_headers, owner_headers


def test_an_admin_sees_every_eval_with_the_cases_a_run_would_run(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    add_cases(engine, CRISIS_CASE, FALSE_ALARM_CASE, SETTINGS_CASE)
    admin = owner_headers(client, auth_verifier)

    response = client.get("/api/admin/evals", headers=admin)

    assert response.status_code == 200
    evals = {item["eval"]: item["case_keys"] for item in response.json()["evals"]}
    assert list(evals) == [name.value for name in EvalName]
    assert evals["safeguard"] == ["plan", "traffic"]
    assert evals["settings"] == ["just-chatting"]
    assert evals["persona"] == []


def test_a_started_run_waits_queued_with_one_variant_and_no_results(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    add_cases(engine, CRISIS_CASE)
    admin = owner_headers(client, auth_verifier)

    run = start_run(client, admin, EvalName.SAFEGUARD)

    assert run["state"] == "queued"
    assert run["started_from"] == "dashboard"
    assert run["started_by_name"] == "owner@example.com"
    assert run["evals"] == ["safeguard"]
    assert run["repeats"] == 1
    assert run["variants"] == [{"letter": "A", "setting_overrides": {}}]
    assert run["case_count"] is None
    assert open_run(client, admin, run["id"])["results"] == []
    listed = client.get("/api/admin/eval-runs", headers=admin).json()["runs"]
    assert [listed_run["id"] for listed_run in listed] == [run["id"]]


def test_terminal_runs_are_hidden_unless_asked_for(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    add_cases(engine, CRISIS_CASE)
    admin = owner_headers(client, auth_verifier)
    dashboard_run = start_run(client, admin, EvalName.SAFEGUARD)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO eval_runs (id, started_from, state, evals, queued_at) "
                "VALUES (:id, 'terminal', 'queued', '[\"safeguard\"]', now())"
            ),
            {"id": uuid4()},
        )

    hidden = client.get("/api/admin/eval-runs", headers=admin).json()["runs"]
    shown = client.get(
        "/api/admin/eval-runs", params={"include_terminal": True}, headers=admin
    ).json()["runs"]

    assert [run["id"] for run in hidden] == [dashboard_run["id"]]
    assert [run["started_from"] for run in shown] == ["terminal", "dashboard"]


@pytest.mark.parametrize(
    ("evals", "message"),
    [([], "Pick at least one Eval"), (["persona"], "no cases")],
)
def test_a_run_with_nothing_to_run_is_refused(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    evals: list[str],
    message: str,
) -> None:
    add_cases(engine, CRISIS_CASE)
    admin = owner_headers(client, auth_verifier)

    response = client.post("/api/admin/eval-runs", json={"evals": evals}, headers=admin)

    assert response.status_code == 422
    assert message in response.json()["detail"]


def test_an_unknown_eval_or_run_is_refused(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    unknown_eval = client.post(
        "/api/admin/eval-runs", json={"evals": ["vibes"]}, headers=admin
    )
    unknown_run = client.get(f"/api/admin/eval-runs/{uuid4()}", headers=admin)

    assert unknown_eval.status_code == 422
    assert unknown_run.status_code == 404


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/admin/evals"),
        ("GET", "/api/admin/eval-runs"),
        ("POST", "/api/admin/eval-runs"),
        ("GET", "/api/admin/eval-runs/6f1c2d3e-0000-4000-8000-000000000001"),
    ],
)
def test_only_admins_reach_the_eval_routes(
    client: TestClient, auth_verifier: FakeAuthVerifier, method: str, path: str
) -> None:
    user = auth_headers(auth_verifier, "user_maya")

    response = client.request(method, path, json={"evals": ["safeguard"]}, headers=user)

    assert response.status_code == 403


def test_the_seed_adds_only_new_keys_and_never_overwrites_or_restores(
    engine: Engine, clock: FakeClock
) -> None:
    cases = PostgresEvalCaseRepository(engine)
    add_seed_cases(cases, [CRISIS_CASE, FALSE_ALARM_CASE], clock)
    with engine.begin() as connection:
        connection.execute(
            text(
                'UPDATE eval_cases SET content = \'{"kind": "clear_crisis", '
                '"message": "edited"}\' WHERE key = \'plan\''
            )
        )
        connection.execute(
            text("UPDATE eval_cases SET archived = true WHERE key = 'traffic'")
        )

    added = add_seed_cases(cases, [CRISIS_CASE, FALSE_ALARM_CASE, SETTINGS_CASE], clock)

    assert added == ["just-chatting"]
    stored = cases.list_for_evals([EvalName.SAFEGUARD, EvalName.SETTINGS])
    assert [(case.key, case.content.get("message")) for case in stored] == [
        ("plan", "edited"),
        ("just-chatting", "had a nice lunch today"),
    ]


def test_a_seed_case_that_does_not_fit_its_eval_is_refused(
    engine: Engine, clock: FakeClock
) -> None:
    broken = EvalCase(key="broken", eval=EvalName.SETTINGS, content={"message": "hi"})

    with pytest.raises(InvalidEvalCaseError, match="broken"):
        add_seed_cases(PostgresEvalCaseRepository(engine), [broken], clock)
