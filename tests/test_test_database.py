from sqlalchemy import Engine, text

from tests.conftest import throwaway_postgres, worker_database_name


def test_tests_run_against_this_workers_own_database(
    engine: Engine, worker_id: str
) -> None:
    with engine.connect() as connection:
        database_name = connection.execute(text("SELECT current_database()")).scalar()

    assert database_name == worker_database_name(worker_id)


def test_the_test_postgres_makes_no_docker_volume() -> None:
    postgres = throwaway_postgres()
    postgres.start()
    try:
        mounts = postgres.get_wrapped_container().attrs["Mounts"]
    finally:
        postgres.stop()

    assert [mount for mount in mounts if mount["Type"] == "volume"] == []
