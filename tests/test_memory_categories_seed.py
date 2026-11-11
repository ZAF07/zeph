import yaml
from sqlalchemy import Engine

from companion.adapters.postgres.database import seed_memory_categories
from companion.adapters.postgres.repositories import build_postgres_repositories
from tests.conftest import MEMORY_CATEGORIES_SEED_FILE


def test_starting_memory_categories_come_from_the_seed_file(engine: Engine) -> None:
    categories = build_postgres_repositories(engine).memory_categories.list_all()

    assert [
        (category.name, category.always_include, category.archived)
        for category in categories
    ] == [
        ("Life details", False, False),
        ("Relationships", False, False),
        ("Goals", False, False),
        ("Values & beliefs", True, False),
        ("Challenges", True, False),
        ("Preferences", True, False),
        ("What helps", False, False),
    ]
    seed = yaml.safe_load(MEMORY_CATEGORIES_SEED_FILE.read_text())
    assert [category.description for category in categories] == [
        entry["description"] for entry in seed
    ]


def test_memory_categories_are_seeded_only_on_first_run(engine: Engine) -> None:
    seed_memory_categories(engine, MEMORY_CATEGORIES_SEED_FILE)

    categories = build_postgres_repositories(engine).memory_categories.list_all()
    assert len(categories) == 7
