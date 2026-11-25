import logging
import threading
from collections.abc import Iterator
from contextlib import contextmanager

APP_LOGGER = "companion"


class FailureCollector(logging.Handler):
    """Keeps the failures one thread logs, as one line each.

    The app logs a step that failed and skips it, so the log is the only
    place a skipped step shows. Other threads' failures are left out, since
    the live app may be working in the same process.
    """

    def __init__(self) -> None:
        """Start with no failure, for the thread that made it."""
        super().__init__(level=logging.ERROR)
        self._thread = threading.get_ident()
        self.failures: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Keep a failure logged by the collector's own thread.

        Args:
            record: The logged failure.
        """
        if record.thread != self._thread:
            return
        error = record.exc_info[1] if record.exc_info else None
        message = record.getMessage()
        self.failures.append(f"{message}: {error!r}" if error else message)


@contextmanager
def logged_failures() -> Iterator[list[str]]:
    """Collect the failures the app logs on this thread while the block runs.

    Yields:
        The failures so far, e.g. "Could not score Patterns:
        ValueError('no settings')", oldest first.
    """
    collector = FailureCollector()
    logger = logging.getLogger(APP_LOGGER)
    logger.addHandler(collector)
    try:
        yield collector.failures
    finally:
        logger.removeHandler(collector)
