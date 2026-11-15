from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from companion.core.evals.models import (
    CaseOutcome,
    CaseResult,
    EvalName,
    EvalRunOverview,
    EvalRunState,
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
    """The Evals a new run runs."""

    evals: list[EvalName]


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
    case_count: int | None
    passed: int
    failed: int
    errored: int
    tokens_in: int
    tokens_out: int


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
        passed=totals.passed,
        failed=totals.failed,
        errored=totals.errored,
        tokens_in=totals.tokens_in,
        tokens_out=totals.tokens_out,
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
    current_admin: Callable[..., User], eval_run_service: EvalRunService
) -> APIRouter:
    """Build the admin routes for Evals and Eval Runs.

    Every route refuses anyone who is not an Admin.

    Args:
        current_admin: The dependency that lets only Admins through.
        eval_run_service: Starts Eval Runs and shows how they went.

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
        """Start a run of some Evals from the Dashboard; it waits as Queued.

        Args:
            request: The Evals to run.
            admin: The Admin starting it.

        Returns:
            The run.

        Raises:
            CoreError: 422 if no Eval is given or they have no cases.
        """
        overview = eval_run_service.start_run(
            admin.id, StartedFrom.DASHBOARD, request.evals
        )
        return to_eval_run_response(overview)

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
