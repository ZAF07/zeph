import logging
import time
from collections.abc import Callable

from companion.core.ports import Scheduler

logger = logging.getLogger(__name__)

TICK_STARTED_LOG = "Load test: tick started"
TICK_TOOK_LOG_PREFIX = "Load test: tick took "


class TimedScheduler:
    """Scheduler for load tests: the real scheduler, logging how long each tick took.

    `make load-test` reads the logs to time a tick.
    """

    def __init__(self, scheduler: Scheduler) -> None:
        """Wrap the real scheduler.

        Args:
            scheduler: The scheduler that runs the ticks.
        """
        self._scheduler = scheduler

    def start(self, tick: Callable[[], None]) -> None:
        """Start the real scheduler with a tick that logs its start and length.

        Args:
            tick: The work to run on each tick.
        """

        def timed_tick() -> None:
            """Run the tick, logging when it started and how long it took."""
            logger.info(TICK_STARTED_LOG)
            started = time.monotonic()
            try:
                tick()
            finally:
                seconds = time.monotonic() - started
                logger.info("%s%.1fs", TICK_TOOK_LOG_PREFIX, seconds)

        self._scheduler.start(timed_tick)

    def stop(self) -> None:
        """Stop the real scheduler."""
        self._scheduler.stop()
