from uuid import UUID

from companion.core.models import User, UserOverview, UserRole
from companion.core.ports import UserRepository


class UserNotFoundError(LookupError):
    """Raised when no User has the given ID."""


class LastAdminError(Exception):
    """Raised when a change would leave the platform without an Admin."""


class AdminUserService:
    """Lets Admins see Users and change who else is an Admin."""

    def __init__(self, users: UserRepository) -> None:
        """Set up the service.

        Args:
            users: Where Users are stored.
        """
        self._users = users

    def list_users(self) -> list[UserOverview]:
        """List every User with activity counts, never message text.

        Returns:
            One overview per User, newest sign-up first.
        """
        return self._users.list_overviews()

    def change_role(self, user_id: UUID, role: UserRole) -> User:
        """Promote a User to Admin, or demote an Admin to a plain User.

        The last Admin can never be demoted, so nobody gets locked out.

        Args:
            user_id: The User to change.
            role: Their new role.

        Returns:
            The saved User.

        Raises:
            UserNotFoundError: If there is no such User.
            LastAdminError: If they are the last Admin and would be demoted.
        """
        user = self._users.get(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        if user.role == role:
            return user
        if role == UserRole.ADMIN:
            return self._users.promote_to_admin(user_id)
        demoted = self._users.demote_unless_last_admin(user_id)
        if demoted is None:
            raise LastAdminError
        return demoted
