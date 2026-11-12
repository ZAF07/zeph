from dataclasses import replace
from datetime import timedelta
from uuid import UUID

from companion.core.models import CheckInKind, CheckInKindDetails, CheckInKindOverview
from companion.core.ports import Clock, Repositories

MAX_NAME_LENGTH = 80
MAX_DESCRIPTION_LENGTH = 500
SENDS_COUNTED_OVER = timedelta(days=30)


class CheckInKindNotFoundError(LookupError):
    """Raised when no Check-in Kind has the given ID."""


class InvalidCheckInKindError(ValueError):
    """Raised when a Check-in Kind's details are not valid."""


class CheckInKindService:
    """Lets Admins add, edit and remove Check-in Kinds.

    The Check-in service reads the list fresh on every tick, so changes take
    effect straight away. Past Check-ins of a removed Kind keep no Kind.
    """

    def __init__(self, repositories: Repositories, clock: Clock) -> None:
        """Set up the service.

        Args:
            repositories: Where Check-in Kinds are stored.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._clock = clock

    def list_overviews(self) -> list[CheckInKindOverview]:
        """List every Check-in Kind in order with its sends in the last 30 days.

        Returns:
            The Check-in Kinds with their send counts.
        """
        return self._repositories.check_ins.list_kind_overviews(
            self._clock.now() - SENDS_COUNTED_OVER
        )

    def add(self, details: CheckInKindDetails) -> CheckInKind:
        """Add a Check-in Kind last in the list.

        Args:
            details: Its name, description and whether it is allowed without
                User Memory.

        Returns:
            The saved Check-in Kind.

        Raises:
            InvalidCheckInKindError: If the name or description is blank or
                too long, or another Kind already has the name.
        """
        checked = self._checked_details(details, editing_id=None)
        return self._repositories.check_ins.add_kind(checked)

    def update(self, kind_id: UUID, details: CheckInKindDetails) -> CheckInKind:
        """Change a Check-in Kind's name, description and User Memory flag.

        Args:
            kind_id: The Check-in Kind's ID.
            details: Its new name, description and User Memory flag.

        Returns:
            The saved Check-in Kind.

        Raises:
            CheckInKindNotFoundError: If there is no such Kind.
            InvalidCheckInKindError: If the name or description is blank or
                too long, or another Kind already has the name.
        """
        kind = self._repositories.check_ins.get_kind(kind_id)
        if kind is None:
            raise CheckInKindNotFoundError(kind_id)
        checked = self._checked_details(details, editing_id=kind_id)
        return self._repositories.check_ins.update_kind(
            replace(
                kind,
                name=checked.name,
                description=checked.description,
                allowed_without_user_memory=checked.allowed_without_user_memory,
            )
        )

    def remove(self, kind_id: UUID) -> None:
        """Remove a Check-in Kind.

        Args:
            kind_id: The Check-in Kind's ID.

        Raises:
            CheckInKindNotFoundError: If there is no such Kind.
        """
        if not self._repositories.check_ins.delete_kind(kind_id):
            raise CheckInKindNotFoundError(kind_id)

    def _checked_details(
        self, details: CheckInKindDetails, editing_id: UUID | None
    ) -> CheckInKindDetails:
        """Check a Check-in Kind's details and tidy their spacing.

        Args:
            details: The details to check.
            editing_id: The Kind being edited, whose own name is not taken;
                None when adding.

        Returns:
            The details with surrounding spaces removed.

        Raises:
            InvalidCheckInKindError: If the name or description is blank or
                too long, or another Kind already has the name.
        """
        name, description = details.name.strip(), details.description.strip()
        if not name or not description:
            raise InvalidCheckInKindError(
                "A Check-in Kind needs a name and description."
            )
        if len(name) > MAX_NAME_LENGTH:
            raise InvalidCheckInKindError(
                f"The name must be at most {MAX_NAME_LENGTH} characters."
            )
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise InvalidCheckInKindError(
                f"The description must be at most {MAX_DESCRIPTION_LENGTH} characters."
            )
        is_taken = any(
            kind.name.lower() == name.lower() and kind.id != editing_id
            for kind in self._repositories.check_ins.list_kinds()
        )
        if is_taken:
            raise InvalidCheckInKindError(
                f"There is already a Check-in Kind called “{name}”."
            )
        return replace(details, name=name, description=description)
