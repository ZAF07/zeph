from enum import StrEnum
from uuid import UUID

from companion.core.models import Helpline, HelplineDetails
from companion.core.ports import HelplineRepository
from companion.core.users import InvalidProfileError, check_country


class MoveDirection(StrEnum):
    """Which way to move a Helpline in its country's list."""

    UP = "up"
    DOWN = "down"


class HelplineNotFoundError(LookupError):
    """Raised when no Helpline has the given ID."""


class InvalidHelplineError(ValueError):
    """Raised when a Helpline's details are not valid."""


class FallbackHelplineError(Exception):
    """Raised when a change would remove the international fallback."""


def checked_details(details: HelplineDetails) -> HelplineDetails:
    """Check a Helpline's details and tidy their spacing.

    Args:
        details: The details an Admin entered.

    Returns:
        The details with surrounding spaces removed; blank hours become None.

    Raises:
        InvalidHelplineError: If the name or number is blank.
    """
    name = details.name.strip()
    number = details.number.strip()
    if not name:
        raise InvalidHelplineError("A Helpline needs a name.")
    if not number:
        raise InvalidHelplineError("A Helpline needs a number.")
    hours = details.hours.strip() if details.hours else None
    return HelplineDetails(name=name, number=number, hours=hours or None)


def checked_country(country: str) -> str:
    """Check a Helpline's country.

    Args:
        country: The country code an Admin entered.

    Returns:
        The country code.

    Raises:
        InvalidHelplineError: If it is not a two-letter code.
    """
    try:
        return check_country(country)
    except InvalidProfileError as error:
        raise InvalidHelplineError(str(error)) from error


class HelplineService:
    """Lets Admins manage Helplines per country and the international fallback.

    The fallback is shared with Users whose country has no Helplines. It can
    be edited but never removed, so every User always has somewhere to turn.
    """

    def __init__(self, helplines: HelplineRepository) -> None:
        """Set up the service.

        Args:
            helplines: Where Helplines are stored.
        """
        self._helplines = helplines

    def list_countries(self) -> list[Helpline]:
        """List every country's Helplines, by country and then sort order.

        Returns:
            The Helplines, without the international fallback.
        """
        return self._helplines.list_countries()

    def international_fallback(self) -> Helpline:
        """Read the international fallback.

        Returns:
            The international fallback.
        """
        return self._helplines.get_international_fallback()

    def add(self, country: str, details: HelplineDetails) -> Helpline:
        """Add a Helpline last in its country's list.

        Args:
            country: Two-letter country code.
            details: Its name, number and hours.

        Returns:
            The saved Helpline.

        Raises:
            InvalidHelplineError: If the country or details are not valid.
        """
        return self._helplines.add(checked_country(country), checked_details(details))

    def update(
        self, helpline_id: UUID, country: str, details: HelplineDetails
    ) -> Helpline:
        """Change a country Helpline.

        Args:
            helpline_id: The Helpline's ID.
            country: Two-letter country code.
            details: Its new name, number and hours.

        Returns:
            The saved Helpline.

        Raises:
            HelplineNotFoundError: If there is no such country Helpline.
            InvalidHelplineError: If the country or details are not valid.
        """
        self._country_of(helpline_id)
        return self._helplines.update(
            helpline_id, checked_country(country), checked_details(details)
        )

    def update_international_fallback(self, details: HelplineDetails) -> Helpline:
        """Change the international fallback.

        Args:
            details: Its new name, number and hours.

        Returns:
            The saved fallback.

        Raises:
            InvalidHelplineError: If the details are not valid.
        """
        fallback = self._helplines.get_international_fallback()
        return self._helplines.update(fallback.id, None, checked_details(details))

    def delete(self, helpline_id: UUID) -> None:
        """Remove a country Helpline.

        Args:
            helpline_id: The Helpline's ID.

        Raises:
            HelplineNotFoundError: If there is no such Helpline.
            FallbackHelplineError: If it is the international fallback.
        """
        helpline = self._helplines.get(helpline_id)
        if helpline is None:
            raise HelplineNotFoundError(helpline_id)
        if helpline.country is None:
            raise FallbackHelplineError
        self._helplines.delete(helpline_id)

    def move(self, helpline_id: UUID, direction: MoveDirection) -> list[Helpline]:
        """Swap a Helpline with its neighbour in its country's list.

        Moving the first one up, or the last one down, changes nothing.

        Args:
            helpline_id: The Helpline's ID.
            direction: Which way to move it.

        Returns:
            Its country's Helplines in their new order.

        Raises:
            HelplineNotFoundError: If there is no such country Helpline.
        """
        country = self._country_of(helpline_id)
        helplines = self._helplines.list_for_country(country)
        index = next(i for i, h in enumerate(helplines) if h.id == helpline_id)
        neighbour_index = index - 1 if direction == MoveDirection.UP else index + 1
        if 0 <= neighbour_index < len(helplines):
            helplines[index], helplines[neighbour_index] = (
                helplines[neighbour_index],
                helplines[index],
            )
            self._helplines.set_sort_orders(
                {helpline.id: order for order, helpline in enumerate(helplines)}
            )
        return self._helplines.list_for_country(country)

    def _country_of(self, helpline_id: UUID) -> str:
        """Find the country a Helpline belongs to.

        Args:
            helpline_id: The Helpline's ID.

        Returns:
            Its two-letter country code.

        Raises:
            HelplineNotFoundError: If there is none, or it is the fallback.
        """
        helpline = self._helplines.get(helpline_id)
        if helpline is None or helpline.country is None:
            raise HelplineNotFoundError(helpline_id)
        return helpline.country
