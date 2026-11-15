import logging
import time
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
    EvalCase,
    EvalRun,
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
from companion.core.ports import Clock, PlatformSettingsRepository

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
        """Take the oldest Queued run, if any, and run all its cases.

        The cases and the Judge's settings are read as they are now, so an
        Admin's edits apply from the next run. Each case gets fresh made-up
        data. A case that raises becomes an Error and the run carries on.

        Returns:
            True if a run was worked; False if none was waiting.
        """
        run = self._runs.take_next_queued(self._clock.now())
        if run is None:
            return False
        snapshot = RunSnapshot(
            settings=dict(self._live_settings.load().values),
            judge=self._judge_settings.load(),
            cases=self._cases.list_for_evals(run.evals),
        )
        self._runs.save_snapshot(run.id, snapshot)
        self._environment.start_run()
        for case in snapshot.cases:
            for variant in run.variants:
                self._runs.add_result(
                    self._run_case(
                        run, variant, case, snapshot.settings, snapshot.judge
                    )
                )
        self._runs.finish(run.id, self._clock.now())
        return True

    def _run_case(
        self,
        run: EvalRun,
        variant: Variant,
        case: EvalCase,
        live_settings: dict[str, Any],
        judge_values: dict[str, Any],
    ) -> CaseResult:
        """Run one case on fresh data with a Variant's settings.

        Args:
            run: The run.
            variant: The Variant.
            case: The case.
            live_settings: The live Platform Settings when the run started.
            judge_values: The Judge's settings for the run; one missing makes
                the case an Error.

        Returns:
            The Case Result.
        """
        started = time.monotonic()
        companion: EvalCompanion | None = None
        try:
            judge = JudgeSettings.from_values(judge_values)
            images = self._images.get_many(
                image_names(CASE_SHAPES[case.eval], case.content)
            )
            companion = self._environment.fresh_companion(
                {**live_settings, **variant.setting_overrides}, images
            )
            result = check_case(case, companion, judge)
        except Exception as error:
            logger.exception("Eval case %s errored", case.key)
            result = CaseCheckResult(
                outcome=CaseOutcome.ERROR, error=str(error) or type(error).__name__
            )
        tokens_in, tokens_out = companion.tokens_used() if companion else (0, 0)
        if companion is not None:
            close_quietly(companion)
        return CaseResult(
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
        )


def close_quietly(companion: EvalCompanion) -> None:
    """Stop a case's app, logging rather than raising if stopping fails.

    Args:
        companion: The app.
    """
    try:
        companion.close()
    except Exception:
        logger.exception("Stopping an Eval case's app failed")
