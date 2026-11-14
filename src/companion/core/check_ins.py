import json
import logging
from dataclasses import dataclass, replace
from datetime import datetime, time, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from companion.core.features import FeatureService
from companion.core.memory_retrieval import (
    format_day,
    format_memory,
    shared_photo_line,
)
from companion.core.models import (
    DAILY_LIMIT_SKIP_REASON,
    ChatLine,
    ChatRole,
    ChatSetting,
    CheckIn,
    CheckInChanges,
    CheckInFrequency,
    CheckInKind,
    CheckInLogEntry,
    CheckInOutcome,
    CheckInSettings,
    CheckInStatus,
    Feature,
    PauseLength,
    SharedPhoto,
    User,
)
from companion.core.ports import (
    ChatBlockedError,
    ChatChannel,
    Clock,
    MessageRefusedError,
    Repositories,
)
from companion.core.settings_changes import record_where_changed
from companion.core.timing import (
    check_in_reply_window,
    is_open,
    quiet_gap,
    users_today,
)
from companion.core.usage import UsageLimiter, UsageRecordingChatModel

logger = logging.getLogger(__name__)

RECENT_CHECK_INS_LIMIT = 10
CHECK_INS_TOLD_TO_MODEL = 5
CHECK_INS_LOOKED_BACK_FOR_IGNORES = 100
CHECK_INS_LOOKED_BACK_FOR_LAST_SENT = 100
MEMORY_INTRO = "What you remember about them:"
REFUSED_CHECK_IN_RETRY_GAP = timedelta(minutes=15)
BLOCKED_SKIP_REASON = "User has blocked the Companion on Telegram"
PAUSE_LENGTHS = {
    PauseLength.DAY: timedelta(days=1),
    PauseLength.WEEK: timedelta(weeks=1),
}


class InvalidCheckInAnswerError(Exception):
    """Raised when the Check-in model's answer is not a decision we can use."""


@dataclass(frozen=True)
class RecentCheckIn:
    """A Check-in decision and what happened after it.

    Attributes:
        check_in: The Check-in.
        status: Skipped, replied, no reply, or sent while a reply can still
            come.
    """

    check_in: CheckIn
    status: CheckInStatus


@dataclass(frozen=True)
class LoggedCheckIn:
    """A Check-in decision for the Admins' Check-in log. Never the message.

    Attributes:
        entry: The decision and who it was for.
        status: Skipped, replied, no reply, or sent while a reply can still
            come.
    """

    entry: CheckInLogEntry
    status: CheckInStatus


@dataclass(frozen=True)
class CheckInDecision:
    """What the Check-in model decided: send a Kind and message, or skip.

    Attributes:
        kind: The Check-in Kind to send; None to skip.
        message: The message to send; "" when skipping.
        skip_reason: Why it skipped; "" when sending.
        shared_photo: The Shared Photo to send after the message; None
            unless the Kind sends one.
    """

    kind: CheckInKind | None
    message: str = ""
    skip_reason: str = ""
    shared_photo: SharedPhoto | None = None


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
        Skipped; replied; sent, while a reply can still come; or no reply.
    """
    if not check_in.was_sent:
        return CheckInStatus.SKIPPED
    if check_in.replied_at is not None:
        return CheckInStatus.REPLIED
    if is_newest and now - check_in.decided_at < reply_window:
        return CheckInStatus.SENT
    return CheckInStatus.NO_REPLY


def check_in_statuses(
    check_ins: list[CheckIn], now: datetime, reply_window: timedelta
) -> list[CheckInStatus]:
    """Work out what happened after each Check-in in a newest-first list.

    Only each User's newest sent Check-in can still get a reply.

    Args:
        check_ins: Check-ins of one or more Users, newest first.
        now: The current time.
        reply_window: How long after a Check-in a reply still counts.

    Returns:
        Each Check-in's status, in the same order.
    """
    users_with_a_newer_send: set[UUID] = set()
    statuses = []
    for check_in in check_ins:
        is_newest = check_in.user_id not in users_with_a_newer_send
        statuses.append(check_in_status(check_in, is_newest, now, reply_window))
        if check_in.was_sent:
            users_with_a_newer_send.add(check_in.user_id)
    return statuses


def ignored_in_a_row(
    recent: list[CheckIn], last_conversation_started_at: datetime | None
) -> int:
    """Count the sent Check-ins the User ignored, newest first, in a row.

    The count stops at a Check-in they replied to, at the last "would you
    like fewer?" message, and at Check-ins sent before they last started a
    Conversation. Skipped Check-ins are passed over.

    Args:
        recent: The User's newest Check-ins, newest first.
        last_conversation_started_at: When the User last started a
            Conversation, if ever.

    Returns:
        How many Check-ins in a row went unanswered.
    """
    count = 0
    for check_in in recent:
        if not check_in.was_sent:
            continue
        if check_in.outcome == CheckInOutcome.ASKED_ABOUT_FEWER:
            break
        if check_in.replied_at is not None:
            break
        if (
            last_conversation_started_at is not None
            and check_in.decided_at < last_conversation_started_at
        ):
            break
        count += 1
    return count


def describe_recent_check_ins(
    recent: list[RecentCheckIn], time_zone: str | None
) -> str:
    """Write the User's recent Check-ins for the Check-in model.

    Args:
        recent: The newest Check-ins and their statuses, newest first.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        One line per Check-in, or a note that there are none.
    """
    if not recent:
        return "None yet."
    lines = []
    for item in recent:
        check_in = item.check_in
        if check_in.outcome == CheckInOutcome.SKIPPED:
            happened = "skipped"
        else:
            sent_what = (
                "asked if they'd like fewer check-ins"
                if check_in.outcome == CheckInOutcome.ASKED_ABOUT_FEWER
                else check_in.kind_name or "a check-in"
            )
            reply = "no reply" if item.status == CheckInStatus.NO_REPLY else item.status
            happened = f"{sent_what}, {reply}"
        lines.append(f"- {format_day(check_in.decided_at, time_zone)}: {happened}")
    return "\n".join(lines)


def describe_shared_photos(
    kinds: list[CheckInKind], shared_photos: list[SharedPhoto], time_zone: str | None
) -> str:
    """Write the User's Shared Photos for the Check-in model, numbered.

    Args:
        kinds: The Check-in Kinds it may choose from.
        shared_photos: The User's Shared Photos, newest first.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        How to name a photo for the Kinds that send one, then one line per
        photo; "" if no offered Kind sends a photo or there are none.
    """
    photo_kinds = [kind.name for kind in kinds if kind.sends_shared_photo]
    if not photo_kinds or not shared_photos:
        return ""
    kind_names = " or ".join(f'"{name}"' for name in photo_kinds)
    photo_lines = "\n".join(
        shared_photo_line(photo, time_zone, bullet=f"{number}.")
        for number, photo in enumerate(shared_photos, start=1)
    )
    return (
        f"Photos they shared with you, newest first. If you choose {kind_names}, "
        f'also add "photo": <the number of one photo below> to your answer; '
        f"that photo is sent right after your message, so the message should "
        f"be about it:\n{photo_lines}"
    )


def describe_check_in(
    user: User,
    kinds: list[CheckInKind],
    local_time: datetime,
    recent: str,
    memory: str,
    shared_photos: str = "",
) -> str:
    """Write what the Check-in model is told to decide on a Check-in.

    Args:
        user: The User it is for.
        kinds: The Check-in Kinds it may choose from.
        local_time: The User's local time now.
        recent: The User's recent Check-ins, as lines.
        memory: What is remembered about the User; "" if nothing.
        shared_photos: The User's numbered Shared Photos; "" if none are
            offered.

    Returns:
        The Kinds, what to call the User, their local time, recent
        Check-ins, what is remembered about them and their Shared Photos.
    """
    kind_lines = "\n".join(f"- {kind.name}: {kind.description}" for kind in kinds)
    remembered = memory or "Nothing remembered about them."
    photos = f"\n\n{shared_photos}" if shared_photos else ""
    return (
        f"Check-in Kinds you may choose from:\n{kind_lines}\n\n"
        f"What to call them: {user.name or 'unknown'}\n"
        f"Their local time: {local_time.strftime('%A, %H:%M')}\n\n"
        f"Recent Check-ins, newest first:\n{recent}\n\n"
        f"{remembered}{photos}"
    )


def read_check_in_decision(
    answer: str, kinds: list[CheckInKind], shared_photos: list[SharedPhoto]
) -> CheckInDecision:
    """Read the Check-in model's JSON decision.

    Text around the JSON object, such as a code fence, is ignored. The Kind
    is matched by name, in any case, and must be one it was offered. A Kind
    that sends a Shared Photo needs the number of one it was listed; any
    other Kind's photo number is ignored.

    Args:
        answer: The model's answer.
        kinds: The Check-in Kinds it could choose from.
        shared_photos: The Shared Photos it was listed, numbered from 1.

    Returns:
        The decision.

    Raises:
        InvalidCheckInAnswerError: If there is no JSON decision, the Kind is
            not one it was offered, the message or reason is empty, or a
            Kind that sends a photo names no listed photo.
    """
    start, end = answer.find("{"), answer.rfind("}")
    try:
        parsed = json.loads(answer[start : end + 1]) if 0 <= start < end else None
    except json.JSONDecodeError:
        parsed = None
    if not isinstance(parsed, dict):
        raise InvalidCheckInAnswerError("No JSON decision")
    decision = parsed.get("decision")
    if decision == "skip":
        reason = parsed.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise InvalidCheckInAnswerError("A skip with no reason")
        return CheckInDecision(kind=None, skip_reason=reason.strip())
    if decision != "send":
        raise InvalidCheckInAnswerError(f"Not send or skip: {decision!r}")
    kind_name, message = parsed.get("kind"), parsed.get("message")
    if not isinstance(kind_name, str):
        raise InvalidCheckInAnswerError("A send with no Kind")
    kinds_by_name = {kind.name.lower(): kind for kind in kinds}
    kind = kinds_by_name.get(kind_name.strip().lower())
    if kind is None:
        raise InvalidCheckInAnswerError(f"Not a Kind it was offered: {kind_name!r}")
    if not isinstance(message, str) or not message.strip():
        raise InvalidCheckInAnswerError("A send with no message")
    if not kind.sends_shared_photo:
        return CheckInDecision(kind=kind, message=message.strip())
    photo_number = parsed.get("photo")
    if (
        not isinstance(photo_number, int)
        or isinstance(photo_number, bool)
        or not 1 <= photo_number <= len(shared_photos)
    ):
        raise InvalidCheckInAnswerError(f"Not a photo it was listed: {photo_number!r}")
    return CheckInDecision(
        kind=kind,
        message=message.strip(),
        shared_photo=shared_photos[photo_number - 1],
    )


class CheckInService:
    """Keeps Users' Check-in settings and sends the Check-ins that are due."""

    def __init__(
        self,
        repositories: Repositories,
        features: FeatureService,
        chat_model: UsageRecordingChatModel,
        usage_limiter: UsageLimiter,
        chat_channel: ChatChannel,
        clock: Clock,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where Users, Check-ins, Conversations and settings
                are stored.
            features: Says whether Check-ins and User Memory work for a User.
            chat_model: Writes each Check-in and records the tokens used.
            usage_limiter: Says whether a User has used up today's daily
                message limit.
            chat_channel: Sends Check-ins, and any Shared Photo with them,
                to Users.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._features = features
        self._chat_model = chat_model
        self._usage_limiter = usage_limiter
        self._chat_channel = chat_channel
        self._clock = clock

    def change_settings(
        self, user: User, changes: CheckInChanges, in_chat: bool = False
    ) -> User:
        """Change and save a User's Check-in settings.

        Only settings whose value really changes are marked as changed in
        chat or on the Dashboard. Turning Check-ins on or off counts as a
        change to the pause, since turning them off ends it.

        Args:
            user: The User making the change.
            changes: The settings to change; None leaves one as it is.
            in_chat: True if the User asked for it in chat, not on the
                Dashboard.

        Returns:
            The saved User.

        Raises:
            FeatureNotAvailableError: If it turns Check-ins on or off while
                the Admin side has them off; nothing is changed.
        """
        current = user.check_ins
        if changes.enabled not in (None, current.enabled):
            self._features.require_available(user.id, Feature.CHECK_INS)
        updated = self.settings_after(current, changes)
        changed = []
        if updated.frequency != current.frequency:
            changed.append(ChatSetting.CHECK_IN_FREQUENCY)
        if (updated.quiet_hours_start, updated.quiet_hours_end) != (
            current.quiet_hours_start,
            current.quiet_hours_end,
        ):
            changed.append(ChatSetting.QUIET_HOURS)
        if updated.enabled != current.enabled:
            changed.append(ChatSetting.CHECK_IN_PAUSE)
        recorded = record_where_changed(user, changed, in_chat, self._clock.now())
        return self._save(recorded, updated)

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

    def pause(self, user: User, length: PauseLength, in_chat: bool = False) -> User:
        """Pause a User's Check-ins, keeping their other settings.

        Pausing turns Check-ins on if they were off.

        Args:
            user: The User pausing.
            length: For a day, a week or until they resume.
            in_chat: True if the User asked for it in chat, not on the
                Dashboard.

        Returns:
            The saved User.
        """
        now = self._clock.now()
        current = user.check_ins
        paused_until = (
            None if length == PauseLength.UNTIL_RESUMED else now + PAUSE_LENGTHS[length]
        )
        paused = replace(current, enabled=True, paused=True, paused_until=paused_until)
        recorded = record_where_changed(
            user, [ChatSetting.CHECK_IN_PAUSE], in_chat, now
        )
        return self._save(recorded, self._with_next_due_time(current, paused))

    def resume(self, user: User, in_chat: bool = False) -> User:
        """End a pause on a User's Check-ins.

        Args:
            user: The User resuming.
            in_chat: True if the User asked for it in chat, not on the
                Dashboard.

        Returns:
            The saved User.
        """
        recorded = record_where_changed(
            user, [ChatSetting.CHECK_IN_PAUSE], in_chat, self._clock.now()
        )
        return self._save(
            recorded, replace(user.check_ins, paused=False, paused_until=None)
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
        """List a User's newest Check-in decisions with what happened after each.

        Args:
            user: The User.

        Returns:
            Each Check-in and its status, newest first.
        """
        return self._recent(user, RECENT_CHECK_INS_LIMIT)

    def last_sent(self, user: User) -> RecentCheckIn | None:
        """Find the newest Check-in that was actually sent to a User.

        Args:
            user: The User.

        Returns:
            The newest Check-in that wasn't skipped, with its status, or None
            if none was sent lately.
        """
        recent = self._recent(user, CHECK_INS_LOOKED_BACK_FOR_LAST_SENT)
        return next(
            (
                entry
                for entry in recent
                if entry.check_in.outcome != CheckInOutcome.SKIPPED
            ),
            None,
        )

    def kinds_for(self, user: User) -> list[CheckInKind]:
        """List the Check-in Kinds that may be sent to a User.

        Args:
            user: The User.

        Returns:
            Every Check-in Kind in order; only those allowed without User
            Memory when it doesn't work for the User.
        """
        kinds = self._repositories.check_ins.list_kinds()
        if self._features.works_for(user.id, Feature.USER_MEMORY):
            return kinds
        return [kind for kind in kinds if kind.allowed_without_user_memory]

    def list_log(self, days: int) -> list[LoggedCheckIn]:
        """List every User's Check-in decisions from the last few days.

        Args:
            days: How many days back to list.

        Returns:
            The decisions with who each was for and what happened after,
            newest first.
        """
        now = self._clock.now()
        entries = self._repositories.check_ins.list_log(now - timedelta(days=days))
        statuses = check_in_statuses(
            [entry.check_in for entry in entries],
            now,
            check_in_reply_window(self._repositories.platform_settings),
        )
        return [
            LoggedCheckIn(entry=entry, status=status)
            for entry, status in zip(entries, statuses, strict=True)
        ]

    def send_due(self) -> None:
        """Decide on a Check-in for every User who is due one right now.

        A User is due when Check-ins work for them, the frequency gap has passed,
        they are not paused, it is outside their quiet hours, they have a
        Telegram Connection and no open Conversation. A decision that fails
        before it is saved is logged and tried again on the next tick; the
        others still go ahead.
        """
        now = self._clock.now()
        for user in self._repositories.check_ins.list_due_users(now):
            try:
                self._check_in_if_due(user, now)
            except Exception:
                logger.exception("Could not decide on a Check-in")

    def _check_in_if_due(self, user: User, now: datetime) -> None:
        """Send, skip, or ask about fewer Check-ins, if nothing holds it back.

        A User who has used up today's daily message limit gets a limit skip
        instead and stays due. After the Admin-set number of ignored Check-ins
        in a row, the User gets the "would you like fewer?" message and their
        Check-ins pause.
        Otherwise the Check-in model decides on a Kind and message, or to
        skip. Kinds that send a Shared Photo are offered only to a User with
        Shared Photos in use. The next attempt is one frequency gap later,
        unless the chat channel refuses the message.

        Args:
            user: A User whose next Check-in is due.
            now: The current time.

        Raises:
            InvalidCheckInAnswerError: If the model's answer can't be used.
        """
        if not self._features.works_for(user.id, Feature.CHECK_INS):
            return
        settings = user.check_ins
        local_time = local_now(now, user.time_zone)
        if settings.is_paused_at(now) or is_in_quiet_hours(settings, local_time.time()):
            return
        connection = self._repositories.telegram_connections.get_by_user(user.id)
        if connection is None or self._has_open_conversation(user, now):
            return
        if self._usage_limiter.has_used_up_daily_message_limit(user.id):
            self._skip_for_daily_limit(user, now)
            return
        next_due_at = now + self._gap(settings.frequency)
        if self._has_ignored_too_many(user):
            self._ask_about_fewer(user, connection.telegram_chat_id, now, next_due_at)
            return
        shared_photos = self._shared_photos(user)
        kinds = [
            kind
            for kind in self.kinds_for(user)
            if shared_photos or not kind.sends_shared_photo
        ]
        if not kinds:
            logger.warning("No Check-in Kind may be sent to this User")
            return
        decision = self._decide(user, kinds, shared_photos, local_time)
        if decision.kind is None:
            skipped = CheckIn(
                id=uuid4(),
                user_id=user.id,
                outcome=CheckInOutcome.SKIPPED,
                decided_at=now,
                skip_reason=decision.skip_reason,
            )
            self._repositories.check_ins.add(
                skipped, next_due_at, pause_until_resumed=False
            )
            return
        shared_photo = decision.shared_photo
        check_in = CheckIn(
            id=uuid4(),
            user_id=user.id,
            outcome=CheckInOutcome.SENT,
            decided_at=now,
            kind_id=decision.kind.id,
            message=decision.message,
            shared_photo_id=shared_photo.id if shared_photo is not None else None,
        )
        was_sent = self._save_then_send(
            user,
            connection.telegram_chat_id,
            decision.message,
            check_in,
            next_due_at,
            pause_until_resumed=False,
        )
        if (
            was_sent
            and shared_photo is not None
            and not self._send_shared_photo(connection.telegram_chat_id, shared_photo)
        ):
            self._repositories.check_ins.remove_shared_photo(check_in.id)

    def _skip_for_daily_limit(self, user: User, now: datetime) -> None:
        """Record a Skipped Check-in for a User who used up today's daily message limit.

        Only one is recorded per User per day. The User stays due, so a
        Check-in can come on their next day.

        Args:
            user: A due User who has used up today's daily message limit.
            now: The current time.
        """
        if self._has_limit_skip_today(user, now):
            return
        skipped = CheckIn(
            id=uuid4(),
            user_id=user.id,
            outcome=CheckInOutcome.SKIPPED,
            decided_at=now,
            skip_reason=DAILY_LIMIT_SKIP_REASON,
        )
        self._repositories.check_ins.add(skipped, now, pause_until_resumed=False)

    def _has_limit_skip_today(self, user: User, now: datetime) -> bool:
        """Tell whether the User's newest Check-in is a limit skip from their today.

        Args:
            user: The User.
            now: The current time.

        Returns:
            True if a limit skip was already recorded on the User's day.
        """
        newest = self._repositories.check_ins.list_recent(user.id, 1)
        return (
            bool(newest)
            and newest[0].skipped_for_daily_limit
            and users_today(user.time_zone, newest[0].decided_at)
            == users_today(user.time_zone, now)
        )

    def _save_then_send(
        self,
        user: User,
        chat_id: int,
        message: str,
        check_in: CheckIn,
        next_due_at: datetime,
        pause_until_resumed: bool,
    ) -> bool:
        """Save a Check-in and the User's next due time, then send its message.

        Saving first means a failed save sends nothing, so a Check-in is
        never sent twice. If the chat channel clearly refuses the message,
        the Check-in is taken back and tried again after the retry gap. If
        the User blocked the Companion, a Skipped Check-in takes its place and
        the next attempt is one frequency gap later, with no pause. Any other
        failure, such as a timeout, may still have delivered it, so it counts
        as sent. If taking it back fails, that Check-in is missed.

        Args:
            user: The User it is for.
            chat_id: Their Telegram chat.
            message: The message to send.
            check_in: The Check-in to save.
            next_due_at: When their next Check-in may be sent.
            pause_until_resumed: Whether sending it pauses their Check-ins
                until they resume.

        Returns:
            True if the message counts as sent.
        """
        self._repositories.check_ins.add(check_in, next_due_at, pause_until_resumed)
        try:
            self._chat_channel.send_text(chat_id, message)
        except ChatBlockedError:
            skipped = CheckIn(
                id=uuid4(),
                user_id=user.id,
                outcome=CheckInOutcome.SKIPPED,
                decided_at=check_in.decided_at,
                skip_reason=BLOCKED_SKIP_REASON,
            )
            self._repositories.check_ins.undo_add(
                check_in, next_due_at, pause_until_resumed, skipped
            )
            return False
        except MessageRefusedError as error:
            logger.warning("The chat channel refused a Check-in: %s", error)
            retry_at = check_in.decided_at + REFUSED_CHECK_IN_RETRY_GAP
            self._repositories.check_ins.undo_add(
                check_in, retry_at, pause_until_resumed, skipped=None
            )
            return False
        except Exception:
            logger.exception("Could not tell if a Check-in arrived; it counts as sent")
        return True

    def _send_shared_photo(self, chat_id: int, shared_photo: SharedPhoto) -> bool:
        """Send a Check-in's Shared Photo after its message.

        If Telegram refuses it, the error is logged and the message still
        counts as sent.

        Args:
            chat_id: The User's Telegram chat.
            shared_photo: The Shared Photo to send.

        Returns:
            True if the photo was sent.
        """
        try:
            self._chat_channel.send_photo(chat_id, shared_photo.file_id)
        except Exception:
            logger.exception("Could not send the Check-in's Shared Photo")
            return False
        return True

    def _ask_about_fewer(
        self, user: User, chat_id: int, now: datetime, next_due_at: datetime
    ) -> None:
        """Send the "would you like fewer?" message and pause the User's Check-ins.

        It is saved before it is sent, like any Check-in.

        Args:
            user: The User who ignored too many Check-ins in a row.
            chat_id: Their Telegram chat.
            now: The current time.
            next_due_at: When their next Check-in may be sent once resumed.
        """
        message = self._repositories.platform_settings.get("check_in_fewer_message")
        self._save_then_send(
            user,
            chat_id,
            message,
            CheckIn(
                id=uuid4(),
                user_id=user.id,
                outcome=CheckInOutcome.ASKED_ABOUT_FEWER,
                decided_at=now,
                message=message,
            ),
            next_due_at,
            pause_until_resumed=True,
        )

    def _recent(self, user: User, limit: int) -> list[RecentCheckIn]:
        """List a User's newest Check-in decisions with their statuses.

        Args:
            user: The User.
            limit: The most to list.

        Returns:
            Each Check-in and its status, newest first.
        """
        recent = self._repositories.check_ins.list_recent(user.id, limit)
        statuses = check_in_statuses(
            recent,
            self._clock.now(),
            check_in_reply_window(self._repositories.platform_settings),
        )
        return [
            RecentCheckIn(check_in=check_in, status=status)
            for check_in, status in zip(recent, statuses, strict=True)
        ]

    def _has_ignored_too_many(self, user: User) -> bool:
        """Tell whether the User ignored the Admin-set number of Check-ins in a row.

        Args:
            user: The User.

        Returns:
            True if it is time to ask whether they'd like fewer.
        """
        threshold: int = self._repositories.platform_settings.get(
            "check_in_ignore_threshold"
        )
        recent = self._repositories.check_ins.list_recent(
            user.id, CHECK_INS_LOOKED_BACK_FOR_IGNORES
        )
        latest = self._repositories.conversations.get_latest_for_user(user.id)
        started_at = latest.started_at if latest is not None else None
        return ignored_in_a_row(recent, started_at) >= threshold

    def _memory(self, user: User) -> str:
        """Write what is remembered about the User, for the Check-in model.

        Args:
            user: The User.

        Returns:
            Their Memory Items by active Memory Category and their newest
            Conversation Summaries, even while User Memory is off; "" if
            nothing is remembered.
        """
        user_memory = self._repositories.user_memory
        settings = self._repositories.platform_settings
        categories = [
            category
            for category in self._repositories.memory_categories.list_all()
            if not category.archived
        ]
        return format_memory(
            categories,
            user_memory.list_items(user.id),
            user_memory.list_summaries(
                user.id, limit=settings.get("recent_conversation_summaries")
            ),
            user.time_zone,
            MEMORY_INTRO,
        )

    def _shared_photos(self, user: User) -> list[SharedPhoto]:
        """List the User's Shared Photos a Check-in may send.

        Args:
            user: The User.

        Returns:
            Their Shared Photos, newest first; none if User Memory or Photo
            Viewing doesn't work for the User, since only Check-in Kinds
            that need User Memory send one.
        """
        if not self._features.works_for(user.id, Feature.USER_MEMORY):
            return []
        if not self._features.works_for(user.id, Feature.PHOTO_VIEWING):
            return []
        return self._repositories.user_memory.list_shared_photos(user.id)

    def _decide(
        self,
        user: User,
        kinds: list[CheckInKind],
        shared_photos: list[SharedPhoto],
        local_time: datetime,
    ) -> CheckInDecision:
        """Ask the Check-in model to choose a Kind and write the message, or skip.

        Args:
            user: The User it is for.
            kinds: The Check-in Kinds it may choose from.
            shared_photos: The User's Shared Photos it may send.
            local_time: The User's local time now.

        Returns:
            The decision.

        Raises:
            InvalidCheckInAnswerError: If the answer can't be used.
        """
        settings = self._repositories.platform_settings
        description = describe_check_in(
            user,
            kinds,
            local_time,
            describe_recent_check_ins(
                self._recent(user, CHECK_INS_TOLD_TO_MODEL), user.time_zone
            ),
            self._memory(user),
            describe_shared_photos(kinds, shared_photos, user.time_zone),
        )
        answer = self._chat_model.generate(
            user_id=user.id,
            model=settings.get("check_in_model"),
            instructions=f"{settings.get('persona')}\n\n{settings.get('check_in_prompt')}",
            history=[ChatLine(role=ChatRole.USER, text=description)],
        )
        return read_check_in_decision(answer, kinds, shared_photos)

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
