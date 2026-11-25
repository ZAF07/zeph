import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from companion.core.check_in_decision import (
    AskAboutFewer,
    AskModel,
    CheckInFacts,
    CheckInPlan,
    CheckInRules,
    HoldBack,
    SkipForDailyLimit,
    decide_check_in,
    kinds_with_pattern_settled,
    next_due_after_change,
    next_due_after_quiet_hours_move,
    retry_after_refusal,
)
from companion.core.curiosities import describe_guess, due_curiosities
from companion.core.features import FeatureService
from companion.core.memory_retrieval import (
    format_day,
    format_memory,
    shared_photo_line,
)
from companion.core.models import (
    DAILY_LIMIT_SKIP_REASON,
    ChangedBy,
    ChatLine,
    ChatRole,
    ChatSetting,
    CheckIn,
    CheckInChanges,
    CheckInKind,
    CheckInLogEntry,
    CheckInNowRequest,
    CheckInOutcome,
    CheckInSettings,
    CheckInStatus,
    Curiosity,
    Feature,
    HeldBack,
    HoldBackReason,
    ModelStep,
    NextDueTimeChange,
    PauseLength,
    PlatformSettings,
    SharedPhoto,
    ShareVia,
    TraceKind,
    User,
    UserSnapshot,
)
from companion.core.pattern_sharing import (
    SHARES_COUNTED_OVER,
    PatternSharing,
    PatternToShare,
    format_pattern_to_share_for_check_in,
    within_weekly_limit,
)
from companion.core.platform_settings import (
    CHECK_IN_FEWER_MESSAGE,
    CHECK_IN_GAPS,
    CHECK_IN_IGNORE_THRESHOLD,
    CHECK_IN_MODEL,
    CHECK_IN_PROMPT,
    CHECK_IN_REPLY_WINDOW,
    CHECK_IN_THINKING,
    CONVERSATION_QUIET_GAP,
    CURIOSITY_CHECK_INS_PER_WEEK,
    PATTERN_SHARE_WAIT,
    PATTERNS_SHARED_PER_WEEK,
    PERSONA,
    RECENT_CONVERSATION_SUMMARIES,
    thinking_to_use,
)
from companion.core.ports import (
    ChatBlockedError,
    ChatChannel,
    Clock,
    MessageRefusedError,
    Repositories,
)
from companion.core.settings_changes import record_where_changed
from companion.core.timing import users_today
from companion.core.usage import UsageLimiter, UsageRecordingChatModel
from companion.core.user_snapshot import UserSnapshotLoader

logger = logging.getLogger(__name__)

RECENT_CHECK_INS_LIMIT = 10
CHECK_INS_TOLD_TO_MODEL = 5
CHECK_INS_LOOKED_BACK_FOR_LAST_SENT = 100
MEMORY_INTRO = "What you remember about them:"
BLOCKED_SKIP_REASON = "User has blocked the Companion on Telegram"
CURIOSITY_CHECK_INS_COUNTED_OVER = timedelta(days=7)
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
class CheckInsPage:
    """What the Dashboard's Check-ins page shows a User. Never a next time.

    Attributes:
        settings: Their Check-in settings.
        available: Whether the Admin side allows Check-ins for them.
        paused: Whether their Check-ins are paused right now.
        recent: Their newest Check-in decisions, newest first.
        kinds: The Check-in Kinds that may be sent to them.
        changed_by_admin: When an Admin last changed each of their settings,
            until they change it themselves.
    """

    settings: CheckInSettings
    available: bool
    paused: bool
    recent: list[RecentCheckIn]
    kinds: list[CheckInKind]
    changed_by_admin: dict[ChatSetting, datetime]


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
        curiosity: The Curiosity the message asks; None unless the Kind
            asks one.
    """

    kind: CheckInKind | None
    message: str = ""
    skip_reason: str = ""
    shared_photo: SharedPhoto | None = None
    curiosity: Curiosity | None = None


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
    Conversation. Skipped and Woven-in Check-ins are passed over, since a
    woven-in one came while they were talking.

    Args:
        recent: The User's newest Check-ins, newest first.
        last_conversation_started_at: When the User last started a
            Conversation, if ever.

    Returns:
        How many Check-ins in a row went unanswered.
    """
    count = 0
    for check_in in recent:
        if not check_in.was_sent or check_in.woven_in:
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


def is_limit_skip_on_their_today(
    newest: CheckIn | None, snapshot: UserSnapshot
) -> bool:
    """Tell whether the User's newest Check-in is a limit skip from their today.

    Args:
        newest: The User's newest Check-in; None if they have none.
        snapshot: The User, with their day, as read for this tick.

    Returns:
        True if a limit skip was already recorded on the User's day.
    """
    return (
        newest is not None
        and newest.skipped_for_daily_limit
        and users_today(snapshot.user.time_zone, newest.decided_at) == snapshot.today
    )


def due_time_change(user: User, plan: HoldBack) -> NextDueTimeChange | None:
    """Work out the change to a held-back User's next due time and why it waits.

    It is held back until its new due time; a User who stays due waits until
    the time the plan gives, or for something with no known end, such as
    their next day.

    Args:
        user: The User, as read for this tick.
        plan: Why they are held back and until when.

    Returns:
        The change; None if their due time and why it waits stay as they are.
    """
    read_as = user.check_ins.next_due_at
    until = plan.until or (None if plan.retry_at == read_as else plan.retry_at)
    held_back = HeldBack(reason=plan.reason, until=until)
    if plan.retry_at == read_as and held_back == user.check_ins.held_back:
        return None
    return NextDueTimeChange(
        user_id=user.id, read_as=read_as, becomes=plan.retry_at, held_back=held_back
    )


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


def describe_due_curiosities_for_check_in(
    kinds: list[CheckInKind], due_curiosities: list[Curiosity]
) -> str:
    """Write the User's due Curiosities for the Check-in model, numbered.

    Args:
        kinds: The Check-in Kinds it may choose from.
        due_curiosities: The User's waiting Curiosities whose day has come,
            oldest first.

    Returns:
        How to name a Curiosity for the Kinds that ask one, then one line
        per Curiosity, with its guess to check if it holds one; "" if no
        offered Kind asks one or none is due.
    """
    curiosity_kinds = [kind.name for kind in kinds if kind.raises_curiosity]
    if not curiosity_kinds or not due_curiosities:
        return ""
    kind_names = " or ".join(f'"{name}"' for name in curiosity_kinds)
    curiosity_lines = "\n".join(
        f"{number}. {curiosity.question} Why: {curiosity.why} "
        f"Sensitivity: {curiosity.sensitivity.value}."
        f"{describe_guess(curiosity.guess, curiosity.how_sure)}"
        for number, curiosity in enumerate(due_curiosities, start=1)
    )
    return (
        f"Things you've been wondering about them, oldest first. If you "
        f'choose {kind_names}, also add "curiosity": <the number of one '
        f"below> to your answer; your message should ask it the way a friend "
        f"would:\n{curiosity_lines}"
    )


def describe_check_in(
    user: User,
    kinds: list[CheckInKind],
    local_time: datetime,
    recent: str,
    memory: str,
    shared_photos: str = "",
    due_curiosities: str = "",
    pattern_to_share: str = "",
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
        due_curiosities: The User's numbered due Curiosities; "" if none
            are offered.
        pattern_to_share: The ready Pattern its message tells them; "" if
            none is offered.

    Returns:
        The Kinds, what to call the User, their local time, recent
        Check-ins, what is remembered about them, their Shared Photos,
        their due Curiosities and the Pattern to tell them.
    """
    kind_lines = "\n".join(f"- {kind.name}: {kind.description}" for kind in kinds)
    remembered = memory or "Nothing remembered about them."
    extras = "".join(
        f"\n\n{extra}"
        for extra in (shared_photos, due_curiosities, pattern_to_share)
        if extra
    )
    return (
        f"Check-in Kinds you may choose from:\n{kind_lines}\n\n"
        f"What to call them: {user.name or 'unknown'}\n"
        f"Their local time: {local_time.strftime('%A, %H:%M')}\n\n"
        f"Recent Check-ins, newest first:\n{recent}\n\n"
        f"{remembered}{extras}"
    )


def read_listed_number(parsed: dict[str, Any], key: str, listed: int) -> int | None:
    """Read the number of something the Check-in model was listed.

    Args:
        parsed: The model's JSON decision.
        key: The field's name, e.g. "photo".
        listed: How many were listed, numbered from 1.

    Returns:
        The number; None if it isn't a whole number in the list.
    """
    number = parsed.get(key)
    if isinstance(number, bool) or not isinstance(number, int):
        return None
    return number if 1 <= number <= listed else None


def read_check_in_decision(
    answer: str,
    kinds: list[CheckInKind],
    shared_photos: list[SharedPhoto],
    due_curiosities: Sequence[Curiosity] = (),
) -> CheckInDecision:
    """Read the Check-in model's JSON decision.

    Text around the JSON object, such as a code fence, is ignored. The Kind
    is matched by name, in any case, and must be one it was offered. A Kind
    that sends a Shared Photo needs the number of one it was listed, and a
    Kind that asks a Curiosity the number of one it was listed; any other
    Kind's photo or Curiosity number is ignored.

    Args:
        answer: The model's answer.
        kinds: The Check-in Kinds it could choose from.
        shared_photos: The Shared Photos it was listed, numbered from 1.
        due_curiosities: The Curiosities it was listed, numbered from 1.

    Returns:
        The decision.

    Raises:
        InvalidCheckInAnswerError: If there is no JSON decision, the Kind is
            not one it was offered, the message or reason is empty, or a
            Kind that sends a photo or asks a Curiosity names none it was
            listed.
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
    if kind.sends_shared_photo:
        photo_number = read_listed_number(parsed, "photo", len(shared_photos))
        if photo_number is None:
            raise InvalidCheckInAnswerError(
                f"Not a photo it was listed: {parsed.get('photo')!r}"
            )
        return CheckInDecision(
            kind=kind,
            message=message.strip(),
            shared_photo=shared_photos[photo_number - 1],
        )
    if kind.raises_curiosity:
        curiosity_number = read_listed_number(parsed, "curiosity", len(due_curiosities))
        if curiosity_number is None:
            raise InvalidCheckInAnswerError(
                f"Not a Curiosity it was listed: {parsed.get('curiosity')!r}"
            )
        return CheckInDecision(
            kind=kind,
            message=message.strip(),
            curiosity=due_curiosities[curiosity_number - 1],
        )
    return CheckInDecision(kind=kind, message=message.strip())


class CheckInService:
    """Keeps Users' Check-in settings and sends the Check-ins that are due."""

    def __init__(
        self,
        repositories: Repositories,
        features: FeatureService,
        user_snapshots: UserSnapshotLoader,
        chat_model: UsageRecordingChatModel,
        usage_limiter: UsageLimiter,
        chat_channel: ChatChannel,
        clock: Clock,
        pattern_sharing: PatternSharing,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where Users, Check-ins, Conversations and settings
                are stored.
            features: Says whether the Admin side allows Check-ins when a
                User changes them.
            user_snapshots: Reads every due User and their Features at once
                on each tick.
            chat_model: Writes each Check-in and records the tokens used.
            usage_limiter: Says whether a User has used up today's daily
                message limit.
            chat_channel: Sends Check-ins, and any Shared Photo with them,
                to Users.
            clock: Tells the current time.
            pattern_sharing: Offers a ready Pattern that waited too long for
                a moment in chat, and records when a Check-in shared it.
        """
        self._repositories = repositories
        self._features = features
        self._user_snapshots = user_snapshots
        self._chat_model = chat_model
        self._usage_limiter = usage_limiter
        self._chat_channel = chat_channel
        self._clock = clock
        self._pattern_sharing = pattern_sharing

    def change_settings(
        self,
        user: User,
        changes: CheckInChanges,
        changed_by: ChangedBy = ChangedBy.DASHBOARD,
    ) -> User:
        """Change and save a User's Check-in settings.

        Only settings whose value really changes are marked as changed in
        chat or on the Dashboard. Turning Check-ins on or off counts as a
        change to the pause, since turning them off ends it.

        Args:
            user: The User making the change.
            changes: The settings to change; None leaves one as it is.
            changed_by: Who changed it: the User on the Dashboard or in
                chat, or an Admin.

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
        now = self._clock.now()
        if ChatSetting.QUIET_HOURS in changed and updated.next_due_at == (
            current.next_due_at
        ):
            updated = replace(
                updated,
                next_due_at=next_due_after_quiet_hours_move(
                    current, user.time_zone, now
                ),
            )
        recorded = record_where_changed(user, changed, changed_by, now)
        return self._save(recorded, updated)

    def settings_after_time_zone_change(self, user: User) -> CheckInSettings:
        """Work out a User's Check-in settings for when their time zone changes.

        Args:
            user: The User, with their time zone before the change.

        Returns:
            Their Check-in settings, due now if they were held back until
            Quiet Hours end in the old time zone.
        """
        return replace(
            user.check_ins,
            next_due_at=next_due_after_quiet_hours_move(
                user.check_ins, user.time_zone, self._clock.now()
            ),
        )

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

    def pause(
        self,
        user: User,
        length: PauseLength,
        changed_by: ChangedBy = ChangedBy.DASHBOARD,
    ) -> User:
        """Pause a User's Check-ins, keeping their other settings.

        Pausing turns Check-ins on if they were off.

        Args:
            user: The User pausing.
            length: For a day, a week or until they resume.
            changed_by: Who changed it: the User on the Dashboard or in
                chat, or an Admin.

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
            user, [ChatSetting.CHECK_IN_PAUSE], changed_by, now
        )
        return self._save(recorded, self._with_next_due_time(current, paused))

    def resume(self, user: User, changed_by: ChangedBy = ChangedBy.DASHBOARD) -> User:
        """End a pause on a User's Check-ins.

        Args:
            user: The User resuming.
            changed_by: Who changed it: the User on the Dashboard or in
                chat, or an Admin.

        Returns:
            The saved User.
        """
        current = user.check_ins
        recorded = record_where_changed(
            user, [ChatSetting.CHECK_IN_PAUSE], changed_by, self._clock.now()
        )
        resumed = replace(current, paused=False, paused_until=None)
        return self._save(recorded, self._with_next_due_time(current, resumed))

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
        return self._recent(
            user, RECENT_CHECK_INS_LIMIT, self._repositories.platform_settings.load()
        )

    def last_sent(
        self, user: User, platform_settings: PlatformSettings
    ) -> RecentCheckIn | None:
        """Find the newest Check-in that was actually sent to a User.

        Args:
            user: The User.
            platform_settings: Holds the reply window, read once per request.

        Returns:
            The newest Check-in that wasn't skipped, with its status, or None
            if none was sent lately.
        """
        recent = self._recent(
            user, CHECK_INS_LOOKED_BACK_FOR_LAST_SENT, platform_settings
        )
        return next(
            (
                entry
                for entry in recent
                if entry.check_in.outcome != CheckInOutcome.SKIPPED
            ),
            None,
        )

    def page(self, user: User) -> CheckInsPage:
        """Gather what the Dashboard's Check-ins page shows a User.

        Args:
            user: The User.

        Returns:
            Their settings, whether Check-ins are available and paused right
            now, their recent Check-ins, the Check-in Kinds (one that
            shares a Pattern only while Pattern sharing works for them),
            and which settings an Admin changed.
        """
        shares_patterns = self._features.works_for(user.id, Feature.PATTERN_SHARING)
        return CheckInsPage(
            settings=user.check_ins,
            available=self._features.available_for(user.id, Feature.CHECK_INS),
            paused=self.is_paused(user),
            recent=self.list_recent(user),
            kinds=[
                kind
                for kind in self.list_kinds()
                if shares_patterns or not kind.shares_pattern
            ],
            changed_by_admin=user.settings_changed_by_admin,
        )

    def list_kinds(self) -> list[CheckInKind]:
        """List the Check-in Kinds, which may all be sent to any User.

        User Memory being off only stops learning, so it limits no Kind.

        Returns:
            Every Check-in Kind in order.
        """
        return self._repositories.check_ins.list_kinds()

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
            self._repositories.platform_settings.load().get(CHECK_IN_REPLY_WINDOW),
        )
        return [
            LoggedCheckIn(entry=entry, status=status)
            for entry, status in zip(entries, statuses, strict=True)
        ]

    def send_due(self, platform_settings: PlatformSettings) -> None:
        """Decide on a Check-in for every User who is due one right now.

        Facts about every due User are gathered together in a few queries,
        then `decide_check_in` says what to do for each. Held-back Users get
        their next due time saved together at the end, so they aren't read
        again until then. A decision that fails before it is saved is logged
        and tried again on the next tick; the others still go ahead.

        Args:
            platform_settings: The platform settings, read once for the tick.
        """
        now = self._clock.now()
        due_users = self._repositories.check_ins.list_due_users(now)
        if not due_users:
            return
        snapshots = self._user_snapshots.load_many(
            [user.id for user in due_users], platform_settings, TraceKind.CHECK_IN
        )
        rules = self._rules(platform_settings)
        plans = [
            (facts.snapshot, decide_check_in(facts, rules, now))
            for facts in self._gather_facts(snapshots, rules)
        ]
        self._hold_back(plans)
        to_carry_out = [
            (snapshot, plan)
            for snapshot, plan in plans
            if not isinstance(plan, HoldBack)
        ]
        fewer_message: str = (
            platform_settings.get(CHECK_IN_FEWER_MESSAGE)
            if any(isinstance(plan, AskAboutFewer) for _, plan in to_carry_out)
            else ""
        )
        for snapshot, plan in to_carry_out:
            try:
                self._carry_out(snapshot, plan, now, fewer_message)
            except Exception:
                logger.exception("Could not decide on a Check-in")

    def _hold_back(self, plans: list[tuple[UserSnapshot, CheckInPlan]]) -> None:
        """Save every held-back User's next due time and why, in one statement.

        This is done before any Check-in is sent, so a User who resumes or
        connects Telegram meanwhile changes their due time after it is read,
        and their change wins.

        Args:
            plans: Each due User and what to do for them.
        """
        due_time_changes = []
        for snapshot, plan in plans:
            if not isinstance(plan, HoldBack):
                continue
            if plan.reason == HoldBackReason.NO_KIND_TO_SEND:
                logger.warning("No Check-in Kind may be sent to this User")
            change = due_time_change(snapshot.user, plan)
            if change is not None:
                due_time_changes.append(change)
        self._repositories.check_ins.save_next_due_times(due_time_changes)

    def _rules(self, platform_settings: PlatformSettings) -> CheckInRules:
        """Read the Admin-set Check-in rules and Kinds, once per tick.

        Args:
            platform_settings: The platform settings, read once for the tick.

        Returns:
            The rules.
        """
        return CheckInRules(
            frequency_gaps=platform_settings.get(CHECK_IN_GAPS),
            quiet_gap=platform_settings.get(CONVERSATION_QUIET_GAP),
            ignore_threshold=platform_settings.get(CHECK_IN_IGNORE_THRESHOLD),
            curiosity_check_ins_per_week=platform_settings.get(
                CURIOSITY_CHECK_INS_PER_WEEK
            ),
            kinds=tuple(self.list_kinds()),
            pattern_share_wait=platform_settings.get(PATTERN_SHARE_WAIT),
            patterns_shared_per_week=platform_settings.get(PATTERNS_SHARED_PER_WEEK),
        )

    def _gather_facts(
        self, snapshots: list[UserSnapshot], rules: CheckInRules
    ) -> list[CheckInFacts]:
        """Gather what is needed to decide on every due User's Check-in.

        Each kind of fact is read for all Users in one query, so the number
        of queries stays the same however many Users are due. At least one
        sent Check-in is read per User, for when they were last sent one.

        Args:
            snapshots: The due Users, as read for this tick.
            rules: The Admin-set Check-in rules.

        Returns:
            One set of facts per User, in the same order.
        """
        user_ids = [snapshot.user.id for snapshot in snapshots]
        repositories = self._repositories
        connections = repositories.telegram_connections.list_for_users(user_ids)
        conversations = repositories.conversations.list_latest_for_users(user_ids)
        used_up_limit = self._usage_limiter.users_who_used_up_daily_message_limit(
            snapshots
        )
        newest = repositories.check_ins.list_recent_for_users(
            user_ids, 1, sent_only=False
        )
        sent_check_ins_to_read = max(rules.ignore_threshold, 1)
        newest_sent = repositories.check_ins.list_recent_for_users(
            user_ids, sent_check_ins_to_read, sent_only=True
        )
        with_shared_photos = repositories.user_memory.list_users_with_shared_photos(
            user_ids
        )
        waiting_curiosities = repositories.curiosities.list_waiting_for_users(user_ids)
        now = self._clock.now()
        curiosity_check_ins = repositories.check_ins.count_curiosity_check_ins_since(
            user_ids, now - CURIOSITY_CHECK_INS_COUNTED_OVER
        )
        with_pattern_ready_long = (
            repositories.patterns.list_users_with_pattern_ready_by(
                user_ids, now - rules.pattern_share_wait
            )
        )
        patterns_shared = repositories.patterns.count_shared_since(
            user_ids, now - SHARES_COUNTED_OVER
        )
        all_facts = []
        for snapshot in snapshots:
            user_id = snapshot.user.id
            connection = connections.get(user_id)
            conversation = conversations.get(user_id)
            sent = newest_sent.get(user_id, [])
            all_facts.append(
                CheckInFacts(
                    snapshot=snapshot,
                    telegram_chat_id=(
                        connection.telegram_chat_id if connection is not None else None
                    ),
                    latest_conversation=conversation,
                    used_up_daily_message_limit=user_id in used_up_limit,
                    limit_skip_today=is_limit_skip_on_their_today(
                        next(iter(newest.get(user_id, [])), None), snapshot
                    ),
                    ignored_in_a_row=ignored_in_a_row(
                        sent,
                        conversation.started_at if conversation is not None else None,
                    ),
                    has_shared_photos=user_id in with_shared_photos,
                    has_due_curiosity=bool(
                        due_curiosities(waiting_curiosities.get(user_id, []), snapshot)
                    ),
                    curiosity_check_ins_this_week=curiosity_check_ins.get(user_id, 0),
                    last_sent_at=sent[0].decided_at if sent else None,
                    pattern_waiting=(
                        snapshot.works(Feature.PATTERN_SHARING)
                        and user_id in with_pattern_ready_long
                        and within_weekly_limit(
                            patterns_shared.get(user_id, 0),
                            rules.patterns_shared_per_week,
                        )
                    ),
                )
            )
        return all_facts

    def _carry_out(
        self,
        snapshot: UserSnapshot,
        plan: CheckInPlan,
        now: datetime,
        fewer_message: str,
    ) -> None:
        """Skip for the Daily Message Limit, ask about fewer, or ask the model.

        Args:
            snapshot: The User, as read for this tick.
            plan: What `decide_check_in` said to do; not a hold back.
            now: The current time.
            fewer_message: The Admin-set "would you like fewer?" message.

        Raises:
            InvalidCheckInAnswerError: If the model's answer can't be used.
        """
        if isinstance(plan, SkipForDailyLimit):
            self._skip_for_daily_limit(snapshot.user, plan, now)
        elif isinstance(plan, AskAboutFewer):
            self._ask_about_fewer(snapshot.user, plan, fewer_message, now)
        elif isinstance(plan, AskModel):
            self._check_in_with_model(snapshot, plan, now)

    def _check_in_with_model(
        self, snapshot: UserSnapshot, plan: AskModel, now: datetime
    ) -> None:
        """Let the Check-in model send a Kind and message, or skip.

        Kinds that send a Shared Photo come with the User's Shared Photos,
        and Kinds that ask a Curiosity with their due Curiosities. A
        Curiosity is marked raised once its message counts as sent. When a
        ready Pattern has waited long enough and still passes its checks,
        only the Kinds that share one are offered, with the Pattern; once
        the message counts as sent, a small check says whether it told them,
        and only then is the Pattern shared. The next
        Due Time is the one for a send or a skip, unless the chat channel
        refuses the message. Nothing is saved or sent if the User's Due Time
        changed since the tick read it.

        Args:
            snapshot: The User, as read for this tick.
            plan: The Kinds it may pick from, the chat, and the next due
                times.
            now: The current time.

        Raises:
            InvalidCheckInAnswerError: If the model's answer can't be used.
        """
        user = snapshot.user
        pattern_to_share = (
            self._pattern_sharing.pattern_to_offer_in_check_in(snapshot)
            if any(kind.shares_pattern for kind in plan.kinds)
            else None
        )
        kinds = list(
            kinds_with_pattern_settled(plan.kinds, pattern_to_share is not None)
        )
        if not kinds:
            logger.warning("No Check-in Kind is left to send to this User")
            return
        shared_photos = (
            self._repositories.user_memory.list_shared_photos(user.id)
            if any(kind.sends_shared_photo for kind in kinds)
            else []
        )
        curiosities_to_ask = (
            due_curiosities(
                self._repositories.curiosities.list_waiting(user.id), snapshot
            )
            if any(kind.raises_curiosity for kind in kinds)
            else []
        )
        requested_by = (
            plan.check_in_now.requested_by if plan.check_in_now is not None else None
        )
        decision = self._decide(
            snapshot, kinds, shared_photos, curiosities_to_ask, pattern_to_share
        )
        if decision.kind is None:
            skipped = CheckIn(
                id=uuid4(),
                user_id=user.id,
                outcome=CheckInOutcome.SKIPPED,
                decided_at=now,
                skip_reason=decision.skip_reason,
                requested_by=requested_by,
            )
            self._repositories.check_ins.add(
                skipped,
                due_at_read=user.check_ins.next_due_at,
                next_due_at=plan.next_due_if_skipped,
                pause_until_resumed=False,
                check_in_now=plan.check_in_now,
            )
            return
        shared_photo = decision.shared_photo
        curiosity = decision.curiosity
        check_in = CheckIn(
            id=uuid4(),
            user_id=user.id,
            outcome=CheckInOutcome.SENT,
            decided_at=now,
            kind_id=decision.kind.id,
            message=decision.message,
            shared_photo_id=shared_photo.id if shared_photo is not None else None,
            curiosity_id=curiosity.id if curiosity is not None else None,
            requested_by=requested_by,
        )
        was_sent = self._save_then_send(
            user,
            plan.telegram_chat_id,
            decision.message,
            check_in,
            plan.next_due_if_sent,
            pause_until_resumed=False,
            check_in_now=plan.check_in_now,
        )
        if was_sent and curiosity is not None:
            self._repositories.curiosities.mark_raised([curiosity.id], None, now)
        if was_sent and pattern_to_share is not None and decision.message:
            self._pattern_sharing.record_if_shared(
                snapshot, pattern_to_share, [decision.message], ShareVia.CHECK_IN, None
            )
        if (
            was_sent
            and shared_photo is not None
            and not self._send_shared_photo(plan.telegram_chat_id, shared_photo)
        ):
            self._repositories.check_ins.remove_shared_photo(check_in.id)

    def _skip_for_daily_limit(
        self, user: User, plan: SkipForDailyLimit, now: datetime
    ) -> None:
        """Record a Skipped Check-in for a User who used up today's daily message limit.

        The User stays due at their Due Time, so a Check-in can come on their
        next day and the rhythm stays. Nothing is saved if their Due Time
        changed since the tick read it.

        Args:
            user: A due User who has used up today's daily message limit.
            plan: Their Due Time to keep.
            now: The current time.
        """
        skipped = CheckIn(
            id=uuid4(),
            user_id=user.id,
            outcome=CheckInOutcome.SKIPPED,
            decided_at=now,
            skip_reason=DAILY_LIMIT_SKIP_REASON,
        )
        self._repositories.check_ins.add(
            skipped,
            due_at_read=user.check_ins.next_due_at,
            next_due_at=plan.stays_due_at,
            pause_until_resumed=False,
        )

    def _save_then_send(
        self,
        user: User,
        chat_id: int,
        message: str,
        check_in: CheckIn,
        next_due_at: datetime,
        pause_until_resumed: bool,
        check_in_now: CheckInNowRequest | None = None,
    ) -> bool:
        """Save a Check-in and the User's next due time, then send its message.

        Saving first means a failed save sends nothing, so a Check-in is
        never sent twice. Nothing is saved or sent if the User's Due Time
        changed since the tick read it, e.g. because a reply wove this
        Check-in in already. If the chat channel clearly refuses the message,
        the Check-in is taken back and tried again after the retry gap, still
        counting the next Due Time from the one it was first due at, and any
        Check in Now it was for waits again. If
        the User blocked the Companion, a Skipped Check-in takes its place and
        the next attempt is at the next Due Time, with no pause. Any other
        failure, such as a timeout, may still have delivered it, so it counts
        as sent. If taking it back fails, that Check-in is missed.

        Args:
            user: The User it is for, as read for the tick.
            chat_id: Their Telegram chat.
            message: The message to send.
            check_in: The Check-in to save.
            next_due_at: When their next Check-in may be sent.
            pause_until_resumed: Whether sending it pauses their Check-ins
                until they resume.
            check_in_now: The Admin's Check in Now it is for; None for none.

        Returns:
            True if the message counts as sent.
        """
        saved = self._repositories.check_ins.add(
            check_in,
            due_at_read=user.check_ins.next_due_at,
            next_due_at=next_due_at,
            pause_until_resumed=pause_until_resumed,
            check_in_now=check_in_now,
        )
        if not saved:
            return False
        try:
            self._chat_channel.send_text(chat_id, message)
        except ChatBlockedError:
            skipped = CheckIn(
                id=uuid4(),
                user_id=user.id,
                outcome=CheckInOutcome.SKIPPED,
                decided_at=check_in.decided_at,
                skip_reason=BLOCKED_SKIP_REASON,
                requested_by=check_in.requested_by,
            )
            self._repositories.check_ins.undo_add(
                check_in,
                next_due_at,
                pause_until_resumed,
                skipped,
                held_back_due_at=None,
                check_in_now=None,
            )
            return False
        except MessageRefusedError as error:
            logger.warning("The chat channel refused a Check-in: %s", error)
            retry_at = retry_after_refusal(check_in.decided_at)
            self._repositories.check_ins.undo_add(
                check_in,
                retry_at,
                pause_until_resumed,
                skipped=None,
                held_back_due_at=user.check_ins.rhythm_due_at,
                check_in_now=check_in_now,
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
        self, user: User, plan: AskAboutFewer, message: str, now: datetime
    ) -> None:
        """Send the "would you like fewer?" message and pause the User's Check-ins.

        It is saved before it is sent, like any Check-in.

        Args:
            user: The User who ignored too many Check-ins in a row.
            plan: Their Telegram chat and next due time once resumed.
            message: The Admin-set "would you like fewer?" message.
            now: The current time.
        """
        self._save_then_send(
            user,
            plan.telegram_chat_id,
            message,
            CheckIn(
                id=uuid4(),
                user_id=user.id,
                outcome=CheckInOutcome.ASKED_ABOUT_FEWER,
                decided_at=now,
                message=message,
            ),
            plan.next_due_at,
            pause_until_resumed=True,
        )

    def _recent(
        self, user: User, limit: int, platform_settings: PlatformSettings
    ) -> list[RecentCheckIn]:
        """List a User's newest Check-in decisions with their statuses.

        Args:
            user: The User.
            limit: The most to list.
            platform_settings: Holds the reply window.

        Returns:
            Each Check-in and its status, newest first.
        """
        recent = self._repositories.check_ins.list_recent(user.id, limit)
        statuses = check_in_statuses(
            recent,
            self._clock.now(),
            platform_settings.get(CHECK_IN_REPLY_WINDOW),
        )
        return [
            RecentCheckIn(check_in=check_in, status=status)
            for check_in, status in zip(recent, statuses, strict=True)
        ]

    def _memory(self, user: User, platform_settings: PlatformSettings) -> str:
        """Write what is remembered about the User, for the Check-in model.

        Args:
            user: The User.
            platform_settings: Holds how many Day Summaries to give.

        Returns:
            Their User Portrait, Memory Items by active Memory Category and
            newest Day Summaries, even while User Memory is off; ""
            if nothing is remembered.
        """
        user_memory = self._repositories.user_memory
        portrait = self._repositories.user_portraits.find(user.id)
        categories = [
            category
            for category in self._repositories.memory_categories.list_all()
            if not category.archived
        ]
        return format_memory(
            categories,
            user_memory.list_items(user.id),
            user_memory.list_summaries(
                user.id, limit=platform_settings.get(RECENT_CONVERSATION_SUMMARIES)
            ),
            user.time_zone,
            MEMORY_INTRO,
            portrait=portrait.text if portrait is not None else "",
        )

    def _decide(
        self,
        snapshot: UserSnapshot,
        kinds: list[CheckInKind],
        shared_photos: list[SharedPhoto],
        due_curiosities: list[Curiosity],
        pattern_to_share: PatternToShare | None,
    ) -> CheckInDecision:
        """Ask the Check-in model to choose a Kind and write the message, or skip.

        Args:
            snapshot: The User it is for, with their local time, as read for
                this tick.
            kinds: The Check-in Kinds it may choose from.
            shared_photos: The User's Shared Photos it may send.
            due_curiosities: The User's due Curiosities it may ask.
            pattern_to_share: The ready Pattern its message tells them;
                None for none.

        Returns:
            The decision.

        Raises:
            InvalidCheckInAnswerError: If the answer can't be used.
        """
        settings = snapshot.settings
        user = snapshot.user
        description = describe_check_in(
            user,
            kinds,
            snapshot.local_now,
            describe_recent_check_ins(
                self._recent(user, CHECK_INS_TOLD_TO_MODEL, settings), user.time_zone
            ),
            self._memory(user, settings),
            describe_shared_photos(kinds, shared_photos, user.time_zone),
            describe_due_curiosities_for_check_in(kinds, due_curiosities),
            (
                format_pattern_to_share_for_check_in(
                    pattern_to_share, [kind.name for kind in kinds]
                )
                if pattern_to_share is not None
                else ""
            ),
        )
        answer = self._chat_model.generate(
            snapshot=snapshot,
            step=ModelStep.CHECK_IN,
            model=settings.get(CHECK_IN_MODEL),
            thinking=thinking_to_use(settings, CHECK_IN_MODEL, CHECK_IN_THINKING),
            instructions=f"{settings.get(PERSONA)}\n\n{settings.get(CHECK_IN_PROMPT)}",
            history=[ChatLine(role=ChatRole.USER, text=description)],
        )
        return read_check_in_decision(answer, kinds, shared_photos, due_curiosities)

    def _with_next_due_time(
        self, current: CheckInSettings, updated: CheckInSettings
    ) -> CheckInSettings:
        """Set the next due time and pause to fit changed settings.

        Args:
            current: The settings before the change.
            updated: The settings after the change.

        Returns:
            The updated settings with no due time or pause when off,
            otherwise with the due time from `next_due_after_change`. A
            Held-back Check-in's first Due Time is dropped when off, just
            turned on or the frequency changed, since the rhythm starts again.
            Turning them off also drops a waiting Check in Now; while one
            waits, they stay due now.
        """
        if not updated.enabled:
            return replace(
                updated,
                paused=False,
                paused_until=None,
                next_due_at=None,
                held_back_due_at=None,
                check_in_now=None,
            )
        starts_new_rhythm = (
            not current.enabled or current.frequency != updated.frequency
        )
        now = self._clock.now()
        return replace(
            updated,
            held_back_due_at=None if starts_new_rhythm else updated.held_back_due_at,
            next_due_at=(
                now
                if updated.check_in_now is not None
                else next_due_after_change(
                    current,
                    updated,
                    self._repositories.platform_settings.load().get(CHECK_IN_GAPS),
                    now,
                )
            ),
        )

    def _save(self, user: User, settings: CheckInSettings) -> User:
        """Save a User's new Check-in settings.

        A change that moves their Due Time ends any hold back: they are
        decided again now, or not due until later.

        Args:
            user: The User.
            settings: Their new Check-in settings.

        Returns:
            The saved User.
        """
        if settings.next_due_at != user.check_ins.next_due_at:
            settings = replace(settings, held_back=None)
        return self._repositories.users.update(replace(user, check_ins=settings))
