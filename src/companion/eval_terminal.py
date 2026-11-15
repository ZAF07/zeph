import argparse
import sys
import time
from collections.abc import Callable

from companion.adapters.evals.terminal_report import progress_line, report_lines
from companion.adapters.postgres.eval_repositories import (
    PostgresEvalCaseRepository,
    PostgresEvalRunRepository,
)
from companion.config import load_settings
from companion.core.errors import InvalidError
from companion.core.evals.models import EvalName, EvalRunState, StartedFrom
from companion.core.evals.runs import EvalRunService
from companion.main import build_clock, build_database_engine

POLL_SECONDS = 2
STILL_GOING = (EvalRunState.QUEUED, EvalRunState.RUNNING)


def read_evals(names: str) -> list[EvalName]:
    """Read the Evals asked for on the command line.

    Args:
        names: Comma-separated Eval names; "" for all six.

    Returns:
        The Evals.

    Raises:
        argparse.ArgumentTypeError: If a name isn't an Eval.
    """
    if not names.strip():
        return list(EvalName)
    try:
        return [EvalName(name.strip()) for name in names.split(",") if name.strip()]
    except ValueError as error:
        known = ", ".join(name.value for name in EvalName)
        raise argparse.ArgumentTypeError(f"{error}; the Evals are {known}") from error


def watch_run(
    service: EvalRunService,
    evals: list[EvalName],
    write: Callable[[str], None],
    sleep: Callable[[float], None],
) -> bool:
    """Queue a terminal run, print each case as it finishes, then the report.

    Args:
        service: Starts and reads Eval Runs.
        evals: The Evals to run.
        write: Prints one line.
        sleep: Waits between looks.

    Returns:
        True if the run finished with no Fail or Error.
    """
    run_id = service.start_run(None, StartedFrom.TERMINAL, evals).run.id
    write(f"Queued Eval Run {run_id} ({', '.join(name.value for name in evals)})")
    printed = 0
    while True:
        details = service.get_details(run_id)
        for result in details.results[printed:]:
            write(progress_line(result))
        printed = len(details.results)
        if details.overview.run.state not in STILL_GOING:
            break
        sleep(POLL_SECONDS)
    write("")
    for line in report_lines(details.overview, details.results):
        write(line)
    totals = details.overview.totals
    return (
        details.overview.run.state == EvalRunState.FINISHED
        and totals.failed == 0
        and totals.errored == 0
    )


def main() -> None:
    """Run `make eval`: queue a terminal run on this stack and watch it.

    Exits 0 when every case passed, 1 on any Fail or Error or when the run
    didn't finish, and 2 when the run can't be started.
    """
    parser = argparse.ArgumentParser(description="Run Evals on this stack.")
    parser.add_argument(
        "--evals",
        type=read_evals,
        default=list(EvalName),
        help="comma-separated Evals, e.g. safeguard,understanding; all if left out",
    )
    arguments = parser.parse_args()
    settings = load_settings()
    engine = build_database_engine(settings)
    service = EvalRunService(
        runs=PostgresEvalRunRepository(engine),
        cases=PostgresEvalCaseRepository(engine),
        clock=build_clock(settings),
    )
    try:
        passed = watch_run(
            service, arguments.evals, lambda line: print(line, flush=True), time.sleep
        )
    except InvalidError as error:
        print(error.message(), file=sys.stderr)
        sys.exit(2)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
