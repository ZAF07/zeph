from collections.abc import Sequence
from uuid import UUID, uuid4

from companion.core.errors import InvalidError, NotFoundError
from companion.core.evals.models import (
    EvalName,
    EvalOverview,
    EvalRunDetails,
    EvalRunOverview,
    StartedFrom,
)
from companion.core.evals.ports import EvalCaseRepository, EvalRunRepository
from companion.core.ports import Clock


class NoEvalsChosenError(InvalidError):
    """Raised when a run is started without any Eval."""

    shown_message = "Pick at least one Eval to run."


class NoEvalCasesError(InvalidError):
    """Raised when the Evals chosen have no cases to run."""

    shown_message = "The Evals picked have no cases to run."


class EvalRunNotFoundError(NotFoundError):
    """Raised when an Eval Run doesn't exist."""

    shown_message = "No such Eval Run."


class EvalRunService:
    """Starts Eval Runs and shows how they went.

    The `eval-runner` service works the runs this saves as Queued.
    """

    def __init__(
        self, runs: EvalRunRepository, cases: EvalCaseRepository, clock: Clock
    ) -> None:
        """Set up the service.

        Args:
            runs: Where Eval Runs and Case Results are stored.
            cases: Where Eval Cases are stored.
            clock: Tells the time.
        """
        self._runs = runs
        self._cases = cases
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
    ) -> EvalRunOverview:
        """Save a new run of some Evals as Queued.

        Args:
            started_by: The Admin starting it; None from the terminal.
            started_from: Where it is started.
            evals: The Evals whose cases it runs.

        Returns:
            The run.

        Raises:
            NoEvalsChosenError: If no Eval is given.
            NoEvalCasesError: If the Evals have no cases.
        """
        chosen = list(dict.fromkeys(evals))
        if not chosen:
            raise NoEvalsChosenError()
        if not self._cases.list_for_evals(chosen):
            raise NoEvalCasesError()
        run_id = uuid4()
        self._runs.add(run_id, started_by, started_from, chosen, self._clock.now())
        return self.get_overview(run_id)

    def list_runs(self, include_terminal: bool) -> list[EvalRunOverview]:
        """List runs with their totals, newest first.

        Args:
            include_terminal: Whether to list runs started from the terminal.

        Returns:
            The runs.
        """
        return self._runs.list_overviews(include_terminal)

    def get_overview(self, run_id: UUID) -> EvalRunOverview:
        """Read one run with its totals.

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
        return overview

    def get_details(self, run_id: UUID) -> EvalRunDetails:
        """Read one run with its Case Results so far.

        Args:
            run_id: The run's ID.

        Returns:
            The run and its results.

        Raises:
            EvalRunNotFoundError: If there is no such run.
        """
        return EvalRunDetails(
            overview=self.get_overview(run_id),
            results=self._runs.list_results(run_id),
        )
