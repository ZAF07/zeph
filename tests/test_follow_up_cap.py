from datetime import UTC, datetime
from uuid import uuid4

from companion.core.models import Move, ReplyPlan, ReplyPlanForm
from companion.core.reply_plan import follow_ups_made, moves_within_follow_up_cap

GET_CURIOUS = Move(
    id=uuid4(),
    name="Get curious",
    when_it_fits="They mention something you know little about.",
    how_to_do_it="Ask one open question.",
    sort_order=1,
    needed_feature=None,
    asks_a_question=True,
)
MIRROR = Move(
    id=uuid4(),
    name="Mirror",
    when_it_fits="They are venting.",
    how_to_do_it="Say back what you heard.",
    sort_order=2,
    needed_feature=None,
)


def earlier_plan(lead: str | None, support: str | None = None) -> ReplyPlan:
    """An earlier Reply Plan in the Conversation, with its Moves."""
    return ReplyPlan(
        id=uuid4(),
        user_id=uuid4(),
        conversation_id=uuid4(),
        message_id=uuid4(),
        form=ReplyPlanForm(need="Just chatting"),
        need="Just chatting",
        asked_why=False,
        made_at=datetime(2026, 11, 24, tzinfo=UTC),
        lead_move=lead,
        support_move=support,
    )


def test_follow_ups_made_count_replies_whose_lead_or_support_asks_a_question() -> None:
    earlier = [
        earlier_plan("Get curious"),
        earlier_plan("Mirror"),
        earlier_plan("Mirror", "get curious"),
        earlier_plan(None),
    ]

    assert follow_ups_made([GET_CURIOUS, MIRROR], earlier) == 2


def test_question_asking_moves_are_offered_until_the_cap_is_reached() -> None:
    two_made = [earlier_plan("Get curious"), earlier_plan("Mirror", "Get curious")]

    assert moves_within_follow_up_cap([GET_CURIOUS, MIRROR], two_made, 3) == [
        GET_CURIOUS,
        MIRROR,
    ]
    assert moves_within_follow_up_cap(
        [GET_CURIOUS, MIRROR], [*two_made, earlier_plan("Get curious")], 3
    ) == [MIRROR]


def test_a_cap_of_zero_offers_no_question_asking_move() -> None:
    assert moves_within_follow_up_cap([GET_CURIOUS, MIRROR], [], 0) == [MIRROR]
