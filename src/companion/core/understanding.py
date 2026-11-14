import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from companion.core.life_threads import (
    RemindedThread,
    describe_reminded_threads,
    format_threads_for_reply,
)
from companion.core.memory_retrieval import SavedMemory, format_day
from companion.core.models import (
    BringUpWay,
    ChatLine,
    ChatRole,
    ConversationMessage,
    MessageDirection,
    ModelStep,
    MoodIntensity,
    Need,
    ThreadLeftAlone,
    ThreadToBringUp,
    Understanding,
    UnderstandingForm,
    UserSnapshot,
)
from companion.core.platform_settings import (
    HOME_GOALS_MEMORY_CATEGORY,
    REPLY_ASK_WHY_NOTE,
    UNDERSTANDING_MODEL,
    UNDERSTANDING_PROMPT,
)
from companion.core.ports import Clock, Repositories
from companion.core.transcripts import split_off_latest_message, to_transcript_lines
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

LIST_FIELDS = ("memory_categories", "look_up_past", "knowledge")


@dataclass(frozen=True)
class UnderstoodMessage:
    """A Message's saved Understanding, and what it tells the reply.

    Attributes:
        understanding: The Understanding, as saved.
        reply_guidance: The section of the reply instructions it adds: the
            Need's "how to reply", the nuance and mood, the "ask why" note
            when it applies, and the Life Threads to bring up or leave alone.
    """

    understanding: Understanding
    reply_guidance: str


def format_local_time(local_now: datetime) -> str:
    """Write the weekday, day and time, e.g. "Wednesday 11 Nov 2026, 17:00".

    Args:
        local_now: The time where the User lives.

    Returns:
        The time.
    """
    return f"{local_now:%A} {format_day(local_now, None)}, {local_now:%H:%M}"


def format_earlier_understanding(understanding: Understanding) -> str:
    """Write one earlier Understanding as the next Understanding reads it.

    Args:
        understanding: The earlier Understanding.

    Returns:
        E.g. "- Need: Be heard; mood: furious (high); cause known: no;
        asked why: no. They want to vent about their boss."
    """
    form = understanding.form
    cause_known = "yes" if form.cause_known else "no"
    asked_why = "yes" if understanding.asked_why else "no"
    line = (
        f"- Need: {understanding.need}; mood: {form.mood or 'unclear'} "
        f"({form.intensity.value}); cause known: {cause_known}; "
        f"asked why: {asked_why}."
    )
    return f"{line} {form.nuance}" if form.nuance else line


def describe_message_for_understanding(
    snapshot: UserSnapshot,
    needs: Sequence[Need],
    saved: SavedMemory,
    earlier: Sequence[Understanding],
    messages: list[ConversationMessage],
    reminded: Sequence[RemindedThread],
) -> str:
    """Write what the Understanding model is given about the Message.

    Args:
        snapshot: The User being answered.
        needs: Every Need, in order.
        saved: The User's saved memory, read for this reply.
        earlier: This Conversation's earlier Understandings, oldest first.
        messages: The Conversation so far, oldest first; the User's messages
            at the end are the Message being answered.
        reminded: The Life Threads the Message reminds the Companion of.

    Returns:
        The time, Needs, Goals, Memory Categories, recent Conversations,
        reminded Life Threads, earlier Understandings, earlier Conversation
        and latest message.
    """
    fallback = fallback_need(needs)
    need_lines = "\n".join(f"- {need.name}: {need.when_it_fits}" for need in needs)
    goals = saved.items_in(snapshot.settings.get(HOME_GOALS_MEMORY_CATEGORY))
    goal_lines = "\n".join(f"- {item.content}" for item in goals)
    category_lines = "\n".join(
        f"- {category.name}: {category.description}" for category in saved.pickable
    )
    summary_lines = "\n".join(
        f"- {format_day(summary.created_at, snapshot.user.time_zone)}: "
        f"{summary.summary} They seemed {summary.mood}."
        for summary in saved.summaries
    )
    earlier_lines = "\n".join(
        format_earlier_understanding(understanding) for understanding in earlier
    )
    earlier_messages, latest_text = split_off_latest_message(messages)
    return (
        f"Time where they are: {format_local_time(snapshot.local_now)}\n\n"
        f"Needs:\n{need_lines}\n"
        f"Fallback Need: {fallback.name}\n\n"
        f"Their Goals:\n{goal_lines or 'None saved.'}\n\n"
        f"Memory Categories with something saved:\n{category_lines or 'None yet.'}"
        f"\n\nRecent Conversations, newest first:\n{summary_lines or 'None yet.'}"
        f"\n\nLife Threads this reminds you of, open ones first:\n"
        f"{describe_reminded_threads(reminded, snapshot.user.time_zone)}"
        f"\n\nEarlier Understandings in this Conversation, oldest first:\n"
        f"{earlier_lines or 'None yet.'}\n\n"
        f"Earlier in the Conversation:\n"
        f"{to_transcript_lines(earlier_messages) or 'Nothing yet.'}\n\n"
        f"Latest message:\nPerson: {latest_text}"
    )


def read_text_list(value: Any) -> tuple[str, ...]:
    """Read a list of texts from the form, keeping only non-empty texts.

    Args:
        value: The field's value.

    Returns:
        The texts without surrounding spaces; none if it isn't a list.
    """
    if not isinstance(value, list):
        return ()
    return tuple(
        item.strip() for item in value if isinstance(item, str) and item.strip()
    )


def read_thread(
    value: Any, by_number: dict[int, RemindedThread]
) -> RemindedThread | None:
    """Find the reminded Thread a number in the form names.

    Args:
        value: The number, as the model wrote it.
        by_number: The reminded Threads, by number.

    Returns:
        The Thread; None if the value isn't one of their numbers.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return by_number.get(value)


def read_threads_touched(
    value: Any, by_number: dict[int, RemindedThread]
) -> tuple[str, ...]:
    """Read the Threads the form says the Message touches.

    Args:
        value: The field's value: a list of Thread numbers.
        by_number: The reminded Threads, by number.

    Returns:
        Their titles, each once; unknown numbers are skipped.
    """
    if not isinstance(value, list):
        return ()
    found = (read_thread(number, by_number) for number in value)
    return tuple(dict.fromkeys(item.thread.title for item in found if item))


def read_bring_up(
    value: Any, by_number: dict[int, RemindedThread]
) -> tuple[ThreadToBringUp, ...]:
    """Read the Threads the form says to bring up, and how.

    Args:
        value: The field's value: a list of {"thread", "how"} entries.
        by_number: The reminded Threads, by number.

    Returns:
        The Threads, each once; an unknown number is skipped and an odd
        "how" reads as weaving it in.
    """
    if not isinstance(value, list):
        return ()
    chosen: dict[UUID, ThreadToBringUp] = {}
    for entry in value:
        if not isinstance(entry, dict):
            continue
        item = read_thread(entry.get("thread"), by_number)
        if item is None or item.thread.id in chosen:
            continue
        how = entry.get("how")
        chosen[item.thread.id] = ThreadToBringUp(
            thread_id=item.thread.id,
            title=item.thread.title,
            how=(
                BringUpWay(how)
                if how in {way.value for way in BringUpWay}
                else BringUpWay.WEAVE
            ),
        )
    return tuple(chosen.values())


def read_left_alone(
    value: Any, by_number: dict[int, RemindedThread]
) -> tuple[ThreadLeftAlone, ...]:
    """Read the Threads the form says to leave alone, and why.

    Args:
        value: The field's value: a list of {"thread", "reason"} entries.
        by_number: The reminded Threads, by number.

    Returns:
        The Threads, each once; an unknown number is skipped.
    """
    if not isinstance(value, list):
        return ()
    chosen: dict[UUID, ThreadLeftAlone] = {}
    for entry in value:
        if not isinstance(entry, dict):
            continue
        item = read_thread(entry.get("thread"), by_number)
        if item is None or item.thread.id in chosen:
            continue
        reason = entry.get("reason")
        chosen[item.thread.id] = ThreadLeftAlone(
            thread_id=item.thread.id,
            title=item.thread.title,
            reason=reason.strip() if isinstance(reason, str) else "",
        )
    return tuple(chosen.values())


def keep_held_back_threads_alone(
    form: UnderstandingForm, reminded: Sequence[RemindedThread]
) -> UnderstandingForm:
    """Make sure the form brings up no Thread that must be left alone.

    A held-back Thread the form chose to bring up is left alone instead,
    with the reason it is held back. One the form chose both to bring up and
    to leave alone is left alone.

    Args:
        form: The form, as read.
        reminded: The reminded Threads, with why any is held back.

    Returns:
        The form, bringing up only Threads that may be.
    """
    held_back = {item.thread.id: item.hold_back for item in reminded if item.hold_back}
    left_alone_ids = {item.thread_id for item in form.left_alone}
    newly_left_alone = tuple(
        ThreadLeftAlone(item.thread_id, item.title, held_back[item.thread_id])
        for item in form.bring_up
        if item.thread_id in held_back and item.thread_id not in left_alone_ids
    )
    return replace(
        form,
        bring_up=tuple(
            item
            for item in form.bring_up
            if item.thread_id not in held_back and item.thread_id not in left_alone_ids
        ),
        left_alone=form.left_alone + newly_left_alone,
    )


def read_understanding_form(
    answer: str, reminded: Sequence[RemindedThread]
) -> UnderstandingForm | None:
    """Read the Understanding model's JSON form.

    Text around the JSON object, such as a code fence, is ignored. A missing
    or odd mood, intensity or cause reads as an unclear, low mood whose
    cause is known, so it never makes the reply ask why. Life Threads are
    named by their numbers in the reminded list; no held-back Thread is
    ever brought up.

    Args:
        answer: The model's answer.
        reminded: The Life Threads the model was shown, numbered.

    Returns:
        The form, or None if it has no JSON object naming a Need.
    """
    start, end = answer.find("{"), answer.rfind("}")
    if start == -1 or end < start:
        return None
    try:
        parsed = json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    need = parsed.get("need")
    if not isinstance(need, str) or not need.strip():
        return None
    nuance, mood = parsed.get("nuance"), parsed.get("mood")
    intensity = parsed.get("intensity")
    cause_known = parsed.get("cause_known")
    lists = {field: read_text_list(parsed.get(field)) for field in LIST_FIELDS}
    by_number = {item.number: item for item in reminded}
    form = UnderstandingForm(
        need=need.strip(),
        nuance=nuance.strip() if isinstance(nuance, str) else "",
        mood=mood.strip() if isinstance(mood, str) else "",
        intensity=(
            MoodIntensity(intensity)
            if intensity in {level.value for level in MoodIntensity}
            else MoodIntensity.LOW
        ),
        cause_known=cause_known if isinstance(cause_known, bool) else True,
        bring_up=read_bring_up(parsed.get("bring_up"), by_number),
        left_alone=read_left_alone(parsed.get("left_alone"), by_number),
        threads_touched=read_threads_touched(parsed.get("threads_touched"), by_number),
        **lists,
    )
    return keep_held_back_threads_alone(form, reminded)


def fallback_form(fallback: Need) -> UnderstandingForm:
    """Make the form used when the Understanding call fails or can't be read.

    Args:
        fallback: The fallback Need.

    Returns:
        A form with the fallback Need, no mood and no Memory Categories.
    """
    return UnderstandingForm(
        need=fallback.name,
        nuance="",
        mood="",
        intensity=MoodIntensity.LOW,
        cause_known=True,
    )


def fallback_need(needs: Sequence[Need]) -> Need:
    """Find the fallback Need, used when it isn't clear what the User needs.

    Args:
        needs: Every Need; exactly one is the fallback.

    Returns:
        The fallback Need.
    """
    return next(need for need in needs if need.is_fallback)


def find_need(needs: Sequence[Need], name: str) -> Need:
    """Find the Need the form named, or the fallback Need if there is none.

    Args:
        needs: Every Need.
        name: The name the form gave, in any case.

    Returns:
        The Need.
    """
    for need in needs:
        if need.name.lower() == name.lower():
            return need
    return fallback_need(needs)


def should_ask_why(form: UnderstandingForm, earlier: Sequence[Understanding]) -> bool:
    """Say whether the reply should gently ask why the User feels as they do.

    Only when their mood stands out (high intensity), the Companion doesn't
    know why, and the previous reply in the Conversation didn't already ask.

    Args:
        form: This Message's form.
        earlier: This Conversation's earlier Understandings, oldest first.

    Returns:
        True if the reply should ask.
    """
    asked_last_time = bool(earlier) and earlier[-1].asked_why
    return (
        form.intensity == MoodIntensity.HIGH
        and not form.cause_known
        and not asked_last_time
    )


def format_reply_guidance(
    need: Need, form: UnderstandingForm, ask_why_note: str, threads_section: str
) -> str:
    """Write the Understanding's section of the reply instructions.

    Args:
        need: The Need the reply follows.
        form: This Message's form.
        ask_why_note: The "ask why" note; "" when the reply shouldn't ask.
        threads_section: The Life Threads to bring up or leave alone; "" if
            none matter.

    Returns:
        The Need and how to reply, the nuance, the mood, the note and the
        Life Threads.
    """
    lines = [f"What they need from you right now: {need.name}.", need.how_to_reply]
    if form.nuance:
        lines.append(form.nuance)
    if form.mood:
        lines.append(f"How they seem: {form.mood} ({form.intensity.value}).")
    if ask_why_note:
        lines.append(ask_why_note)
    guidance = "\n".join(lines)
    return f"{guidance}\n\n{threads_section}" if threads_section else guidance


def newest_incoming_message_id(messages: list[ConversationMessage]) -> UUID:
    """Find the newest text the User sent, which the Understanding goes with.

    Args:
        messages: The Conversation so far, oldest first.

    Returns:
        Its ID.

    Raises:
        ValueError: If the User sent nothing in the Conversation.
    """
    for message in reversed(messages):
        if message.direction == MessageDirection.INCOMING:
            return message.id
    raise ValueError("The Conversation has no message from the User.")


class UnderstandingService:
    """Makes the Understanding of each Message before the Companion replies.

    One cheap model call fills in a fixed form: which Need fits, how the
    User seems and whether the Companion knows why, and which Memory
    Categories matter. It sees this Conversation's earlier Understandings,
    so it knows how their mood is moving and whether it already asked why.
    """

    def __init__(
        self,
        repositories: Repositories,
        chat_model: UsageRecordingChatModel,
        clock: Clock,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where Needs, Conversations and Understandings are
                stored.
            chat_model: Fills in the form and records the tokens used.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._chat_model = chat_model
        self._clock = clock

    def understand(
        self,
        snapshot: UserSnapshot,
        conversation_id: UUID,
        saved: SavedMemory,
        reminded: Sequence[RemindedThread],
    ) -> UnderstoodMessage:
        """Make and save the Understanding of the Conversation's newest Message.

        An unknown Need falls back to the fallback Need; an unreadable form
        or a failed call falls back to the fallback Need with no mood and no
        Memory Categories, so the reply still goes, with every reminded Life
        Thread that isn't held back but none brought up.

        Args:
            snapshot: The User being answered.
            conversation_id: The Conversation the Message is in.
            saved: The User's saved memory, read for this reply.
            reminded: The Life Threads the Message reminds the Companion of.

        Returns:
            The saved Understanding and what it adds to the reply.
        """
        messages = self._repositories.conversations.list_messages(conversation_id)
        needs = self._repositories.needs.list_all()
        earlier = self._repositories.understandings.list_for_conversation(
            conversation_id
        )
        model_form = self._ask(
            snapshot,
            describe_message_for_understanding(
                snapshot, needs, saved, earlier, messages, reminded
            ),
            reminded,
        )
        if model_form is None:
            need = fallback_need(needs)
            form = fallback_form(need)
        else:
            form = model_form
            need = find_need(needs, form.need)
        asked_why = should_ask_why(form, earlier)
        understanding = Understanding(
            id=uuid4(),
            user_id=snapshot.user.id,
            conversation_id=conversation_id,
            message_id=newest_incoming_message_id(messages),
            form=form,
            need=need.name,
            asked_why=asked_why,
            made_at=self._clock.now(),
        )
        self._repositories.understandings.add(understanding)
        ask_why_note = snapshot.settings.get(REPLY_ASK_WHY_NOTE) if asked_why else ""
        return UnderstoodMessage(
            understanding=understanding,
            reply_guidance=format_reply_guidance(
                need,
                form,
                ask_why_note,
                format_threads_for_reply(reminded, model_form, snapshot.user.time_zone),
            ),
        )

    def _ask(
        self,
        snapshot: UserSnapshot,
        description: str,
        reminded: Sequence[RemindedThread],
    ) -> UnderstandingForm | None:
        """Ask the model to fill in the form.

        Args:
            snapshot: The User being answered.
            description: What the model is given about the Message.
            reminded: The Life Threads it was shown, numbered.

        Returns:
            The form; None if the call failed or the answer can't be read.
        """
        settings = snapshot.settings
        try:
            answer = self._chat_model.generate(
                snapshot=snapshot,
                step=ModelStep.UNDERSTANDING,
                model=settings.get(UNDERSTANDING_MODEL),
                instructions=settings.get(UNDERSTANDING_PROMPT),
                history=[ChatLine(role=ChatRole.USER, text=description)],
            )
        except Exception:
            logger.exception("The Understanding call failed; using the fallback Need")
            return None
        form = read_understanding_form(answer, reminded)
        if form is None:
            logger.warning(
                "The Understanding form couldn't be read; using the fallback Need"
            )
        return form
