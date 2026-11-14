from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from companion.core.conversations import ConversationService
from companion.core.models import MessageToAnswer, RiskType
from companion.core.safeguard import Safeguard
from companion.core.usage import UsageLimiter
from companion.core.user_data import ChatDataDeletion, DataDeletionAnswer


class StopReason(StrEnum):
    """Why a message gets no composed reply."""

    CRISIS = "crisis"
    DATA_DELETED = "data_deleted"
    OVER_LIMIT = "over_limit"


@dataclass(frozen=True)
class Stopped:
    """The message was handled without a composed reply.

    Attributes:
        reason: Why no reply is composed.
    """

    reason: StopReason


@dataclass(frozen=True)
class ReplyNeeded:
    """The message passed the house rules and needs a composed reply.

    Attributes:
        conversation_id: The Conversation the message was saved into.
        data_deletion_cancelled: Whether the message cancelled a pending
            Delete My Data, so the reply can mention it.
    """

    conversation_id: UUID
    data_deletion_cancelled: bool


class ReplyGate:
    """Saves a User's message and applies the house rules before any reply.

    The rules run in this order: the Safeguard, then a pending Delete My
    Data, then the Daily Message Limit.
    """

    def __init__(
        self,
        conversations: ConversationService,
        safeguard: Safeguard,
        data_deletion: ChatDataDeletion,
        usage_limiter: UsageLimiter,
    ) -> None:
        """Set up the gate.

        Args:
            conversations: Saves messages and sends replies.
            safeguard: Checks each message for crisis and writes the Crisis Reply.
            data_deletion: Settles a Delete My Data the User asked for in chat.
            usage_limiter: Keeps each User within the Daily Message Limit.
        """
        self._conversations = conversations
        self._safeguard = safeguard
        self._data_deletion = data_deletion
        self._usage_limiter = usage_limiter

    def check(self, message: MessageToAnswer) -> Stopped | ReplyNeeded:
        """Save the message, then decide whether it needs a composed reply.

        On a crisis the Crisis Reply is sent, then any pending Delete My Data
        is cancelled, and the message isn't counted toward the Daily Message
        Limit. Otherwise a pending Delete My Data is settled: the confirmation
        word deletes the User's data, anything else cancels the request. Over
        the limit, the Limit Reply is sent.

        Args:
            message: The message to answer.

        Returns:
            `Stopped` with the reason no reply is composed, or `ReplyNeeded`.
        """
        conversation_id = self._conversations.record_incoming(
            message.user_id,
            message.chat_id,
            message.text,
            message.kind,
            message.photos,
            message.sticker,
        )
        risk_type = self._safeguard.assess(
            conversation_id, message.user_id, message.safeguard_text
        )
        if risk_type != RiskType.NONE:
            crisis_reply = self._safeguard.respond_to_crisis(message.user_id, risk_type)
            self._conversations.deliver_at_once(
                conversation_id, message.chat_id, crisis_reply
            )
            self._data_deletion.cancel(message.user_id)
            return Stopped(StopReason.CRISIS)
        data_deletion_answer = self._data_deletion.settle(
            message.user_id, message.chat_id, message.text
        )
        if data_deletion_answer == DataDeletionAnswer.CONFIRMED:
            return Stopped(StopReason.DATA_DELETED)
        if not self._usage_limiter.claim_message(message.user_id):
            self._conversations.deliver_at_once(
                conversation_id, message.chat_id, self._usage_limiter.limit_reply()
            )
            return Stopped(StopReason.OVER_LIMIT)
        data_deletion_cancelled = data_deletion_answer == DataDeletionAnswer.CANCELLED
        return ReplyNeeded(conversation_id, data_deletion_cancelled)
