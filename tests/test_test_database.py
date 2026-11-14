from sqlalchemy import Engine, text

from tests.conftest import worker_database_name


def test_tests_run_against_this_workers_own_database(
    engine: Engine, worker_id: str
) -> None:
    with engine.connect() as connection:
        database_name = connection.execute(text("SELECT current_database()")).scalar()

    assert database_name == worker_database_name(worker_id)
