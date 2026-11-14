import logging

from companion.core.models import (
    Feature,
    KnowledgeChunkMatch,
    KnowledgeDocument,
    KnowledgeLookup,
    KnowledgeStatus,
    UserSnapshot,
)
from companion.core.platform_settings import (
    KNOWLEDGE_CHUNKS_PER_REPLY,
    KNOWLEDGE_CLOSENESS_PERCENT,
    REPLY_KNOWLEDGE_INTRO,
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


def chosen_documents(
    documents: list[KnowledgeDocument], lookup: KnowledgeLookup
) -> list[KnowledgeDocument]:
    """Find the Ready documents the Understanding chose, by title.

    Args:
        documents: Every Knowledge document.
        lookup: What the Understanding chose.

    Returns:
        The Ready documents whose title it named, in any case; a title that
        matches none is ignored.
    """
    titles = {title.casefold() for title in lookup.documents}
    return [
        document
        for document in documents
        if document.status == KnowledgeStatus.READY
        and document.title.casefold() in titles
    ]


class KnowledgeRetrieval:
    """Finds passages in the Knowledge documents the Understanding chose."""

    def __init__(
        self,
        repositories: Repositories,
        embedder: Embedder,
        vector_store: KnowledgeVectorStore,
    ) -> None:
        """Set up Knowledge retrieval.

        Args:
            repositories: Where Knowledge documents are stored.
            embedder: Embeds the Understanding's search phrase.
            vector_store: Finds the closest Knowledge chunks.
        """
        self._repositories = repositories
        self._embedder = embedder
        self._vector_store = vector_store

    def recall(self, snapshot: UserSnapshot, lookup: KnowledgeLookup | None) -> str:
        """Write the passages from the chosen documents closest to the phrase.

        Only the chosen Ready documents are searched, and only passages at
        least as close as the Admin-set bar count, at most
        `knowledge_chunks_per_reply`, given with where they come from.
        Nothing is searched when the Understanding chose nothing or
        Knowledge doesn't work for the User. If the search fails the reply
        goes ahead without them.

        Args:
            snapshot: The User being replied to.
            lookup: What the Understanding chose to search; None for nothing.

        Returns:
            The Knowledge section for the reply instructions; "" if none.
        """
        if lookup is None or not snapshot.works(Feature.KNOWLEDGE):
            return ""
        settings = snapshot.settings
        limit = settings.get(KNOWLEDGE_CHUNKS_PER_REPLY)
        documents = self._repositories.knowledge_documents.list_all()
        chosen = chosen_documents(documents, lookup)
        if limit < 1 or not chosen:
            return ""
        try:
            matches = self._vector_store.search(
                self._embedder.embed_query(lookup.search),
                [document.id for document in chosen],
                min_closeness=settings.get(KNOWLEDGE_CLOSENESS_PERCENT) / 100,
                limit=limit,
            )
        except Exception:
            logger.exception("Knowledge retrieval could not search Knowledge")
            return ""
        return format_knowledge(matches, chosen, settings.get(REPLY_KNOWLEDGE_INTRO))
