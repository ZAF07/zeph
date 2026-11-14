import logging
from uuid import UUID

from companion.core.models import (
    Feature,
    KnowledgeChunkMatch,
    KnowledgeDocument,
    KnowledgeStatus,
    UserSnapshot,
)
from companion.core.ports import Embedder, KnowledgeVectorStore, Repositories

logger = logging.getLogger(__name__)


def format_knowledge(
    matches: list[KnowledgeChunkMatch],
    documents: list[KnowledgeDocument],
    intro: str,
) -> str:
    """Write the Knowledge part of the reply instructions.

    Chunks from documents that are not ready, or no longer exist, are left
    out.

    Args:
        matches: The closest chunks, best match first.
        documents: Every Knowledge document.
        intro: The Admin-set line that tells the model how to use Knowledge.

    Returns:
        The Knowledge section, or "" if there is nothing to give.
    """
    ready_documents = {
        document.id: document
        for document in documents
        if document.status == KnowledgeStatus.READY
    }
    passages = [
        f"From “{document.title}” ({document.source}, {document.tradition}):\n"
        f"{match.text}"
        for match in matches
        if (document := ready_documents.get(match.document_id)) is not None
    ]
    if not passages:
        return ""
    return intro + "\n\n" + "\n\n".join(passages)


class KnowledgeRetrieval:
    """Finds the Knowledge that may fit the message being answered."""

    def __init__(
        self,
        repositories: Repositories,
        embedder: Embedder,
        vector_store: KnowledgeVectorStore,
    ) -> None:
        """Set up Knowledge retrieval.

        Args:
            repositories: Where Conversations, Knowledge documents and
                settings are stored.
            embedder: Embeds the message to search with.
            vector_store: Finds the closest Knowledge chunks.
        """
        self._repositories = repositories
        self._embedder = embedder
        self._vector_store = vector_store

    def recall(self, snapshot: UserSnapshot, conversation_id: UUID) -> str:
        """Write the Knowledge passages closest to the newest message.

        The newest message is embedded and the top few chunks, as many as the
        `knowledge_chunks_per_reply` setting says, are given with where they
        come from. Nothing is searched when Knowledge doesn't work for the
        User. If the search fails the reply goes ahead without them.

        Args:
            snapshot: The User being replied to.
            conversation_id: The Conversation the message is in.

        Returns:
            The Knowledge section for the reply instructions; "" if none.
        """
        if not snapshot.works(Feature.KNOWLEDGE):
            return ""
        settings = self._repositories.platform_settings
        limit = settings.get("knowledge_chunks_per_reply")
        messages = self._repositories.conversations.list_messages(conversation_id)
        if limit < 1 or not messages:
            return ""
        try:
            matches = self._vector_store.search(
                self._embedder.embed_query(messages[-1].content), limit
            )
        except Exception:
            logger.exception("Knowledge retrieval could not search Knowledge")
            return ""
        if not matches:
            return ""
        return format_knowledge(
            matches,
            self._repositories.knowledge_documents.list_all(),
            settings.get("reply_knowledge_intro"),
        )
