import json
from datetime import timedelta

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import MIGRATIONS_DIR, migrate
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import CheckInFrequency
from companion.core.platform_settings import CHECK_IN_GAPS
from tests.test_photo_viewing import stored_setting

GAPS_BEFORE_A_FEW_TIMES_A_DAY = {"weekly": 168, "few_times_a_week": 56, "most_days": 20}


def test_an_existing_install_gets_the_a_few_times_a_day_gap(
    engine: Engine, database_url: str
) -> None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.downgrade(config, "0046")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = :gaps "
                    "WHERE key = 'check_in_hours_between'"
                ),
                {"gaps": json.dumps(GAPS_BEFORE_A_FEW_TIMES_A_DAY)},
            )
    finally:
        migrate(database_url)

    assert stored_setting(engine, "check_in_hours_between") == (
        GAPS_BEFORE_A_FEW_TIMES_A_DAY | {"a_few_times_a_day": 6}
    )
    gaps = (
        build_postgres_repositories(engine).platform_settings.load().get(CHECK_IN_GAPS)
    )
    assert gaps[CheckInFrequency.A_FEW_TIMES_A_DAY] == timedelta(hours=6)
    assert gaps[CheckInFrequency.MOST_DAYS] == timedelta(hours=20)


def test_a_gap_already_set_for_a_few_times_a_day_is_kept(
    engine: Engine, database_url: str
) -> None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.downgrade(config, "0046")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = :gaps "
                    "WHERE key = 'check_in_hours_between'"
                ),
                {
                    "gaps": json.dumps(
                        GAPS_BEFORE_A_FEW_TIMES_A_DAY | {"a_few_times_a_day": 4}
                    )
                },
            )
    finally:
        migrate(database_url)

    assert stored_setting(engine, "check_in_hours_between")["a_few_times_a_day"] == 4
