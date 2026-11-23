import logging
import threading
from collections import deque
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class ThreadPoolUserWorkQueue:
    """Runs Users' chat work on a fixed thread pool of its own, in memory.

    Each key has a line of waiting work. A key with work waiting has one
    turn in the pool at a time: the turn runs the line's first piece, then
    hands the next piece a new turn at the back of the pool's line, so a
    heavy texter can't keep a thread from other Users. A key with nothing
    waiting holds no thread. Work not yet run is lost if the backend stops
    (ADR-0018).
    """

    def __init__(self, max_running: int) -> None:
        """Start with nothing waiting.

        Args:
            max_running: The most pieces of work that run at once.
        """
        self._pool = ThreadPoolExecutor(
            max_workers=max_running, thread_name_prefix="user-work"
        )
        self._waiting: dict[str, deque[Callable[[], None]]] = {}
        self._guard = threading.Lock()

    def add(self, key: str, work: Callable[[], None]) -> None:
        """Add a piece of work to the end of a key's line, and return at once.

        Args:
            key: Names one line of a User's work, e.g. their texts to check.
            work: What to run when its turn comes.
        """
        with self._guard:
            line = self._waiting.get(key)
            if line is not None:
                line.append(work)
                return
            self._waiting[key] = deque([work])
        self._pool.submit(self._run_next, key)

    def _run_next(self, key: str) -> None:
        """Run a key's first piece of work, then give its next piece a turn.

        A failure is logged, not raised. Once the key's line is empty it is
        forgotten.

        Args:
            key: The line to run.
        """
        with self._guard:
            work = self._waiting[key][0]
        try:
            work()
        except Exception:
            logger.exception("A User's queued work failed")
        with self._guard:
            line = self._waiting[key]
            line.popleft()
            if not line:
                del self._waiting[key]
                return
        self._pool.submit(self._run_next, key)
