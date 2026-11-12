import logging
from dataclasses import dataclass, replace
from datetime import datetime, time, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from companion.core.models import (
    ChatLine,
    ChatRole,
    CheckIn,
    CheckInChanges,
    CheckInFrequency,
    CheckInKind,
    CheckInSettings,
    CheckInStatus,
    PauseLength,
    User,
)
from companion.core.ports import ChatChannel, ChatModel, Clock, Repositories
from companion.core.timing import check_in_reply_window, is_open, quiet_gap

logger = logging.getLogger(__name__)

RECENT_CHECK_INS_LIMIT = 10
PAUSE_LENGTHS = {
    PauseLength.DAY: timedelta(days=1),
    PauseLength.WEEK: timedelta(weeks=1),
}


class EmptyCheckInError(Exception):
    """Raised when the Check-in model writes no message."""


@dataclass(frozen=True)
class RecentCheckIn:
    """A sent Check-in and what happened after it.

    Attributes:
        check_in: The Check-in.
        status: Whether it was replied to, had no reply, or can still be.
    """

    check_in: CheckIn
    status: CheckInStatus


def is_in_quiet_hours(settings: CheckInSettings, local_time: time) -> bool:
    """Tell whether a local time falls in a User's quiet hours.

    Quiet hours may run past midnight, e.g. 22:00 until 07:30. When they
    start and end at the same time there are none.

    Args:
        settings: The User's Check-in settings.
        local_time: The time of day where the User is.

    Returns:
        True if it is quiet hours.
    """
    start, end = settings.quiet_hours_start, settings.quiet_hours_end
    if start < end:
        return start <= local_time < end
    if start > end:
        return local_time >= start or local_time < end
    return False


def local_now(now: datetime, time_zone: str | None) -> datetime:
    """Turn a time into the User's local time.

    Args:
        now: The time, timezone-aware.
        time_zone: The User's IANA time zone; UTC if they have none.

    Returns:
        The same moment in the User's time zone.
    """
    return now.astimezone(ZoneInfo(time_zone or "UTC"))


def check_in_status(
    check_in: CheckIn, is_newest: bool, now: datetime, reply_window: timedelta
) -> CheckInStatus:
    """Work out what happened after a Check-in was sent.

    Only the User's newest Check-in can get a reply, and only within the
    reply window.

    Args:
        check_in: The Check-in.
        is_newest: Whether it is the User's newest Check-in.
        now: The current time.
        reply_window: How long after a Check-in a reply still counts.

    Returns:
        Replied; sent, while a reply can still come; or no reply.
    """
    if check_in.replied_at is not None:
        return CheckInStatus.REPLIED
    if is_newest and now - check_in.sent_at < reply_window:
        return CheckInStatus.SENT
    return CheckInStatus.NO_REPLY


def describe_check_in(user: User, kind: CheckInKind, local_time: datetime) -> str:
    """Write what the Check-in model is told about the Check-in to write.

    Args:
        user: The User it is for.
        kind: The Check-in Kind to write.
        local_time: The User's local time now.

    Returns:
        The Kind, what to call the User and their local time.
    """
    return (
        f"Kind of Check-in: {kind.name} — {kind.description}\n"
        f"What to call them: {user.name or 'unknown'}\n"
        f"Their local time: {local_time.strftime('%A, %H:%M')}"
    )


class CheckInService:
    """Keeps Users' Check-in settings and sends the Check-ins that are due."""

    def __init__(
        self,
        repositories: Repositories,
        chat_model: ChatModel,
        chat_channel: ChatChannel,
        clock: Clock,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where Users, Check-ins, Conversations and settings
                are stored.
            chat_model: Writes each Check-in.
            chat_channel: Sends Check-ins to Users.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._chat_model = chat_model
        self._chat_channel = chat_channel
        self._clock = clock

    def change_settings(self, user: User, changes: CheckInChanges) -> User:
        """Change and save a User's Check-in settings.

        Args:
            user: The User making the change.
            changes: The settings to change; None leaves one as it is.

        Returns:
            The saved User.
        """
        return self._save(user, self.settings_after(user.check_ins, changes))

    def settings_after(
        self, current: CheckInSettings, changes: CheckInChanges
    ) -> CheckInSettings:
        """Work out a User's Check-in settings after a change, without saving.

        Turning Check-ins on, or changing the frequency, sets the next due
        time one frequency gap from now. Turning them off also ends any
        pause.

        Args:
            current: The settings now.
            changes: The settings to change; None leaves one as it is.

        Returns:
            The changed settings.
        """
        updated = replace(
            current,
            enabled=current.enabled if changes.enabled is None else changes.enabled,
            frequency=(
                current.frequency if changes.frequency is None else changes.frequency
            ),
            quiet_hours_start=(
                current.quiet_hours_start
                if changes.quiet_hours_start is None
                else changes.quiet_hours_start
            ),
            quiet_hours_end=(
                current.quiet_hours_end
                if changes.quiet_hours_end is None
                else changes.quiet_hours_end
            ),
        )
        return self._with_next_due_time(current, updated)

    def pause(self, user: User, length: PauseLength) -> User:
        """Pause a User's Check-ins, keeping their other settings.

        Pausing turns Check-ins on if they were off.

        Args:
            user: The User pausing.
            length: For a day, a week or until they resume.

        Returns:
            The saved User.
        """
        current = user.check_ins
        paused_until = (
            None
            if length == PauseLength.UNTIL_RESUMED
            else self._clock.now() + PAUSE_LENGTHS[length]
        )
        paused = replace(current, enabled=True, paused=True, paused_until=paused_until)
        return self._save(user, self._with_next_due_time(current, paused))

    def resume(self, user: User) -> User:
        """End a pause on a User's Check-ins.

        Args:
            user: The User resuming.

        Returns:
            The saved User.
        """
        return self._save(
            user, replace(user.check_ins, paused=False, paused_until=None)
        )

    def is_paused(self, user: User) -> bool:
        """Tell whether a User's Check-ins are paused right now.

        Args:
            user: The User.

        Returns:
            True while paused; a timed pause ends by itself.
        """
        return user.check_ins.is_paused_at(self._clock.now())

    def list_recent(self, user: User) -> list[RecentCheckIn]:
        """List a User's newest Check-ins with what happened after each.

        Args:
            user: The User.

        Returns:
            Each Check-in and its status, newest first.
        """
        recent = self._repositories.check_ins.list_recent(
            user.id, RECENT_CHECK_INS_LIMIT
        )
        now = self._clock.now()
        reply_window = check_in_reply_window(self._repositories.platform_settings)
        return [
            RecentCheckIn(
                check_in=check_in,
                status=check_in_status(check_in, index == 0, now, reply_window),
            )
            for index, check_in in enumerate(recent)
        ]

    def send_due(self) -> None:
        """Send a Check-in to every User who is due one right now.

        A User is due when Check-ins are on, the frequency gap has passed,
        they are not paused, it is outside their quiet hours, they have a
        Telegram Connection and no open Conversation. A Check-in that fails
        to send is logged and tried again on the next tick; the others still
        go ahead.
        """
        now = self._clock.now()
        for user in self._repositories.check_ins.list_due_users(now):
            try:
                self._send_if_due(user, now)
            except Exception:
                logger.exception("Could not send a Check-in")

    def _send_if_due(self, user: User, now: datetime) -> None:
        """Send one User a casual-hello Check-in if nothing holds it back.

        Args:
            user: A User whose next Check-in is due.
            now: The current time.

        Raises:
            EmptyCheckInError: If the model writes no message.
        """
        settings = user.check_ins
        local_time = local_now(now, user.time_zone)
        if settings.is_paused_at(now) or is_in_quiet_hours(settings, local_time.time()):
            return
        connection = self._repositories.telegram_connections.get_by_user(user.id)
        if connection is None or self._has_open_conversation(user, now):
            return
        kind = self._casual_hello()
        if kind is None:
            logger.warning("No Check-in Kind is allowed without User Memory")
            return
        message = self._write(describe_check_in(user, kind, local_time))
        self._chat_channel.send_text(connection.telegram_chat_id, message)
        self._repositories.check_ins.add(
            CheckIn(
                id=uuid4(),
                user_id=user.id,
                kind_id=kind.id,
                kind_name=kind.name,
                message=message,
                sent_at=now,
            ),
            next_due_at=now + self._gap(settings.frequency),
        )

    def _casual_hello(self) -> CheckInKind | None:
        """Pick the Check-in Kind for a casual hello.

        Returns:
            The first Check-in Kind allowed without User Memory, or None.
        """
        kinds = self._repositories.check_ins.list_kinds()
        return next((kind for kind in kinds if kind.allowed_without_user_memory), None)

    def _has_open_conversation(self, user: User, now: datetime) -> bool:
        """Tell whether the User is in the middle of a Conversation.

        Args:
            user: The User.
            now: The current time.

        Returns:
            True if their newest Conversation is still open.
        """
        latest = self._repositories.conversations.get_latest_for_user(user.id)
        gap = quiet_gap(self._repositories.platform_settings)
        return latest is not None and is_open(latest, now, gap)

    def _write(self, description: str) -> str:
        """Ask the Check-in model to write the message.

        Args:
            description: The Kind, what to call the User and their local time.

        Returns:
            The message.

        Raises:
            EmptyCheckInError: If the model writes no message.
        """
        settings = self._repositories.platform_settings
        message = self._chat_model.generate(
            model=settings.get("check_in_model"),
            instructions=f"{settings.get('persona')}\n\n{settings.get('check_in_prompt')}",
            history=[ChatLine(role=ChatRole.USER, text=description)],
        ).strip()
        if not message:
            raise EmptyCheckInError
        return message

    def _gap(self, frequency: CheckInFrequency) -> timedelta:
        """Look up the fewest hours between two Check-ins for a frequency.

        Args:
            frequency: The User's frequency.

        Returns:
            The gap.
        """
        hours_between = self._repositories.platform_settings.get(
            "check_in_hours_between"
        )
        return timedelta(hours=hours_between[frequency.value])

    def _with_next_due_time(
        self, current: CheckInSettings, updated: CheckInSettings
    ) -> CheckInSettings:
        """Set the next due time and pause to fit changed settings.

        Args:
            current: The settings before the change.
            updated: The settings after the change.

        Returns:
            The updated settings, due one gap from now if Check-ins were
            just turned on or the frequency changed, and with no due time or
            pause when off.
        """
        if not updated.enabled:
            return replace(updated, paused=False, paused_until=None, next_due_at=None)
        if not current.enabled or current.frequency != updated.frequency:
            return replace(
                updated, next_due_at=self._clock.now() + self._gap(updated.frequency)
            )
        return updated

    def _save(self, user: User, settings: CheckInSettings) -> User:
        """Save a User's new Check-in settings.

        Args:
            user: The User.
            settings: Their new Check-in settings.

        Returns:
            The saved User.
        """
        return self._repositories.users.update(replace(user, check_ins=settings))
