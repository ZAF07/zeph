from typing import ClassVar


class CoreError(Exception):
    """An error core raises when it refuses what a caller asked for.

    Each error inherits from one of the kinds below, and the kind says what
    went wrong, so an adapter can answer every error of a kind the same way.

    Attributes:
        shown_message: The text shown to the person; when empty, the text the
            error was raised with is shown.
    """

    shown_message: ClassVar[str] = ""

    def message(self) -> str:
        """Give the text to show the person.

        Returns:
            The class's fixed text, or the text the error was raised with.
        """
        return self.shown_message or str(self)


class NotFoundError(CoreError, LookupError):
    """Raised when the thing asked for does not exist, or isn't theirs."""


class NotAllowedError(CoreError):
    """Raised when the person may not do what they asked."""


class InvalidError(CoreError, ValueError):
    """Raised when a value given is not acceptable."""


class ConflictError(CoreError):
    """Raised when the request clashes with how things stand right now."""


class OutsideServiceError(CoreError):
    """Raised when an outside service core needed didn't answer."""
