import argparse
import sys
import time
from collections.abc import Callable

from sqlalchemy import Engine

from companion.adapters.evals.terminal_report import (
    estimate_line,
    progress_line,
    report_lines,
)
from companion.adapters.postgres.eval_repositories import (
    PostgresEvalCaseRepository,
    PostgresEvalRunRepository,
)
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.config import load_settings
from companion.core.errors import InvalidError
from companion.core.evals.models import (
    EvalName,
    EvalRunState,
    StartedFrom,
    evals_run_by_default,
)
from companion.core.evals.runs import EvalRunService
from companion.core.evals.setting_overrides import SettingOverrideService
from companion.core.moves import MoveService
from companion.core.needs import NeedService
from companion.core.platform_settings import PlatformSettingsService
from companion.core.ports import Clock
from companion.main import build_clock, build_database_engine

POLL_SECONDS = 2
STILL_GOING = (EvalRunState.QUEUED, EvalRunState.RUNNING)


def read_evals(names: str) -> list[EvalName]:
    """Read the Evals asked for on the command line.

    Args:
        names: Comma-separated Eval names; "" for every Eval that runs
            without being named.

    Returns:
        The Evals.

    Raises:
        argparse.ArgumentTypeError: If a name isn't an Eval.
    """
    if not names.strip():
        return evals_run_by_default()
    try:
        return [EvalName(name.strip()) for name in names.split(",") if name.strip()]
    except ValueError as error:
        known = ", ".join(name.value for name in EvalName)
        raise argparse.ArgumentTypeError(f"{error}; the Evals are {known}") from error


def read_case_keys(keys: str) -> list[str]:
    """Read the case keys asked for on the command line.

    Args:
        keys: Comma-separated case keys; "" for none.

    Returns:
        The keys.
    """
    return [key.strip() for key in keys.split(",") if key.strip()]


def start_and_watch_run(
    service: EvalRunService,
    evals: list[EvalName],
    case_keys: list[str],
    write: Callable[[str], None],
    sleep: Callable[[float], None],
) -> bool:
    """Print the estimate, queue a terminal run, print each case, then the report.

    Args:
        service: Starts and reads Eval Runs.
        evals: The Evals whose every case to run.
        case_keys: Single cases to run as well.
        write: Prints one line.
        sleep: Waits between looks.

    Returns:
        True if the run finished with no Fail or Error.
    """
    write(estimate_line(service.estimate(evals, case_keys)))
    run = service.start_run(None, StartedFrom.TERMINAL, evals, case_keys).run
    picked = [name.value for name in evals] + case_keys
    write(f"Queued Eval Run {run.id} ({', '.join(picked)})")
    run_id = run.id
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


def build_eval_run_service(engine: Engine, clock: Clock) -> EvalRunService:
    """Build the Eval Runs service on the app database, as the backend does.

    Args:
        engine: The app database.
        clock: Tells the time.

    Returns:
        The service.
    """
    repositories = build_postgres_repositories(engine)
    return EvalRunService(
        runs=PostgresEvalRunRepository(engine),
        cases=PostgresEvalCaseRepository(engine),
        settings=repositories.platform_settings,
        overrides=SettingOverrideService(
            PlatformSettingsService(repositories.platform_settings, clock),
            NeedService(repositories),
            MoveService(repositories),
        ),
        clock=clock,
    )


def main() -> None:
    """Run `make eval`: queue a terminal run on this stack and watch it.

    Runs every Eval unless `--evals` or `--cases` picks some. The
    Whole-pipeline Eval costs far more than the others, so it runs only when
    named.

    Exits 0 when every case passed, 1 on any Fail or Error or when the run
    didn't finish, and 2 when the run can't be started.
    """
    parser = argparse.ArgumentParser(description="Run Evals on this stack.")
    parser.add_argument(
        "--evals",
        type=read_evals,
        default=[],
        help="comma-separated Evals, e.g. safeguard,understanding",
    )
    parser.add_argument(
        "--cases",
        type=read_case_keys,
        default=[],
        help="comma-separated case keys, e.g. reminded-of-sister",
    )
    arguments = parser.parse_args()
    evals = arguments.evals or ([] if arguments.cases else evals_run_by_default())
    settings = load_settings()
    engine = build_database_engine(settings)
    service = build_eval_run_service(engine, build_clock(settings))
    try:
        passed = start_and_watch_run(
            service,
            evals,
            arguments.cases,
            lambda line: print(line, flush=True),
            time.sleep,
        )
    except InvalidError as error:
        print(error.message(), file=sys.stderr)
        sys.exit(2)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
