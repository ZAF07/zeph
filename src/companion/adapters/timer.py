import logging
import threading
from collections.abc import Callable

logger = logging.getLogger(__name__)


class ThreadTimer:
    """Runs work after a wait on a background thread inside the backend."""

    def __init__(self) -> None:
        """Start with nothing waiting."""
        self._timers: dict[str, threading.Timer] = {}
        self._guard = threading.Lock()

    def start(self, key: str, seconds: float, work: Callable[[], None]) -> None:
        """Run work after a wait; starting the same key again restarts its wait.

        Args:
            key: Names the wait, so a later start can restart it.
            seconds: How long to wait.
            work: What to run when the wait ends.
        """
        timer = threading.Timer(seconds, self._run, args=(key, work))
        timer.daemon = True
        with self._guard:
            waiting = self._timers.pop(key, None)
            if waiting is not None:
                waiting.cancel()
            self._timers[key] = timer
        timer.start()

    def _run(self, key: str, work: Callable[[], None]) -> None:
        """Run the work once its wait ends; a failure is logged, not raised.

        Args:
            key: The wait that ended.
            work: What to run.
        """
        with self._guard:
            self._timers.pop(key, None)
        try:
            work()
        except Exception:
            logger.exception("Work run after a wait failed")
