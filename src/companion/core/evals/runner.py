import logging
import time
from itertools import product
from typing import Any
from uuid import UUID, uuid4

from companion.core.evals.case_shapes import CASE_SHAPES, image_names
from companion.core.evals.eval_checks import check_case
from companion.core.evals.judge import JudgeSettings
from companion.core.evals.models import (
    FIRST_TRY,
    CaseCheckResult,
    CaseOutcome,
    CaseResult,
    CaseStoppedError,
    EvalCase,
    EvalRun,
    EvalRunState,
    RunSnapshot,
    Variant,
)
from companion.core.evals.ports import (
    EvalCaseRepository,
    EvalCompanion,
    EvalEnvironment,
    EvalImageRepository,
    EvalRunRepository,
    JudgeSettingsRepository,
)
from companion.core.models import ModelCall
from companion.core.platform_settings import EVAL_RUN_TOKEN_LIMIT
from companion.core.ports import Clock, PlatformSettingsRepository

TRACES_PER_CASE_AT_MOST = 500
STOP_REASONS = {
    EvalRunState.CANCELLED: "the run was cancelled",
    EvalRunState.STOPPED_OVER_LIMIT: "the run went over its token limit",
}

logger = logging.getLogger(__name__)


class EvalRunner:
    """Works Eval Runs one at a time, case by case, against the Eval database."""

    def __init__(
        self,
        runs: EvalRunRepository,
        cases: EvalCaseRepository,
        images: EvalImageRepository,
        judge_settings: JudgeSettingsRepository,
        live_settings: PlatformSettingsRepository,
        environment: EvalEnvironment,
        clock: Clock,
    ) -> None:
        """Set up the runner.

        Args:
            runs: The app database's Eval Runs and Case Results.
            cases: The app database's Eval Cases.
            images: The app database's test images for the cases.
            judge_settings: The app database's Judge settings, read only.
            live_settings: The app database's Platform Settings, read only.
            environment: Prepares the Eval database and builds the app on it.
            clock: Tells the time.
        """
        self._runs = runs
        self._cases = cases
        self._images = images
        self._judge_settings = judge_settings
        self._live_settings = live_settings
        self._environment = environment
        self._clock = clock

    def interrupt_unfinished(self) -> list[UUID]:
        """Mark runs left Running by a runner that stopped as Interrupted.

        Called when the runner starts. They are never retried, since runs
        cost money.

        Returns:
            The runs marked.
        """
        return self._runs.interrupt_running(self._clock.now())

    def work_next_run(self) -> bool:
        """Take the oldest Queued run, if any, and run its cases.

        The cases and the Judge's settings are read as they are now, so an
        Admin's edits apply from the next run. Each case gets fresh made-up
        data. A case that raises becomes an Error and the run carries on.
        After each case, and between the Messages of an Understanding case,
        the run ends Cancelled if an Admin cancelled it, or Stopped over
        limit once its tokens are over the Eval run token limit.

        Returns:
            True if a run was worked; False if none was waiting.
        """
        run = self._runs.take_next_queued(self._clock.now())
        if run is None:
            return False
        live = self._live_settings.load()
        snapshot = RunSnapshot(
            settings=dict(live.values),
            judge=self._judge_settings.load(),
            cases=self._cases.list_for_keys(run.case_keys),
        )
        token_limit = live.get(EVAL_RUN_TOKEN_LIMIT)
        self._runs.save_snapshot(run.id, snapshot, token_limit)
        self._environment.start_run()
        tokens_used = 0
        ended_as = EvalRunState.FINISHED
        for case, variant in product(snapshot.cases, run.variants):
            result = self._run_and_save_case(
                run,
                variant,
                case,
                snapshot.settings,
                snapshot.judge,
                tokens_used,
                token_limit,
            )
            tokens_used += result.tokens_in + result.tokens_out
            stop_state = self._stop_state(run.id, tokens_used, token_limit)
            if stop_state is not None:
                ended_as = stop_state
                break
        self._runs.end(run.id, ended_as, self._clock.now())
        return True

    def _stop_state(
        self, run_id: UUID, tokens_used: int, token_limit: int
    ) -> EvalRunState | None:
        """Say how a run is to end now, if it is to stop early.

        Args:
            run_id: The run.
            tokens_used: Its tokens so far.
            token_limit: The most tokens it may use.

        Returns:
            Cancelled or Stopped over limit; None to carry on.
        """
        if self._runs.is_cancel_requested(run_id):
            return EvalRunState.CANCELLED
        if tokens_used > token_limit:
            return EvalRunState.STOPPED_OVER_LIMIT
        return None

    def _run_and_save_case(
        self,
        run: EvalRun,
        variant: Variant,
        case: EvalCase,
        live_settings: dict[str, Any],
        judge_values: dict[str, Any],
        tokens_before: int,
        token_limit: int,
    ) -> CaseResult:
        """Run one case on fresh data with a Variant's settings, then save it.

        Args:
            run: The run.
            variant: The Variant.
            case: The case.
            live_settings: The live Platform Settings when the run started.
            judge_values: The Judge's settings for the run; one missing makes
                the case an Error.
            tokens_before: The run's tokens before this case.
            token_limit: The most tokens the run may use.

        Returns:
            The Case Result, with the model calls it made.
        """
        started = time.monotonic()
        companion: EvalCompanion | None = None
        calls: list[ModelCall] = []

        def should_stop() -> str | None:
            """Say why the run is to stop part-way through this case.

            Returns:
                Why; None to carry on.
            """
            used = sum(companion.tokens_used()) if companion else 0
            stop_state = self._stop_state(run.id, tokens_before + used, token_limit)
            return STOP_REASONS.get(stop_state) if stop_state else None

        try:
            judge = JudgeSettings.from_values(judge_values)
            images = self._images.get_many(
                image_names(CASE_SHAPES[case.eval], case.content)
            )
            companion = self._environment.fresh_companion(
                {**live_settings, **variant.setting_overrides}, images
            )
            result = check_case(case, companion, judge, should_stop)
        except CaseStoppedError as stopped:
            result = CaseCheckResult(outcome=CaseOutcome.ERROR, error=str(stopped))
        except Exception as error:
            logger.exception("Eval case %s errored", case.key)
            result = CaseCheckResult(
                outcome=CaseOutcome.ERROR, error=str(error) or type(error).__name__
            )
        tokens_in, tokens_out = companion.tokens_used() if companion else (0, 0)
        if companion is not None:
            calls = read_case_model_calls(companion)
            close_quietly(companion)
        case_result = CaseResult(
            id=uuid4(),
            run_id=run.id,
            variant=variant.letter,
            try_number=FIRST_TRY,
            case_key=case.key,
            eval=case.eval,
            case_content=case.content,
            result=result,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            duration_ms=round((time.monotonic() - started) * 1000),
            finished_at=self._clock.now(),
            tokens_by_model=companion.tokens_by_model() if companion else {},
        )
        self._runs.add_result(case_result, calls)
        return case_result


def read_case_model_calls(companion: EvalCompanion) -> list[ModelCall]:
    """Read every model call a case made, its full trace.

    The Eval database is emptied before each case, so every call in it is
    this case's. Reading them never fails the case: a failure is logged and
    the trace left empty.

    Args:
        companion: The case's app.

    Returns:
        The calls, oldest trace first, each trace's calls in order.
    """
    model_calls = companion.repositories.model_calls
    try:
        overviews = model_calls.list_traces(
            user_id=None,
            since=None,
            step=None,
            errors_only=False,
            limit=TRACES_PER_CASE_AT_MOST,
        )
        if len(overviews) == TRACES_PER_CASE_AT_MOST:
            logger.warning(
                "An Eval case made %d traces or more; only the newest are kept",
                TRACES_PER_CASE_AT_MOST,
            )
        calls: list[ModelCall] = []
        for overview in reversed(overviews):
            details = model_calls.get_trace(overview.trace.id)
            if details is not None:
                calls += details.calls
        return calls
    except Exception:
        logger.exception("Reading an Eval case's model calls failed")
        return []


def close_quietly(companion: EvalCompanion) -> None:
    """Stop a case's app, logging rather than raising if stopping fails.

    Args:
        companion: The app.
    """
    try:
        companion.close()
    except Exception:
        logger.exception("Stopping an Eval case's app failed")
