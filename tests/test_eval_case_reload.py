import logging
from datetime import UTC, datetime

import pytest
from sqlalchemy import Engine, text

from companion.adapters.postgres.eval_case_reload import reload_eval_case_unless_edited
from companion.adapters.postgres.eval_repositories import PostgresEvalCaseRepository
from companion.core.evals.models import EvalCase, EvalName

CASE_KEY = "guess-checked-gently"
PREVIOUS_SEED_CASE = EvalCase(
    CASE_KEY, EvalName.UNDERSTANDING, {"messages": [{"text": "the previous seed"}]}
)
NEW_SEED_CASE = EvalCase(
    CASE_KEY, EvalName.UNDERSTANDING, {"messages": [{"text": "the new seed"}]}
)


def store_previous_seed_case(engine: Engine) -> None:
    """Store the case as the previous seed loaded it."""
    PostgresEvalCaseRepository(engine).add_missing(
        [PREVIOUS_SEED_CASE], datetime.now(UTC)
    )


def mark_stored_case(engine: Engine, column: str) -> None:
    """Mark the stored case as edited or archived, as an Admin's change would."""
    with engine.begin() as connection:
        connection.execute(
            text(f"UPDATE eval_cases SET {column} = true WHERE key = :key"),
            {"key": CASE_KEY},
        )


def stored_case_text(engine: Engine) -> str | None:
    """Read the stored case's first message text, or None if it isn't stored."""
    with engine.connect() as connection:
        message: str | None = connection.execute(
            text(
                "SELECT content #>> '{messages,0,text}' FROM eval_cases "
                "WHERE key = :key"
            ),
            {"key": CASE_KEY},
        ).scalar_one_or_none()
    return message


def reload_case(engine: Engine) -> None:
    """Run the helper as a migration replacing the seed case would, then seed."""
    with engine.begin() as connection:
        reload_eval_case_unless_edited(connection, CASE_KEY)
    PostgresEvalCaseRepository(engine).add_missing([NEW_SEED_CASE], datetime.now(UTC))


def test_a_case_no_admin_changed_reloads_from_the_new_seed(
    engine: Engine, caplog: pytest.LogCaptureFixture
) -> None:
    store_previous_seed_case(engine)

    with caplog.at_level(logging.WARNING):
        reload_case(engine)

    assert stored_case_text(engine) == "the new seed"
    assert caplog.text == ""


@pytest.mark.parametrize("admin_change", ["edited", "archived"])
def test_a_case_an_admin_edited_or_archived_is_kept_and_a_warning_names_it(
    engine: Engine, caplog: pytest.LogCaptureFixture, admin_change: str
) -> None:
    store_previous_seed_case(engine)
    mark_stored_case(engine, admin_change)

    with caplog.at_level(logging.WARNING):
        reload_case(engine)

    assert stored_case_text(engine) == "the previous seed"
    assert CASE_KEY in caplog.text


def test_a_case_not_stored_yet_is_left_alone_without_a_warning(
    engine: Engine, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING):
        with engine.begin() as connection:
            reload_eval_case_unless_edited(connection, CASE_KEY)

    assert stored_case_text(engine) is None
    assert caplog.text == ""
