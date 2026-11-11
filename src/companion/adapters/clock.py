import time
from datetime import UTC, datetime


class SystemClock:
    """Tells the real current time."""

    def now(self) -> datetime:
        """Return the current time.

        Returns:
            The current time in UTC.
        """
        return datetime.now(UTC)

    def sleep(self, seconds: float) -> None:
        """Wait before carrying on.

        Args:
            seconds: How long to wait.
        """
        time.sleep(seconds)
