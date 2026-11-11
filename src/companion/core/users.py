from uuid import uuid4

from companion.core.models import AccountIdentity, User
from companion.core.ports import Clock, UserRepository


class UserService:
    """Finds the User behind a Dashboard account, creating them on first visit."""

    def __init__(self, users: UserRepository, clock: Clock) -> None:
        """Set up the service.

        Args:
            users: Where Users are stored.
            clock: Tells the current time.
        """
        self._users = users
        self._clock = clock

    def get_or_create(self, identity: AccountIdentity) -> User:
        """Return the User for an account, creating them if they are new.

        Args:
            identity: The verified account identity.

        Returns:
            The User keyed by the account's auth ID.
        """
        existing = self._users.get_by_auth_id(identity.auth_id)
        if existing is not None:
            return existing
        new_user = User(
            id=uuid4(),
            auth_id=identity.auth_id,
            email=identity.email,
            created_at=self._clock.now(),
        )
        return self._users.add(new_user)
