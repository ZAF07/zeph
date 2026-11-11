import logging
import threading
from collections.abc import Callable

logger = logging.getLogger(__name__)


class InProcessScheduler:
    """Runs the tick on a background thread inside the backend, every so often."""

    def __init__(self, interval_seconds: float) -> None:
        """Set up the scheduler.

        Args:
            interval_seconds: How long to wait between ticks.
        """
        self._interval_seconds = interval_seconds
        self._stopping = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self, tick: Callable[[], None]) -> None:
        """Start running the tick every interval, until stopped.

        Args:
            tick: The work to run on each tick.
        """
        self._stopping.clear()
        self._thread = threading.Thread(
            target=self._run, args=(tick,), name="scheduler", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop running ticks, waiting for a running tick to finish."""
        self._stopping.set()
        if self._thread is not None:
            self._thread.join()
            self._thread = None

    def _run(self, tick: Callable[[], None]) -> None:
        """Run the tick after each interval; a failing tick doesn't stop the loop.

        Args:
            tick: The work to run on each tick.
        """
        while not self._stopping.wait(self._interval_seconds):
            try:
                tick()
            except Exception:
                logger.exception("A scheduler tick failed")
