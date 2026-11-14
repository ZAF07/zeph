from dataclasses import dataclass

from companion.core.conversations import ConversationService
from companion.core.knowledge_retrieval import KnowledgeRetrieval
from companion.core.memory_retrieval import MemoryRetrieval
from companion.core.reply_gate import ReplyGate
from companion.core.response_composition import ResponseComposer


@dataclass(frozen=True)
class ConversationServices:
    """The core services the conversation engine runs.

    Attributes:
        reply_gate: Saves each message and applies the house rules.
        conversations: Sends composed replies.
        memory_retrieval: Finds the User Memory that matters for a message.
        knowledge_retrieval: Finds the Knowledge that may fit a message.
        response_composer: Writes the Companion's reply.
    """

    reply_gate: ReplyGate
    conversations: ConversationService
    memory_retrieval: MemoryRetrieval
    knowledge_retrieval: KnowledgeRetrieval
    response_composer: ResponseComposer
