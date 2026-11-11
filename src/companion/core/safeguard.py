import re
from datetime import timedelta
from uuid import UUID, uuid4

from companion.core.models import (
    ChatLine,
    ChatRole,
    Helpline,
    RiskType,
    SafeguardEvent,
    SafeguardEventOverview,
)
from companion.core.ports import ChatModel, Clock, Repositories
from companion.core.response_composition import to_chat_history

HELPLINES_PLACEHOLDER = "{helplines}"
WORD = re.compile(r"[a-z_]+")
CRISIS_RISK_TYPES = frozenset(RiskType) - {RiskType.NONE}


class InvalidEventFilterError(ValueError):
    """Raised when Safeguard Events are filtered by something that isn't a crisis."""


def read_risk_type(answer: str) -> RiskType:
    """Read the risk type from the Safeguard model's answer.

    The first crisis label in the answer wins, whatever its case or the words
    around it. An answer with no crisis label counts as no crisis.

    Args:
        answer: The model's answer, ideally just one label.

    Returns:
        The risk type.
    """
    for word in WORD.findall(answer.lower()):
        if word in CRISIS_RISK_TYPES:
            return RiskType(word)
    return RiskType.NONE


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
        self, repositories: Repositories, chat_model: ChatModel, clock: Clock
    ) -> None:
        """Set up the Safeguard.

        Args:
            repositories: Where Conversations, Users, Helplines, Safeguard
                Events and settings are stored.
            chat_model: Classifies messages.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._chat_model = chat_model
        self._clock = clock

    def assess(self, conversation_id: UUID) -> RiskType:
        """Classify the risk in the Conversation's newest message.

        The model sees the whole Conversation as one transcript, so a message
        that is only worrying in context is still caught. Uses the Safeguard
        prompt and model from platform settings.

        Args:
            conversation_id: The Conversation the message was added to.

        Returns:
            The risk type, or `RiskType.NONE` if it is not a crisis.
        """
        settings = self._repositories.platform_settings
        history = to_chat_history(
            self._repositories.conversations.list_messages(conversation_id)
        )
        answer = self._chat_model.generate(
            model=settings.get("safeguard_model"),
            instructions=settings.get("safeguard_prompt"),
            history=[ChatLine(role=ChatRole.USER, text=to_transcript(history))],
        )
        return read_risk_type(answer)

    def respond_to_crisis(self, user_id: UUID, risk_type: RiskType) -> str:
        """Write the Crisis Reply and record a Safeguard Event.

        The Crisis Reply is the Admin-edited wording with `{helplines}`
        replaced by the User's country Helplines, or by the international
        fallback when their country has none. The event never holds message
        text.

        Args:
            user_id: The User in crisis.
            risk_type: What kind of crisis the Safeguard saw.

        Returns:
            The Crisis Reply.
        """
        user = self._repositories.users.get(user_id)
        country = user.country if user is not None else None
        helplines = (
            self._repositories.helplines.list_for_country(country) if country else []
        )
        helplines_country = country if helplines else None
        if not helplines:
            helplines = [self._repositories.helplines.get_international_fallback()]
        self._repositories.safeguard_events.add(
            SafeguardEvent(
                id=uuid4(),
                user_id=user_id,
                risk_type=risk_type,
                created_at=self._clock.now(),
                helplines_country=helplines_country,
            )
        )
        wording: str = self._repositories.platform_settings.get("crisis_reply")
        return wording.replace(HELPLINES_PLACEHOLDER, format_helplines(helplines))

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
