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

    def search(self, embedding: list[float], limit: int) -> list[KnowledgeChunkMatch]:
        """Find the chunks closest to an embedding.

        Args:
            embedding: What to search with.
            limit: The most chunks to return.

        Returns:
            The closest chunks, best match first.
        """
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(knowledge_chunks.c.document_id, knowledge_chunks.c.text)
                .order_by(knowledge_chunks.c.embedding.cosine_distance(embedding))
                .limit(limit)
            ).all()
        return [
            KnowledgeChunkMatch(document_id=row.document_id, text=row.text)
            for row in rows
        ]
