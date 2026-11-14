from uuid import UUID, uuid4

from companion.core.models import MessageToAnswer, RiskType
from companion.core.reply_gate import ReplyGate, ReplyNeeded, Stopped, StopReason
from companion.core.user_data import DataDeletionAnswer

CHAT_ID = 42
CONVERSATION_ID = uuid4()
CRISIS_REPLY = "Please reach out to a helpline."
LIMIT_REPLY = "I'm wiped for today, talk tomorrow?"


class FakeConversations:
    """Saves messages and sends replies into a shared call log."""

    def __init__(self, calls: list[str]) -> None:
        """Start with no messages sent."""
        self.calls = calls
        self.sent: list[str] = []

    def record_incoming(
        self, user_id: UUID, chat_id: int, text: str, *args: object
    ) -> UUID:
        """Note the message was saved and hand back the Conversation's ID."""
        self.calls.append("record_incoming")
        return CONVERSATION_ID

    def deliver_at_once(self, conversation_id: UUID, chat_id: int, text: str) -> None:
        """Note the reply that was sent."""
        self.calls.append("deliver_at_once")
        self.sent.append(text)


class FakeSafeguard:
    """Sees the risk it was told to see."""

    def __init__(self, calls: list[str], risk_type: RiskType) -> None:
        """Remember what risk to report."""
        self.calls = calls
        self.risk_type = risk_type

    def assess(
        self, conversation_id: UUID, user_id: UUID, newest_text: str | None = None
    ) -> RiskType:
        """Report the set risk."""
        self.calls.append("assess")
        return self.risk_type

    def respond_to_crisis(self, user_id: UUID, risk_type: RiskType) -> str:
        """Hand back the Crisis Reply."""
        self.calls.append("respond_to_crisis")
        return CRISIS_REPLY


class FakeDataDeletion:
    """Settles a Delete My Data with a set answer."""

    def __init__(self, calls: list[str], answer: DataDeletionAnswer) -> None:
        """Remember what answer to give."""
        self.calls = calls
        self.answer = answer

    def settle(self, user_id: UUID, chat_id: int, text: str) -> DataDeletionAnswer:
        """Give the set answer."""
        self.calls.append("settle")
        return self.answer

    def cancel(self, user_id: UUID) -> DataDeletionAnswer:
        """Note the cancel."""
        self.calls.append("cancel")
        return DataDeletionAnswer.CANCELLED


class FakeUsageLimiter:
    """Lets a message through, or not, as told."""

    def __init__(self, calls: list[str], within_limit: bool) -> None:
        """Remember whether the User is within the limit."""
        self.calls = calls
        self.within_limit = within_limit

    def claim_message(self, user_id: UUID) -> bool:
        """Count the message."""
        self.calls.append("claim_message")
        return self.within_limit

    def limit_reply(self) -> str:
        """Hand back the Limit Reply."""
        return LIMIT_REPLY


def check_message(
    risk_type: RiskType = RiskType.NONE,
    data_deletion_answer: DataDeletionAnswer = DataDeletionAnswer.NOTHING_ASKED,
    within_limit: bool = True,
) -> tuple[Stopped | ReplyNeeded, list[str], list[str]]:
    """Run one message through a ReplyGate built from fakes.

    Returns:
        The gate's result, the calls made in order, and the replies sent.
    """
    calls: list[str] = []
    conversations = FakeConversations(calls)
    gate = ReplyGate(
        conversations=conversations,
        safeguard=FakeSafeguard(calls, risk_type),
        data_deletion=FakeDataDeletion(calls, data_deletion_answer),
        usage_limiter=FakeUsageLimiter(calls, within_limit),
    )
    result = gate.check(MessageToAnswer(user_id=uuid4(), chat_id=CHAT_ID, text="hi"))
    return result, calls, conversations.sent


def test_a_crisis_sends_the_crisis_reply_cancels_deletion_and_is_not_counted() -> None:
    result, calls, sent = check_message(risk_type=RiskType.SUICIDE_OR_SELF_HARM)

    assert result == Stopped(StopReason.CRISIS)
    assert sent == [CRISIS_REPLY]
    assert calls == [
        "record_incoming",
        "assess",
        "respond_to_crisis",
        "deliver_at_once",
        "cancel",
    ]


def test_a_confirmed_deletion_stops_the_reply() -> None:
    result, calls, sent = check_message(
        data_deletion_answer=DataDeletionAnswer.CONFIRMED
    )

    assert result == Stopped(StopReason.DATA_DELETED)
    assert sent == []
    assert "claim_message" not in calls


def test_a_message_with_a_pending_deletion_cancels_it_and_needs_a_reply() -> None:
    result, _, _ = check_message(data_deletion_answer=DataDeletionAnswer.CANCELLED)

    assert result == ReplyNeeded(CONVERSATION_ID, data_deletion_cancelled=True)


def test_a_message_over_the_limit_sends_the_limit_reply() -> None:
    result, calls, sent = check_message(within_limit=False)

    assert result == Stopped(StopReason.OVER_LIMIT)
    assert sent == [LIMIT_REPLY]
    assert calls == [
        "record_incoming",
        "assess",
        "settle",
        "claim_message",
        "deliver_at_once",
    ]


def test_a_normal_message_needs_a_reply() -> None:
    result, calls, sent = check_message()

    assert result == ReplyNeeded(CONVERSATION_ID, data_deletion_cancelled=False)
    assert sent == []
    assert calls == ["record_incoming", "assess", "settle", "claim_message"]
