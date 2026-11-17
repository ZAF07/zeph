from uuid import UUID

from companion.core.errors import ConflictError, InvalidError, NotFoundError
from companion.core.models import Move, MoveDetails, MoveDirection
from companion.core.ports import NameTakenError, Repositories

MAX_NAME_LENGTH = 80
MAX_WHEN_IT_FITS_LENGTH = 500
MAX_HOW_TO_DO_IT_LENGTH = 2000


class MoveNotFoundError(NotFoundError):
    """Raised when no Move has the given ID."""

    shown_message = "No such Move"


class InvalidMoveError(InvalidError):
    """Raised when a Move's details are not valid."""


class MoveNameTakenError(ConflictError):
    """Raised when another Move already has the name, ignoring case."""


def name_taken_error(name: str) -> MoveNameTakenError:
    """Make the error that refuses a Move name already in use.

    Args:
        name: The name asked for.

    Returns:
        The error, saying which name is taken.
    """
    return MoveNameTakenError(f"There is already a Move called “{name}”.")


class MoveService:
    """Lets Admins add, edit, reorder and delete Moves.

    The Understanding reads the list fresh before every reply, so changes take
    effect straight away. Deleting a Move removes it from every Need's
    rule-outs; saved Understandings name their Moves, so they keep the name.
    """

    def __init__(self, repositories: Repositories) -> None:
        """Set up the service.

        Args:
            repositories: Where Moves are stored.
        """
        self._repositories = repositories

    def list_all(self) -> list[Move]:
        """List every Move in order.

        Returns:
            The Moves.
        """
        return self._repositories.moves.list_all()

    def add(self, details: MoveDetails) -> Move:
        """Add a Move last in the list.

        Args:
            details: Its name, when it fits, how to do it and needed Feature.

        Returns:
            The saved Move.

        Raises:
            InvalidMoveError: If a field is blank or too long.
            MoveNameTakenError: If another Move already has the name.
        """
        checked = self._checked_details(details, None)
        try:
            return self._repositories.moves.add(checked)
        except NameTakenError as error:
            raise name_taken_error(checked.name) from error

    def update(self, move_id: UUID, details: MoveDetails) -> Move:
        """Change a Move's name, when it fits, how to do it and needed Feature.

        Args:
            move_id: The Move's ID.
            details: Its new values.

        Returns:
            The saved Move.

        Raises:
            MoveNotFoundError: If there is no such Move.
            InvalidMoveError: If a field is blank or too long.
            MoveNameTakenError: If another Move already has the name.
        """
        checked = self.checked(move_id, details)
        try:
            return self._repositories.moves.update(move_id, checked)
        except NameTakenError as error:
            raise name_taken_error(checked.name) from error

    def checked(self, move_id: UUID, details: MoveDetails) -> MoveDetails:
        """Check new details for a Move, without saving them.

        Args:
            move_id: The Move's ID.
            details: Its new values.

        Returns:
            The details with surrounding spaces removed.

        Raises:
            MoveNotFoundError: If there is no such Move.
            InvalidMoveError: If a field is blank or too long.
            MoveNameTakenError: If another Move already has the name.
        """
        self.get(move_id)
        return self._checked_details(details, move_id)

    def delete(self, move_id: UUID) -> None:
        """Remove a Move, and with it every Need's rule-out of it.

        Args:
            move_id: The Move's ID.

        Raises:
            MoveNotFoundError: If there is no such Move.
        """
        self.get(move_id)
        self._repositories.moves.delete(move_id)

    def move(self, move_id: UUID, direction: MoveDirection) -> list[Move]:
        """Swap a Move with its neighbour in the list.

        Moving the first one up, or the last one down, changes nothing.

        Args:
            move_id: The Move's ID.
            direction: Which way to move it.

        Returns:
            Every Move in the new order.

        Raises:
            MoveNotFoundError: If there is no such Move.
        """
        self.get(move_id)
        moves = self._repositories.moves.list_all()
        index = next(i for i, move in enumerate(moves) if move.id == move_id)
        neighbour_index = index - 1 if direction == MoveDirection.UP else index + 1
        if 0 <= neighbour_index < len(moves):
            moves[index], moves[neighbour_index] = moves[neighbour_index], moves[index]
            self._repositories.moves.set_sort_orders(
                {move.id: order for order, move in enumerate(moves)}
            )
        return self._repositories.moves.list_all()

    def get(self, move_id: UUID) -> Move:
        """Find a Move.

        Args:
            move_id: The Move's ID.

        Returns:
            The Move.

        Raises:
            MoveNotFoundError: If there is no such Move.
        """
        move = self._repositories.moves.get(move_id)
        if move is None:
            raise MoveNotFoundError(move_id)
        return move

    def _checked_details(
        self, details: MoveDetails, editing_id: UUID | None
    ) -> MoveDetails:
        """Check a Move's details and tidy their spacing.

        Args:
            details: The details to check.
            editing_id: The Move being edited, whose own name is not taken;
                None when adding.

        Returns:
            The details with surrounding spaces removed.

        Raises:
            InvalidMoveError: If a field is blank or too long.
            MoveNameTakenError: If another Move already has the name.
        """
        checked = MoveDetails(
            name=details.name.strip(),
            when_it_fits=details.when_it_fits.strip(),
            how_to_do_it=details.how_to_do_it.strip(),
            needed_feature=details.needed_feature,
        )
        if not checked.name or not checked.when_it_fits or not checked.how_to_do_it:
            raise InvalidMoveError(
                "A Move needs a name, when it fits and how to do it."
            )
        if len(checked.name) > MAX_NAME_LENGTH:
            raise InvalidMoveError(
                f"The name must be at most {MAX_NAME_LENGTH} characters."
            )
        if len(checked.when_it_fits) > MAX_WHEN_IT_FITS_LENGTH:
            raise InvalidMoveError(
                f"“When it fits” must be at most {MAX_WHEN_IT_FITS_LENGTH} characters."
            )
        if len(checked.how_to_do_it) > MAX_HOW_TO_DO_IT_LENGTH:
            raise InvalidMoveError(
                f"“How to do it” must be at most {MAX_HOW_TO_DO_IT_LENGTH} characters."
            )
        is_taken = any(
            move.name.lower() == checked.name.lower() and move.id != editing_id
            for move in self._repositories.moves.list_all()
        )
        if is_taken:
            raise name_taken_error(checked.name)
        return checked
