import threading
from collections.abc import Callable


class ReplyDroppedError(Exception):
    """Raised when a new text drops a reply before any of it was sent."""


class ReplyAttempt:
    """One try at answering a User's Message.

    Until any of the reply is sent, a new text from the User drops it, so
    the Message is answered again with every text in it. Once sending
    starts, or the try ends, it can't be dropped, and a new text starts the
    next Message.

    Attributes:
        data_deletion_note: What the house rules told the reply, once the
            Message passed them; None until then. Kept from a dropped try,
            so the Message passes the house rules, and counts toward the
            Daily Message Limit, only once.
    """

    def __init__(
        self,
        on_sending: Callable[[], None],
        data_deletion_note: str | None = None,
    ) -> None:
        """Set up a try that nothing has dropped yet.

        Args:
            on_sending: Run once, just before the first part of the reply is
                sent, while no new text can drop the try.
            data_deletion_note: The house rules' note from an earlier try at
                the same Message; None if none passed them.
        """
        self.data_deletion_note = data_deletion_note
        self._on_sending = on_sending
        self._lock = threading.Lock()
        self._dropped = False
        self._settled = False

    def drop(self) -> bool:
        """Drop the try, unless sending has started or the try has ended.

        Returns:
            True if it was dropped.
        """
        with self._lock:
            if self._settled:
                return False
            self._dropped = True
            return True

    def raise_if_dropped(self) -> None:
        """Stop the try here if a new text dropped it.

        Raises:
            ReplyDroppedError: If it was dropped.
        """
        with self._lock:
            if self._dropped:
                raise ReplyDroppedError

    def start_sending(self) -> None:
        """Mark that the reply is about to be sent, so it can't be dropped.

        Safe to call before each part; only the first call runs `on_sending`.

        Raises:
            ReplyDroppedError: If it was dropped; nothing may be sent then.
        """
        with self._lock:
            if self._dropped:
                raise ReplyDroppedError
            if not self._settled:
                self._settled = True
                self._on_sending()

    def finish(self) -> bool:
        """End the try, so a new text no longer drops it.

        Returns:
            True if it was dropped before it ended.
        """
        with self._lock:
            self._settled = True
            return self._dropped
