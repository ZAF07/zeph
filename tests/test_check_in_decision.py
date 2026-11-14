from dataclasses import replace
from datetime import UTC, datetime, time, timedelta
from typing import Any
from uuid import uuid4

import pytest

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
    next_due_after_check_in,
    next_due_after_quiet_hours_move,
)
from companion.core.features import feature_statuses, switches_for_everyone
from companion.core.models import (
    CheckInFrequency,
    CheckInKind,
    CheckInSettings,
    Conversation,
    Feature,
    FeatureSwitch,
    ModelCallTrace,
    PlatformSettings,
    TraceKind,
    User,
    UserSnapshot,
)
from companion.core.timing import local_now, users_today

NOW = datetime(2026, 11, 14, 9, 0, tzinfo=UTC)
WAS_DUE_AT = NOW - timedelta(minutes=3)
CHAT_ID = 42
HELLO = CheckInKind(id=uuid4(), name="A casual hello", description="Hi", sort_order=0)
PHOTO_LOOK_BACK = CheckInKind(
    id=uuid4(),
    name="A look back",
    description="A photo they shared",
    sort_order=1,
    sends_shared_photo=True,
)
GAPS = {
    CheckInFrequency.WEEKLY: timedelta(hours=168),
    CheckInFrequency.FEW_TIMES_A_WEEK: timedelta(hours=48),
    CheckInFrequency.MOST_DAYS: timedelta(hours=24),
}
QUIET_GAP = timedelta(minutes=30)
RULES = CheckInRules(
    frequency_gaps=GAPS,
    quiet_gap=QUIET_GAP,
    ignore_threshold=3,
    kinds=(HELLO, PHOTO_LOOK_BACK),
)
NEXT_GAP = NOW + timedelta(hours=24)


def facts(
    now: datetime = NOW,
    time_zone: str = "Asia/Singapore",
    admin_off: tuple[Feature, ...] = (),
    **changes: Any,
) -> CheckInFacts:
    """Build a due User's facts; by default nothing holds the Check-in back.

    The User has Check-ins on "most days" with Quiet Hours 22:00 to 07:30.
    NOW is 17:00 in Singapore.

    Args:
        now: When the tick runs.
        time_zone: The User's time zone.
        admin_off: Features the Admin side has off for everyone.
        **changes: Check-in settings (`check_ins`), User fields (`user`) or
            other facts to change.

    Returns:
        The facts.
    """
    check_ins = CheckInSettings(
        enabled=True,
        frequency=CheckInFrequency.MOST_DAYS,
        next_due_at=WAS_DUE_AT,
    )
    check_ins = replace(check_ins, **changes.pop("check_ins", {}))
    user = User(
        id=uuid4(),
        auth_id="user_maya",
        email="maya@example.com",
        created_at=NOW - timedelta(days=30),
        name="Maya",
        time_zone=time_zone,
        check_ins=check_ins,
    )
    user = replace(user, **changes.pop("user", {}))
    everyone = switches_for_everyone(
        [
            FeatureSwitch(
                feature=feature, on=False, changed_by_email=None, changed_at=None
            )
            for feature in admin_off
        ]
    )
    snapshot = UserSnapshot(
        user=user,
        local_now=local_now(user.time_zone, now),
        today=users_today(user.time_zone, now),
        features=tuple(feature_statuses(user, everyone, [])),
        settings=PlatformSettings({}),
        trace=ModelCallTrace(id=uuid4(), kind=TraceKind.MESSAGE),
    )
    defaults: dict[str, Any] = {
        "telegram_chat_id": CHAT_ID,
        "latest_conversation": None,
        "used_up_daily_message_limit": False,
        "limit_skip_today": False,
        "ignored_in_a_row": 0,
        "has_shared_photos": False,
    }
    return CheckInFacts(snapshot=snapshot, **(defaults | changes))


def conversation(last_message_at: datetime, ended: bool = False) -> Conversation:
    """Build a Conversation whose newest message was at a time.

    Args:
        last_message_at: When its newest message was sent.
        ended: Whether the scheduler ended it already.

    Returns:
        The Conversation.
    """
    return Conversation(
        id=uuid4(),
        user_id=uuid4(),
        started_at=last_message_at - timedelta(minutes=10),
        last_message_at=last_message_at,
        ended_at=last_message_at + QUIET_GAP if ended else None,
    )


def at_singapore_time(hour: int, minute: int = 0, days: int = 0) -> datetime:
    """Give the UTC time for a time of day in Singapore, from NOW's day.

    Args:
        hour: The hour in Singapore.
        minute: The minute in Singapore.
        days: Days after NOW's day.

    Returns:
        The time in UTC.
    """
    return datetime(2026, 11, 14 + days, hour, minute, tzinfo=UTC) - timedelta(hours=8)


ASK_MODEL = AskModel(kinds=(HELLO,), telegram_chat_id=CHAT_ID, next_due_at=NEXT_GAP)


@pytest.mark.parametrize(
    ("user_facts", "now", "expected"),
    [
        pytest.param(facts(), NOW, ASK_MODEL, id="nothing holds it back"),
        pytest.param(
            facts(check_ins={"enabled": False}),
            NOW,
            HoldBack(HoldBackReason.CHECK_INS_OFF, retry_at=WAS_DUE_AT),
            id="off by the User: stays due",
        ),
        pytest.param(
            facts(admin_off=(Feature.CHECK_INS,)),
            NOW,
            HoldBack(HoldBackReason.CHECK_INS_OFF, retry_at=WAS_DUE_AT),
            id="off on the Admin side: stays due",
        ),
        pytest.param(
            facts(check_ins={"paused": True}),
            NOW,
            HoldBack(HoldBackReason.PAUSED, retry_at=None),
            id="paused until resumed: no due time",
        ),
        pytest.param(
            facts(check_ins={"paused": True, "paused_until": NOW + timedelta(hours=5)}),
            NOW,
            HoldBack(HoldBackReason.PAUSED, retry_at=NOW + timedelta(hours=5)),
            id="paused until a time: due then",
        ),
        pytest.param(
            facts(check_ins={"paused": True, "paused_until": NOW}),
            NOW,
            ASK_MODEL,
            id="a timed pause ending now is over",
        ),
        pytest.param(
            facts(
                now=at_singapore_time(23),
                check_ins={"paused": True, "paused_until": NOW + timedelta(hours=10)},
            ),
            at_singapore_time(23),
            HoldBack(HoldBackReason.PAUSED, retry_at=NOW + timedelta(hours=10)),
            id="paused and in Quiet Hours: the pause comes first",
        ),
        pytest.param(
            facts(now=at_singapore_time(23)),
            at_singapore_time(23),
            HoldBack(HoldBackReason.QUIET_HOURS, retry_at=at_singapore_time(7, 30, 1)),
            id="Quiet Hours before midnight: due when they end tomorrow",
        ),
        pytest.param(
            facts(now=at_singapore_time(3)),
            at_singapore_time(3),
            HoldBack(HoldBackReason.QUIET_HOURS, retry_at=at_singapore_time(7, 30)),
            id="Quiet Hours after midnight: due when they end today",
        ),
        pytest.param(
            facts(now=at_singapore_time(22)),
            at_singapore_time(22),
            HoldBack(HoldBackReason.QUIET_HOURS, retry_at=at_singapore_time(7, 30, 1)),
            id="Quiet Hours start",
        ),
        pytest.param(
            facts(now=at_singapore_time(21, 59)),
            at_singapore_time(21, 59),
            replace(ASK_MODEL, next_due_at=at_singapore_time(21, 59, 1)),
            id="a minute before Quiet Hours",
        ),
        pytest.param(
            facts(now=at_singapore_time(7, 30)),
            at_singapore_time(7, 30),
            replace(ASK_MODEL, next_due_at=at_singapore_time(7, 30, 1)),
            id="Quiet Hours end",
        ),
        pytest.param(
            facts(
                check_ins={"quiet_hours_start": time(13), "quiet_hours_end": time(18)}
            ),
            NOW,
            HoldBack(HoldBackReason.QUIET_HOURS, retry_at=at_singapore_time(18)),
            id="Quiet Hours within one day",
        ),
        pytest.param(
            facts(
                check_ins={"quiet_hours_start": time(17), "quiet_hours_end": time(17)}
            ),
            NOW,
            ASK_MODEL,
            id="Quiet Hours starting and ending together are none",
        ),
        pytest.param(
            facts(user={"time_zone": None}, now=NOW - timedelta(hours=6)),
            NOW - timedelta(hours=6),
            HoldBack(
                HoldBackReason.QUIET_HOURS,
                retry_at=NOW - timedelta(hours=1, minutes=30),
            ),
            id="Quiet Hours in UTC for a User with no time zone",
        ),
        pytest.param(
            facts(telegram_chat_id=None),
            NOW,
            HoldBack(HoldBackReason.NO_TELEGRAM_CONNECTION, retry_at=None),
            id="no Telegram Connection: no due time",
        ),
        pytest.param(
            facts(latest_conversation=conversation(NOW - timedelta(minutes=10))),
            NOW,
            HoldBack(
                HoldBackReason.IN_CONVERSATION,
                retry_at=NOW - timedelta(minutes=10) + QUIET_GAP,
            ),
            id="mid-Conversation: due when it could end",
        ),
        pytest.param(
            facts(latest_conversation=conversation(NOW - QUIET_GAP)),
            NOW,
            ASK_MODEL,
            id="the quiet gap has passed",
        ),
        pytest.param(
            facts(
                latest_conversation=conversation(NOW - timedelta(minutes=5), ended=True)
            ),
            NOW,
            ASK_MODEL,
            id="the Conversation was ended",
        ),
        pytest.param(
            facts(used_up_daily_message_limit=True),
            NOW,
            SkipForDailyLimit(),
            id="daily limit used up",
        ),
        pytest.param(
            facts(used_up_daily_message_limit=True, limit_skip_today=True),
            NOW,
            HoldBack(HoldBackReason.LIMIT_SKIP_DONE_TODAY, retry_at=WAS_DUE_AT),
            id="daily limit used up, already skipped today: stays due",
        ),
        pytest.param(
            facts(used_up_daily_message_limit=True, ignored_in_a_row=3),
            NOW,
            SkipForDailyLimit(),
            id="the daily limit comes before asking about fewer",
        ),
        pytest.param(
            facts(ignored_in_a_row=3),
            NOW,
            AskAboutFewer(telegram_chat_id=CHAT_ID, next_due_at=NEXT_GAP),
            id="ignored the threshold in a row",
        ),
        pytest.param(facts(ignored_in_a_row=2), NOW, ASK_MODEL, id="ignored one fewer"),
        pytest.param(
            facts(has_shared_photos=True),
            NOW,
            replace(ASK_MODEL, kinds=(HELLO, PHOTO_LOOK_BACK)),
            id="Shared Photos: photo Kinds offered",
        ),
        pytest.param(
            facts(has_shared_photos=True, user={"photo_viewing_enabled": False}),
            NOW,
            ASK_MODEL,
            id="Shared Photos with Photo Viewing off: no photo Kinds",
        ),
        pytest.param(
            facts(has_shared_photos=True, user={"user_memory_enabled": False}),
            NOW,
            replace(ASK_MODEL, kinds=(HELLO, PHOTO_LOOK_BACK)),
            id="User Memory off: every Kind still offered",
        ),
        pytest.param(
            facts(check_ins={"frequency": CheckInFrequency.WEEKLY}),
            NOW,
            replace(ASK_MODEL, next_due_at=NOW + timedelta(hours=168)),
            id="next due one frequency gap later",
        ),
    ],
)
def test_decide_check_in(
    user_facts: CheckInFacts, now: datetime, expected: CheckInPlan
) -> None:
    assert decide_check_in(user_facts, RULES, now) == expected


def test_with_no_kind_that_may_be_sent_the_user_stays_due() -> None:
    only_photo_kinds = replace(RULES, kinds=(PHOTO_LOOK_BACK,))

    assert decide_check_in(facts(), only_photo_kinds, NOW) == HoldBack(
        HoldBackReason.NO_KIND_TO_SEND, retry_at=WAS_DUE_AT
    )


def test_next_due_after_check_in_is_one_frequency_gap_later() -> None:
    assert next_due_after_check_in(CheckInFrequency.FEW_TIMES_A_WEEK, GAPS, NOW) == (
        NOW + timedelta(hours=48)
    )


ON = CheckInSettings(
    enabled=True,
    frequency=CheckInFrequency.MOST_DAYS,
    next_due_at=NOW + timedelta(hours=10),
)
PAUSE_END = NOW + timedelta(days=3)


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        pytest.param(
            CheckInSettings(),
            replace(CheckInSettings(), enabled=True),
            NOW + timedelta(hours=48),
            id="turned on: one gap from now",
        ),
        pytest.param(
            ON,
            replace(ON, frequency=CheckInFrequency.WEEKLY),
            NOW + timedelta(hours=168),
            id="frequency changed: one gap from now",
        ),
        pytest.param(ON, replace(ON, enabled=False), None, id="turned off: none"),
        pytest.param(
            ON,
            replace(ON, quiet_hours_start=time(23)),
            ON.next_due_at,
            id="Quiet Hours changed: kept",
        ),
        pytest.param(
            ON,
            replace(ON, paused=True, paused_until=PAUSE_END),
            ON.next_due_at,
            id="paused: kept",
        ),
        pytest.param(
            replace(ON, paused=True, next_due_at=None),
            replace(ON, next_due_at=None),
            NOW,
            id="resumed after being held back with no due time: now",
        ),
        pytest.param(
            replace(ON, paused=True, paused_until=PAUSE_END, next_due_at=PAUSE_END),
            replace(ON, next_due_at=PAUSE_END),
            NOW,
            id="resumed early after being held back to the pause end: now",
        ),
        pytest.param(
            replace(ON, paused=True, paused_until=PAUSE_END),
            ON,
            ON.next_due_at,
            id="resumed before it was ever held back: kept",
        ),
        pytest.param(
            replace(ON, paused=True, next_due_at=None),
            replace(ON, paused=True, paused_until=PAUSE_END, next_due_at=None),
            NOW,
            id="pause until resumed changed to a timed pause: now",
        ),
        pytest.param(
            replace(ON, paused=True, paused_until=PAUSE_END, next_due_at=PAUSE_END),
            replace(
                ON,
                paused=True,
                paused_until=NOW + timedelta(days=1),
                next_due_at=PAUSE_END,
            ),
            NOW,
            id="a shorter timed pause: now",
        ),
        pytest.param(
            replace(ON, paused=True, next_due_at=None),
            replace(ON, paused=True, quiet_hours_end=time(8), next_due_at=None),
            None,
            id="other changes while paused until resumed: still none",
        ),
        pytest.param(
            replace(ON, paused=True, next_due_at=NOW - timedelta(minutes=1)),
            replace(ON, next_due_at=NOW - timedelta(minutes=1)),
            NOW,
            id="resumed after the due time passed, while a tick holds it back: now",
        ),
    ],
)
def test_next_due_after_change(
    before: CheckInSettings, after: CheckInSettings, expected: datetime | None
) -> None:
    assert next_due_after_change(before, after, GAPS, NOW) == expected


HELD_TO_QUIET_HOURS_END = replace(ON, next_due_at=at_singapore_time(7, 30, 1))


@pytest.mark.parametrize(
    ("before", "time_zone", "now", "expected"),
    [
        pytest.param(
            HELD_TO_QUIET_HOURS_END,
            "Asia/Singapore",
            at_singapore_time(23),
            at_singapore_time(23),
            id="held back until Quiet Hours end: now",
        ),
        pytest.param(
            HELD_TO_QUIET_HOURS_END,
            "Asia/Singapore",
            at_singapore_time(17),
            HELD_TO_QUIET_HOURS_END.next_due_at,
            id="outside Quiet Hours, due later: kept",
        ),
        pytest.param(
            HELD_TO_QUIET_HOURS_END,
            "Europe/London",
            at_singapore_time(23),
            HELD_TO_QUIET_HOURS_END.next_due_at,
            id="the due time isn't when Quiet Hours end there: kept",
        ),
        pytest.param(
            replace(ON, next_due_at=NOW - timedelta(minutes=1)),
            "Asia/Singapore",
            NOW,
            NOW,
            id="the due time passed: now",
        ),
        pytest.param(
            replace(ON, next_due_at=None),
            "Asia/Singapore",
            NOW,
            None,
            id="no due time: still none",
        ),
    ],
)
def test_next_due_after_quiet_hours_move(
    before: CheckInSettings,
    time_zone: str,
    now: datetime,
    expected: datetime | None,
) -> None:
    assert next_due_after_quiet_hours_move(before, time_zone, now) == expected
