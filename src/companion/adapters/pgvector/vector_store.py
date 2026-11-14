from collections.abc import Sequence
from uuid import UUID, uuid4

from sqlalchemy import Engine, delete, insert, select

from companion.adapters.postgres.tables import knowledge_chunks
from companion.core.models import EmbeddedChunk, KnowledgeChunkMatch


class PgvectorKnowledgeVectorStore:
    """Stores Knowledge chunk embeddings in Postgres with pgvector.

    Chunks are found by cosine distance, closest first.
    """

    def __init__(self, engine: Engine) -> None:
        """Set up the store.

        Args:
            engine: The database engine.
        """
        self._engine = engine

    def replace_chunks(self, document_id: UUID, chunks: list[EmbeddedChunk]) -> None:
        """Save a document's chunks in place of any it had, in one step.

        Args:
            document_id: The document the chunks are from.
            chunks: The chunks, in reading order.
        """
        with self._engine.begin() as connection:
            connection.execute(
                delete(knowledge_chunks).where(
                    knowledge_chunks.c.document_id == document_id
                )
            )
            if chunks:
                connection.execute(
                    insert(knowledge_chunks),
                    [
                        {
                            "id": uuid4(),
                            "document_id": document_id,
                            "position": position,
                            "text": chunk.text,
                            "embedding": chunk.embedding,
                        }
                        for position, chunk in enumerate(chunks)
                    ],
                )

    def delete_chunks(self, document_id: UUID) -> None:
        """Remove every chunk of a document.

        Args:
            document_id: The document.
        """
        with self._engine.begin() as connection:
            connection.execute(
                delete(knowledge_chunks).where(
                    knowledge_chunks.c.document_id == document_id
                )
            )

    def search(
        self,
        embedding: list[float],
        document_ids: Sequence[UUID],
        min_closeness: float,
        limit: int,
    ) -> list[KnowledgeChunkMatch]:
        """Find the chunks of some documents closest to an embedding.

        Closeness is cosine similarity.

        Args:
            embedding: What to search with.
            document_ids: The documents to search; only their chunks count.
            min_closeness: How close a chunk must be, from 0 to 1.
            limit: The most chunks to return.

        Returns:
            The closest chunks, best match first.
        """
        if not document_ids or limit < 1:
            return []
        distance = knowledge_chunks.c.embedding.cosine_distance(embedding)
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(knowledge_chunks.c.document_id, knowledge_chunks.c.text)
                .where(
                    knowledge_chunks.c.document_id.in_(document_ids),
                    distance <= 1 - min_closeness,
                )
                .order_by(distance)
                .limit(limit)
            ).all()
        return [
            KnowledgeChunkMatch(document_id=row.document_id, text=row.text)
            for row in rows
        ]
