import logging
import time

from companion.adapters.evals.environment import (
    PostgresEvalEnvironment,
    create_database_if_missing,
)
from companion.adapters.postgres.eval_repositories import (
    PostgresEvalCaseRepository,
    PostgresEvalRunRepository,
    hold_runner_lock,
)
from companion.adapters.postgres.repositories import PostgresPlatformSettingsRepository
from companion.config import load_settings
from companion.core.evals.runner import EvalRunner
from companion.main import (
    SEED_DIR,
    build_chat_model,
    build_clock,
    build_database_engine,
    build_embedder,
    build_photo_viewer,
    quiet_http_client_logs,
)

IDLE_SECONDS = 2

logger = logging.getLogger(__name__)


def run_forever() -> None:
    """Work Queued Eval Runs one at a time, for as long as the service is up.

    The Eval database is created if missing. The app is always built with
    the recording chat channel, no web search and no scheduler, whatever
    `.env` says, so an Eval never reaches a real chat or spends search
    credits (ADR-0013). Runs left Running by an earlier runner are marked
    Interrupted first.
    """
    logging.basicConfig(level=logging.INFO)
    quiet_http_client_logs()
    settings = load_settings()
    engine = build_database_engine(settings)
    create_database_if_missing(settings.eval_database_url)
    runner = EvalRunner(
        runs=PostgresEvalRunRepository(engine),
        cases=PostgresEvalCaseRepository(engine),
        live_settings=PostgresPlatformSettingsRepository(engine),
        environment=PostgresEvalEnvironment(
            database_url=settings.eval_database_url,
            chat_model=build_chat_model(settings),
            photo_viewer=build_photo_viewer(settings),
            embedder=build_embedder(settings),
            seed_dir=SEED_DIR,
        ),
        clock=build_clock(settings),
    )
    with hold_runner_lock(engine):
        interrupted = runner.interrupt_unfinished()
        if interrupted:
            logger.info("Marked %d unfinished Eval Runs Interrupted", len(interrupted))
        logger.info("Eval runner ready")
        while True:
            if not runner.work_next_run():
                time.sleep(IDLE_SECONDS)


if __name__ == "__main__":
    run_forever()
