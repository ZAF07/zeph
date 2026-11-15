from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any
from uuid import UUID, uuid4

from companion.core.errors import ConflictError, InvalidError, NotFoundError
from companion.core.evals.case_editing import EvalCaseNotFoundError
from companion.core.evals.costs import (
    ROUGH_TOKENS_PER_CASE,
    price_tokens,
    stored_prices,
)
from companion.core.evals.models import (
    ENDED_STATES,
    FIRST_TRY,
    MAX_REPEATS,
    VARIANT_LETTERS,
    CaseHistory,
    CaseHistoryEntry,
    CaseHistoryRow,
    CaseOutcome,
    CaseResult,
    Estimate,
    EvalCase,
    EvalName,
    EvalOverview,
    EvalRunDetails,
    EvalRunOverview,
    EvalRunState,
    ModelTokens,
    RunSnapshot,
    RunTotals,
    StartedFrom,
    Variant,
    VariantEstimate,
    VariantTotals,
    add_tokens_by_model,
)
from companion.core.evals.ports import EvalCaseRepository, EvalRunRepository
from companion.core.evals.setting_overrides import SettingOverrideService
from companion.core.models import ModelCall
from companion.core.platform_settings import (
    EVAL_RUN_TOKEN_LIMIT,
    MODEL_PRICES,
    RESPONSE_MODEL,
    ModelPrice,
)
from companion.core.ports import Clock, PlatformSettingsRepository

CASE_HISTORY_LENGTH = 20
COST_SETTING_KEYS = frozenset({MODEL_PRICES.key, EVAL_RUN_TOKEN_LIMIT.key})
FAILED_OUTCOMES = (CaseOutcome.FAIL, CaseOutcome.ERROR)


class NoEvalsChosenError(InvalidError):
    """Raised when a run is started without any Eval or case."""

    shown_message = "Pick at least one Eval or case to run."


class NoEvalCasesError(InvalidError):
    """Raised when the Evals chosen have no cases to run."""

    shown_message = "The Evals picked have no cases to run."


class UnknownEvalCaseError(InvalidError):
    """Raised when a case picked by key doesn't exist or is archived."""


class EvalRunNotFoundError(NotFoundError):
    """Raised when an Eval Run doesn't exist."""

    shown_message = "No such Eval Run."


class CaseResultNotFoundError(NotFoundError):
    """Raised when a run has no such Case Result."""

    shown_message = "No such Case Result in this run."


class EvalRunEndedError(ConflictError):
    """Raised when cancelling a run that has already ended."""

    shown_message = "This run has already ended."


class EvalRunStillGoingError(ConflictError):
    """Raised when re-running or deleting a run that hasn't ended."""


class InvalidVariantsError(InvalidError):
    """Raised when a run has no Variants or more than it may have."""

    shown_message = f"A run has 1 to {len(VARIANT_LETTERS)} Variants."


class InvalidRepeatsError(InvalidError):
    """Raised when a run's Repeats are out of range."""

    shown_message = f"Repeats must be a whole number from {FIRST_TRY} to {MAX_REPEATS}."


class NothingFailedError(InvalidError):
    """Raised when re-running the failed cases of a run with none."""

    shown_message = "No case failed or errored in this run."


def changed_keys(older: dict[str, Any], newer: dict[str, Any]) -> list[str]:
    """List the keys whose values differ between two sets of settings.

    Args:
        older: The older settings, by key.
        newer: The newer settings, by key.

    Returns:
        The keys added, removed or changed, sorted.
    """
    return sorted(
        key for key in older.keys() | newer.keys() if older.get(key) != newer.get(key)
    )


def changed_setting_names(older: CaseHistoryRow, newer: CaseHistoryRow) -> list[str]:
    """Name the settings that differ between two runs of a case.

    Model Prices and the token limit are left out, since they never change
    a result.

    Args:
        older: The older result's run.
        newer: The newer result's run.

    Returns:
        The Platform Settings' keys, then the Judge settings' as
        `judge.<name>`.
    """
    platform = [
        key
        for key in changed_keys(older.settings, newer.settings)
        if key not in COST_SETTING_KEYS
    ]
    judge = [f"judge.{key}" for key in changed_keys(older.judge, newer.judge)]
    return platform + judge


def mark_changes(rows: Sequence[CaseHistoryRow]) -> list[CaseHistoryEntry]:
    """Mark each result with what changed since the older result after it.

    Args:
        rows: A case's results with what their runs used, newest first.

    Returns:
        The same results, newest first; the oldest has nothing marked.
    """
    entries = []
    for row, older in zip(rows, [*rows[1:], None], strict=True):
        entries.append(
            CaseHistoryEntry(
                result=row.result,
                run_queued_at=row.run_queued_at,
                case_changed=(
                    older is not None
                    and older.result.case_content != row.result.case_content
                ),
                changed_settings=(
                    changed_setting_names(older, row) if older is not None else []
                ),
            )
        )
    return entries


def check_variants_and_repeats(
    variant_overrides: Sequence[Mapping[str, Any]], repeats: int
) -> None:
    """Check a run has 1 to 3 Variants and Repeats in range.

    Args:
        variant_overrides: Each Variant's Setting Overrides.
        repeats: How many times each case runs per Variant.

    Raises:
        InvalidVariantsError: If there are no Variants or too many.
        InvalidRepeatsError: If Repeats are out of range.
    """
    if not FIRST_TRY <= repeats <= MAX_REPEATS:
        raise InvalidRepeatsError()
    if not 1 <= len(variant_overrides) <= len(VARIANT_LETTERS):
        raise InvalidVariantsError()


def variant_totals(
    letter: str, results: Sequence[CaseResult], prices: Mapping[str, ModelPrice]
) -> VariantTotals:
    """Add up one Variant's Case Results.

    Args:
        letter: The Variant's letter.
        results: Its Case Results.
        prices: The Model Prices the run started with.

    Returns:
        Its passes, fails, errors, tokens, time and cost.
    """
    outcomes = [result.result.outcome for result in results]
    tokens_by_model: dict[str, ModelTokens] = add_tokens_by_model(
        *(result.tokens_by_model for result in results)
    )
    return VariantTotals(
        letter=letter,
        totals=RunTotals(
            passed=outcomes.count(CaseOutcome.PASS),
            failed=outcomes.count(CaseOutcome.FAIL),
            errored=outcomes.count(CaseOutcome.ERROR),
            tokens_in=sum(result.tokens_in for result in results),
            tokens_out=sum(result.tokens_out for result in results),
            tokens_by_model=tokens_by_model,
        ),
        duration_ms=sum(result.duration_ms for result in results),
        cost=price_tokens(tokens_by_model, prices),
    )


class EvalRunService:
    """Starts, estimates, cancels, re-runs and deletes Eval Runs, and shows them.

    The `eval-runner` service works the runs this saves as Queued.
    """

    def __init__(
        self,
        runs: EvalRunRepository,
        cases: EvalCaseRepository,
        settings: PlatformSettingsRepository,
        overrides: SettingOverrideService,
        clock: Clock,
    ) -> None:
        """Set up the service.

        Args:
            runs: Where Eval Runs and Case Results are stored.
            cases: Where Eval Cases are stored.
            settings: The live Platform Settings, for estimates.
            overrides: Checks Variants' Setting Overrides.
            clock: Tells the time.
        """
        self._runs = runs
        self._cases = cases
        self._settings = settings
        self._overrides = overrides
        self._clock = clock

    def list_evals(self) -> list[EvalOverview]:
        """List every Eval with the cases a new run of it would run.

        Returns:
            One overview per Eval, in a fixed order.
        """
        cases = self._cases.list_for_evals(list(EvalName))
        return [
            EvalOverview(
                eval=name,
                case_keys=[case.key for case in cases if case.eval == name],
            )
            for name in EvalName
        ]

    def start_run(
        self,
        started_by: UUID | None,
        started_from: StartedFrom,
        evals: Sequence[EvalName],
        case_keys: Sequence[str] = (),
        variant_overrides: Sequence[Mapping[str, Any]] = ({},),
        repeats: int = FIRST_TRY,
    ) -> EvalRunOverview:
        """Save a new run of whole Evals and single cases as Queued.

        Each Variant's Setting Overrides are held to the same checks as a
        save on the settings pages; the live settings are never touched.

        Args:
            started_by: The Admin starting it; None from the terminal.
            started_from: Where it is started.
            evals: The Evals whose every case it runs.
            case_keys: Single cases it runs as well, by key.
            variant_overrides: Each Variant's Setting Overrides, lettered
                A, B, C in order; an empty one runs the live settings.
            repeats: How many times each case runs per Variant.

        Returns:
            The run.

        Raises:
            NoEvalsChosenError: If no Eval or case is given.
            UnknownEvalCaseError: If a key isn't a case that can run.
            NoEvalCasesError: If the Evals have no cases.
            InvalidVariantsError: If there are no Variants or too many.
            InvalidRepeatsError: If Repeats are out of range.
            InvalidError: If a Setting Override is refused.
            NotFoundError: If a Setting Override names no live Need.
        """
        cases = self._pick_cases(evals, case_keys)
        check_variants_and_repeats(variant_overrides, repeats)
        variants = [
            Variant(letter, self._overrides.checked(overrides))
            for letter, overrides in zip(
                VARIANT_LETTERS, variant_overrides, strict=False
            )
        ]
        return self._queue(started_by, started_from, cases, variants, repeats, None)

    def estimate(
        self,
        evals: Sequence[EvalName],
        case_keys: Sequence[str] = (),
        variant_overrides: Sequence[Mapping[str, Any]] = ({},),
        repeats: int = FIRST_TRY,
    ) -> Estimate:
        """Estimate what a run of whole Evals and single cases would use.

        Each case counts the tokens of its newest Case Result; a case never
        run counts a rough figure for its Eval, on the Variant's reply
        model. Every Variant counts every case once per Repeat. Overrides
        aren't checked here, so an estimate shows while they are typed.

        Args:
            evals: The Evals whose every case it would run.
            case_keys: Single cases it would run as well, by key.
            variant_overrides: Each Variant's Setting Overrides.
            repeats: How many times each case would run per Variant.

        Returns:
            The estimate, priced at the live Model Prices.

        Raises:
            NoEvalsChosenError: If no Eval or case is given.
            UnknownEvalCaseError: If a key isn't a case that can run.
            NoEvalCasesError: If the Evals have no cases.
            InvalidVariantsError: If there are no Variants or too many.
            InvalidRepeatsError: If Repeats are out of range.
        """
        cases = self._pick_cases(evals, case_keys)
        check_variants_and_repeats(variant_overrides, repeats)
        newest = self._runs.newest_tokens_by_case([case.key for case in cases])
        settings = self._settings.load()
        prices = stored_prices(settings.values)
        variants = []
        for letter, overrides in zip(VARIANT_LETTERS, variant_overrides, strict=False):
            rough_model = overrides.get(RESPONSE_MODEL.key)
            if not isinstance(rough_model, str):
                rough_model = settings.get(RESPONSE_MODEL)
            per_case = add_tokens_by_model(
                *(
                    newest.get(
                        case.key, {rough_model: ROUGH_TOKENS_PER_CASE[case.eval]}
                    )
                    for case in cases
                )
            )
            tokens = {model: count.times(repeats) for model, count in per_case.items()}
            variants.append(
                VariantEstimate(letter, tokens, price_tokens(tokens, prices))
            )
        tokens = add_tokens_by_model(*(variant.tokens for variant in variants))
        return Estimate(
            tokens=tokens,
            cost=price_tokens(tokens, prices),
            case_count=len(cases) * len(variants) * repeats,
            rough_case_count=sum(1 for case in cases if case.key not in newest),
            variants=variants,
        )

    def rerun_failed(
        self, run_id: UUID, started_by: UUID | None, started_from: StartedFrom
    ) -> EvalRunOverview:
        """Start a new run of an ended run's Fail and Error cases.

        A case is run again if any of its tries on any Variant failed or
        errored. The new run has the same Variants and Repeats, so its
        results compare fairly; their overrides are checked again, as
        settings may have changed since. Cases archived since are left out.

        Args:
            run_id: The run whose failed cases to run again.
            started_by: The Admin starting it; None from the terminal.
            started_from: Where it is started.

        Returns:
            The new run.

        Raises:
            EvalRunNotFoundError: If there is no such run.
            EvalRunStillGoingError: If the run hasn't ended.
            NothingFailedError: If none of its cases failed or errored, or
                those that did are archived.
            InvalidError: If a Setting Override is refused now.
            NotFoundError: If a Setting Override names a Need deleted since.
        """
        run = self.get_overview(run_id).run
        if run.state not in ENDED_STATES:
            raise EvalRunStillGoingError("Wait for this run to end first.")
        failed_keys = list(
            dict.fromkeys(
                result.case_key
                for result in self._runs.list_results(run_id)
                if result.result.outcome in FAILED_OUTCOMES
            )
        )
        cases = self._cases.list_for_keys(failed_keys) if failed_keys else []
        if not cases:
            raise NothingFailedError()
        variants = [
            Variant(variant.letter, self._overrides.checked(variant.setting_overrides))
            for variant in run.variants
        ]
        return self._queue(
            started_by, started_from, cases, variants, run.repeats, run_id
        )

    def cancel_run(self, run_id: UUID) -> EvalRunOverview:
        """Cancel a run: a Queued one at once, a Running one after its case.

        Finished Case Results are kept.

        Args:
            run_id: The run.

        Returns:
            The run after the change.

        Raises:
            EvalRunNotFoundError: If there is no such run.
            EvalRunEndedError: If the run has already ended.
        """
        if self.get_overview(run_id).run.state in ENDED_STATES:
            raise EvalRunEndedError()
        self._runs.request_cancel(run_id, self._clock.now())
        return self.get_overview(run_id)

    def delete_run(self, run_id: UUID) -> None:
        """Delete a run with its Case Results and their traces.

        Args:
            run_id: The run.

        Raises:
            EvalRunNotFoundError: If there is no such run.
            EvalRunStillGoingError: If the run is Running.
        """
        if self.get_overview(run_id).run.state == EvalRunState.RUNNING:
            raise EvalRunStillGoingError("Cancel this run before deleting it.")
        self._runs.delete(run_id)

    def list_runs(self, include_terminal: bool) -> list[EvalRunOverview]:
        """List runs with their totals and cost, newest first.

        Args:
            include_terminal: Whether to list runs started from the terminal.

        Returns:
            The runs.
        """
        return [
            self._priced(overview)
            for overview in self._runs.list_overviews(include_terminal)
        ]

    def get_overview(self, run_id: UUID) -> EvalRunOverview:
        """Read one run with its totals and cost.

        Args:
            run_id: The run's ID.

        Returns:
            The run.

        Raises:
            EvalRunNotFoundError: If there is no such run.
        """
        overview = self._runs.get_overview(run_id)
        if overview is None:
            raise EvalRunNotFoundError()
        return self._priced(overview)

    def get_details(self, run_id: UUID) -> EvalRunDetails:
        """Read one run with its Case Results so far.

        Args:
            run_id: The run's ID.

        Returns:
            The run, its results and each Variant's totals.

        Raises:
            EvalRunNotFoundError: If there is no such run.
        """
        overview = self.get_overview(run_id)
        results = self._runs.list_results(run_id)
        snapshot = overview.run.snapshot
        prices = stored_prices(snapshot.settings) if snapshot else {}
        return EvalRunDetails(
            overview=overview,
            results=results,
            variant_totals=[
                variant_totals(
                    variant.letter,
                    [result for result in results if result.variant == variant.letter],
                    prices,
                )
                for variant in overview.run.variants
            ],
        )

    def get_snapshot(self, run_id: UUID) -> RunSnapshot | None:
        """Read what a run used: settings, Judge settings and cases as they were.

        Args:
            run_id: The run's ID.

        Returns:
            The snapshot; None while the run is Queued.

        Raises:
            EvalRunNotFoundError: If there is no such run.
        """
        return self.get_overview(run_id).run.snapshot

    def get_result_trace(
        self, run_id: UUID, result_id: UUID
    ) -> tuple[CaseResult, list[ModelCall]]:
        """Read one Case Result with its full trace.

        Args:
            run_id: The run.
            result_id: The result.

        Returns:
            The result and every model call its case made, in order.

        Raises:
            CaseResultNotFoundError: If the run has no such result.
        """
        result = self._runs.get_result(run_id, result_id)
        if result is None:
            raise CaseResultNotFoundError()
        return result, self._runs.list_result_calls(result_id)

    def case_history(self, case_key: str) -> CaseHistory:
        """Read a case and how it went in its most recent runs.

        Args:
            case_key: The case's key.

        Returns:
            The case and its newest results, each marked where the case or
            the settings changed since the result before.

        Raises:
            EvalCaseNotFoundError: If there is no such case.
        """
        stored = self._cases.get(case_key)
        if stored is None:
            raise EvalCaseNotFoundError()
        rows = self._runs.list_case_history(case_key, CASE_HISTORY_LENGTH + 1)
        return CaseHistory(
            case=stored.case, entries=mark_changes(rows)[:CASE_HISTORY_LENGTH]
        )

    def _pick_cases(
        self, evals: Sequence[EvalName], case_keys: Sequence[str]
    ) -> list[EvalCase]:
        """Find the cases a run of whole Evals and single cases runs.

        Args:
            evals: The Evals whose every case it runs.
            case_keys: Single cases it runs as well, by key.

        Returns:
            The cases, by Eval, then in the order added.

        Raises:
            NoEvalsChosenError: If no Eval or case is given.
            UnknownEvalCaseError: If a key isn't a case that can run.
            NoEvalCasesError: If the Evals have no cases.
        """
        if not evals and not case_keys:
            raise NoEvalsChosenError()
        available = self._cases.list_for_evals(list(EvalName))
        known = {case.key for case in available}
        unknown = [key for key in dict.fromkeys(case_keys) if key not in known]
        if unknown:
            raise UnknownEvalCaseError(
                f"There's no case to run named {', '.join(unknown)}."
            )
        picked = set(case_keys)
        cases = [case for case in available if case.eval in evals or case.key in picked]
        if not cases:
            raise NoEvalCasesError()
        return cases

    def _queue(
        self,
        started_by: UUID | None,
        started_from: StartedFrom,
        cases: Sequence[EvalCase],
        variants: Sequence[Variant],
        repeats: int,
        rerun_of: UUID | None,
    ) -> EvalRunOverview:
        """Save a run of some cases as Queued.

        Args:
            started_by: The Admin starting it; None from the terminal.
            started_from: Where it is started.
            cases: The cases it runs, in order.
            variants: Its Variants.
            repeats: How many times each case runs per Variant.
            rerun_of: The run whose failed cases it runs again, if any.

        Returns:
            The run.
        """
        run_id = uuid4()
        self._runs.add(
            run_id,
            started_by,
            started_from,
            list(dict.fromkeys(case.eval for case in cases)),
            [case.key for case in cases],
            self._clock.now(),
            variants,
            repeats,
            rerun_of,
        )
        return self.get_overview(run_id)

    def _priced(self, overview: EvalRunOverview) -> EvalRunOverview:
        """Price a run's tokens at the Model Prices it started with.

        A Queued run has used no tokens yet, so it is priced at nothing.

        Args:
            overview: The run and its totals.

        Returns:
            The same run with its cost.
        """
        snapshot = overview.run.snapshot
        prices = stored_prices(snapshot.settings) if snapshot else {}
        return replace(
            overview, cost=price_tokens(overview.totals.tokens_by_model, prices)
        )
