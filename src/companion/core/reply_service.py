from companion.core.conversations import ConversationService
from companion.core.knowledge_retrieval import KnowledgeRetrieval
from companion.core.memory_retrieval import MemoryRetrieval
from companion.core.models import MessageToAnswer, UserSnapshot
from companion.core.reply_gate import ReplyGate, Stopped
from companion.core.response_composition import ResponseComposer
from companion.core.understanding import UnderstandingService


class ReplyService:
    """Answers a connected User's Message, one step after another (ADR-0009).

    The steps run in this order: the ReplyGate applies the house rules left
    once the Message's texts are saved and checked, then the Understanding
    works out what the User needs and which User Memory matters, then that
    memory, any older Conversations it asked to look up and the Knowledge
    that may fit are recalled, then the reply is composed and delivered.
    Every step reads the User from the same snapshot.
    """

    def __init__(
        self,
        reply_gate: ReplyGate,
        conversations: ConversationService,
        understanding: UnderstandingService,
        memory_retrieval: MemoryRetrieval,
        knowledge_retrieval: KnowledgeRetrieval,
        response_composer: ResponseComposer,
    ) -> None:
        """Set up the service.

        Args:
            reply_gate: Applies the house rules to each Message.
            conversations: Sends composed replies.
            understanding: Works out what the User needs before each reply.
            memory_retrieval: Reads the User Memory and picks out what the
                Understanding chose.
            knowledge_retrieval: Finds the Knowledge that may fit a message.
            response_composer: Writes the Companion's reply.
        """
        self._reply_gate = reply_gate
        self._conversations = conversations
        self._understanding = understanding
        self._memory_retrieval = memory_retrieval
        self._knowledge_retrieval = knowledge_retrieval
        self._response_composer = response_composer

    def handle(self, message: MessageToAnswer, snapshot: UserSnapshot) -> None:
        """Answer one screened Message: apply the house rules, then reply if needed.

        When the ReplyGate stops the reply nothing is composed. A failing
        step raises, so the caller can send its fallback message.

        Args:
            message: The Message to answer, its texts already saved and
                checked by the Safeguard.
            snapshot: The User who sent it, read once as the reply starts.
        """
        gate_result = self._reply_gate.check(message, snapshot)
        if isinstance(gate_result, Stopped):
            return
        saved_memory = self._memory_retrieval.read(snapshot)
        understood = self._understanding.understand(
            snapshot, message.conversation_id, saved_memory
        )
        form = understood.understanding.form
        memory = self._memory_retrieval.recall(
            snapshot, saved_memory, form.memory_categories, form.look_up_past
        )
        knowledge = self._knowledge_retrieval.recall(snapshot, message.conversation_id)
        reply = self._response_composer.compose(
            message.conversation_id,
            snapshot,
            memory.text,
            knowledge,
            reply_guidance=understood.reply_guidance,
            data_deletion_note=gate_result.data_deletion_note,
            shared_photo_ids=memory.shared_photo_ids,
        )
        self._conversations.deliver_reply(
            message.user_id,
            message.conversation_id,
            message.chat_id,
            reply.parts,
            snapshot.settings,
            reply.sticker.id if reply.sticker else None,
            reply.shared_photo.id if reply.shared_photo else None,
        )
