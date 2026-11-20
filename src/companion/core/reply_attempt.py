import threading
from collections.abc import Callable

from companion.core.reply_gate import ReplyNeeded, Stopped


class ReplyDroppedError(Exception):
    """Raised when a new text drops a reply before any of it was sent."""


class ReplyAttempt:
    """One try at answering a User's Message.

    Until any of the reply is sent, a new text from the User drops it, so
    the Message is answered again with every text in it. Once sending
    starts, the house rules stop the Message, or the try ends, it can't be
    dropped, and a new text starts the next Message.

    Attributes:
        house_rules: What the house rules said, once the Message passed
            them; None until then. Kept from a dropped try, so the Message
            passes the house rules, and counts toward the Daily Message
            Limit, only once.
    """

    def __init__(
        self,
        on_sending: Callable[[], None],
        house_rules: ReplyNeeded | None = None,
    ) -> None:
        """Set up a try that nothing has dropped yet.

        Args:
            on_sending: Run once, when the reply is about to be sent or the
                house rules stop the Message, while no new text can drop
                the try.
            house_rules: What the house rules said to an earlier try at the
                same Message; None if none passed them.
        """
        self.house_rules = house_rules
        self._on_sending = on_sending
        self._lock = threading.Lock()
        self._dropped = False
        self._settled = False

    def drop(self) -> None:
        """Drop the try, unless sending has started or the try has ended."""
        with self._lock:
            if not self._settled:
                self._dropped = True

    def raise_if_dropped(self) -> None:
        """Stop the try here if a new text dropped it.

        Raises:
            ReplyDroppedError: If it was dropped.
        """
        with self._lock:
            self._raise_if_dropped()

    def apply_house_rules(
        self, check: Callable[[], ReplyNeeded | Stopped]
    ) -> ReplyNeeded | Stopped:
        """Apply the house rules once per Message, while no new text can drop the try.

        What they say is kept, so a try started over skips them. When they
        stop the Message, whatever they sent counts as its reply, so the try
        is settled like one being sent.

        Args:
            check: Applies the house rules, and may send the Limit Reply.

        Returns:
            What the house rules said, or said to an earlier try.

        Raises:
            ReplyDroppedError: If it was dropped before the house rules ran.
        """
        with self._lock:
            self._raise_if_dropped()
            if self.house_rules is not None:
                return self.house_rules
            result = check()
            if isinstance(result, Stopped):
                self._settle()
            else:
                self.house_rules = result
            return result

    def start_sending(self) -> None:
        """Mark that the reply is about to be sent, so it can't be dropped.

        Safe to call before each part; only the first call runs `on_sending`.

        Raises:
            ReplyDroppedError: If it was dropped; nothing may be sent then.
        """
        with self._lock:
            self._raise_if_dropped()
            self._settle()

    def finish(self) -> bool:
        """End the try, so a new text no longer drops it.

        Returns:
            True if it was dropped before it ended.
        """
        with self._lock:
            self._settled = True
            return self._dropped

    def _raise_if_dropped(self) -> None:
        """Raise if the try was dropped; the caller holds the lock.

        Raises:
            ReplyDroppedError: If it was dropped.
        """
        if self._dropped:
            raise ReplyDroppedError

    def _settle(self) -> None:
        """Settle the try once, so no new text drops it; the caller holds the lock."""
        if not self._settled:
            self._settled = True
            self._on_sending()
