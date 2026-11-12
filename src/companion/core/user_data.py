from companion.core.models import User
from companion.core.ports import AuthAccounts, ConversationEngine, Repositories


class LastAdminError(Exception):
    """Raised when the only Admin asks to delete their account."""


class UserDataService:
    """Deletes a User's data, or their whole account, when they ask."""

    def __init__(
        self,
        repositories: Repositories,
        conversation_engine: ConversationEngine,
        auth_accounts: AuthAccounts,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where the User's data is stored.
            conversation_engine: Forgets what it saved for a User.
            auth_accounts: Deletes accounts at the auth provider.
        """
        self._repositories = repositories
        self._conversation_engine = conversation_engine
        self._auth_accounts = auth_accounts

    def delete_data(self, user: User) -> None:
        """Delete the User's messages, memory, Check-ins and Telegram Connection.

        Their account, profile and settings stay, so they can start fresh.

        Args:
            user: The User.
        """
        self._repositories.users.delete_data(user.id)
        self._conversation_engine.forget_user(user.id)

    def delete_account(self, user: User) -> None:
        """Delete everything of the User's, then their account at the auth provider.

        Our data goes first, so if anything fails the User can try again
        and nothing of theirs is left behind.

        Args:
            user: The User.

        Raises:
            LastAdminError: If they are the only Admin; their account and data
                stay.
        """
        self._conversation_engine.forget_user(user.id)
        if not self._repositories.users.delete_unless_last_admin(user.id):
            raise LastAdminError
        self._auth_accounts.delete_account(user.auth_id)
