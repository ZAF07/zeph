import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from companion.core.check_in_decision import next_due_after_decision
from companion.core.check_ins import (
    CHECK_INS_TOLD_TO_MODEL,
    MEMORY_INTRO,
    RecentCheckIn,
    check_in_statuses,
    describe_recent_check_ins,
)
from companion.core.life_threads import RemindedThread
from companion.core.memory_retrieval import SavedMemory, format_memory
from companion.core.model_call_log import ModelCallLog
from companion.core.models import (
    ChatLine,
    ChatRole,
    CheckIn,
    CheckInKind,
    CheckInNowRequest,
    CheckInOutcome,
    CheckInShape,
    ConversationMessage,
    Feature,
    MessageDirection,
    ModelStep,
    UnderstandingForm,
    UserSnapshot,
)
from companion.core.platform_settings import (
    CHECK_IN_GAPS,
    CHECK_IN_MODEL,
    CHECK_IN_REPLY_WINDOW,
    CHECK_IN_THINKING,
    PERSONA,
    WOVEN_CHECK_IN_PROMPT,
)
from companion.core.ports import Clock, Repositories
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WovenCheckIn:
    """A due Check-in the Check-in model chose to weave into this reply.

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
        True if the woven-in Check-in call may be made.
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
    Curiosities and sends Shared Photos back by its own rules.

    Args:
        kinds: Every Check-in Kind, in order.

    Returns:
        The Kinds that send no Shared Photo and ask no Curiosity.
    """
    return [
        kind
        for kind in kinds
        if not kind.sends_shared_photo and not kind.raises_curiosity
    ]


def describe_conversation_for_check_in(messages: Sequence[ConversationMessage]) -> str:
    """Write the current Conversation for the Check-in model.

    Args:
        messages: The Conversation's messages, oldest first.

    Returns:
        One line per message, saying who sent it.
    """
    return "\n".join(
        f"{'You' if message.direction == MessageDirection.OUTGOING else 'Them'}: "
        f"{message.content}"
        for message in messages
    )


def describe_understanding_for_check_in(
    form: UnderstandingForm,
    reminded: Sequence[RemindedThread],
    reply_asks_a_question: bool,
) -> str:
    """Write how the Companion read the newest Message, for the Check-in model.

    Args:
        form: This Message's Understanding.
        reminded: The Life Threads the Message reminded the Companion of.
        reply_asks_a_question: Whether the reply already asks them a
            question: through a Move that asks one, asking why or a
            Curiosity.

    Returns:
        The Need, mood, nuance, Life Threads reminded of, brought up and left
        alone, Curiosities to bring up, and whether the reply already asks
        a question.
    """
    lines = [
        f"What they need from you right now: {form.need}.",
        f"How they seem: {form.mood or 'unclear'} ({form.intensity.value}).",
    ]
    if form.nuance:
        lines.append(form.nuance)
    if reminded:
        titles = ", ".join(item.thread.title for item in reminded)
        lines.append(f"It reminded you of: {titles}.")
    if form.bring_up:
        titles = ", ".join(item.title for item in form.bring_up)
        lines.append(f"Your reply will bring up: {titles}.")
    if form.left_alone:
        left = "; ".join(f"{item.title} ({item.reason})" for item in form.left_alone)
        lines.append(f"You chose to leave alone: {left}.")
    if form.curiosities:
        questions = " ".join(item.question for item in form.curiosities)
        lines.append(f"Your reply will also ask: {questions}")
    if reply_asks_a_question:
        lines.append("Your reply already asks them a question.")
    return "\n".join(lines)


def describe_woven_check_in(
    snapshot: UserSnapshot,
    kinds: Sequence[CheckInKind],
    recent: str,
    memory: str,
    conversation: str,
    understanding: str,
) -> str:
    """Write what the Check-in model is told to decide on a woven-in Check-in.

    Args:
        snapshot: The User being answered, with their local time.
        kinds: The Check-in Kinds it may choose from.
        recent: The User's recent Check-ins, as lines.
        memory: What is remembered about the User; "" if nothing.
        conversation: The current Conversation, as lines.
        understanding: How the Companion read the newest Message.

    Returns:
        The Kinds, what to call the User, their local time, recent
        Check-ins, what is remembered, the Conversation and the
        Understanding.
    """
    kind_lines = "\n".join(f"- {kind.name}: {kind.description}" for kind in kinds)
    return (
        f"Check-in Kinds you may choose from:\n{kind_lines}\n\n"
        f"What to call them: {snapshot.user.name or 'unknown'}\n"
        f"Their local time: {snapshot.local_now.strftime('%A, %H:%M')}\n\n"
        f"Recent Check-ins, newest first:\n{recent}\n\n"
        f"{memory or 'Nothing remembered about them.'}\n\n"
        f"This Conversation so far, oldest first:\n{conversation}\n\n"
        f"How you read their newest message:\n{understanding}"
    )


def read_woven_check_in_answer(
    answer: str,
    kinds: Sequence[CheckInKind],
    due_at: datetime,
    check_in_now: CheckInNowRequest | None,
) -> WovenCheckIn | None:
    """Read the Check-in model's "weave in" or "not now" answer.

    Text around the JSON object, such as a code fence, is ignored. The Kind
    is matched by name, in any case, and must be one it was offered.

    Args:
        answer: The model's answer.
        kinds: The Check-in Kinds it could choose from.
        due_at: The User's Due Time as read for the reply.
        check_in_now: The Admin's Check in Now waiting; None for none.

    Returns:
        The Check-in to weave in; None for "not now", an unknown Kind, an
        empty note or an answer that can't be read.
    """
    start, end = answer.find("{"), answer.rfind("}")
    try:
        parsed = json.loads(answer[start : end + 1]) if 0 <= start < end else None
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or parsed.get("decision") != "weave_in":
        return None
    kind_name, note = parsed.get("kind"), parsed.get("note")
    if not isinstance(kind_name, str) or not isinstance(note, str) or not note.strip():
        return None
    kinds_by_name = {kind.name.lower(): kind for kind in kinds}
    kind = kinds_by_name.get(kind_name.strip().lower())
    if kind is None:
        return None
    return WovenCheckIn(
        kind=kind, note=note.strip(), due_at=due_at, check_in_now=check_in_now
    )


def format_woven_check_in_for_reply(woven: WovenCheckIn) -> str:
    """Write the reply's section on the Check-in to weave in.

    Args:
        woven: The Check-in to weave in.

    Returns:
        The section.
    """
    return (
        "A Check-in with them is due, and this is a good moment for it. Weave "
        "it into this reply naturally, once, the way a friend drifts onto a "
        "side topic, without saying it is a Check-in:\n"
        f"- {woven.kind.name}: {woven.kind.description} "
        f"What to bring up: {woven.note}"
    )


class WovenCheckIns:
    """Lets a reply weave in a Check-in that comes due mid-Conversation.

    After the Understanding, the Check-in model decides whether this reply
    weaves the Check-in in and which Kind, or leaves it for later. One woven
    in is saved before the reply goes, and taken back if the reply fails,
    so it is never sent twice and is only logged when it was sent.
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
            repositories: Where Check-ins, Conversations and settings are
                stored.
            chat_model: Makes the decision and records the tokens used.
            model_call_log: Records the shape of each decision.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._chat_model = chat_model
        self._model_call_log = model_call_log
        self._clock = clock

    def decide(
        self,
        snapshot: UserSnapshot,
        conversation_id: UUID,
        form: UnderstandingForm,
        saved: SavedMemory,
        reminded: Sequence[RemindedThread],
        reply_asks_a_question: bool,
    ) -> WovenCheckIn | None:
        """Ask the Check-in model whether this reply weaves in the due Check-in.

        No call is made unless `may_weave_check_in` allows it and a Kind may
        be woven in. Its shape goes into the Model Call Log. It never raises:
        a failed call or an answer that can't be used means "not now".

        Args:
            snapshot: The User being answered.
            conversation_id: The Conversation the Message is in.
            form: This Message's Understanding.
            saved: The User's saved memory, read for this reply.
            reminded: The Life Threads the Message reminded the Companion of.
            reply_asks_a_question: Whether the reply already asks them a
                question, so the model is told.

        Returns:
            The Check-in to weave in; None for "not now" or no call.
        """
        due_at = snapshot.user.check_ins.next_due_at
        if due_at is None or not may_weave_check_in(snapshot, form, self._clock.now()):
            return None
        kinds = kinds_to_weave_in(self._repositories.check_ins.list_kinds())
        if not kinds:
            return None
        settings = snapshot.settings
        try:
            answer = self._chat_model.generate(
                snapshot=snapshot,
                step=ModelStep.CHECK_IN,
                model=settings.get(CHECK_IN_MODEL),
                thinking=settings.get(CHECK_IN_THINKING),
                instructions=(
                    f"{settings.get(PERSONA)}\n\n{settings.get(WOVEN_CHECK_IN_PROMPT)}"
                ),
                history=[
                    ChatLine(
                        role=ChatRole.USER,
                        text=self._describe(
                            snapshot,
                            conversation_id,
                            kinds,
                            form,
                            saved,
                            reminded,
                            reply_asks_a_question,
                        ),
                    )
                ],
            )
        except Exception:
            logger.exception("The woven-in Check-in call failed; not now")
            return None
        woven = read_woven_check_in_answer(
            answer, kinds, due_at, snapshot.user.check_ins.check_in_now
        )
        self._model_call_log.record_check_in_shape(
            snapshot,
            CheckInShape(
                kinds_offered=len(kinds),
                woven_in=woven is not None,
                kind=woven.kind.name if woven is not None else None,
            ),
        )
        return woven

    def save(self, snapshot: UserSnapshot, woven: WovenCheckIn) -> CheckIn | None:
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
            The saved Check-in; None if it wasn't saved.
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
        return check_in if saved else None

    def take_back(
        self, snapshot: UserSnapshot, woven: WovenCheckIn, check_in: CheckIn
    ) -> None:
        """Take back a saved Woven-in Check-in whose reply was never sent.

        The User stays due at the Due Time read for the reply, and a Check
        in Now it was for waits again. It never raises: if taking it back
        fails, that Check-in is missed, not sent twice.

        Args:
            snapshot: The User being answered, as read for the reply, whose
                Due Time was due.
            woven: The Check-in that was to be woven in.
            check_in: The saved Check-in.
        """
        settings = snapshot.user.check_ins
        if settings.next_due_at is None:
            return
        try:
            self._repositories.check_ins.undo_add(
                check_in,
                settings.next_due_at,
                end_pause=False,
                skipped=None,
                held_back_due_at=settings.held_back_due_at,
                check_in_now=woven.check_in_now,
            )
        except Exception:
            logger.exception("Could not take back a Woven-in Check-in; it is missed")

    def _describe(
        self,
        snapshot: UserSnapshot,
        conversation_id: UUID,
        kinds: Sequence[CheckInKind],
        form: UnderstandingForm,
        saved: SavedMemory,
        reminded: Sequence[RemindedThread],
        reply_asks_a_question: bool,
    ) -> str:
        """Gather and write what the Check-in model is told.

        Args:
            snapshot: The User being answered.
            conversation_id: The Conversation the Message is in.
            kinds: The Check-in Kinds it may choose from.
            form: This Message's Understanding.
            saved: The User's saved memory, read for this reply.
            reminded: The Life Threads the Message reminded the Companion of.
            reply_asks_a_question: Whether the reply already asks them a
                question.

        Returns:
            The description.
        """
        user = snapshot.user
        recent = self._repositories.check_ins.list_recent(
            user.id, CHECK_INS_TOLD_TO_MODEL
        )
        statuses = check_in_statuses(
            recent, self._clock.now(), snapshot.settings.get(CHECK_IN_REPLY_WINDOW)
        )
        return describe_woven_check_in(
            snapshot,
            kinds,
            describe_recent_check_ins(
                [
                    RecentCheckIn(check_in=check_in, status=status)
                    for check_in, status in zip(recent, statuses, strict=True)
                ],
                user.time_zone,
            ),
            format_memory(
                saved.categories,
                saved.items,
                saved.summaries,
                user.time_zone,
                MEMORY_INTRO,
                portrait=saved.portrait,
            ),
            describe_conversation_for_check_in(
                self._repositories.conversations.list_messages(conversation_id)
            ),
            describe_understanding_for_check_in(form, reminded, reply_asks_a_question),
        )
