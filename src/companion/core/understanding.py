import json
import logging
from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from companion.core.memory_retrieval import format_day
from companion.core.model_call_log import ModelCallLog
from companion.core.models import (
    ChatLine,
    ChatRole,
    ConversationMessage,
    MessageDirection,
    ModelStep,
    MoodIntensity,
    SaidReadUnclear,
    Understanding,
    UnderstandingForm,
    UnderstandingShape,
    UserSnapshot,
)
from companion.core.platform_settings import (
    UNDERSTANDING_MODEL,
    UNDERSTANDING_PROMPT,
    UNDERSTANDING_THINKING,
    thinking_to_use,
)
from companion.core.ports import Clock, Repositories
from companion.core.recent_messages import RecentMessages, describe_recent_messages
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)


def format_local_time(local_now: datetime) -> str:
    """Write the weekday, day and time, e.g. "Wednesday 11 Nov 2026, 17:00".

    Args:
        local_now: The time where the User lives.

    Returns:
        The time.
    """
    return f"{local_now:%A} {format_day(local_now, None)}, {local_now:%H:%M}"


def describe_said_read_unclear(label: str, value: SaidReadUnclear) -> str:
    """Write one said / read / unclear part of an Understanding.

    Args:
        label: What it is about, e.g. "Feelings".
        value: What they said, what is guessed and what is unclear.

    Returns:
        E.g. "Feelings: said “I'm fine”; read: hurt; unclear: why.", with
        empty parts left out and each part's own full stop dropped;
        "Feelings: nothing yet." when all are empty.
    """
    parts = [
        f"{name}: {text.rstrip('.')}"
        for name, text in (
            ("said", value.said),
            ("read (a guess)", value.read),
            ("unclear", value.unclear),
        )
        if text
    ]
    return f"{label}: {'; '.join(parts) or 'nothing yet'}."


def describe_understanding(form: UnderstandingForm) -> str:
    """Write an Understanding as the steps after it read it.

    Args:
        form: The Understanding's form.

    Returns:
        What they said and mean, their feelings, mood and wants, whether the
        cause is known, whether they are struggling or asked for a photo.
    """
    lines = []
    if form.said:
        lines.append(f"They said: {form.said}")
    if form.means:
        lines.append(f"They mean: {form.means}")
    lines += [
        describe_said_read_unclear("Feelings", form.feelings),
        f"Mood: {form.mood or 'unclear'} ({form.intensity.value}).",
        describe_said_read_unclear("What they want", form.wants),
        f"Cause known: {'yes' if form.cause_known else 'no'}.",
        f"Struggling: {'yes' if form.struggling else 'no'}.",
    ]
    if form.asked_for_photo:
        lines.append("They asked to see one of their photos.")
    return "\n".join(lines)


def format_earlier_understanding(understanding: Understanding) -> str:
    """Write one earlier Understanding as the next Understanding reads it.

    Args:
        understanding: The earlier Understanding.

    Returns:
        E.g. "- Mood: furious (high); cause known: no; struggling: yes. They
        mean: their boss undercut them again."
    """
    form = understanding.form
    cause_known = "yes" if form.cause_known else "no"
    struggling = "yes" if form.struggling else "no"
    line = (
        f"- Mood: {form.mood or 'unclear'} ({form.intensity.value}); "
        f"cause known: {cause_known}; struggling: {struggling}."
    )
    return f"{line} They mean: {form.means}" if form.means else line


def describe_message_for_understanding(
    snapshot: UserSnapshot,
    portrait: str | None,
    earlier: Sequence[Understanding],
    recent: RecentMessages,
) -> str:
    """Write what the Understanding model is given about the Message.

    It is given nothing to pick: no Needs, Moves, Life Threads, Curiosities,
    Knowledge or Memory Categories.

    Args:
        snapshot: The User being answered.
        portrait: The User Portrait; None if it isn't written yet.
        earlier: This Conversation's earlier Understandings, oldest first.
        recent: The Recent Messages: every message from the last hours,
            across Conversations.

    Returns:
        The time, User Portrait, earlier Understandings, earlier messages
        across Conversations and latest message.
    """
    earlier_lines = "\n".join(
        format_earlier_understanding(understanding) for understanding in earlier
    )
    return (
        f"Time where they are: {format_local_time(snapshot.local_now)}\n\n"
        f"Their User Portrait:\n{portrait or 'Not written yet.'}\n\n"
        f"Earlier Understandings in this Conversation, oldest first:\n"
        f"{earlier_lines or 'None yet.'}\n\n"
        f"{describe_recent_messages(recent, snapshot.user.time_zone)}"
    )


def read_text_list(value: Any) -> tuple[str, ...]:
    """Read a list of texts from a form, keeping only non-empty texts.

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


def read_form_text(value: Any) -> str:
    """Read a text field from a form, such as a Move's name.

    Args:
        value: The field's value.

    Returns:
        The text without surrounding spaces; "" if it isn't text.
    """
    return value.strip() if isinstance(value, str) else ""


def read_said_read_unclear(value: Any) -> SaidReadUnclear:
    """Read a said / read / unclear field from the form.

    Args:
        value: The field's value, e.g. {"said": "...", "read": "...",
            "unclear": "..."}.

    Returns:
        Its parts; an odd value or part reads as empty.
    """
    if not isinstance(value, dict):
        return SaidReadUnclear()
    return SaidReadUnclear(
        said=read_form_text(value.get("said")),
        read=read_form_text(value.get("read")),
        unclear=read_form_text(value.get("unclear")),
    )


def read_understanding_form(answer: str) -> UnderstandingForm | None:
    """Read the Understanding model's JSON form.

    Text around the JSON object, such as a code fence, is ignored. A missing
    or odd mood, intensity or cause reads as an unclear, low mood whose
    cause is known, so it never makes the reply ask why. A missing or odd
    "struggling" or "asked_for_photo" reads as false.

    Args:
        answer: The model's answer.

    Returns:
        The form, or None if it has no JSON object.
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
    intensity = parsed.get("intensity")
    cause_known = parsed.get("cause_known")
    return UnderstandingForm(
        said=read_form_text(parsed.get("said")),
        means=read_form_text(parsed.get("means")),
        feelings=read_said_read_unclear(parsed.get("feelings")),
        mood=read_form_text(parsed.get("mood")),
        intensity=(
            MoodIntensity(intensity)
            if intensity in {level.value for level in MoodIntensity}
            else MoodIntensity.LOW
        ),
        wants=read_said_read_unclear(parsed.get("wants")),
        cause_known=cause_known if isinstance(cause_known, bool) else True,
        look_up_past=read_text_list(parsed.get("look_up_past")),
        struggling=parsed.get("struggling") is True,
        asked_for_photo=parsed.get("asked_for_photo") is True,
    )


def fallback_form() -> UnderstandingForm:
    """Make the form used when the Understanding call fails or can't be read.

    Returns:
        A form with no mood, low intensity and the cause known, so the reply
        never asks why.
    """
    return UnderstandingForm(mood="", intensity=MoodIntensity.LOW, cause_known=True)


def describe_understanding_shape(form: UnderstandingForm) -> UnderstandingShape:
    """Describe the shape of an Understanding for the Model Call Log.

    Args:
        form: The form the reply follows.

    Returns:
        Intensity, whether the cause is known, whether they are struggling
        and how many past look-ups there were; never any words.
    """
    return UnderstandingShape(
        intensity=form.intensity,
        cause_known=form.cause_known,
        struggling=form.struggling,
        past_look_ups=len(form.look_up_past),
    )


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

    One model call reads the Message and decides nothing about the reply:
    what the User said and means, how they feel and what they want (each
    keeping what they said apart from what is guessed and what is unclear),
    how strongly they feel it and whether the Companion knows why, whether
    they are struggling or asked for a photo, and what past to look up. It
    sees the User Portrait, this Conversation's earlier Understandings, so
    it knows how their mood is moving, and the Recent Messages: every message
    from the last hours, across Conversations.
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
            repositories: Where Conversations and Understandings are stored.
            chat_model: Fills in the form and records the tokens used.
            model_call_log: Records the shape of each Understanding.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._chat_model = chat_model
        self._model_call_log = model_call_log
        self._clock = clock

    def understand(
        self, snapshot: UserSnapshot, recent: RecentMessages, portrait: str | None
    ) -> Understanding:
        """Make and save the Understanding of the Conversation's newest Message.

        Its shape goes into the Model Call Log, for every User. An unreadable
        form or a failed call falls back to an unclear, low mood whose cause
        is known, so the reply still goes.

        Args:
            snapshot: The User being answered.
            recent: The Recent Messages, ending with the Message.
            portrait: The User Portrait; None if it isn't written yet.

        Returns:
            The saved Understanding.
        """
        conversation_id = recent.conversation_id
        earlier = self._repositories.understandings.list_for_conversation(
            conversation_id
        )
        model_form = self._ask(
            snapshot,
            describe_message_for_understanding(snapshot, portrait, earlier, recent),
        )
        form = model_form if model_form is not None else fallback_form()
        understanding = Understanding(
            id=uuid4(),
            user_id=snapshot.user.id,
            conversation_id=conversation_id,
            message_id=newest_incoming_message_id(recent.messages),
            form=form,
            made_at=self._clock.now(),
            is_fallback=model_form is None,
        )
        self._repositories.understandings.add(understanding)
        self._model_call_log.record_understanding_shape(
            snapshot, describe_understanding_shape(form)
        )
        return understanding

    def _ask(
        self, snapshot: UserSnapshot, description: str
    ) -> UnderstandingForm | None:
        """Ask the model to fill in the form.

        Args:
            snapshot: The User being answered.
            description: What the model is given about the Message.

        Returns:
            The form; None if the call failed or the answer can't be read.
        """
        settings = snapshot.settings
        try:
            answer = self._chat_model.generate(
                snapshot=snapshot,
                step=ModelStep.UNDERSTANDING,
                model=settings.get(UNDERSTANDING_MODEL),
                thinking=thinking_to_use(
                    settings, UNDERSTANDING_MODEL, UNDERSTANDING_THINKING
                ),
                instructions=settings.get(UNDERSTANDING_PROMPT),
                history=[ChatLine(role=ChatRole.USER, text=description)],
            )
        except Exception:
            logger.exception(
                "The Understanding call failed; using the fallback Understanding"
            )
            return None
        form = read_understanding_form(answer)
        if form is None:
            logger.warning(
                "The Understanding form couldn't be read; using the fallback "
                "Understanding"
            )
        return form
