from functools import partial

from sqlalchemy import Engine

from companion.adapters.clock import SystemClock
from companion.adapters.knowledge_seed import read_knowledge_seed
from companion.adapters.pgvector.vector_store import PgvectorKnowledgeVectorStore
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.adapters.pypdf.text_extractor import PypdfTextExtractor
from companion.core.knowledge import KnowledgeService
from companion.core.models import KnowledgeStatus
from tests.conftest import KNOWLEDGE_SEED_FILE
from tests.fakes import FakeEmbedder


def knowledge_service(engine: Engine) -> KnowledgeService:
    return KnowledgeService(
        repositories=build_postgres_repositories(engine),
        text_extractor=PypdfTextExtractor(),
        embedder=FakeEmbedder(),
        vector_store=PgvectorKnowledgeVectorStore(engine),
        clock=SystemClock(),
    )


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
