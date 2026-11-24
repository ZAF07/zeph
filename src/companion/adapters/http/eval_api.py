from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

from companion.adapters.http.admin_api import ModelCallResponse, to_model_call_response
from companion.core.evals.costs import EvalCosts, EvalCostsService, PriceRow
from companion.core.evals.make_live import MakeLiveService
from companion.core.evals.models import (
    FIRST_TRY,
    CaseOutcome,
    CaseResult,
    Cost,
    EvalCase,
    EvalName,
    EvalRunOverview,
    EvalRunState,
    ModelTokens,
    StartedFrom,
    Variant,
    VariantTotals,
)
from companion.core.evals.runs import EvalRunService
from companion.core.evals.setting_overrides import (
    SettingOverrideService,
    move_override_key,
    move_values,
    need_override_key,
    need_values,
)
from companion.core.models import Move, Need, User
from companion.core.platform_settings import SettingKind


class EvalResponse(BaseModel):
    """An Eval and the cases a new run of it would run."""

    eval: EvalName
    case_keys: list[str]


class EvalsResponse(BaseModel):
    """Every Eval, in a fixed order."""

    evals: list[EvalResponse]


class StartEvalRunRequest(BaseModel):
    """The whole Evals and single cases a new run runs, its Variants and Repeats.

    Each Variant is its Setting Overrides, by setting key or `need:<id>`;
    they are lettered A, B, C in order. One empty Variant runs the live
    settings.
    """

    evals: list[EvalName] = []
    case_keys: list[str] = []
    variants: list[dict[str, Any]] = [{}]
    repeats: int = FIRST_TRY


class VariantEstimateResponse(BaseModel):
    """What one Variant would use, counting every Repeat."""

    letter: str
    tokens_in: int
    tokens_out: int
    cost_sgd: float
    unpriced_models: list[str]


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
    variants: list[VariantEstimateResponse]


class MadeLiveResponse(BaseModel):
    """Who made a Variant live, when, and what was applied or left out."""

    by_name: str | None
    at: datetime
    applied_keys: list[str]
    left_out_keys: list[str]


class VariantResponse(BaseModel):
    """One set of settings a run runs its cases with."""

    letter: str
    setting_overrides: dict[str, Any]
    made_live: MadeLiveResponse | None


class VariantTotalsResponse(BaseModel):
    """How one Variant's finished cases went, added up."""

    letter: str
    passed: int
    failed: int
    errored: int
    tokens_in: int
    tokens_out: int
    duration_ms: int
    cost_sgd: float
    unpriced_models: list[str]


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


class DaySummaryAnswerResponse(BaseModel):
    """One question of a Day Summary case, answered from the Summary and marked."""

    question: str
    expected: str
    answer: str
    matched: bool
    reason: str


class DaySummaryResultResponse(BaseModel):
    """The Day Summary a Day Summary case wrote, and each question's answer."""

    summary: str
    answers: list[DaySummaryAnswerResponse]


class KeptObservationResponse(BaseModel):
    """An Observation a Tagging case's tagging step kept."""

    pattern_types: list[str]
    sign: str
    direction: str
    unclear: bool
    situational: bool
    quote: str
    context: str
    about: str
    thread: str | None
    expected: bool


class DroppedObservationResponse(BaseModel):
    """An Observation the tagging model wrote that code dropped, and why."""

    pattern_types: list[str]
    sign: str
    direction: str
    quote: str
    reason: str


class ExpectedObservationResponse(BaseModel):
    """An Observation a Tagging case expected, and whether one like it was kept."""

    pattern_type: str
    direction: str
    unclear: bool
    situational: bool
    matched: bool


class TaggingResultResponse(BaseModel):
    """What a Tagging case's tagging step kept and dropped, and what it expected."""

    answered: bool
    kept: list[KeptObservationResponse]
    dropped: list[DroppedObservationResponse]
    expected: list[ExpectedObservationResponse]


class CaseResultResponse(BaseModel):
    """One case's result in a run.

    `day_summary` only for a checked Day Summary case, `tagging` only for a
    checked Tagging case.
    """

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
    day_summary: DaySummaryResultResponse | None = None
    tagging: TaggingResultResponse | None = None


class EvalRunDetailsResponse(EvalRunResponse):
    """An Eval Run with its Case Results so far, in the order they finished."""

    results: list[CaseResultResponse]
    variant_totals: list[VariantTotalsResponse]


class OverridableSettingResponse(BaseModel):
    """A Platform Setting a Variant can override, with its rule and live value."""

    key: str
    label: str
    kind: SettingKind
    minimum: int
    maximum: int
    max_length: int
    hint: str
    value: Any


class NeedResponse(BaseModel):
    """A Need keyed as its override would be, `need:<id>`, with its details."""

    key: str
    name: str
    value: dict[str, str]


class MoveResponse(BaseModel):
    """A Move keyed as its override would be, `move:<id>`, with its text."""

    key: str
    name: str
    value: dict[str, str]


class OverrideChoicesResponse(BaseModel):
    """What a Variant can override, as on the settings pages."""

    settings: list[OverridableSettingResponse]
    needs: list[NeedResponse]
    moves: list[MoveResponse]
    models: list[str]


class LiveChangeResponse(BaseModel):
    """An overridden setting whose live value changed since the run started.

    `now` is null for a Need or Move deleted since.
    """

    key: str
    then: Any
    now: Any
    override: Any


class LiveChangesResponse(BaseModel):
    """The settings to confirm or leave out before making a Variant live."""

    changes: list[LiveChangeResponse]


class MakeLiveRequest(BaseModel):
    """The changed settings the Admin chose to apply as well."""

    confirmed_keys: list[str] = []


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
    needs: list[NeedResponse] | None
    moves: list[MoveResponse] | None


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
        variants=[to_variant_response(variant) for variant in run.variants],
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


def to_need_response(need: Need) -> NeedResponse:
    """Turn a Need into its API shape, keyed as its override would be.

    Args:
        need: The Need.

    Returns:
        The response.
    """
    return NeedResponse(
        key=need_override_key(need.id), name=need.name, value=need_values(need)
    )


def to_move_response(move: Move) -> MoveResponse:
    """Turn a Move into its API shape, keyed as its override would be.

    Args:
        move: The Move.

    Returns:
        The response.
    """
    return MoveResponse(
        key=move_override_key(move.id), name=move.name, value=move_values(move)
    )


def to_variant_response(variant: Variant) -> VariantResponse:
    """Turn a Variant into its API shape.

    Args:
        variant: The Variant.

    Returns:
        The response.
    """
    made_live = variant.made_live
    return VariantResponse(
        letter=variant.letter,
        setting_overrides=variant.setting_overrides,
        made_live=(
            MadeLiveResponse(
                by_name=made_live.by_name,
                at=made_live.at,
                applied_keys=made_live.applied_keys,
                left_out_keys=made_live.left_out_keys,
            )
            if made_live
            else None
        ),
    )


def to_variant_totals_response(totals: VariantTotals) -> VariantTotalsResponse:
    """Turn a Variant's totals into their API shape.

    Args:
        totals: The Variant's totals.

    Returns:
        The response.
    """
    return VariantTotalsResponse(
        letter=totals.letter,
        passed=totals.totals.passed,
        failed=totals.totals.failed,
        errored=totals.totals.errored,
        tokens_in=totals.totals.tokens_in,
        tokens_out=totals.totals.tokens_out,
        duration_ms=totals.duration_ms,
        **cost_fields(totals.cost),
    )


def to_day_summary_result(result: CaseResult) -> DaySummaryResultResponse | None:
    """Read what a Day Summary case wrote and answered from its result's facts.

    Args:
        result: The Case Result.

    Returns:
        The Summary and each answer; None for another Eval's case, or a Day
        Summary case that couldn't be checked.
    """
    facts = result.result.facts
    if result.eval != EvalName.DAY_SUMMARY or "summary" not in facts:
        return None
    return DaySummaryResultResponse(
        summary=facts["summary"],
        answers=[DaySummaryAnswerResponse(**answer) for answer in facts["answers"]],
    )


def to_tagging_result(result: CaseResult) -> TaggingResultResponse | None:
    """Read what a Tagging case kept and dropped from its result's facts.

    Args:
        result: The Case Result.

    Returns:
        What was kept, dropped and expected; None for another Eval's case,
        or a Tagging case that couldn't be checked.
    """
    facts = result.result.facts
    if result.eval != EvalName.TAGGING or "tagging" not in facts:
        return None
    return TaggingResultResponse(**facts["tagging"])


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
        day_summary=to_day_summary_result(result),
        tagging=to_tagging_result(result),
    )


def build_eval_api_router(
    current_admin: Callable[..., User],
    eval_run_service: EvalRunService,
    eval_costs_service: EvalCostsService,
    make_live_service: MakeLiveService,
    setting_override_service: SettingOverrideService,
) -> APIRouter:
    """Build the admin routes for Evals, Eval Runs and their costs.

    Every route refuses anyone who is not an Admin.

    Args:
        current_admin: The dependency that lets only Admins through.
        eval_run_service: Starts Eval Runs and shows how they went.
        eval_costs_service: Reads and saves Model Prices and the token limit.
        make_live_service: Makes a Variant's Setting Overrides live.
        setting_override_service: Lists what a Variant can override.

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
            CoreError: 422 if nothing is picked, a case key is unknown, the
                Evals have no cases, the Variants or Repeats are out of
                range or a Setting Override is refused; 404 if an override
                names no live Need.
        """
        overview = eval_run_service.start_run(
            admin.id,
            StartedFrom.DASHBOARD,
            request.evals,
            request.case_keys,
            request.variants,
            request.repeats,
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
        estimate = eval_run_service.estimate(
            request.evals, request.case_keys, request.variants, request.repeats
        )
        return EstimateResponse(
            case_count=estimate.case_count,
            rough_case_count=estimate.rough_case_count,
            tokens_in=sum(count.tokens_in for count in estimate.tokens.values()),
            tokens_out=sum(count.tokens_out for count in estimate.tokens.values()),
            models=to_model_tokens_responses(estimate.tokens),
            **cost_fields(estimate.cost),
            variants=[
                VariantEstimateResponse(
                    letter=variant.letter,
                    tokens_in=sum(count.tokens_in for count in variant.tokens.values()),
                    tokens_out=sum(
                        count.tokens_out for count in variant.tokens.values()
                    ),
                    **cost_fields(variant.cost),
                )
                for variant in estimate.variants
            ],
        )

    @router.get("/setting-override-choices")
    def list_setting_override_choices() -> OverrideChoicesResponse:
        """List what a Variant can override, with each one's live value.

        Returns:
            The settings Admins can edit with their rules, the Needs, and
            the models a model setting can pick.
        """
        choices = setting_override_service.choices()
        return OverrideChoicesResponse(
            settings=[
                OverridableSettingResponse(
                    key=choice.setting.key,
                    label=choice.setting.label,
                    kind=choice.setting.kind,
                    minimum=choice.setting.minimum,
                    maximum=choice.setting.maximum,
                    max_length=choice.setting.max_length,
                    hint=choice.setting.hint,
                    value=choice.value,
                )
                for choice in choices.settings
            ],
            needs=[to_need_response(need) for need in choices.needs],
            moves=[to_move_response(move) for move in choices.moves],
            models=choices.models,
        )

    @router.get("/eval-runs/{run_id}/variants/{letter}/live-changes")
    def list_live_changes(run_id: UUID, letter: str) -> LiveChangesResponse:
        """List a Variant's overridden settings changed live since its run.

        Args:
            run_id: The run's ID.
            letter: The Variant's letter.

        Returns:
            Each with its value then, now and the override; empty when
            Make Live needs no confirming.

        Raises:
            CoreError: 404 if there is no such run or Variant; 409 if the
                run didn't finish or the Variant was made live already; 422
                if it has no overrides.
        """
        return LiveChangesResponse(
            changes=[
                LiveChangeResponse(
                    key=change.key,
                    then=change.then,
                    now=change.now,
                    override=change.override,
                )
                for change in make_live_service.changes_since_run(run_id, letter)
            ]
        )

    @router.post("/eval-runs/{run_id}/variants/{letter}/make-live")
    def make_variant_live(
        run_id: UUID,
        letter: str,
        request: MakeLiveRequest,
        admin: Annotated[User, Depends(current_admin)],
    ) -> VariantResponse:
        """Apply a Variant's Setting Overrides to the live settings.

        Overrides unchanged live since the run are applied, with the changed
        ones the Admin confirmed; other changed ones are left out.

        Args:
            run_id: The run's ID.
            letter: The Variant's letter.
            request: The changed settings to apply as well.
            admin: The Admin making it live.

        Returns:
            The Variant, with who made it live, when and what.

        Raises:
            CoreError: 404 if there is no such run, Variant or Need; 409 if
                the run didn't finish or the Variant was made live already;
                422 if it has no overrides or the settings save refuses one.
        """
        variant = make_live_service.make_live(
            run_id, letter, admin, set(request.confirmed_keys)
        )
        return to_variant_response(variant)

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
            The snapshot, with the live Needs and Moves keyed as their
            overrides would be; all null while the run is Queued.

        Raises:
            CoreError: 404 if there is no such run.
        """
        snapshot = eval_run_service.get_snapshot(run_id)
        if snapshot is None:
            return EvalRunSnapshotResponse(
                settings=None, judge=None, cases=None, needs=None, moves=None
            )
        return EvalRunSnapshotResponse(
            settings=snapshot.settings,
            judge=snapshot.judge,
            cases=[to_eval_case_response(case) for case in snapshot.cases],
            needs=[to_need_response(need) for need in snapshot.needs],
            moves=[to_move_response(move) for move in snapshot.moves],
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
            variant_totals=[
                to_variant_totals_response(totals) for totals in details.variant_totals
            ],
        )

    return router
