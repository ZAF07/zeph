from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

from companion.adapters.http.admin_api import ModelCallResponse, to_model_call_response
from companion.core.evals.costs import EvalCosts, EvalCostsService, PriceRow
from companion.core.evals.models import (
    CaseOutcome,
    CaseResult,
    Cost,
    EvalCase,
    EvalName,
    EvalRunOverview,
    EvalRunState,
    ModelTokens,
    StartedFrom,
)
from companion.core.evals.runs import EvalRunService
from companion.core.models import User


class EvalResponse(BaseModel):
    """An Eval and the cases a new run of it would run."""

    eval: EvalName
    case_keys: list[str]


class EvalsResponse(BaseModel):
    """Every Eval, in a fixed order."""

    evals: list[EvalResponse]


class StartEvalRunRequest(BaseModel):
    """The whole Evals and single cases a new run runs."""

    evals: list[EvalName] = []
    case_keys: list[str] = []


class ModelTokensResponse(BaseModel):
    """The tokens one model used."""

    model: str
    tokens_in: int
    tokens_out: int


class EstimateResponse(BaseModel):
    """What a run would use, before it starts; only an estimate.

    `cost_sgd` leaves out the tokens of `unpriced_models`.
    """

    case_count: int
    rough_case_count: int
    tokens_in: int
    tokens_out: int
    models: list[ModelTokensResponse]
    cost_sgd: float
    unpriced_models: list[str]


class VariantResponse(BaseModel):
    """One set of settings a run runs its cases with."""

    letter: str
    setting_overrides: dict[str, Any]


class EvalRunResponse(BaseModel):
    """An Eval Run and its totals so far."""

    id: str
    state: EvalRunState
    started_from: StartedFrom
    started_by_name: str | None
    evals: list[EvalName]
    repeats: int
    variants: list[VariantResponse]
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    case_count: int
    case_keys: list[str]
    cancel_requested: bool
    token_limit: int | None
    rerun_of: str | None
    passed: int
    failed: int
    errored: int
    tokens_in: int
    tokens_out: int
    cost_sgd: float
    unpriced_models: list[str]


class EvalRunsResponse(BaseModel):
    """Eval Runs, newest first."""

    runs: list[EvalRunResponse]


class CheckResponse(BaseModel):
    """One thing checked in a case, such as a Judge rule and its reason."""

    name: str
    passed: bool
    detail: str
    group: str


class CaseResultResponse(BaseModel):
    """One case's result in a run."""

    id: str
    variant: str
    try_number: int
    case_key: str
    eval: EvalName
    outcome: CaseOutcome
    checks: list[CheckResponse]
    notes: list[str]
    error: str
    tokens_in: int
    tokens_out: int
    duration_ms: int
    finished_at: datetime


class EvalRunDetailsResponse(EvalRunResponse):
    """An Eval Run with its Case Results so far, in the order they finished."""

    results: list[CaseResultResponse]


class CaseResultTraceResponse(BaseModel):
    """A Case Result with its full trace: every model call its case made."""

    run_id: str
    result: CaseResultResponse
    calls: list[ModelCallResponse]


class EvalCaseResponse(BaseModel):
    """An Eval Case as it is, or as it was when a run started."""

    key: str
    eval: EvalName
    content: dict[str, Any]
    archived: bool


class EvalRunSnapshotResponse(BaseModel):
    """What a run used; every field is null while it is Queued."""

    settings: dict[str, Any] | None
    judge: dict[str, Any] | None
    cases: list[EvalCaseResponse] | None


class CaseHistoryEntryResponse(BaseModel):
    """A case's result in one run, marked with what changed since the older one."""

    run_id: str
    run_queued_at: datetime
    result_id: str
    variant: str
    try_number: int
    outcome: CaseOutcome
    case_changed: bool
    changed_settings: list[str]


class CaseHistoryResponse(BaseModel):
    """A case and its results in recent runs, newest first."""

    case: EvalCaseResponse
    entries: list[CaseHistoryEntryResponse]


class ModelPriceBody(BaseModel):
    """One model's price in SGD per 1,000,000 tokens; null for no price."""

    model: str
    sgd_in: float | None
    sgd_out: float | None


class EvalCostsBody(BaseModel):
    """The Model Prices and the Eval run token limit."""

    prices: list[ModelPriceBody]
    token_limit: int


def to_model_tokens_responses(
    tokens: dict[str, ModelTokens],
) -> list[ModelTokensResponse]:
    """Turn tokens by model into their API shape.

    Args:
        tokens: Each model's tokens.

    Returns:
        One entry per model, by name.
    """
    return [
        ModelTokensResponse(
            model=model, tokens_in=count.tokens_in, tokens_out=count.tokens_out
        )
        for model, count in sorted(tokens.items())
    ]


def to_eval_costs_body(costs: EvalCosts) -> EvalCostsBody:
    """Turn the Model Prices and token limit into their API shape.

    Args:
        costs: The prices and limit.

    Returns:
        The body; a model with no price has null prices.
    """
    return EvalCostsBody(
        prices=[
            ModelPriceBody(model=row.model, sgd_in=row.sgd_in, sgd_out=row.sgd_out)
            for row in costs.prices
        ],
        token_limit=costs.token_limit,
    )


def to_eval_case_response(case: EvalCase) -> EvalCaseResponse:
    """Turn an Eval Case into its API shape.

    Args:
        case: The case.

    Returns:
        The response.
    """
    return EvalCaseResponse(
        key=case.key, eval=case.eval, content=case.content, archived=case.archived
    )


def cost_fields(cost: Cost) -> dict[str, Any]:
    """Write a cost as response fields.

    Args:
        cost: The cost.

    Returns:
        `cost_sgd` and `unpriced_models`.
    """
    return {"cost_sgd": cost.sgd, "unpriced_models": cost.unpriced_models}


def to_eval_run_response(overview: EvalRunOverview) -> EvalRunResponse:
    """Turn a run with its totals into its API shape.

    Args:
        overview: The run and its totals.

    Returns:
        The response.
    """
    run = overview.run
    totals = overview.totals
    return EvalRunResponse(
        id=str(run.id),
        state=run.state,
        started_from=run.started_from,
        started_by_name=run.started_by_name,
        evals=run.evals,
        repeats=run.repeats,
        variants=[
            VariantResponse(
                letter=variant.letter, setting_overrides=variant.setting_overrides
            )
            for variant in run.variants
        ],
        queued_at=run.queued_at,
        started_at=run.started_at,
        finished_at=run.finished_at,
        case_count=overview.case_count,
        case_keys=run.case_keys,
        cancel_requested=run.cancel_requested,
        token_limit=run.token_limit,
        rerun_of=str(run.rerun_of) if run.rerun_of else None,
        passed=totals.passed,
        failed=totals.failed,
        errored=totals.errored,
        tokens_in=totals.tokens_in,
        tokens_out=totals.tokens_out,
        **cost_fields(overview.cost),
    )


def to_case_result_response(result: CaseResult) -> CaseResultResponse:
    """Turn a Case Result into its API shape.

    Args:
        result: The Case Result.

    Returns:
        The response.
    """
    return CaseResultResponse(
        id=str(result.id),
        variant=result.variant,
        try_number=result.try_number,
        case_key=result.case_key,
        eval=result.eval,
        outcome=result.result.outcome,
        checks=[
            CheckResponse(
                name=check.name,
                passed=check.passed,
                detail=check.detail,
                group=check.group,
            )
            for check in result.result.checks
        ],
        notes=result.result.notes,
        error=result.result.error,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        duration_ms=result.duration_ms,
        finished_at=result.finished_at,
    )


def build_eval_api_router(
    current_admin: Callable[..., User],
    eval_run_service: EvalRunService,
    eval_costs_service: EvalCostsService,
) -> APIRouter:
    """Build the admin routes for Evals, Eval Runs and their costs.

    Every route refuses anyone who is not an Admin.

    Args:
        current_admin: The dependency that lets only Admins through.
        eval_run_service: Starts Eval Runs and shows how they went.
        eval_costs_service: Reads and saves Model Prices and the token limit.

    Returns:
        The router.
    """
    router = APIRouter(prefix="/api/admin", dependencies=[Depends(current_admin)])

    @router.get("/evals")
    def list_evals() -> EvalsResponse:
        """List every Eval with the cases a new run of it would run.

        Returns:
            The Evals.
        """
        return EvalsResponse(
            evals=[
                EvalResponse(eval=overview.eval, case_keys=overview.case_keys)
                for overview in eval_run_service.list_evals()
            ]
        )

    @router.get("/eval-runs")
    def list_eval_runs(include_terminal: bool = False) -> EvalRunsResponse:
        """List Eval Runs, newest first.

        Args:
            include_terminal: Whether to list runs started from the terminal,
                which are left out by default.

        Returns:
            The runs.
        """
        return EvalRunsResponse(
            runs=[
                to_eval_run_response(overview)
                for overview in eval_run_service.list_runs(include_terminal)
            ]
        )

    @router.post("/eval-runs", status_code=status.HTTP_201_CREATED)
    def start_eval_run(
        request: StartEvalRunRequest, admin: Annotated[User, Depends(current_admin)]
    ) -> EvalRunResponse:
        """Start a run from the Dashboard; it waits as Queued.

        Args:
            request: The whole Evals and single cases to run.
            admin: The Admin starting it.

        Returns:
            The run.

        Raises:
            CoreError: 422 if nothing is picked, a case key is unknown or
                the Evals have no cases.
        """
        overview = eval_run_service.start_run(
            admin.id, StartedFrom.DASHBOARD, request.evals, request.case_keys
        )
        return to_eval_run_response(overview)

    @router.post("/eval-runs/estimate")
    def estimate_eval_run(request: StartEvalRunRequest) -> EstimateResponse:
        """Estimate a run's tokens and SGD before it starts.

        Args:
            request: The whole Evals and single cases it would run.

        Returns:
            The estimate.

        Raises:
            CoreError: 422 as for starting the run.
        """
        estimate = eval_run_service.estimate(request.evals, request.case_keys)
        return EstimateResponse(
            case_count=estimate.case_count,
            rough_case_count=estimate.rough_case_count,
            tokens_in=sum(count.tokens_in for count in estimate.tokens.values()),
            tokens_out=sum(count.tokens_out for count in estimate.tokens.values()),
            models=to_model_tokens_responses(estimate.tokens),
            **cost_fields(estimate.cost),
        )

    @router.post("/eval-runs/{run_id}/cancel")
    def cancel_eval_run(run_id: UUID) -> EvalRunResponse:
        """Cancel a run: a Queued one at once, a Running one after its case.

        Args:
            run_id: The run's ID.

        Returns:
            The run after the change.

        Raises:
            CoreError: 404 if there is no such run; 409 if it has ended.
        """
        return to_eval_run_response(eval_run_service.cancel_run(run_id))

    @router.post("/eval-runs/{run_id}/rerun-failed", status_code=201)
    def rerun_failed_cases(
        run_id: UUID, admin: Annotated[User, Depends(current_admin)]
    ) -> EvalRunResponse:
        """Start a new run of an ended run's Fail and Error cases.

        Args:
            run_id: The run's ID.
            admin: The Admin starting it.

        Returns:
            The new run.

        Raises:
            CoreError: 404 if there is no such run; 409 if it hasn't ended;
                422 if nothing in it failed or errored.
        """
        overview = eval_run_service.rerun_failed(
            run_id, admin.id, StartedFrom.DASHBOARD
        )
        return to_eval_run_response(overview)

    @router.delete("/eval-runs/{run_id}", status_code=204)
    def delete_eval_run(run_id: UUID) -> Response:
        """Delete a run with its Case Results and their traces.

        Args:
            run_id: The run's ID.

        Returns:
            An empty response.

        Raises:
            CoreError: 404 if there is no such run; 409 if it is Running.
        """
        eval_run_service.delete_run(run_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.get("/eval-runs/{run_id}/snapshot")
    def open_eval_run_snapshot(run_id: UUID) -> EvalRunSnapshotResponse:
        """Read what a run used: settings, Judge settings and cases as they were.

        Args:
            run_id: The run's ID.

        Returns:
            The snapshot; all null while the run is Queued.

        Raises:
            CoreError: 404 if there is no such run.
        """
        snapshot = eval_run_service.get_snapshot(run_id)
        if snapshot is None:
            return EvalRunSnapshotResponse(settings=None, judge=None, cases=None)
        return EvalRunSnapshotResponse(
            settings=snapshot.settings,
            judge=snapshot.judge,
            cases=[to_eval_case_response(case) for case in snapshot.cases],
        )

    @router.get("/eval-runs/{run_id}/results/{result_id}")
    def open_case_result_trace(
        run_id: UUID, result_id: UUID
    ) -> CaseResultTraceResponse:
        """Open a Case Result with its full trace.

        Args:
            run_id: The run's ID.
            result_id: The result's ID.

        Returns:
            The result and every model call its case made, in order.

        Raises:
            CoreError: 404 if the run has no such result.
        """
        result, calls = eval_run_service.get_result_trace(run_id, result_id)
        return CaseResultTraceResponse(
            run_id=str(run_id),
            result=to_case_result_response(result),
            calls=[to_model_call_response(call) for call in calls],
        )

    @router.get("/eval-cases/{case_key}/history")
    def open_case_history(case_key: str) -> CaseHistoryResponse:
        """Read a case and its pass or fail in recent runs.

        Args:
            case_key: The case's key.

        Returns:
            The case and its newest results, marked where the case or the
            settings changed.

        Raises:
            CoreError: 404 if there is no such case.
        """
        history = eval_run_service.case_history(case_key)
        return CaseHistoryResponse(
            case=to_eval_case_response(history.case),
            entries=[
                CaseHistoryEntryResponse(
                    run_id=str(entry.result.run_id),
                    run_queued_at=entry.run_queued_at,
                    result_id=str(entry.result.id),
                    variant=entry.result.variant,
                    try_number=entry.result.try_number,
                    outcome=entry.result.result.outcome,
                    case_changed=entry.case_changed,
                    changed_settings=entry.changed_settings,
                )
                for entry in history.entries
            ],
        )

    @router.get("/eval-costs")
    def open_eval_costs() -> EvalCostsBody:
        """Read the Model Prices and the Eval run token limit.

        Returns:
            A price per model, null where none is set, and the limit.
        """
        return to_eval_costs_body(eval_costs_service.get())

    @router.put("/eval-costs")
    def save_eval_costs(
        body: EvalCostsBody, admin: Annotated[User, Depends(current_admin)]
    ) -> EvalCostsBody:
        """Save the Model Prices and the Eval run token limit.

        A model with null prices is saved with no price.

        Args:
            body: The prices and limit.
            admin: The Admin saving them.

        Returns:
            The prices and limit after saving.

        Raises:
            CoreError: 422 if a price or the limit is out of range, or only
                one of a model's two prices is given.
        """
        prices = [
            PriceRow(price.model, price.sgd_in, price.sgd_out) for price in body.prices
        ]
        return to_eval_costs_body(
            eval_costs_service.update(admin, prices, body.token_limit)
        )

    @router.get("/eval-runs/{run_id}")
    def open_eval_run(run_id: UUID) -> EvalRunDetailsResponse:
        """Open a run with its Case Results so far.

        Args:
            run_id: The run's ID.

        Returns:
            The run and its results.

        Raises:
            CoreError: 404 if there is no such run.
        """
        details = eval_run_service.get_details(run_id)
        return EvalRunDetailsResponse(
            **to_eval_run_response(details.overview).model_dump(),
            results=[to_case_result_response(result) for result in details.results],
        )

    return router
