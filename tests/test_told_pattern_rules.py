from dataclasses import replace
from datetime import timedelta
from uuid import uuid4

from companion.core.models import (
    CatalogPattern,
    LifeThread,
    NarrowingTag,
    ObservationDirection,
    PatternNarrowing,
    PatternState,
    Prediction,
)
from companion.core.told_patterns import told_patterns, was_told, where_it_shows
from tests.test_ready_gate_rules import (
    BELONG,
    NOW,
    PATTERN_TYPES,
    TODAY,
    WORTH,
    story,
)


def told(
    state: PatternState, days_ago: int = 0, pattern_type: str = BELONG
) -> CatalogPattern:
    """A Pattern the User was told some days ago, now in the given state."""
    return CatalogPattern(
        id=uuid4(),
        user_id=uuid4(),
        pattern_type_id=pattern_type,
        state=state,
        started_at=NOW,
        updated_at=NOW,
        shared_at=NOW - timedelta(days=days_ago),
    )


def thread(title: str) -> LifeThread:
    """A Life Thread with the given title."""
    return LifeThread(
        id=uuid4(),
        user_id=uuid4(),
        title=title,
        story="",
        people=(),
        is_open=True,
        started_at=NOW,
        updated_at=NOW,
    )


def test_only_a_pattern_the_user_was_told_may_be_seen() -> None:
    seen = {state: was_told(told(state)) for state in PatternState}
    never_shared = replace(told(PatternState.CLOSED), shared_at=None)

    assert [state.value for state, shown in seen.items() if shown] == [
        "shared",
        "confirmed",
        "contested",
        "closed",
    ]
    assert was_told(never_shared) is False


def test_patterns_come_tested_first_then_confirmed_disagreed_and_closed() -> None:
    closed = told(PatternState.CLOSED)
    contested = told(PatternState.CONTESTED)
    confirmed = told(PatternState.CONFIRMED)
    older = told(PatternState.SHARED, days_ago=9)
    newer = told(PatternState.SHARED, days_ago=1, pattern_type=WORTH)
    gone_from_catalog = told(PatternState.SHARED, pattern_type="NOT.IN.CATALOG")

    shown = told_patterns(
        [closed, older, gone_from_catalog, contested, newer, confirmed],
        PATTERN_TYPES,
        [],
        [],
        [],
    )

    assert [entry.pattern for entry in shown] == [
        newer,
        older,
        confirmed,
        contested,
        closed,
    ]
    assert shown[0].wording == PATTERN_TYPES[WORTH].approved_wording


def test_quotes_are_grouped_by_life_thread_newest_first_and_no_thread_last() -> None:
    mei, work = thread("Falling-out with Mei"), thread("New manager")
    old_mei = replace(
        story(thread=mei.id, quote="old Mei"), day=TODAY - timedelta(days=5)
    )
    new_mei = replace(
        story(thread=mei.id, quote="new Mei"), day=TODAY - timedelta(days=2)
    )
    at_work = replace(story(thread=work.id, quote="work"), day=TODAY)
    no_thread = replace(story(quote="Jun"), thread_id=None, day=TODAY)
    against = story(
        thread=mei.id, quote="said no", direction=ObservationDirection.AGAINST
    )
    unclear = story(thread=mei.id, quote="could be either", second=WORTH)

    [shown] = told_patterns(
        [told(PatternState.SHARED)],
        PATTERN_TYPES,
        [old_mei, no_thread, against, at_work, unclear, new_mei],
        [],
        [mei, work],
    )

    assert [
        (group.life_thread, [quote.quote for quote in group.quotes])
        for group in shown.quote_groups
    ] == [
        ("New manager", ["work"]),
        ("Falling-out with Mei", ["new Mei", "old Mei"]),
        (None, ["Jun"]),
    ]


def test_a_pattern_shows_its_own_predictions_newest_first() -> None:
    pattern = told(PatternState.SHARED)

    def prediction(wording: str, days_ago: int, pattern_id: object) -> Prediction:
        return Prediction(
            id=uuid4(),
            user_id=pattern.user_id,
            pattern_id=pattern_id,  # type: ignore[arg-type]
            wording=wording,
            made_at=NOW - timedelta(days=days_ago),
        )

    [shown] = told_patterns(
        [pattern],
        PATTERN_TYPES,
        [],
        [
            prediction("first", 8, pattern.id),
            prediction("another Pattern's", 4, uuid4()),
            prediction("second", 1, pattern.id),
        ],
        [],
    )

    assert [entry.wording for entry in shown.predictions] == ["second", "first"]


def test_where_it_shows_is_said_to_the_user() -> None:
    pattern = replace(
        told(PatternState.SHARED),
        narrowings=(
            PatternNarrowing(NarrowingTag.RELATIONSHIP, ("family",), ("partner",)),
            PatternNarrowing(NarrowingTag.POWER, ("above",), ("equal", "below")),
        ),
    )

    shown = where_it_shows(pattern)

    assert [(where.shows_with, where.not_with) for where in shown] == [
        (("family",), ("partner",)),
        (("people above you",), ("your equals", "people below you")),
    ]
