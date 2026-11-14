import logging
from dataclasses import replace
from enum import StrEnum
from uuid import UUID

from companion.core.admin_users import refuse_if_last_admin
from companion.core.models import PlatformSettings, User, UserSnapshot
from companion.core.platform_settings import (
    DATA_DELETED_REPLY,
    DATA_DELETION_CONFIRMATION_WORD,
)
from companion.core.ports import AuthAccounts, ChatChannel, Clock, Repositories

logger = logging.getLogger(__name__)

LAST_ADMIN_ACCOUNT_DELETION = (
    "You’re the only Admin. Make someone else an Admin before deleting your account."
)


def delete_user_data(repositories: Repositories, user_id: UUID) -> None:
    """Delete a User's data in one transaction, keeping their account.

    Their Conversations and messages, Model Call Log entries, Memory Items,
    Conversation Summaries, Shared Photos, Personal Stickers, Check-in
    history, connection tokens and Telegram Connection go. Their profile,
    settings, Usage, Safeguard Events and Feature Switches stay.

    Args:
        repositories: Where the User's data is stored.
        user_id: The User's ID.
    """
    with repositories.transaction() as transaction:
        in_transaction = transaction.repositories
        in_transaction.conversations.delete_for_user(user_id)
        in_transaction.model_calls.delete_for_user(user_id)
        in_transaction.user_memory.delete_for_user(user_id)
        in_transaction.personal_stickers.delete_for_user(user_id)
        in_transaction.check_ins.delete_for_user(user_id)
        in_transaction.connection_tokens.delete_for_user(user_id)
        in_transaction.telegram_connections.delete_for_user(user_id)


def _delete_user(repositories: Repositories, user_id: UUID) -> bool:
    """Delete everything of a User's and then the User, in one transaction.

    Beyond their data, their Usage, Safeguard Events and Feature Switches go.

    Args:
        repositories: Where the User and their data are stored.
        user_id: The User's ID.

    Returns:
        True if they were deleted; False if there was no such User.
    """
    with repositories.transaction() as transaction:
        in_transaction = transaction.repositories
        delete_user_data(in_transaction, user_id)
        in_transaction.usage.delete_for_user(user_id)
        in_transaction.safeguard_events.delete_for_user(user_id)
        in_transaction.feature_switches.delete_for_user(user_id)
        return in_transaction.users.delete(user_id)


class UserDataService:
    """Deletes a User's data, or their whole account, when they ask."""

    def __init__(
        self,
        repositories: Repositories,
        auth_accounts: AuthAccounts,
        clock: Clock,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where the User's data is stored.
            auth_accounts: Deletes accounts at the auth provider.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._auth_accounts = auth_accounts
        self._clock = clock

    def delete_data(self, user: User) -> None:
        """Delete the User's messages, memory, Check-ins and Telegram Connection.

        Their account, profile and settings stay, so they can start fresh.

        Args:
            user: The User.
        """
        delete_user_data(self._repositories, user.id)

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
        with self._repositories.transaction() as transaction:
            refuse_if_last_admin(transaction, user.id, LAST_ADMIN_ACCOUNT_DELETION)
            if _delete_user(transaction.repositories, user.id):
                transaction.repositories.pending_auth_account_deletions.add(
                    user.auth_id, self._clock.now()
                )
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
        deleted too, as the account they signed in with is gone. If any step
        fails, the failure is logged and the account stays on the list.

        Args:
            auth_id: The auth provider's account ID.
        """
        try:
            self._auth_accounts.delete_account(auth_id)
            with self._repositories.transaction() as transaction:
                in_transaction = transaction.repositories
                user_signed_in_again = in_transaction.users.get_by_auth_id(auth_id)
                if user_signed_in_again is not None:
                    _delete_user(in_transaction, user_signed_in_again.id)
                in_transaction.pending_auth_account_deletions.complete(auth_id)
        except Exception:
            logger.exception(
                "Could not delete an account at the auth provider (%s); will try again",
                auth_id,
            )


class DataDeletionAnswer(StrEnum):
    """What a User's message did to a Delete My Data they asked for in chat."""

    NOTHING_ASKED = "nothing_asked"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    CANCELLED_WORD_NOT_ALONE = "cancelled_word_not_alone"


class ChatDataDeletion:
    """Runs Delete My Data when a User asks in chat and then confirms.

    The User's next message settles the request: only the confirmation word
    deletes their data; anything else cancels it. It deletes the same data as
    `UserDataService.delete_data`.
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

    def confirmation_word(self, settings: PlatformSettings) -> str:
        """Read the word a User must reply with to confirm.

        Args:
            settings: The platform settings, read once for the reply.

        Returns:
            The confirmation word Admins set, e.g. "DELETE".
        """
        return settings.get(DATA_DELETION_CONFIRMATION_WORD)

    def ask(self, user: User) -> None:
        """Note that the User asked to delete their data, pending confirmation.

        Args:
            user: The User asking.
        """
        self._repositories.users.update(
            replace(user, data_deletion_requested_at=self._clock.now())
        )

    def settle(
        self, snapshot: UserSnapshot, chat_id: int, text: str
    ) -> DataDeletionAnswer:
        """Delete the User's data if they confirmed, or else cancel the request.

        The confirmation must be the whole Message, sent on its own; case and
        the spaces around it don't matter. A Message that has the word as one
        of several texts cancels too, and says so, so the reply can tell them
        why. Once the data is gone a fixed reply is sent, and not saved, so
        nothing of theirs is left behind.

        Args:
            snapshot: The User who sent the message, as read when the reply
                started.
            chat_id: The chat to reply in.
            text: Their Message, its texts one per line.

        Returns:
            Whether there was a request, and if so whether it was confirmed.
        """
        if not self._clear_request(snapshot):
            return DataDeletionAnswer.NOTHING_ASKED
        word = self.confirmation_word(snapshot.settings).casefold()
        if text.strip().casefold() != word:
            texts = [line.strip().casefold() for line in text.splitlines()]
            if word in texts:
                return DataDeletionAnswer.CANCELLED_WORD_NOT_ALONE
            return DataDeletionAnswer.CANCELLED
        delete_user_data(self._repositories, snapshot.user.id)
        self._chat_channel.send_text(chat_id, snapshot.settings.get(DATA_DELETED_REPLY))
        return DataDeletionAnswer.CONFIRMED

    def cancel(self, snapshot: UserSnapshot) -> DataDeletionAnswer:
        """Cancel the User's pending request, if they have one.

        Args:
            snapshot: The User, as read when the reply started.

        Returns:
            Whether there was a request to cancel.
        """
        if not self._clear_request(snapshot):
            return DataDeletionAnswer.NOTHING_ASKED
        return DataDeletionAnswer.CANCELLED

    def _clear_request(self, snapshot: UserSnapshot) -> bool:
        """Clear the User's pending request to delete their data.

        The snapshot says whether there is one; only then is the User read
        again, right before the change is saved.

        Args:
            snapshot: The User, as read when the reply started.

        Returns:
            True if they had a pending request.
        """
        if snapshot.user.data_deletion_requested_at is None:
            return False
        stored = self._repositories.users.get(snapshot.user.id)
        if stored is None or stored.data_deletion_requested_at is None:
            return False
        self._repositories.users.update(
            replace(stored, data_deletion_requested_at=None)
        )
        return True
