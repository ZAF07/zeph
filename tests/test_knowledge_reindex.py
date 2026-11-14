from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Engine

from companion.adapters.clock import SystemClock
from companion.adapters.pgvector.vector_store import PgvectorKnowledgeVectorStore
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.adapters.pypdf.text_extractor import PypdfTextExtractor
from companion.core.knowledge import KnowledgeService
from companion.core.models import (
    ChatLine,
    KnowledgeDetailsChange,
    KnowledgeFileType,
    KnowledgeStatus,
    KnowledgeUpload,
    ModelAnswer,
)
from companion.core.ports import ChatTool
from tests.fakes import FakeEmbedder, ScriptedChatModel


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
        chat_model=ScriptedChatModel(),
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


class EditingDuringDraftChatModel(ScriptedChatModel):
    """Chat model that runs an Admin's "when it helps" edit while it drafts, once."""

    def __init__(self) -> None:
        super().__init__()
        self.edit_while_drafting: list[tuple[KnowledgeService, UUID, str]] = []

    def generate(
        self,
        model: str,
        instructions: str,
        history: list[ChatLine],
        tools: Sequence[ChatTool] = (),
    ) -> ModelAnswer:
        while self.edit_while_drafting:
            service, document_id, text = self.edit_while_drafting.pop()
            service.update_details(
                document_id, KnowledgeDetailsChange(when_it_helps=text)
            )
        return ModelAnswer(text="A drafted description.", tokens_in=1, tokens_out=1)


def test_a_draft_never_overwrites_an_admins_edit_saved_meanwhile(
    engine: Engine,
) -> None:
    chat_model = EditingDuringDraftChatModel()
    service = KnowledgeService(
        repositories=build_postgres_repositories(engine),
        text_extractor=PypdfTextExtractor(),
        embedder=FakeEmbedder(),
        vector_store=PgvectorKnowledgeVectorStore(engine),
        chat_model=chat_model,
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
    chat_model.edit_while_drafting.append(
        (service, document.id, "When they can't sleep.")
    )

    service.ingest(document.id)

    finished = service.get_document(document.id).document
    assert finished.status == KnowledgeStatus.READY
    assert finished.when_it_helps == "When they can't sleep."
