from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.eval_repositories import (
    PostgresEvalCaseRepository,
    PostgresEvalImageRepository,
)
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

SOME_RUN = "/api/admin/eval-runs/6f1c2d3e-0000-4000-8000-000000000001"


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
    assert run["variants"] == [
        {"letter": "A", "setting_overrides": {}, "made_live": None}
    ]
    assert run["case_count"] == 1
    assert run["case_keys"] == ["plan"]
    assert run["cancel_requested"] is False
    assert (run["cost_sgd"], run["unpriced_models"]) == (0, [])
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
        ("POST", "/api/admin/eval-runs/estimate"),
        ("POST", f"{SOME_RUN}/cancel"),
        ("POST", f"{SOME_RUN}/rerun-failed"),
        ("DELETE", SOME_RUN),
        ("GET", f"{SOME_RUN}/snapshot"),
        ("GET", f"{SOME_RUN}/results/6f1c2d3e-0000-4000-8000-000000000002"),
        ("GET", "/api/admin/eval-cases/plan/history"),
        ("GET", "/api/admin/eval-costs"),
        ("PUT", "/api/admin/eval-costs"),
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
    images = PostgresEvalImageRepository(engine)
    add_seed_cases(cases, images, [CRISIS_CASE, FALSE_ALARM_CASE], [], clock)
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

    added = add_seed_cases(
        cases, images, [CRISIS_CASE, FALSE_ALARM_CASE, SETTINGS_CASE], [], clock
    )

    assert added == ["just-chatting"]
    stored = cases.list_for_evals([EvalName.SAFEGUARD, EvalName.SETTINGS])
    assert [(case.key, case.content.get("message")) for case in stored] == [
        ("plan", "edited"),
        ("just-chatting", "had a nice lunch today"),
    ]


def test_a_seed_case_that_does_not_fit_its_eval_is_refused(
    engine: Engine, clock: FakeClock
) -> None:
    broken = EvalCase(key="broken", eval=EvalName.SETTINGS, content={"tools": []})

    with pytest.raises(InvalidEvalCaseError, match="broken"):
        add_seed_cases(
            PostgresEvalCaseRepository(engine),
            PostgresEvalImageRepository(engine),
            [broken],
            [],
            clock,
        )


def test_a_run_of_single_cases_runs_only_those_and_unknown_keys_are_refused(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    add_cases(engine, CRISIS_CASE, FALSE_ALARM_CASE, SETTINGS_CASE)
    admin = owner_headers(client, auth_verifier)

    run = client.post(
        "/api/admin/eval-runs",
        json={"evals": ["settings"], "case_keys": ["traffic"]},
        headers=admin,
    ).json()
    unknown = client.post(
        "/api/admin/eval-runs", json={"case_keys": ["no-such-case"]}, headers=admin
    )

    assert run["case_keys"] == ["traffic", "just-chatting"]
    assert run["evals"] == ["safeguard", "settings"]
    assert run["case_count"] == 2
    assert unknown.status_code == 422
    assert "no-such-case" in unknown.json()["detail"]


def test_a_case_never_run_is_estimated_with_its_evals_rough_figure(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    add_cases(engine, CRISIS_CASE, FALSE_ALARM_CASE)
    admin = owner_headers(client, auth_verifier)

    response = client.post(
        "/api/admin/eval-runs/estimate", json={"evals": ["safeguard"]}, headers=admin
    )

    assert response.status_code == 200
    estimate = response.json()
    assert (estimate["case_count"], estimate["rough_case_count"]) == (2, 2)
    assert (estimate["tokens_in"], estimate["tokens_out"]) == (8_000, 800)
    assert estimate["models"] == [
        {
            "model": "deepseek/deepseek-v4.1-flash-1017",
            "tokens_in": 8_000,
            "tokens_out": 800,
        }
    ]
    assert estimate["cost_sgd"] == pytest.approx((8_000 * 0.38 + 800 * 1.54) / 1e6)
    assert estimate["unpriced_models"] == []


def test_a_queued_run_is_cancelled_at_once_and_an_ended_run_cannot_be(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    add_cases(engine, CRISIS_CASE)
    admin = owner_headers(client, auth_verifier)
    run = start_run(client, admin, EvalName.SAFEGUARD)

    cancelled = client.post(f"/api/admin/eval-runs/{run['id']}/cancel", headers=admin)
    again = client.post(f"/api/admin/eval-runs/{run['id']}/cancel", headers=admin)

    assert cancelled.status_code == 200
    assert cancelled.json()["state"] == "cancelled"
    assert cancelled.json()["finished_at"] is not None
    assert again.status_code == 409


def test_a_running_run_is_only_marked_for_cancelling_and_cannot_be_deleted(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    clock: FakeClock,
) -> None:
    add_cases(engine, CRISIS_CASE)
    admin = owner_headers(client, auth_verifier)
    run = start_run(client, admin, EvalName.SAFEGUARD)
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE eval_runs SET state = 'running' WHERE id = :id"),
            {"id": run["id"]},
        )

    cancelled = client.post(f"/api/admin/eval-runs/{run['id']}/cancel", headers=admin)
    deleted = client.delete(f"/api/admin/eval-runs/{run['id']}", headers=admin)
    rerun = client.post(f"/api/admin/eval-runs/{run['id']}/rerun-failed", headers=admin)

    assert cancelled.json()["state"] == "running"
    assert cancelled.json()["cancel_requested"] is True
    assert deleted.status_code == 409
    assert rerun.status_code == 409


def test_a_deleted_run_is_gone(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    add_cases(engine, CRISIS_CASE)
    admin = owner_headers(client, auth_verifier)
    run = start_run(client, admin, EvalName.SAFEGUARD)

    deleted = client.delete(f"/api/admin/eval-runs/{run['id']}", headers=admin)

    assert deleted.status_code == 204
    assert (
        client.get(f"/api/admin/eval-runs/{run['id']}", headers=admin).status_code
        == 404
    )
    assert client.get("/api/admin/eval-runs", headers=admin).json()["runs"] == []


def test_a_queued_run_has_no_snapshot_yet(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    add_cases(engine, CRISIS_CASE)
    admin = owner_headers(client, auth_verifier)
    run = start_run(client, admin, EvalName.SAFEGUARD)

    response = client.get(f"/api/admin/eval-runs/{run['id']}/snapshot", headers=admin)

    assert response.json() == {
        "settings": None,
        "judge": None,
        "cases": None,
        "needs": None,
        "moves": None,
    }


def test_model_prices_are_seeded_and_admins_change_them_with_the_limit(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    seeded = client.get("/api/admin/eval-costs", headers=admin).json()
    saved = client.put(
        "/api/admin/eval-costs",
        json={
            "prices": [
                {
                    "model": "deepseek/deepseek-v4.1-flash-1017",
                    "sgd_in": 0.5,
                    "sgd_out": 2,
                },
                {
                    "model": "deepseek/deepseek-v4-pro-0813",
                    "sgd_in": None,
                    "sgd_out": None,
                },
            ],
            "token_limit": 250_000,
        },
        headers=admin,
    )

    assert seeded == {
        "prices": [
            {
                "model": "deepseek/deepseek-v4.1-flash-1017",
                "sgd_in": 0.38,
                "sgd_out": 1.54,
            },
            {"model": "deepseek/deepseek-v4-pro-0813", "sgd_in": 1.69, "sgd_out": 5.07},
        ],
        "token_limit": 1_000_000,
    }
    assert saved.status_code == 200
    assert saved.json() == {
        "prices": [
            {
                "model": "deepseek/deepseek-v4.1-flash-1017",
                "sgd_in": 0.5,
                "sgd_out": 2.0,
            }
        ],
        "token_limit": 250_000,
    }


@pytest.mark.parametrize(
    "body",
    [
        {"prices": [], "token_limit": 5},
        {"prices": [{"model": "x", "sgd_in": -1, "sgd_out": 1}], "token_limit": 50_000},
        {
            "prices": [{"model": "x", "sgd_in": 1, "sgd_out": None}],
            "token_limit": 50_000,
        },
        {
            "prices": [
                {"model": "x", "sgd_in": 1, "sgd_out": 1},
                {"model": "x", "sgd_in": 2, "sgd_out": 2},
            ],
            "token_limit": 50_000,
        },
    ],
)
def test_a_price_or_limit_out_of_range_is_refused_and_nothing_saved(
    client: TestClient, auth_verifier: FakeAuthVerifier, body: dict[str, object]
) -> None:
    admin = owner_headers(client, auth_verifier)

    response = client.put("/api/admin/eval-costs", json=body, headers=admin)

    assert response.status_code == 422
    after = client.get("/api/admin/eval-costs", headers=admin).json()
    assert after["token_limit"] == 1_000_000


def test_the_estimate_counts_every_variant_and_repeat(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    add_cases(engine, CRISIS_CASE)
    admin = owner_headers(client, auth_verifier)

    response = client.post(
        "/api/admin/eval-runs/estimate",
        json={
            "evals": ["safeguard"],
            "variants": [{}, {"response_thinking": True}],
            "repeats": 3,
        },
        headers=admin,
    )

    assert response.status_code == 200, response.text
    estimate = response.json()
    assert estimate["case_count"] == 6
    assert estimate["rough_case_count"] == 1
    assert [
        (variant["letter"], variant["tokens_in"]) for variant in estimate["variants"]
    ] == [("A", 12_000), ("B", 12_000)]
    assert estimate["tokens_in"] == 24_000


@pytest.mark.parametrize(
    ("change", "status"),
    [
        ({"repeats": 0}, 422),
        ({"repeats": 6}, 422),
        ({"variants": []}, 422),
        ({"variants": [{}, {}, {}, {}]}, 422),
        ({"variants": [{"no_such_setting": 1}]}, 422),
        ({"variants": [{"daily_message_limit": -1}]}, 422),
        ({"variants": [{"model_prices": {}}]}, 422),
        ({"variants": [{"need:not-an-id": {}}]}, 422),
        ({"variants": [{"move:not-an-id": {}}]}, 422),
        ({"variants": [{f"move:{uuid4()}": {"name": "x"}}]}, 422),
        (
            {
                "variants": [
                    {
                        f"move:{uuid4()}": {
                            "name": "x",
                            "when_it_fits": "y",
                            "how_to_do_it": "z",
                        }
                    }
                ]
            },
            404,
        ),
        ({"variants": [{f"need:{uuid4()}": {"name": "x"}}]}, 422),
        (
            {
                "variants": [
                    {
                        f"need:{uuid4()}": {
                            "name": "x",
                            "when_it_fits": "y",
                            "how_to_reply": "z",
                        }
                    }
                ]
            },
            404,
        ),
    ],
)
def test_variants_repeats_and_overrides_out_of_range_are_refused(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    change: dict[str, Any],
    status: int,
) -> None:
    add_cases(engine, CRISIS_CASE)
    admin = owner_headers(client, auth_verifier)

    response = client.post(
        "/api/admin/eval-runs",
        json={"evals": ["safeguard"], **change},
        headers=admin,
    )

    assert response.status_code == status, response.text
    runs = client.get("/api/admin/eval-runs", headers=admin).json()["runs"]
    assert runs == []


def test_override_choices_list_the_editable_settings_needs_moves_and_models(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    response = client.get("/api/admin/setting-override-choices", headers=admin)

    assert response.status_code == 200
    choices = response.json()
    thinking = next(
        setting
        for setting in choices["settings"]
        if setting["key"] == "understanding_thinking"
    )
    assert (thinking["kind"], thinking["value"]) == ("on_off", True)
    keys = {setting["key"] for setting in choices["settings"]}
    assert "model_prices" not in keys
    assert "eval_run_token_limit" not in keys
    fallback = next(need for need in choices["needs"] if need["name"] == "Ask more")
    assert fallback["key"].startswith("need:")
    assert set(fallback["value"]) == {
        "name",
        "when_it_fits",
        "how_to_reply",
        "curiosities",
    }
    assert fallback["value"]["curiosities"] == "only_if_it_fits"
    research = next(move for move in choices["moves"] if move["name"] == "Research")
    assert research["key"].startswith("move:")
    assert set(research["value"]) == {"name", "when_it_fits", "how_to_do_it"}
    assert choices["models"] == [
        "deepseek/deepseek-v4.1-flash-1017",
        "deepseek/deepseek-v4-pro-0813",
    ]
