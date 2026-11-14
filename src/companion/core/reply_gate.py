from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from companion.core.conversations import ConversationService
from companion.core.models import (
    MessageToAnswer,
    RiskType,
    TextToScreen,
    UserSnapshot,
)
from companion.core.safeguard import Safeguard
from companion.core.usage import UsageLimiter
from companion.core.user_data import ChatDataDeletion, DataDeletionAnswer


class StopReason(StrEnum):
    """Why a Message gets no composed reply."""

    CRISIS = "crisis"
    DATA_DELETED = "data_deleted"
    OVER_LIMIT = "over_limit"


@dataclass(frozen=True)
class Stopped:
    """The Message was handled without a composed reply.

    Attributes:
        reason: Why no reply is composed.
    """

    reason: StopReason


@dataclass(frozen=True)
class Screened:
    """The text was saved and passed the Safeguard.

    Attributes:
        conversation_id: The Conversation the text was saved into.
    """

    conversation_id: UUID


@dataclass(frozen=True)
class ReplyNeeded:
    """The Message passed the house rules and needs a composed reply.

    Attributes:
        data_deletion_cancelled: Whether the Message cancelled a pending
            Delete My Data, so the reply can mention it.
    """

    data_deletion_cancelled: bool


class ReplyGate:
    """Saves a User's texts and applies the house rules before any reply.

    Each text is saved and checked by the Safeguard as it arrives. Once the
    User pauses, their Message goes through a pending Delete My Data, then
    the Daily Message Limit.
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
            safeguard: Checks each text for crisis and writes the Crisis Reply.
            data_deletion: Settles a Delete My Data the User asked for in chat.
            usage_limiter: Keeps each User within the Daily Message Limit.
        """
        self._conversations = conversations
        self._safeguard = safeguard
        self._data_deletion = data_deletion
        self._usage_limiter = usage_limiter

    def screen(self, text: TextToScreen, snapshot: UserSnapshot) -> Stopped | Screened:
        """Save one text of a Message and check it for crisis.

        On a crisis the Crisis Reply is sent at once, then any pending Delete
        My Data is cancelled. A crisis never counts toward the Daily Message
        Limit.

        Args:
            text: The text, as it arrived.
            snapshot: The User who sent it.

        Returns:
            `Stopped` for a crisis, or `Screened` with the Conversation it
            was saved into.
        """
        conversation_id = self._conversations.record_incoming(
            text.user_id,
            text.chat_id,
            text.text,
            snapshot.settings,
            text.kind,
            text.photos,
            text.sticker,
        )
        risk_type = self._safeguard.assess(
            conversation_id, snapshot, text.safeguard_text
        )
        if risk_type == RiskType.NONE:
            return Screened(conversation_id)
        crisis_reply = self._safeguard.respond_to_crisis(snapshot, risk_type)
        self._conversations.deliver_at_once(conversation_id, text.chat_id, crisis_reply)
        self._data_deletion.cancel(snapshot)
        return Stopped(StopReason.CRISIS)

    def check(
        self, message: MessageToAnswer, snapshot: UserSnapshot
    ) -> Stopped | ReplyNeeded:
        """Decide whether a screened Message needs a composed reply.

        A pending Delete My Data is settled first: the confirmation word
        deletes the User's data, anything else cancels the request. Then the
        Message counts once toward the Daily Message Limit; over it, the
        Limit Reply is sent.

        Args:
            message: The Message, all of whose texts passed the Safeguard.
            snapshot: The User who sent it, as read when the reply started.

        Returns:
            `Stopped` with the reason no reply is composed, or `ReplyNeeded`.
        """
        data_deletion_answer = self._data_deletion.settle(
            snapshot, message.chat_id, message.text
        )
        if data_deletion_answer == DataDeletionAnswer.CONFIRMED:
            return Stopped(StopReason.DATA_DELETED)
        if not self._usage_limiter.claim_message(snapshot):
            self._conversations.deliver_at_once(
                message.conversation_id,
                message.chat_id,
                self._usage_limiter.limit_reply(snapshot.settings),
            )
            return Stopped(StopReason.OVER_LIMIT)
        data_deletion_cancelled = data_deletion_answer == DataDeletionAnswer.CANCELLED
        return ReplyNeeded(data_deletion_cancelled)
