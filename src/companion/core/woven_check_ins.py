import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from companion.core.check_in_decision import next_due_after_decision
from companion.core.model_call_log import ModelCallLog
from companion.core.models import (
    ChatLine,
    ChatRole,
    CheckIn,
    CheckInKind,
    CheckInNowRequest,
    CheckInOutcome,
    CheckInShape,
    Feature,
    ModelStep,
    UnderstandingForm,
    UserSnapshot,
)
from companion.core.platform_settings import (
    CHECK_IN_GAPS,
    CHECK_IN_MODEL,
    thinking_for_model,
)
from companion.core.ports import Clock, Repositories
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

BROUGHT_UP_CHECK_PROMPT = (
    "You check whether a reply brought up a Check-in. You are given the "
    "Check-in (its Kind and what to bring up) and the reply as it will be "
    "sent. Answer yes if the reply brings it up in any way, even briefly or "
    "in other words. Answer no if it leaves it out. Answer with only yes or no."
)


@dataclass(frozen=True)
class WovenCheckIn:
    """A due Check-in the Reply Plan chose to offer this reply.

    Attributes:
        kind: The Check-in Kind to weave in.
        note: One line on what to bring up.
        due_at: The User's Due Time as read for the reply.
        check_in_now: The Admin's Check in Now it is for; None for a
            scheduled one.
    """

    kind: CheckInKind
    note: str
    due_at: datetime
    check_in_now: CheckInNowRequest | None = None


def may_weave_check_in(
    snapshot: UserSnapshot, form: UnderstandingForm, now: datetime
) -> bool:
    """Tell whether a reply may be offered the User's due Check-in.

    This is a rule, not a model choice: they must be opted in and onboarded
    and the Understanding must not find them struggling. Then either an
    Admin's Check in Now is waiting, which goes past the Feature switch and
    the pause, or their Check-in must be due, with the Feature on and not
    paused. Quiet Hours don't matter, since they are already talking.

    Args:
        snapshot: The User being answered, as read for the reply.
        form: This Message's Understanding.
        now: The current time.

    Returns:
        True if the Reply Plan may be offered Check-in Kinds.
    """
    settings = snapshot.user.check_ins
    if (
        not settings.enabled
        or not snapshot.user.has_finished_onboarding
        or form.struggling
    ):
        return False
    if settings.check_in_now is not None:
        return True
    return (
        snapshot.works(Feature.CHECK_INS)
        and settings.next_due_at is not None
        and settings.next_due_at <= now
        and not settings.is_paused_at(now)
    )


def kinds_to_weave_in(kinds: Sequence[CheckInKind]) -> list[CheckInKind]:
    """List the Check-in Kinds a reply may weave in.

    Kinds with fixed behaviour are left out: a reply already raises
    Curiosities, sends Shared Photos back and shares a ready Pattern by
    its own rules.

    Args:
        kinds: Every Check-in Kind, in order.

    Returns:
        The Kinds that send no Shared Photo, ask no Curiosity and share no
        Pattern.
    """
    return [kind for kind in kinds if not kind.has_fixed_behaviour]


@dataclass(frozen=True)
class SavedWovenCheckIn:
    """A Woven-in Check-in offered to a reply, with the row saved for it.

    Attributes:
        woven: The Check-in the reply was offered.
        check_in: The Check-in as saved before the reply, to take back if
            the reply leaves it out or fails.
    """

    woven: WovenCheckIn
    check_in: CheckIn


def describe_woven_check_in(woven: WovenCheckIn) -> str:
    """Write one line on a Woven-in Check-in: its Kind and what to bring up.

    Args:
        woven: The Check-in.

    Returns:
        E.g. "A follow-up: On something you shared. What to bring up: Ask
        how the interview went."
    """
    return f"{woven.kind.name}: {woven.kind.description} What to bring up: {woven.note}"


def format_woven_check_in_for_reply(woven: WovenCheckIn) -> str:
    """Write the reply's section on the due Check-in, as an optional extra.

    Args:
        woven: The Check-in the reply may bring up.

    Returns:
        The section, which says the reply may leave it out.
    """
    return (
        "A Check-in with them is due. Bring it up only if it fits what they "
        "need right now, once, the way a friend drifts onto a side topic, "
        "without saying it is a Check-in; if it doesn't fit, leave it out and "
        f"it will wait:\n- {describe_woven_check_in(woven)}"
    )


def describe_reply_for_brought_up_check(
    woven: WovenCheckIn, reply_parts: Sequence[str]
) -> str:
    """Write what the brought-up check is given: the Check-in and the reply.

    Args:
        woven: The Check-in the reply was offered.
        reply_parts: The reply's texts, in order.

    Returns:
        The Check-in's Kind, description and note, then the reply.
    """
    reply = "\n".join(reply_parts)
    return f"The Check-in: {describe_woven_check_in(woven)}\n\nThe reply:\n{reply}"


def read_brought_up_answer(answer: str) -> bool:
    """Read the brought-up check's yes or no.

    Args:
        answer: The model's answer.

    Returns:
        True only for an answer that starts with "yes", in any case.
    """
    return answer.strip().lower().startswith("yes")


class WovenCheckIns:
    """Lets a reply weave in a Check-in that comes due mid-Conversation.

    Code decides whether one may be offered, and lists the Kinds the Reply
    Plan weighs. One the Reply Plan chose is saved before the reply goes
    and reaches the reply as an optional extra. Once the reply is written,
    a small model call checks whether it brought the Check-in up; one it
    left out, or whose reply fails, is taken back, so it is only logged
    when it was sent and never sent twice.
    """

    def __init__(
        self,
        repositories: Repositories,
        chat_model: UsageRecordingChatModel,
        model_call_log: ModelCallLog,
        clock: Clock,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where Check-ins, Check-in Kinds and Users are
                stored.
            chat_model: Makes the brought-up check and records the tokens
                used.
            model_call_log: Records the shape of each check.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._chat_model = chat_model
        self._model_call_log = model_call_log
        self._clock = clock

    def kinds_to_offer(
        self, snapshot: UserSnapshot, understanding: UnderstandingForm
    ) -> list[CheckInKind]:
        """List the Check-in Kinds the Reply Plan may weave in, if one is due.

        Args:
            snapshot: The User being answered.
            understanding: This Message's Understanding.

        Returns:
            The Kinds without fixed behaviour; none unless
            `may_weave_check_in` allows it and the User has a Due Time.
        """
        if snapshot.user.check_ins.next_due_at is None or not may_weave_check_in(
            snapshot, understanding, self._clock.now()
        ):
            return []
        return kinds_to_weave_in(self._repositories.check_ins.list_kinds())

    def was_brought_up(
        self, snapshot: UserSnapshot, woven: WovenCheckIn, reply_parts: Sequence[str]
    ) -> bool:
        """Ask a small model call whether the reply brought the Check-in up.

        It uses the Check-in model, without thinking unless that model
        always thinks, and its shape goes into the Model Call Log. It never
        raises: a failed call counts as left out, so the Check-in is only
        logged when it is known to be sent.

        Args:
            snapshot: The User being answered.
            woven: The Check-in the reply was offered.
            reply_parts: The reply's texts, in order.

        Returns:
            True if the reply brought it up.
        """
        model = snapshot.settings.get(CHECK_IN_MODEL)
        try:
            answer = self._chat_model.generate(
                snapshot=snapshot,
                step=ModelStep.CHECK_IN,
                model=model,
                thinking=thinking_for_model(snapshot.settings, model, wanted=False),
                instructions=BROUGHT_UP_CHECK_PROMPT,
                history=[
                    ChatLine(
                        role=ChatRole.USER,
                        text=describe_reply_for_brought_up_check(woven, reply_parts),
                    )
                ],
            )
        except Exception:
            logger.exception("The brought-up check failed; taking the Check-in back")
            return False
        brought_up = read_brought_up_answer(answer)
        self._model_call_log.record_check_in_shape(
            snapshot, CheckInShape(kind=woven.kind.name, brought_up=brought_up)
        )
        return brought_up

    def save(
        self, snapshot: UserSnapshot, woven: WovenCheckIn
    ) -> SavedWovenCheckIn | None:
        """Save the Woven-in Check-in and move the Due Time on, before the reply goes.

        The next Due Time follows the same rules as a sent Check-in: one
        frequency gap from now for a Check in Now, which records the Admin
        who asked and is cleared. Nothing is saved if the User's Due Time
        changed since it was read. It never raises: a failed save means the
        reply weaves nothing in.

        Args:
            snapshot: The User being answered, as read for the reply.
            woven: The Check-in to weave in.

        Returns:
            The Check-in with its saved row; None if it wasn't saved.
        """
        settings = snapshot.user.check_ins
        now = self._clock.now()
        gap = snapshot.settings.get(CHECK_IN_GAPS)[settings.frequency]
        check_in_now = woven.check_in_now
        next_due_at = (
            now + gap
            if check_in_now is not None
            else next_due_after_decision(settings.rhythm_due_at, now, gap, now)
        )
        check_in = CheckIn(
            id=uuid4(),
            user_id=snapshot.user.id,
            outcome=CheckInOutcome.SENT,
            decided_at=now,
            kind_id=woven.kind.id,
            woven_in=True,
            requested_by=(
                check_in_now.requested_by if check_in_now is not None else None
            ),
        )
        try:
            saved = self._repositories.check_ins.add_woven_in(
                check_in, woven.due_at, next_due_at, check_in_now
            )
        except Exception:
            logger.exception("Could not save a Woven-in Check-in; not woven in")
            return None
        return SavedWovenCheckIn(woven, check_in) if saved else None

    def take_back(self, snapshot: UserSnapshot, saved: SavedWovenCheckIn) -> None:
        """Take back a saved Woven-in Check-in whose reply was never sent.

        The User stays due at the Due Time read for the reply, and a Check
        in Now it was for waits again. It never raises: if taking it back
        fails, that Check-in is missed, not sent twice.

        Args:
            snapshot: The User being answered, as read for the reply, whose
                Due Time was due.
            saved: The Check-in that was to be woven in, with its saved row.
        """
        settings = snapshot.user.check_ins
        if settings.next_due_at is None:
            return
        try:
            self._repositories.check_ins.undo_add(
                saved.check_in,
                settings.next_due_at,
                end_pause=False,
                skipped=None,
                held_back_due_at=settings.held_back_due_at,
                check_in_now=saved.woven.check_in_now,
            )
        except Exception:
            logger.exception("Could not take back a Woven-in Check-in; it is missed")
