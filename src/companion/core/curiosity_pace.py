from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from companion.core.models import Curiosity, ThreadReaction

BRUSH_OFFS = {ThreadReaction.BRUSHED_OFF, ThreadReaction.ASKED_TO_DROP}


@dataclass(frozen=True)
class CuriosityPace:
    """The Admin-set numbers for how often Curiosities are asked.

    Attributes:
        replies_between: The fewest replies between two Curiosities.
        brush_offs_to_back_off: How many brush-offs in a row make Zeph back
            off.
        back_off_for: How long the spacing stays doubled after backing off.
    """

    replies_between: int
    brush_offs_to_back_off: int
    back_off_for: timedelta


def brush_offs_in_a_row(recently_raised: Sequence[Curiosity]) -> list[Curiosity]:
    """Find the Curiosities brushed off since the User last engaged with one.

    Asking to drop one counts as a brush-off. One whose reaction isn't known
    is skipped: it neither counts nor ends the run.

    Args:
        recently_raised: The Curiosities raised with the User, newest first.

    Returns:
        The brush-offs before the newest engaged answer, newest first.
    """
    streak = []
    for curiosity in recently_raised:
        if curiosity.reaction == ThreadReaction.ENGAGED:
            break
        if curiosity.reaction in BRUSH_OFFS:
            streak.append(curiosity)
    return streak


def backed_off_by(
    recently_raised: Sequence[Curiosity], pace: CuriosityPace
) -> Curiosity | None:
    """Find the brush-off that made Zeph back off, if it is backing off.

    Args:
        recently_raised: The Curiosities raised with the User, newest first.
        pace: The Admin-set numbers.

    Returns:
        The newest brush-off, when the brush-offs in a row reached the
        Admin-set number; None otherwise.
    """
    streak = brush_offs_in_a_row(recently_raised)
    return streak[0] if len(streak) >= pace.brush_offs_to_back_off else None


def replies_needed(
    recently_raised: Sequence[Curiosity], now: datetime, pace: CuriosityPace
) -> int:
    """Work out the fewest replies needed since the last Curiosity.

    Args:
        recently_raised: The Curiosities raised with the User, newest first.
        now: The current time.
        pace: The Admin-set numbers.

    Returns:
        The Admin-set number, doubled while Zeph backs off: from the brush-off
        that made it back off until the Admin-set time has passed.
    """
    brush_off = backed_off_by(recently_raised, pace)
    if (
        brush_off is not None
        and brush_off.raised_at is not None
        and now < brush_off.raised_at + pace.back_off_for
    ):
        return pace.replies_between * 2
    return pace.replies_between


def may_offer_curiosity(
    recently_raised: Sequence[Curiosity],
    conversation_id: UUID,
    replies_since_last: int | None,
    now: datetime,
    pace: CuriosityPace,
) -> bool:
    """Decide whether the pace lets a Curiosity be offered in this reply.

    Args:
        recently_raised: The Curiosities raised with the User, newest first.
        conversation_id: The Conversation being answered.
        replies_since_last: The replies made since the last Curiosity was
            raised, in any Conversation; None if none ever was.
        now: The current time.
        pace: The Admin-set numbers.

    Returns:
        False for the rest of a Conversation in which Zeph backed off, and
        until enough replies have passed since the last one; True otherwise.
    """
    brush_off = backed_off_by(recently_raised, pace)
    if brush_off is not None and brush_off.raised_conversation_id == conversation_id:
        return False
    if replies_since_last is None:
        return True
    return replies_since_last >= replies_needed(recently_raised, now, pace)


def may_offer_testing_the_water(raised_here: Sequence[Curiosity]) -> bool:
    """Decide whether a Need that tests the water may still ask a Curiosity.

    Args:
        raised_here: The Curiosities raised in this Conversation.

    Returns:
        True for the light opener, and while the User engaged with every one
        raised; False once one wasn't engaged with, or how they took it isn't
        known.
    """
    return all(
        curiosity.reaction == ThreadReaction.ENGAGED for curiosity in raised_here
    )
