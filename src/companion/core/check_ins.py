import json
import logging
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from companion.core.check_in_decision import (
    AskAboutFewer,
    AskModel,
    CheckInFacts,
    CheckInPlan,
    CheckInRules,
    HoldBack,
    HoldBackReason,
    SkipForDailyLimit,
    decide_check_in,
    next_due_after_change,
    next_due_after_quiet_hours_move,
    retry_after_refusal,
)
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
    CheckInKind,
    CheckInLogEntry,
    CheckInOutcome,
    CheckInSettings,
    CheckInStatus,
    Feature,
    NextDueTimeChange,
    PauseLength,
    PlatformSettings,
    SharedPhoto,
    User,
    UserSnapshot,
)
from companion.core.platform_settings import (
    CHECK_IN_FEWER_MESSAGE,
    CHECK_IN_GAPS,
    CHECK_IN_IGNORE_THRESHOLD,
    CHECK_IN_MODEL,
    CHECK_IN_PROMPT,
    CHECK_IN_REPLY_WINDOW,
    CONVERSATION_QUIET_GAP,
    PERSONA,
    RECENT_CONVERSATION_SUMMARIES,
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
    """Work out the change to a held-back User's next due time.

    Args:
        user: The User, as read for this tick.
        plan: Why they are held back and until when.

    Returns:
        The change; None if their due time stays as it is.
    """
    read_as = user.check_ins.next_due_at
    if plan.retry_at == read_as:
        return None
    return NextDueTimeChange(user_id=user.id, read_as=read_as, becomes=plan.retry_at)


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
        user_snapshots: UserSnapshotLoader,
        chat_model: UsageRecordingChatModel,
        usage_limiter: UsageLimiter,
        chat_channel: ChatChannel,
        clock: Clock,
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
        """
        self._repositories = repositories
        self._features = features
        self._user_snapshots = user_snapshots
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
        recorded = record_where_changed(user, changed, in_chat, now)
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
        current = user.check_ins
        recorded = record_where_changed(
            user, [ChatSetting.CHECK_IN_PAUSE], in_chat, self._clock.now()
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
            [user.id for user in due_users], platform_settings
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
        """Save every held-back User's next due time, in one statement.

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
            kinds=tuple(self.list_kinds()),
        )

    def _gather_facts(
        self, snapshots: list[UserSnapshot], rules: CheckInRules
    ) -> list[CheckInFacts]:
        """Gather what is needed to decide on every due User's Check-in.

        Each kind of fact is read for all Users in one query, so the number
        of queries stays the same however many Users are due.

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
        newest_sent = repositories.check_ins.list_recent_for_users(
            user_ids, rules.ignore_threshold, sent_only=True
        )
        with_shared_photos = repositories.user_memory.list_users_with_shared_photos(
            user_ids
        )
        all_facts = []
        for snapshot in snapshots:
            user_id = snapshot.user.id
            connection = connections.get(user_id)
            conversation = conversations.get(user_id)
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
                        newest_sent.get(user_id, []),
                        conversation.started_at if conversation is not None else None,
                    ),
                    has_shared_photos=user_id in with_shared_photos,
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
            self._skip_for_daily_limit(snapshot.user, now)
        elif isinstance(plan, AskAboutFewer):
            self._ask_about_fewer(snapshot.user, plan, fewer_message, now)
        elif isinstance(plan, AskModel):
            self._check_in_with_model(snapshot, plan, now)

    def _check_in_with_model(
        self, snapshot: UserSnapshot, plan: AskModel, now: datetime
    ) -> None:
        """Let the Check-in model send a Kind and message, or skip.

        Kinds that send a Shared Photo come with the User's Shared Photos.
        The next attempt is one frequency gap later, unless the chat channel
        refuses the message.

        Args:
            snapshot: The User, as read for this tick.
            plan: The Kinds it may pick from, the chat, and the next due time.
            now: The current time.

        Raises:
            InvalidCheckInAnswerError: If the model's answer can't be used.
        """
        user = snapshot.user
        kinds = list(plan.kinds)
        shared_photos = (
            self._repositories.user_memory.list_shared_photos(user.id)
            if any(kind.sends_shared_photo for kind in kinds)
            else []
        )
        decision = self._decide(snapshot, kinds, shared_photos)
        if decision.kind is None:
            skipped = CheckIn(
                id=uuid4(),
                user_id=user.id,
                outcome=CheckInOutcome.SKIPPED,
                decided_at=now,
                skip_reason=decision.skip_reason,
            )
            self._repositories.check_ins.add(
                skipped, plan.next_due_at, pause_until_resumed=False
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
            plan.telegram_chat_id,
            decision.message,
            check_in,
            plan.next_due_at,
            pause_until_resumed=False,
        )
        if (
            was_sent
            and shared_photo is not None
            and not self._send_shared_photo(plan.telegram_chat_id, shared_photo)
        ):
            self._repositories.check_ins.remove_shared_photo(check_in.id)

    def _skip_for_daily_limit(self, user: User, now: datetime) -> None:
        """Record a Skipped Check-in for a User who used up today's daily message limit.

        The User stays due, so a Check-in can come on their next day.

        Args:
            user: A due User who has used up today's daily message limit.
            now: The current time.
        """
        skipped = CheckIn(
            id=uuid4(),
            user_id=user.id,
            outcome=CheckInOutcome.SKIPPED,
            decided_at=now,
            skip_reason=DAILY_LIMIT_SKIP_REASON,
        )
        self._repositories.check_ins.add(skipped, now, pause_until_resumed=False)

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
            retry_at = retry_after_refusal(check_in.decided_at)
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
            platform_settings: Holds how many Conversation Summaries to give.

        Returns:
            Their Memory Items by active Memory Category and their newest
            Conversation Summaries, even while User Memory is off; "" if
            nothing is remembered.
        """
        user_memory = self._repositories.user_memory
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
        )

    def _decide(
        self,
        snapshot: UserSnapshot,
        kinds: list[CheckInKind],
        shared_photos: list[SharedPhoto],
    ) -> CheckInDecision:
        """Ask the Check-in model to choose a Kind and write the message, or skip.

        Args:
            snapshot: The User it is for, with their local time, as read for
                this tick.
            kinds: The Check-in Kinds it may choose from.
            shared_photos: The User's Shared Photos it may send.

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
        )
        answer = self._chat_model.generate(
            snapshot=snapshot,
            model=settings.get(CHECK_IN_MODEL),
            instructions=f"{settings.get(PERSONA)}\n\n{settings.get(CHECK_IN_PROMPT)}",
            history=[ChatLine(role=ChatRole.USER, text=description)],
        )
        return read_check_in_decision(answer, kinds, shared_photos)

    def _with_next_due_time(
        self, current: CheckInSettings, updated: CheckInSettings
    ) -> CheckInSettings:
        """Set the next due time and pause to fit changed settings.

        Args:
            current: The settings before the change.
            updated: The settings after the change.

        Returns:
            The updated settings with no due time or pause when off,
            otherwise with the due time from `next_due_after_change`.
        """
        if not updated.enabled:
            return replace(updated, paused=False, paused_until=None, next_due_at=None)
        return replace(
            updated,
            next_due_at=next_due_after_change(
                current,
                updated,
                self._repositories.platform_settings.load().get(CHECK_IN_GAPS),
                self._clock.now(),
            ),
        )

    def _save(self, user: User, settings: CheckInSettings) -> User:
        """Save a User's new Check-in settings.

        Args:
            user: The User.
            settings: Their new Check-in settings.

        Returns:
            The saved User.
        """
        return self._repositories.users.update(replace(user, check_ins=settings))
