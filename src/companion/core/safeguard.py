import logging
import re
from dataclasses import replace
from datetime import timedelta
from uuid import UUID, uuid4

from companion.core.helplines import HelplineService
from companion.core.models import (
    ChatLine,
    ChatRole,
    Helpline,
    RiskType,
    SafeguardEvent,
    SafeguardEventOverview,
    UserSnapshot,
)
from companion.core.platform_settings import (
    CRISIS_REPLY,
    HELPLINES_PLACEHOLDER,
    SAFEGUARD_MODEL,
    SAFEGUARD_PROMPT,
)
from companion.core.ports import Clock, Repositories
from companion.core.response_composition import to_chat_history
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

WORD = re.compile(r"[a-z_]+")
CRISIS_LABELS = frozenset(
    {
        RiskType.SUICIDE_OR_SELF_HARM,
        RiskType.DANGER_TO_OTHERS,
        RiskType.ABUSE,
        RiskType.MEDICAL_EMERGENCY,
    }
)


class InvalidEventFilterError(ValueError):
    """Raised when Safeguard Events are filtered by something that isn't a crisis."""


def read_risk_type(answer: str) -> RiskType | None:
    """Read the risk type from the Safeguard model's answer.

    The first crisis label in the answer wins, whatever its case or the words
    around it. Otherwise "none" means no crisis.

    Args:
        answer: The model's answer, ideally just one label.

    Returns:
        The risk type, or None if the answer has no label at all.
    """
    words = WORD.findall(answer.lower())
    for word in words:
        if word in CRISIS_LABELS:
            return RiskType(word)
    if RiskType.NONE.value in words:
        return RiskType.NONE
    return None


def speaker_name(line: ChatLine) -> str:
    """Name who said a line, as the Safeguard transcript shows it.

    Args:
        line: A line of the Conversation.

    Returns:
        "Person" for the User, "Companion" for Zeph.
    """
    return "Person" if line.role == ChatRole.USER else "Companion"


def to_transcript(history: list[ChatLine]) -> str:
    """Write a Conversation as one transcript for the Safeguard to classify.

    Given as separate chat turns, the model tends to answer the person like a
    companion instead of naming a label, most of all right after a Companion
    reply. One transcript ending in the message to classify keeps it a
    classifier.

    Args:
        history: The Conversation so far, oldest first; the last line is the
            message to classify.

    Returns:
        The transcript.
    """
    *earlier, latest = history
    latest_part = f"Latest message to classify:\n{speaker_name(latest)}: {latest.text}"
    if not earlier:
        return latest_part
    earlier_lines = "\n".join(f"{speaker_name(line)}: {line.text}" for line in earlier)
    return f"Earlier in the conversation:\n{earlier_lines}\n\n{latest_part}"


def format_helplines(helplines: list[Helpline]) -> str:
    """Write Helplines one per line, as the Crisis Reply lists them.

    Args:
        helplines: The Helplines, in the order to show them.

    Returns:
        Lines like "Samaritans of Singapore (SOS): 1767 (24 hours)".
    """
    lines = []
    for helpline in helplines:
        line = f"{helpline.details.name}: {helpline.details.number}"
        if helpline.details.hours:
            line += f" ({helpline.details.hours})"
        lines.append(line)
    return "\n".join(lines)


class Safeguard:
    """Checks every incoming message for crisis and answers a crisis safely."""

    def __init__(
        self,
        repositories: Repositories,
        helplines: HelplineService,
        chat_model: UsageRecordingChatModel,
        clock: Clock,
    ) -> None:
        """Set up the Safeguard.

        Args:
            repositories: Where Conversations, Users, Safeguard Events and
                settings are stored.
            helplines: Picks the Helplines to share in the Crisis Reply.
            chat_model: Classifies messages and records the tokens used.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._helplines = helplines
        self._chat_model = chat_model
        self._clock = clock

    def assess(
        self,
        conversation_id: UUID,
        snapshot: UserSnapshot,
        newest_text: str | None = None,
    ) -> RiskType:
        """Classify the risk in the Conversation's newest message.

        The model sees the whole Conversation as one transcript, so a message
        that is only worrying in context is still caught. Uses the Safeguard
        prompt and model from platform settings. An answer with no label is
        asked again once; if it still has none, it counts as a crisis.

        Args:
            conversation_id: The Conversation the message was added to.
            snapshot: The User who sent it.
            newest_text: The newest message as the Safeguard reads it, when
                that differs from the saved one, e.g. a photo's description
                with Photo Viewing off; None to read the saved one.

        Returns:
            The risk type, or `RiskType.NONE` if it is not a crisis.
        """
        settings = snapshot.settings
        history = to_chat_history(
            self._repositories.conversations.list_messages(conversation_id)
        )
        if newest_text is not None:
            history[-1] = replace(history[-1], text=newest_text)
        transcript = [ChatLine(role=ChatRole.USER, text=to_transcript(history))]
        for _ in range(2):
            answer = self._chat_model.generate(
                snapshot=snapshot,
                model=settings.get(SAFEGUARD_MODEL),
                instructions=settings.get(SAFEGUARD_PROMPT),
                history=transcript,
            )
            risk_type = read_risk_type(answer)
            if risk_type is not None:
                return risk_type
        logger.warning("The Safeguard model gave no label twice; treating as crisis")
        return RiskType.UNCLEAR

    def respond_to_crisis(self, snapshot: UserSnapshot, risk_type: RiskType) -> str:
        """Write the Crisis Reply and record a Safeguard Event.

        The Crisis Reply is the Admin-edited wording with `{helplines}`
        replaced by the User's country Helplines, or by the international
        fallback when their country has none. The event never holds message
        text.

        Args:
            snapshot: The User in crisis.
            risk_type: What kind of crisis the Safeguard saw.

        Returns:
            The Crisis Reply.
        """
        to_share = self._helplines.to_share_with(snapshot.user.country)
        self._repositories.safeguard_events.add(
            SafeguardEvent(
                id=uuid4(),
                user_id=snapshot.user.id,
                risk_type=risk_type,
                created_at=self._clock.now(),
                helplines_country=to_share.country,
            )
        )
        wording = snapshot.settings.get(CRISIS_REPLY)
        return wording.replace(
            HELPLINES_PLACEHOLDER, format_helplines(to_share.helplines)
        )

    def list_events(
        self, days: int | None, risk_type: RiskType | None
    ) -> list[SafeguardEventOverview]:
        """List Safeguard Events for Admins, newest first.

        Args:
            days: Only events from the last this many days; None for all time.
            risk_type: Only events of this crisis type; None for every type.

        Returns:
            The events with who each User is.

        Raises:
            InvalidEventFilterError: If `risk_type` is `RiskType.NONE`, which
                is never recorded.
        """
        if risk_type == RiskType.NONE:
            raise InvalidEventFilterError("Filter by a crisis risk type.")
        since = self._clock.now() - timedelta(days=days) if days else None
        return self._repositories.safeguard_events.list_overviews(since, risk_type)
