from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from enum import StrEnum

from companion.core.models import (
    CheckInFrequency,
    CheckInKind,
    CheckInSettings,
    Conversation,
    Feature,
    UserSnapshot,
)
from companion.core.timing import is_open, local_now

REFUSED_CHECK_IN_RETRY_GAP = timedelta(minutes=15)


class HoldBackReason(StrEnum):
    """Why a due User's Check-in is held back."""

    CHECK_INS_OFF = "check_ins_off"
    PAUSED = "paused"
    QUIET_HOURS = "quiet_hours"
    NO_TELEGRAM_CONNECTION = "no_telegram_connection"
    IN_CONVERSATION = "in_conversation"
    LIMIT_SKIP_DONE_TODAY = "limit_skip_done_today"
    NO_KIND_TO_SEND = "no_kind_to_send"


@dataclass(frozen=True)
class CheckInRules:
    """The Admin-set Check-in rules, read once per tick.

    Attributes:
        frequency_gaps: The fewest time between two Check-ins, per frequency.
        quiet_gap: How long with no message ends a Conversation.
        ignore_threshold: How many ignored Check-ins in a row bring the
            "would you like fewer?" message.
        curiosity_check_ins_per_week: The most Check-ins that ask a
            Curiosity one User gets in 7 days.
        kinds: Every Check-in Kind, in order.
    """

    frequency_gaps: Mapping[CheckInFrequency, timedelta]
    quiet_gap: timedelta
    ignore_threshold: int
    curiosity_check_ins_per_week: int
    kinds: tuple[CheckInKind, ...]


@dataclass(frozen=True)
class CheckInFacts:
    """What is known about one due User when deciding on their Check-in.

    Attributes:
        snapshot: The User, their local time and Features, as read for this
            tick.
        telegram_chat_id: Their Telegram chat; None without a Telegram
            Connection.
        latest_conversation: Their newest Conversation, if any.
        used_up_daily_message_limit: Whether they used up today's Daily
            Message Limit.
        limit_skip_today: Whether a limit skip was already recorded on their
            day.
        ignored_in_a_row: How many sent Check-ins in a row they ignored,
            counted at most up to the ignore threshold.
        has_shared_photos: Whether they have any Shared Photos.
        has_due_curiosity: Whether they have a waiting Curiosity whose day
            has come.
        curiosity_check_ins_this_week: How many Check-ins that ask a
            Curiosity were sent to them in the last 7 days.
    """

    snapshot: UserSnapshot
    telegram_chat_id: int | None
    latest_conversation: Conversation | None
    used_up_daily_message_limit: bool
    limit_skip_today: bool
    ignored_in_a_row: int
    has_shared_photos: bool
    has_due_curiosity: bool
    curiosity_check_ins_this_week: int


@dataclass(frozen=True)
class HoldBack:
    """Send nothing and log nothing; try again at `retry_at`.

    Attributes:
        reason: Why it is held back.
        retry_at: The User's next due time; None for no due time, until they
            resume or connect Telegram. The current due time means they stay
            due.
    """

    reason: HoldBackReason
    retry_at: datetime | None


@dataclass(frozen=True)
class SkipForDailyLimit:
    """Record a Skipped Check-in for the Daily Message Limit; the User stays due."""


@dataclass(frozen=True)
class AskAboutFewer:
    """Send the "would you like fewer?" message, then pause until resumed.

    Attributes:
        telegram_chat_id: The User's Telegram chat.
        next_due_at: Their next due time once they resume.
    """

    telegram_chat_id: int
    next_due_at: datetime


@dataclass(frozen=True)
class AskModel:
    """Let the Check-in model pick a Kind and write the message, or skip.

    Attributes:
        kinds: The Check-in Kinds it may pick from.
        telegram_chat_id: The User's Telegram chat.
        next_due_at: Their next due time after this Check-in.
    """

    kinds: tuple[CheckInKind, ...]
    telegram_chat_id: int
    next_due_at: datetime


CheckInPlan = HoldBack | SkipForDailyLimit | AskAboutFewer | AskModel


def decide_check_in(
    facts: CheckInFacts, rules: CheckInRules, now: datetime
) -> CheckInPlan:
    """Decide what to do for a User whose Check-in is due.

    Checked in this order: Check-ins off, paused, Quiet Hours, no Telegram
    Connection, mid-Conversation, the Daily Message Limit, ignored too many,
    and whether any Kind may be sent. Photo Kinds are offered only with
    Shared Photos and Photo Viewing working. Kinds that ask a Curiosity are
    offered only with a Curiosity due, Curiosities working and the weekly
    limit not reached.

    Args:
        facts: What is known about the User.
        rules: The Admin-set Check-in rules.
        now: The current time.

    Returns:
        Hold back, skip for the Daily Message Limit, ask about fewer, or ask
        the Check-in model.
    """
    snapshot = facts.snapshot
    settings = snapshot.user.check_ins
    current_due_at = settings.next_due_at
    if not snapshot.works(Feature.CHECK_INS):
        return HoldBack(HoldBackReason.CHECK_INS_OFF, retry_at=current_due_at)
    if settings.is_paused_at(now):
        return HoldBack(HoldBackReason.PAUSED, retry_at=settings.paused_until)
    if is_in_quiet_hours(settings, snapshot.local_now.time()):
        return HoldBack(
            HoldBackReason.QUIET_HOURS,
            retry_at=quiet_hours_end_after(settings, snapshot.local_now),
        )
    chat_id = facts.telegram_chat_id
    if chat_id is None:
        return HoldBack(HoldBackReason.NO_TELEGRAM_CONNECTION, retry_at=None)
    conversation = facts.latest_conversation
    if conversation is not None and is_open(conversation, now, rules.quiet_gap):
        return HoldBack(
            HoldBackReason.IN_CONVERSATION,
            retry_at=conversation.last_message_at + rules.quiet_gap,
        )
    if facts.used_up_daily_message_limit:
        if facts.limit_skip_today:
            return HoldBack(
                HoldBackReason.LIMIT_SKIP_DONE_TODAY, retry_at=current_due_at
            )
        return SkipForDailyLimit()
    next_due_at = next_due_after_check_in(settings.frequency, rules.frequency_gaps, now)
    if facts.ignored_in_a_row >= rules.ignore_threshold:
        return AskAboutFewer(telegram_chat_id=chat_id, next_due_at=next_due_at)
    photos_may_be_sent = facts.has_shared_photos and snapshot.works(
        Feature.PHOTO_VIEWING
    )
    curiosity_may_be_asked = (
        facts.has_due_curiosity
        and snapshot.works(Feature.CURIOSITIES)
        and facts.curiosity_check_ins_this_week < rules.curiosity_check_ins_per_week
    )
    kinds = tuple(
        kind
        for kind in rules.kinds
        if (photos_may_be_sent or not kind.sends_shared_photo)
        and (curiosity_may_be_asked or not kind.raises_curiosity)
    )
    if not kinds:
        return HoldBack(HoldBackReason.NO_KIND_TO_SEND, retry_at=current_due_at)
    return AskModel(kinds=kinds, telegram_chat_id=chat_id, next_due_at=next_due_at)


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


def quiet_hours_end_after(settings: CheckInSettings, local_now: datetime) -> datetime:
    """Work out when the User's quiet hours next end.

    Args:
        settings: The User's Check-in settings.
        local_now: The time where the User is, with their time zone.

    Returns:
        The next time their quiet hours end, after `local_now`, in UTC.
    """
    end_today = datetime.combine(
        local_now.date(), settings.quiet_hours_end, tzinfo=local_now.tzinfo
    )
    if end_today > local_now:
        return end_today.astimezone(UTC)
    end_tomorrow = datetime.combine(
        local_now.date() + timedelta(days=1),
        settings.quiet_hours_end,
        tzinfo=local_now.tzinfo,
    )
    return end_tomorrow.astimezone(UTC)


def next_due_after_check_in(
    frequency: CheckInFrequency,
    frequency_gaps: Mapping[CheckInFrequency, timedelta],
    now: datetime,
) -> datetime:
    """Work out the next due time after a Check-in is sent or skipped.

    Args:
        frequency: The User's frequency.
        frequency_gaps: The fewest time between two Check-ins, per frequency.
        now: When the Check-in was decided.

    Returns:
        One frequency gap later.
    """
    return now + frequency_gaps[frequency]


def retry_after_refusal(decided_at: datetime) -> datetime:
    """Work out when to try again after the chat channel refused a Check-in.

    Args:
        decided_at: When the refused Check-in was decided.

    Returns:
        One retry gap later.
    """
    return decided_at + REFUSED_CHECK_IN_RETRY_GAP


def next_due_after_change(
    before: CheckInSettings,
    after: CheckInSettings,
    frequency_gaps: Mapping[CheckInFrequency, timedelta],
    now: datetime,
) -> datetime | None:
    """Work out the next due time after the User changes their Check-in settings.

    A pause holds a due User back with no due time, or until the pause ends.
    So when the pause changes or ends, a due time the pause set, or one
    already passed, becomes now, and the next tick decides again. A due time
    of now also wins over a tick that read the old one and is holding the
    User back meanwhile.

    Args:
        before: The settings before the change.
        after: The settings after the change, with the old due time.
        frequency_gaps: The fewest time between two Check-ins, per frequency.
        now: The current time.

    Returns:
        None when off; one frequency gap from now when just turned on or the
        frequency changed; now when the pause changed and had set the due
        time or it had passed; otherwise the due time as it was.
    """
    if not after.enabled:
        return None
    if not before.enabled or before.frequency != after.frequency:
        return next_due_after_check_in(after.frequency, frequency_gaps, now)
    pause_changed = (before.paused, before.paused_until) != (
        after.paused,
        after.paused_until,
    )
    pause_set_due_time = before.paused and (
        before.next_due_at is None
        or before.next_due_at == before.paused_until
        or before.next_due_at <= now
    )
    if pause_changed and pause_set_due_time:
        return now
    return after.next_due_at


def next_due_after_quiet_hours_move(
    before: CheckInSettings, time_zone: str | None, now: datetime
) -> datetime | None:
    """Work out the next due time after the User's Quiet Hours or time zone change.

    A User held back by Quiet Hours is due when the old Quiet Hours end. So
    that due time, or one already passed, becomes now, and the next tick
    decides with the new Quiet Hours.

    Args:
        before: The settings before the change.
        time_zone: The User's time zone before the change.
        now: The current time.

    Returns:
        Now if the old Quiet Hours set the due time or it had passed;
        otherwise the due time as it was.
    """
    due_at = before.next_due_at
    if due_at is None:
        return None
    if due_at <= now:
        return now
    old_local_now = local_now(time_zone, now)
    set_by_quiet_hours = is_in_quiet_hours(
        before, old_local_now.time()
    ) and due_at == quiet_hours_end_after(before, old_local_now)
    return now if set_by_quiet_hours else due_at
