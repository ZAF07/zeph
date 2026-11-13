import logging
from dataclasses import replace
from enum import StrEnum
from uuid import UUID

from companion.core.models import User
from companion.core.ports import (
    AuthAccounts,
    ChatChannel,
    Clock,
    ConversationEngine,
    Repositories,
)

CONFIRMATION_WORD_SETTING = "data_deletion_confirmation_word"
DELETED_REPLY_SETTING = "data_deleted_reply"

logger = logging.getLogger(__name__)


class LastAdminError(Exception):
    """Raised when the only Admin asks to delete their account."""


class UserDataService:
    """Deletes a User's data, or their whole account, when they ask."""

    def __init__(
        self,
        repositories: Repositories,
        conversation_engine: ConversationEngine,
        auth_accounts: AuthAccounts,
        clock: Clock,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where the User's data is stored.
            conversation_engine: Forgets what it saved for a User.
            auth_accounts: Deletes accounts at the auth provider.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._conversation_engine = conversation_engine
        self._auth_accounts = auth_accounts
        self._clock = clock

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

        Our data goes first, and their auth account is noted as still to
        delete in the same step. If the auth provider then fails, the account
        stays on that list for `delete_pending_auth_accounts` to try again;
        the User's data is gone either way.

        Args:
            user: The User.

        Raises:
            LastAdminError: If they are the only Admin; their account and data
                stay.
        """
        self._conversation_engine.forget_user(user.id)
        if not self._repositories.users.delete_unless_last_admin(
            user.id, self._clock.now()
        ):
            raise LastAdminError
        self._delete_auth_account(user.auth_id)

    def delete_pending_auth_accounts(self) -> None:
        """Try again to delete each auth account still on the pending list.

        One that fails stays on the list for next time; the others still go
        ahead.
        """
        pending = self._repositories.pending_auth_account_deletions
        for auth_id in pending.list_auth_ids():
            self._delete_auth_account(auth_id)

    def _delete_auth_account(self, auth_id: str) -> None:
        """Delete an account at the auth provider and take it off the pending list.

        A User made with that auth ID by signing in again before now is
        deleted too, as the account they signed in with is gone. If the auth
        provider fails, the failure is logged and the account stays on the
        list.

        Args:
            auth_id: The auth provider's account ID.
        """
        try:
            self._auth_accounts.delete_account(auth_id)
        except Exception:
            logger.exception(
                "Could not delete an account at the auth provider; will try again"
            )
            return
        user_signed_in_again = self._repositories.users.get_by_auth_id(auth_id)
        if user_signed_in_again is not None:
            self._conversation_engine.forget_user(user_signed_in_again.id)
        self._repositories.pending_auth_account_deletions.complete(auth_id)


class DataDeletionAnswer(StrEnum):
    """What a User's message did to a Delete My Data they asked for in chat."""

    NOTHING_ASKED = "nothing_asked"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class ChatDataDeletion:
    """Runs Delete My Data when a User asks in chat and then confirms.

    The User's next message settles the request: only the confirmation word
    deletes their data; anything else cancels it. It deletes the same data as
    `UserDataService.delete_data`, but leaves forgetting the conversation
    engine's saved state to the engine itself, which is running the turn.
    """

    def __init__(
        self, repositories: Repositories, chat_channel: ChatChannel, clock: Clock
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where the User's data and settings are stored.
            chat_channel: Sends the reply once the data is gone.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._chat_channel = chat_channel
        self._clock = clock

    def confirmation_word(self) -> str:
        """Read the word a User must reply with to confirm.

        Returns:
            The confirmation word Admins set, e.g. "DELETE".
        """
        word: str = self._repositories.platform_settings.get(CONFIRMATION_WORD_SETTING)
        return word

    def ask(self, user: User) -> None:
        """Note that the User asked to delete their data, pending confirmation.

        Args:
            user: The User asking.
        """
        self._repositories.users.update(
            replace(user, data_deletion_requested_at=self._clock.now())
        )

    def settle(self, user_id: UUID, chat_id: int, text: str) -> DataDeletionAnswer:
        """Delete the User's data if they confirmed, or else cancel the request.

        The confirmation must be the whole message; case and the spaces
        around it don't matter. Once the data is gone a fixed reply is sent,
        and not saved, so nothing of theirs is left behind.

        Args:
            user_id: The User who sent the message.
            chat_id: The chat to reply in.
            text: Their message.

        Returns:
            Whether there was a request, and if so whether it was confirmed.
        """
        if not self._clear_request(user_id):
            return DataDeletionAnswer.NOTHING_ASKED
        if text.strip().casefold() != self.confirmation_word().casefold():
            return DataDeletionAnswer.CANCELLED
        self._repositories.users.delete_data(user_id)
        self._chat_channel.send_text(
            chat_id, self._repositories.platform_settings.get(DELETED_REPLY_SETTING)
        )
        return DataDeletionAnswer.CONFIRMED

    def cancel(self, user_id: UUID) -> DataDeletionAnswer:
        """Cancel the User's pending request, if they have one.

        Args:
            user_id: The User.

        Returns:
            Whether there was a request to cancel.
        """
        if not self._clear_request(user_id):
            return DataDeletionAnswer.NOTHING_ASKED
        return DataDeletionAnswer.CANCELLED

    def _clear_request(self, user_id: UUID) -> bool:
        """Clear the User's pending request to delete their data.

        Args:
            user_id: The User.

        Returns:
            True if they had a pending request.
        """
        user = self._repositories.users.get(user_id)
        if user is None or user.data_deletion_requested_at is None:
            return False
        self._repositories.users.update(replace(user, data_deletion_requested_at=None))
        return True
