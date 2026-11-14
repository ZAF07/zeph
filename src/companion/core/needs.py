from uuid import UUID

from companion.core.errors import ConflictError, InvalidError, NotFoundError
from companion.core.models import MoveDirection, Need, NeedDetails
from companion.core.ports import Repositories

MAX_NAME_LENGTH = 80
MAX_WHEN_IT_FITS_LENGTH = 500
MAX_HOW_TO_REPLY_LENGTH = 2000


class NeedNotFoundError(NotFoundError):
    """Raised when no Need has the given ID."""

    shown_message = "No such Need"


class InvalidNeedError(InvalidError):
    """Raised when a Need's details are not valid."""


class FallbackNeedError(ConflictError):
    """Raised when a change would remove the fallback Need."""

    shown_message = "The fallback Need can't be deleted, only edited."


class NeedService:
    """Lets Admins add, edit, reorder and delete Needs.

    The Understanding reads the list fresh before every reply, so changes take
    effect straight away. Saved Understandings name their Need, so deleting
    one leaves them as they are.
    """

    def __init__(self, repositories: Repositories) -> None:
        """Set up the service.

        Args:
            repositories: Where Needs are stored.
        """
        self._repositories = repositories

    def list_all(self) -> list[Need]:
        """List every Need in order.

        Returns:
            The Needs.
        """
        return self._repositories.needs.list_all()

    def add(self, details: NeedDetails) -> Need:
        """Add a Need last in the list.

        Args:
            details: Its name, when it fits and how to reply.

        Returns:
            The saved Need.

        Raises:
            InvalidNeedError: If a field is blank or too long, or another Need
                already has the name.
        """
        return self._repositories.needs.add(self._checked_details(details, None))

    def update(self, need_id: UUID, details: NeedDetails) -> Need:
        """Change a Need's name, when it fits and how to reply.

        Args:
            need_id: The Need's ID.
            details: Its new values.

        Returns:
            The saved Need.

        Raises:
            NeedNotFoundError: If there is no such Need.
            InvalidNeedError: If a field is blank or too long, or another Need
                already has the name.
        """
        self._get(need_id)
        checked = self._checked_details(details, need_id)
        return self._repositories.needs.update(need_id, checked)

    def delete(self, need_id: UUID) -> None:
        """Remove a Need.

        Args:
            need_id: The Need's ID.

        Raises:
            NeedNotFoundError: If there is no such Need.
            FallbackNeedError: If it is the fallback Need.
        """
        if self._get(need_id).is_fallback:
            raise FallbackNeedError
        self._repositories.needs.delete(need_id)

    def move(self, need_id: UUID, direction: MoveDirection) -> list[Need]:
        """Swap a Need with its neighbour in the list.

        Moving the first one up, or the last one down, changes nothing.

        Args:
            need_id: The Need's ID.
            direction: Which way to move it.

        Returns:
            Every Need in the new order.

        Raises:
            NeedNotFoundError: If there is no such Need.
        """
        self._get(need_id)
        needs = self._repositories.needs.list_all()
        index = next(i for i, need in enumerate(needs) if need.id == need_id)
        neighbour_index = index - 1 if direction == MoveDirection.UP else index + 1
        if 0 <= neighbour_index < len(needs):
            needs[index], needs[neighbour_index] = needs[neighbour_index], needs[index]
            self._repositories.needs.set_sort_orders(
                {need.id: order for order, need in enumerate(needs)}
            )
        return self._repositories.needs.list_all()

    def _get(self, need_id: UUID) -> Need:
        """Find a Need.

        Args:
            need_id: The Need's ID.

        Returns:
            The Need.

        Raises:
            NeedNotFoundError: If there is no such Need.
        """
        need = self._repositories.needs.get(need_id)
        if need is None:
            raise NeedNotFoundError(need_id)
        return need

    def _checked_details(
        self, details: NeedDetails, editing_id: UUID | None
    ) -> NeedDetails:
        """Check a Need's details and tidy their spacing.

        Args:
            details: The details to check.
            editing_id: The Need being edited, whose own name is not taken;
                None when adding.

        Returns:
            The details with surrounding spaces removed.

        Raises:
            InvalidNeedError: If a field is blank or too long, or another Need
                already has the name.
        """
        checked = NeedDetails(
            name=details.name.strip(),
            when_it_fits=details.when_it_fits.strip(),
            how_to_reply=details.how_to_reply.strip(),
        )
        if not checked.name or not checked.when_it_fits or not checked.how_to_reply:
            raise InvalidNeedError(
                "A Need needs a name, when it fits and how to reply."
            )
        if len(checked.name) > MAX_NAME_LENGTH:
            raise InvalidNeedError(
                f"The name must be at most {MAX_NAME_LENGTH} characters."
            )
        if len(checked.when_it_fits) > MAX_WHEN_IT_FITS_LENGTH:
            raise InvalidNeedError(
                f"“When it fits” must be at most {MAX_WHEN_IT_FITS_LENGTH} characters."
            )
        if len(checked.how_to_reply) > MAX_HOW_TO_REPLY_LENGTH:
            raise InvalidNeedError(
                f"“How to reply” must be at most {MAX_HOW_TO_REPLY_LENGTH} characters."
            )
        is_taken = any(
            need.name.lower() == checked.name.lower() and need.id != editing_id
            for need in self._repositories.needs.list_all()
        )
        if is_taken:
            raise InvalidNeedError(f"There is already a Need called “{checked.name}”.")
        return checked
