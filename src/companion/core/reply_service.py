from companion.core.conversations import ConversationService
from companion.core.knowledge_retrieval import KnowledgeRetrieval
from companion.core.memory_retrieval import MemoryRetrieval
from companion.core.models import MessageToAnswer, UserSnapshot
from companion.core.reply_gate import ReplyGate, Stopped
from companion.core.response_composition import ResponseComposer


class ReplyService:
    """Answers a connected User's message, one step after another (ADR-0009).

    The steps run in this order: the ReplyGate saves the message and applies
    the house rules, then the User Memory that matters and the Knowledge that
    may fit are recalled, then the reply is composed and delivered. Every step
    reads the User from the same snapshot.
    """

    def __init__(
        self,
        reply_gate: ReplyGate,
        conversations: ConversationService,
        memory_retrieval: MemoryRetrieval,
        knowledge_retrieval: KnowledgeRetrieval,
        response_composer: ResponseComposer,
    ) -> None:
        """Set up the service.

        Args:
            reply_gate: Saves each message and applies the house rules.
            conversations: Sends composed replies.
            memory_retrieval: Finds the User Memory that matters for a message.
            knowledge_retrieval: Finds the Knowledge that may fit a message.
            response_composer: Writes the Companion's reply.
        """
        self._reply_gate = reply_gate
        self._conversations = conversations
        self._memory_retrieval = memory_retrieval
        self._knowledge_retrieval = knowledge_retrieval
        self._response_composer = response_composer

    def handle(self, message: MessageToAnswer, snapshot: UserSnapshot) -> None:
        """Answer one message: apply the house rules, then reply if needed.

        When the ReplyGate stops the reply nothing is composed. A failing
        step raises, so the caller can send its fallback message.

        Args:
            message: The message to answer.
            snapshot: The User who sent it, read once as the reply starts.
        """
        gate_result = self._reply_gate.check(message, snapshot)
        if isinstance(gate_result, Stopped):
            return
        memory = self._memory_retrieval.recall(snapshot, gate_result.conversation_id)
        knowledge = self._knowledge_retrieval.recall(
            snapshot, gate_result.conversation_id
        )
        reply = self._response_composer.compose(
            gate_result.conversation_id,
            snapshot,
            memory.text,
            knowledge,
            data_deletion_cancelled=gate_result.data_deletion_cancelled,
            shared_photo_ids=memory.shared_photo_ids,
        )
        self._conversations.deliver_reply(
            message.user_id,
            gate_result.conversation_id,
            message.chat_id,
            reply.parts,
            snapshot.settings,
            reply.sticker.id if reply.sticker else None,
            reply.shared_photo.id if reply.shared_photo else None,
        )
