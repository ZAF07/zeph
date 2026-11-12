from uuid import UUID

from sqlalchemy import Engine

from companion.adapters.clock import SystemClock
from companion.adapters.pgvector.vector_store import PgvectorKnowledgeVectorStore
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.adapters.pypdf.text_extractor import PypdfTextExtractor
from companion.core.knowledge import KnowledgeService
from companion.core.models import KnowledgeFileType, KnowledgeStatus, KnowledgeUpload
from tests.fakes import FakeEmbedder


class EditingDuringIndexingEmbedder(FakeEmbedder):
    """Embedder that runs an Admin's next text edit while it embeds, once."""

    def __init__(self) -> None:
        super().__init__()
        self.edit_while_embedding: list[tuple[KnowledgeService, UUID, str]] = []

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        while self.edit_while_embedding:
            service, document_id, text = self.edit_while_embedding.pop()
            service.save_text(document_id, text)
        return super().embed_passages(texts)


def test_an_older_reindex_never_overwrites_a_newer_edit(engine: Engine) -> None:
    embedder = EditingDuringIndexingEmbedder()
    service = KnowledgeService(
        repositories=build_postgres_repositories(engine),
        text_extractor=PypdfTextExtractor(),
        embedder=embedder,
        vector_store=PgvectorKnowledgeVectorStore(engine),
        clock=SystemClock(),
    )
    document = service.upload(
        KnowledgeUpload(
            title="Breath",
            source="Owner’s summary",
            tradition="Mindfulness",
            file_name="breath.txt",
            file_type=KnowledgeFileType.TEXT,
            content=b"Notice the breath.",
        )
    )
    service.ingest(document.id)
    service.save_text(document.id, "First edit.")
    embedder.edit_while_embedding.append((service, document.id, "Second edit."))

    service.ingest(document.id)

    assert service.get_document(document.id).document.status == (
        KnowledgeStatus.PENDING
    )
    service.ingest(document.id)
    finished = service.get_document(document.id)
    assert finished.document.status == KnowledgeStatus.READY
    assert finished.text == "Second edit."
