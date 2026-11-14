from uuid import UUID

from companion.core.errors import ConflictError, NotFoundError
from companion.core.models import User, UserOverview, UserRole
from companion.core.ports import Repositories, Transaction

LAST_ADMIN_DEMOTION = "This is the last Admin. Make someone else an Admin first."


class UserNotFoundError(NotFoundError):
    """Raised when no User has the given ID."""

    shown_message = "No such User"


class LastAdminError(ConflictError):
    """Raised when a change would leave the platform without an Admin.

    It is raised with the text that tells the Admin what to do instead.
    """


def refuse_if_last_admin(transaction: Transaction, user_id: UUID, refusal: str) -> None:
    """Make sure a User can stop being an Admin without leaving none.

    The Admins stay locked until the transaction ends, so two Admins removing
    each other at the same time can never leave the platform without one.
    Call it before demoting or deleting the User, in the same transaction.

    Args:
        transaction: The transaction the change runs in.
        user_id: The User about to stop being an Admin.
        refusal: What to tell them if they are the only Admin.

    Raises:
        LastAdminError: If they are the only Admin.
    """
    if transaction.lock_admins() == [user_id]:
        raise LastAdminError(refusal)


class AdminUserService:
    """Lets Admins see Users and change who else is an Admin."""

    def __init__(self, repositories: Repositories) -> None:
        """Set up the service.

        Args:
            repositories: Where Users are stored, and how to change them in
                one transaction.
        """
        self._repositories = repositories

    def list_users(self) -> list[UserOverview]:
        """List every User with activity counts, never message text.

        Returns:
            One overview per User, newest sign-up first.
        """
        return self._repositories.users.list_overviews()

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
        user = self._repositories.users.get(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        if user.role == role:
            return user
        if role == UserRole.ADMIN:
            return self._repositories.users.promote_to_admin(user_id)
        with self._repositories.transaction() as transaction:
            refuse_if_last_admin(transaction, user_id, LAST_ADMIN_DEMOTION)
            return transaction.repositories.users.demote_to_user(user_id)
