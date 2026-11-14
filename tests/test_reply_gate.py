from datetime import UTC, datetime
from uuid import UUID, uuid4

from companion.core.models import (
    MessageToAnswer,
    ModelCallTrace,
    PlatformSettings,
    RiskType,
    TextToScreen,
    TraceKind,
    User,
    UserSnapshot,
)
from companion.core.reply_gate import (
    ReplyGate,
    ReplyNeeded,
    Screened,
    Stopped,
    StopReason,
)
from companion.core.user_data import DataDeletionAnswer

CHAT_ID = 42
CONVERSATION_ID = uuid4()
CRISIS_REPLY = "Please reach out to a helpline."
LIMIT_REPLY = "I'm wiped for today, talk tomorrow?"
CANCELLED_NOTE = "Nothing was deleted."
WORD_NOT_ALONE_NOTE = "The word only counts on its own."


class FakeConversations:
    """Saves messages and sends replies, noting each call in a shared log."""

    def __init__(self, calls: list[str]) -> None:
        """Start with no replies sent.

        Args:
            calls: The shared log of calls made, in order.
        """
        self.calls = calls
        self.sent: list[str] = []

    def record_incoming(
        self, user_id: UUID, chat_id: int, text: str, *details: object
    ) -> UUID:
        """Note that the message was saved.

        Args:
            user_id: The User who sent it.
            chat_id: The chat it came from.
            text: The message.
            *details: The platform settings, its kind, photos and sticker,
                which are ignored.

        Returns:
            The Conversation's ID.
        """
        self.calls.append("record_incoming")
        return CONVERSATION_ID

    def deliver_at_once(self, conversation_id: UUID, chat_id: int, text: str) -> None:
        """Note the reply that was sent.

        Args:
            conversation_id: The Conversation.
            chat_id: The chat to reply in.
            text: The reply.
        """
        self.calls.append("deliver_at_once")
        self.sent.append(text)


class FakeSafeguard:
    """Sees the risk it was told to see."""

    def __init__(self, calls: list[str], risk_type: RiskType) -> None:
        """Remember what risk to report.

        Args:
            calls: The shared log of calls made, in order.
            risk_type: The risk every message is seen to have.
        """
        self.calls = calls
        self.risk_type = risk_type

    def assess(
        self,
        conversation_id: UUID,
        snapshot: UserSnapshot,
        newest_text: str | None = None,
    ) -> RiskType:
        """Report the set risk.

        Args:
            conversation_id: The Conversation.
            snapshot: The User.
            newest_text: The message as the Safeguard reads it, if different.

        Returns:
            The set risk.
        """
        self.calls.append("assess")
        return self.risk_type

    def respond_to_crisis(self, snapshot: UserSnapshot, risk_type: RiskType) -> str:
        """Write the Crisis Reply.

        Args:
            snapshot: The User in crisis.
            risk_type: The risk seen.

        Returns:
            The Crisis Reply.
        """
        self.calls.append("respond_to_crisis")
        return CRISIS_REPLY


class FakeDataDeletion:
    """Settles a Delete My Data with a set answer."""

    def __init__(self, calls: list[str], answer: DataDeletionAnswer) -> None:
        """Remember what answer to give.

        Args:
            calls: The shared log of calls made, in order.
            answer: What every message does to a Delete My Data.
        """
        self.calls = calls
        self.answer = answer

    def settle(
        self, snapshot: UserSnapshot, chat_id: int, text: str
    ) -> DataDeletionAnswer:
        """Settle a pending Delete My Data.

        Args:
            snapshot: The User.
            chat_id: The chat to reply in.
            text: The message.

        Returns:
            The set answer.
        """
        self.calls.append("settle")
        return self.answer

    def cancel(self, snapshot: UserSnapshot) -> DataDeletionAnswer:
        """Cancel a pending Delete My Data.

        Args:
            snapshot: The User.

        Returns:
            That a request was cancelled.
        """
        self.calls.append("cancel")
        return DataDeletionAnswer.CANCELLED


class FakeUsageLimiter:
    """Lets a message through, or not, as told."""

    def __init__(self, calls: list[str], within_limit: bool) -> None:
        """Remember whether the User is within the limit.

        Args:
            calls: The shared log of calls made, in order.
            within_limit: Whether every message is within the limit.
        """
        self.calls = calls
        self.within_limit = within_limit

    def claim_message(self, snapshot: UserSnapshot) -> bool:
        """Count the message.

        Args:
            snapshot: The User who sent it.

        Returns:
            Whether it is within the limit.
        """
        self.calls.append("claim_message")
        return self.within_limit

    def limit_reply(self, settings: PlatformSettings) -> str:
        """Read the Limit Reply.

        Args:
            settings: The platform settings, which are ignored.

        Returns:
            The Limit Reply.
        """
        return LIMIT_REPLY


def build_gate(
    risk_type: RiskType = RiskType.NONE,
    data_deletion_answer: DataDeletionAnswer = DataDeletionAnswer.NOTHING_ASKED,
    within_limit: bool = True,
) -> tuple[ReplyGate, UserSnapshot, list[str], list[str]]:
    """Build a ReplyGate from fakes.

    Args:
        risk_type: The risk the Safeguard sees.
        data_deletion_answer: What the Message does to a Delete My Data.
        within_limit: Whether the Message is within the Daily Message Limit.

    Returns:
        The gate, the User, the calls made in order, and the replies sent.
    """
    calls: list[str] = []
    conversations = FakeConversations(calls)
    gate = ReplyGate(
        conversations=conversations,
        safeguard=FakeSafeguard(calls, risk_type),
        data_deletion=FakeDataDeletion(calls, data_deletion_answer),
        usage_limiter=FakeUsageLimiter(calls, within_limit),
    )
    now = datetime(2026, 11, 14, 9, 0, tzinfo=UTC)
    user = User(id=uuid4(), auth_id="user_maya", email=None, created_at=now)
    snapshot = UserSnapshot(
        user=user,
        local_now=now,
        today=now.date(),
        features=(),
        settings=PlatformSettings(
            {
                "reply_data_deletion_cancelled_note": CANCELLED_NOTE,
                "reply_data_deletion_word_not_alone_note": WORD_NOT_ALONE_NOTE,
            }
        ),
        trace=ModelCallTrace(id=uuid4(), kind=TraceKind.MESSAGE),
    )
    return gate, snapshot, calls, conversations.sent


def screen_text(
    risk_type: RiskType = RiskType.NONE,
) -> tuple[Stopped | Screened, list[str], list[str]]:
    """Run one text through a ReplyGate built from fakes.

    Args:
        risk_type: The risk the Safeguard sees.

    Returns:
        The gate's result, the calls made in order, and the replies sent.
    """
    gate, snapshot, calls, sent = build_gate(risk_type=risk_type)
    result = gate.screen(
        TextToScreen(user_id=snapshot.user.id, chat_id=CHAT_ID, text="hi"), snapshot
    )
    return result, calls, sent


def check_message(
    data_deletion_answer: DataDeletionAnswer = DataDeletionAnswer.NOTHING_ASKED,
    within_limit: bool = True,
) -> tuple[Stopped | ReplyNeeded, list[str], list[str]]:
    """Run one screened Message through a ReplyGate built from fakes.

    Args:
        data_deletion_answer: What the Message does to a Delete My Data.
        within_limit: Whether the Message is within the Daily Message Limit.

    Returns:
        The gate's result, the calls made in order, and the replies sent.
    """
    gate, snapshot, calls, sent = build_gate(
        data_deletion_answer=data_deletion_answer, within_limit=within_limit
    )
    result = gate.check(
        MessageToAnswer(
            user_id=snapshot.user.id,
            chat_id=CHAT_ID,
            conversation_id=CONVERSATION_ID,
            text="hi\nyou there?",
        ),
        snapshot,
    )
    return result, calls, sent


def test_a_crisis_text_sends_the_crisis_reply_and_cancels_deletion() -> None:
    result, calls, sent = screen_text(risk_type=RiskType.SUICIDE_OR_SELF_HARM)

    assert result == Stopped(StopReason.CRISIS)
    assert sent == [CRISIS_REPLY]
    assert calls == [
        "record_incoming",
        "assess",
        "respond_to_crisis",
        "deliver_at_once",
        "cancel",
    ]


def test_a_normal_text_is_saved_and_checked_but_not_counted() -> None:
    result, calls, sent = screen_text()

    assert result == Screened(CONVERSATION_ID)
    assert sent == []
    assert calls == ["record_incoming", "assess"]


def test_a_confirmed_deletion_stops_the_reply() -> None:
    result, calls, sent = check_message(
        data_deletion_answer=DataDeletionAnswer.CONFIRMED
    )

    assert result == Stopped(StopReason.DATA_DELETED)
    assert sent == []
    assert calls == ["settle"]


def test_a_message_with_a_pending_deletion_cancels_it_and_needs_a_reply() -> None:
    result, _, _ = check_message(data_deletion_answer=DataDeletionAnswer.CANCELLED)

    assert result == ReplyNeeded(data_deletion_note=CANCELLED_NOTE)


def test_the_word_sent_with_other_texts_gets_the_note_that_says_why() -> None:
    result, _, _ = check_message(
        data_deletion_answer=DataDeletionAnswer.CANCELLED_WORD_NOT_ALONE
    )

    assert result == ReplyNeeded(data_deletion_note=WORD_NOT_ALONE_NOTE)


def test_a_message_over_the_limit_sends_the_limit_reply() -> None:
    result, calls, sent = check_message(within_limit=False)

    assert result == Stopped(StopReason.OVER_LIMIT)
    assert sent == [LIMIT_REPLY]
    assert calls == ["settle", "claim_message", "deliver_at_once"]


def test_a_normal_message_counts_once_and_needs_a_reply() -> None:
    result, calls, sent = check_message()

    assert result == ReplyNeeded(data_deletion_note="")
    assert sent == []
    assert calls == ["settle", "claim_message"]
