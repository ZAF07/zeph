from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from companion.core.curiosity_pace import (
    CuriosityPace,
    brush_offs_in_a_row,
    may_offer_curiosity,
    replies_needed,
)
from companion.core.models import (
    Curiosity,
    CuriosityAim,
    CuriositySensitivity,
    CuriosityState,
    ThreadReaction,
)

NOW = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
PACE = CuriosityPace(
    replies_between=3, brush_offs_to_back_off=2, back_off_for=timedelta(days=3)
)
THIS_CONVERSATION = uuid4()
EARLIER_CONVERSATION = uuid4()
ENGAGED = ThreadReaction.ENGAGED
BRUSHED_OFF = ThreadReaction.BRUSHED_OFF
ASKED_TO_DROP = ThreadReaction.ASKED_TO_DROP


def raised(
    reaction: ThreadReaction | None,
    ago: timedelta = timedelta(hours=1),
    conversation_id: UUID = EARLIER_CONVERSATION,
) -> Curiosity:
    """A Curiosity raised some time ago, taken as given."""
    return Curiosity(
        id=uuid4(),
        user_id=uuid4(),
        question="How did the presentation go?",
        why="They were nervous.",
        not_before=None,
        sensitivity=CuriositySensitivity.LOW,
        state=CuriosityState.RAISED,
        created_at=NOW - ago - timedelta(days=1),
        aim=CuriosityAim.LOOK_BACK,
        raised_at=NOW - ago,
        raised_conversation_id=conversation_id,
        reaction=reaction,
    )


def test_brush_offs_in_a_row_stop_at_the_newest_engaged_answer() -> None:
    newest, older = raised(BRUSHED_OFF), raised(ASKED_TO_DROP)

    streak = brush_offs_in_a_row([newest, older, raised(ENGAGED), raised(BRUSHED_OFF)])

    assert streak == [newest, older]


def test_a_curiosity_whose_reaction_is_unknown_neither_counts_nor_breaks_a_streak() -> (
    None
):
    newest, older = raised(BRUSHED_OFF), raised(BRUSHED_OFF)

    assert brush_offs_in_a_row([newest, raised(None), older]) == [newest, older]


def test_with_nothing_raised_before_a_curiosity_may_be_offered() -> None:
    assert may_offer_curiosity([], THIS_CONVERSATION, None, NOW, PACE)


def test_no_curiosity_is_offered_until_the_set_number_of_replies_has_passed() -> None:
    history = [raised(ENGAGED)]

    assert not may_offer_curiosity(history, THIS_CONVERSATION, 2, NOW, PACE)
    assert may_offer_curiosity(history, THIS_CONVERSATION, 3, NOW, PACE)


def test_after_the_set_brush_offs_in_a_row_none_is_offered_for_the_rest_of_it() -> None:
    history = [
        raised(BRUSHED_OFF, conversation_id=THIS_CONVERSATION),
        raised(BRUSHED_OFF, ago=timedelta(days=1)),
    ]

    assert not may_offer_curiosity(history, THIS_CONVERSATION, 50, NOW, PACE)


def test_one_brush_off_short_of_the_set_number_only_keeps_the_normal_spacing() -> None:
    history = [raised(BRUSHED_OFF, conversation_id=THIS_CONVERSATION)]

    assert may_offer_curiosity(history, THIS_CONVERSATION, 3, NOW, PACE)
    assert replies_needed(history, NOW, PACE) == 3


def test_backing_off_doubles_the_spacing_in_later_conversations_for_the_set_time() -> (
    None
):
    history = [raised(BRUSHED_OFF, ago=timedelta(days=1)), raised(BRUSHED_OFF)]

    assert replies_needed(history, NOW, PACE) == 6
    assert not may_offer_curiosity(history, THIS_CONVERSATION, 5, NOW, PACE)
    assert may_offer_curiosity(history, THIS_CONVERSATION, 6, NOW, PACE)


def test_the_doubled_spacing_ends_once_the_set_time_has_passed() -> None:
    history = [
        raised(BRUSHED_OFF, ago=timedelta(days=3, minutes=1)),
        raised(BRUSHED_OFF, ago=timedelta(days=4)),
    ]

    assert replies_needed(history, NOW, PACE) == 3


def test_one_engaged_answer_returns_the_spacing_to_normal() -> None:
    history = [
        raised(ENGAGED, conversation_id=THIS_CONVERSATION),
        raised(BRUSHED_OFF, ago=timedelta(hours=2)),
        raised(BRUSHED_OFF, ago=timedelta(hours=3)),
    ]

    assert replies_needed(history, NOW, PACE) == 3
    assert may_offer_curiosity(history, THIS_CONVERSATION, 3, NOW, PACE)
