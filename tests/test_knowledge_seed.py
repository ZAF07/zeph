from functools import partial
from uuid import UUID

from sqlalchemy import Engine, select, update

from companion.adapters.clock import SystemClock
from companion.adapters.knowledge_seed import read_knowledge_seed
from companion.adapters.pgvector.vector_store import PgvectorKnowledgeVectorStore
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.adapters.postgres.tables import knowledge_chunks, knowledge_documents
from companion.adapters.pypdf.text_extractor import PypdfTextExtractor
from companion.core.knowledge import KnowledgeService
from companion.core.models import KnowledgeFileType, KnowledgeStatus, KnowledgeUpload
from tests.conftest import KNOWLEDGE_SEED_FILE
from tests.fakes import FakeEmbedder
from tests.knowledge_helpers import blank_pdf


def knowledge_service(engine: Engine) -> KnowledgeService:
    return KnowledgeService(
        repositories=build_postgres_repositories(engine),
        text_extractor=PypdfTextExtractor(),
        embedder=FakeEmbedder(),
        vector_store=PgvectorKnowledgeVectorStore(engine),
        clock=SystemClock(),
    )


def chunk_ids(engine: Engine) -> set[UUID]:
    with engine.connect() as connection:
        return set(connection.execute(select(knowledge_chunks.c.id)).scalars())


def test_the_starter_mindfulness_set_is_seeded_ready_from_the_data_files(
    engine: Engine,
) -> None:
    service = knowledge_service(engine)

    service.seed_starter_set(partial(read_knowledge_seed, KNOWLEDGE_SEED_FILE))

    documents = service.list_documents()
    assert sorted((d.title, d.tradition) for d in documents) == [
        ("Dhammapada (selections)", "Buddhism"),
        ("Meditations, Books II and IV", "Stoicism"),
        ("Mindful breathing", "Mindfulness"),
        ("Noticing thoughts without following them", "Mindfulness"),
        ("Self-compassion", "Psychology"),
        ("Tao Te Ching (selections)", "Taoism"),
    ]
    assert {document.status for document in documents} == {KnowledgeStatus.READY}


def test_the_starter_set_is_seeded_only_on_first_run(engine: Engine) -> None:
    service = knowledge_service(engine)
    read_starter_set = partial(read_knowledge_seed, KNOWLEDGE_SEED_FILE)
    service.seed_starter_set(read_starter_set)
    [deleted, *kept] = service.list_documents()
    service.delete(deleted.id)

    service.seed_starter_set(read_starter_set)

    assert [document.id for document in service.list_documents()] == [
        document.id for document in kept
    ]


def test_documents_left_pending_by_a_restart_are_ingested_on_the_next_start(
    engine: Engine,
) -> None:
    service = knowledge_service(engine)
    [upload, *_] = read_knowledge_seed(KNOWLEDGE_SEED_FILE)
    interrupted = service.upload(upload)

    service.ingest_pending()

    [document] = service.list_documents()
    assert document.id == interrupted.id
    assert document.status == KnowledgeStatus.READY


def test_every_starter_document_has_its_text(engine: Engine) -> None:
    service = knowledge_service(engine)

    service.seed_starter_set(partial(read_knowledge_seed, KNOWLEDGE_SEED_FILE))

    for document in service.list_documents():
        text = service.get_document(document.id).text
        assert text, document.title
        assert not text.startswith(" ")


def test_documents_from_before_text_was_saved_get_it_on_start_without_reindexing(
    engine: Engine,
) -> None:
    service = knowledge_service(engine)
    [upload, *_] = read_knowledge_seed(KNOWLEDGE_SEED_FILE)
    older = service.upload(upload)
    service.ingest(older.id)
    scan = service.upload(
        KnowledgeUpload(
            title="Scan",
            source="Unknown",
            tradition="Other",
            file_name="scan.pdf",
            file_type=KnowledgeFileType.PDF,
            content=blank_pdf(),
        )
    )
    service.ingest(scan.id)
    with engine.begin() as connection:
        connection.execute(update(knowledge_documents).values(text=None))
    chunk_ids_before = chunk_ids(engine)

    service.read_missing_texts()

    assert service.get_document(older.id).text == upload.content.decode().strip()
    assert service.get_document(older.id).document.status == KnowledgeStatus.READY
    assert chunk_ids(engine) == chunk_ids_before
    still_failed = service.get_document(scan.id)
    assert still_failed.text is None
    assert still_failed.document.status == KnowledgeStatus.FAILED


def test_a_text_edit_left_pending_by_a_restart_is_finished_on_the_next_start(
    engine: Engine,
) -> None:
    service = knowledge_service(engine)
    [upload, *_] = read_knowledge_seed(KNOWLEDGE_SEED_FILE)
    document = service.upload(upload)
    service.ingest(document.id)
    service.save_text(document.id, "Edited by an Admin before a restart.")

    service.ingest_pending()

    finished = service.get_document(document.id)
    assert finished.document.status == KnowledgeStatus.READY
    assert finished.document.text_edited
    assert finished.text == "Edited by an Admin before a restart."
