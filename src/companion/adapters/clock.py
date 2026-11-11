from datetime import UTC, datetime


class SystemClock:
    """Tells the real current time."""

    def now(self) -> datetime:
        """Return the current time.

        Returns:
            The current time in UTC.
        """
        return datetime.now(UTC)
