import time
from datetime import datetime, timedelta

from tests.fakes import FakeClock


class RunningClock(FakeClock):
    """A fake clock that also moves on with real time.

    It can still be moved on or back, and sleeping on it moves it on without
    waiting, so typing pauses don't slow an eval down. Because it moves with
    real time, the Model Call Log records how long each model call really
    took.
    """

    def __init__(self, start: datetime) -> None:
        """Set the starting time.

        Args:
            start: The time the clock starts at.
        """
        super().__init__(start)
        self._started = time.monotonic()

    def now(self) -> datetime:
        """Return the fake time plus the real time passed since the start.

        Returns:
            The current time.
        """
        return super().now() + timedelta(seconds=time.monotonic() - self._started)
