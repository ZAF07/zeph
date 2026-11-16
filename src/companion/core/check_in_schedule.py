from uuid import UUID

from companion.core.admin_users import UserNotFoundError
from companion.core.check_ins import CheckInService
from companion.core.errors import ConflictError
from companion.core.features import feature_statuses, switches_for_everyone
from companion.core.models import (
    AdminCheckInChanges,
    ChangedBy,
    CheckInChanges,
    CheckInScheduleEntry,
    CheckInSchedulePage,
    Feature,
    PauseLength,
    User,
)
from companion.core.ports import Clock, Repositories


class CheckInsNotOnError(ConflictError):
    """Raised when an Admin changes the settings of a User not opted in to Check-ins."""

    shown_message = "This User hasn't turned Check-ins on"


class CheckInScheduleService:
    """Shows Admins opted-in Users' Check-ins and lets them change their settings.

    An Admin Setting Change changes the User's real settings through the same
    rules as the User's own change, and marks each one "changed by an
    Admin". Admins can never turn a User's Check-ins on or off.
    """

    def __init__(
        self, repositories: Repositories, check_ins: CheckInService, clock: Clock
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where Users and Feature switches are stored.
            check_ins: Changes Check-in settings by the User's own rules.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._check_ins = check_ins
        self._clock = clock

    def list_page(self, search: str, page: int, page_size: int) -> CheckInSchedulePage:
        """List one page of the Users who opted in to Check-ins.

        Reads stay the same however many Users are on the page: the page,
        its count, and the Feature switches for everyone and for those Users.

        Args:
            search: Only Users whose name or email holds this; "" for all.
            page: Which page, from 1.
            page_size: The most Users on a page.

        Returns:
            The page, soonest Due Time first, with each User's settings,
            whether Check-ins work for them and why one is held back now.
        """
        found = self._repositories.check_ins.list_opted_in_users(
            search.strip(), page_size, (page - 1) * page_size
        )
        return CheckInSchedulePage(
            entries=self._entries(found.users),
            total=found.total,
            now=self._clock.now(),
        )

    def change_settings(
        self, user_id: UUID, changes: AdminCheckInChanges
    ) -> CheckInScheduleEntry:
        """Change a User's Check-in Frequency or Quiet Hours for them.

        Args:
            user_id: The User.
            changes: The settings to change; None leaves one as it is.

        Returns:
            The User's row on the Schedule after the change.

        Raises:
            UserNotFoundError: If there is no such User.
            CheckInsNotOnError: If they haven't opted in to Check-ins.
        """
        user = self._check_ins.change_settings(
            self._opted_in_user(user_id),
            CheckInChanges(
                frequency=changes.frequency,
                quiet_hours_start=changes.quiet_hours_start,
                quiet_hours_end=changes.quiet_hours_end,
            ),
            changed_by=ChangedBy.ADMIN,
        )
        return self._entry(user)

    def pause(self, user_id: UUID, length: PauseLength) -> CheckInScheduleEntry:
        """Pause a User's Check-ins for them.

        Args:
            user_id: The User.
            length: For a day, a week or until resumed.

        Returns:
            The User's row on the Schedule after the change.

        Raises:
            UserNotFoundError: If there is no such User.
            CheckInsNotOnError: If they haven't opted in to Check-ins.
        """
        user = self._check_ins.pause(
            self._opted_in_user(user_id), length, changed_by=ChangedBy.ADMIN
        )
        return self._entry(user)

    def resume(self, user_id: UUID) -> CheckInScheduleEntry:
        """End the pause on a User's Check-ins for them.

        Args:
            user_id: The User.

        Returns:
            The User's row on the Schedule after the change.

        Raises:
            UserNotFoundError: If there is no such User.
            CheckInsNotOnError: If they haven't opted in to Check-ins.
        """
        user = self._check_ins.resume(
            self._opted_in_user(user_id), changed_by=ChangedBy.ADMIN
        )
        return self._entry(user)

    def _opted_in_user(self, user_id: UUID) -> User:
        """Find a User who opted in to Check-ins.

        Args:
            user_id: The User.

        Returns:
            The User.

        Raises:
            UserNotFoundError: If there is no such User.
            CheckInsNotOnError: If they haven't opted in to Check-ins.
        """
        user = self._repositories.users.get(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        if not user.check_ins.enabled:
            raise CheckInsNotOnError(user_id)
        return user

    def _entry(self, user: User) -> CheckInScheduleEntry:
        """Work out one User's row on the Schedule.

        Args:
            user: The User, as just saved.

        Returns:
            Their row.
        """
        [entry] = self._entries([user])
        return entry

    def _entries(self, users: list[User]) -> list[CheckInScheduleEntry]:
        """Work out the Users' rows on the Schedule, reading Feature switches once.

        Args:
            users: The Users.

        Returns:
            One row per User, in the same order.
        """
        everyone_switches = switches_for_everyone(
            self._repositories.feature_switches.list_for_everyone()
        )
        switches_by_user = self._repositories.feature_switches.list_for_users(
            [user.id for user in users]
        )
        now = self._clock.now()
        return [
            CheckInScheduleEntry(
                user=user,
                paused=user.check_ins.is_paused_at(now),
                check_ins_work=next(
                    status.works
                    for status in feature_statuses(
                        user, everyone_switches, switches_by_user.get(user.id, [])
                    )
                    if status.feature == Feature.CHECK_INS
                ),
            )
            for user in users
        ]
