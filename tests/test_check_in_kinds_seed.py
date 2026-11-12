from sqlalchemy import Engine

from companion.adapters.postgres.database import seed_check_in_kinds
from companion.adapters.postgres.repositories import build_postgres_repositories
from tests.conftest import CHECK_IN_KINDS_SEED_FILE


def test_starting_check_in_kinds_come_from_the_seed_file(engine: Engine) -> None:
    kinds = build_postgres_repositories(engine).check_ins.list_kinds()

    assert [(kind.name, kind.allowed_without_user_memory) for kind in kinds] == [
        ("A casual hello", True),
        ("A follow-up", False),
        ("A present-moment pause", True),
        ("A thought to reflect on", False),
    ]
    assert kinds[0].description == "Just checking how you are."


def test_check_in_kinds_are_seeded_only_on_first_run(engine: Engine) -> None:
    seed_check_in_kinds(engine, CHECK_IN_KINDS_SEED_FILE)

    kinds = build_postgres_repositories(engine).check_ins.list_kinds()
    assert len(kinds) == 4
