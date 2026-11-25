import logging

import pytest
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import seed_platform_settings
from companion.adapters.postgres.prompt_reload import (
    prompt_hash,
    reload_prompt_unless_edited,
)
from scripts.seed_prompt_hash import seed_prompt_hash
from tests.conftest import SEED_FILE

PROMPT_KEY = "pattern_tagging_prompt"
PREVIOUS_SEED_PROMPT = "You read a Conversation — and note what the person said.\n"
ADMIN_PROMPT = "The Admin's own words for the tagging step."


def store_prompt(engine: Engine, prompt: str) -> None:
    """Store a prompt's text, as the old seed or an Admin would have."""
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE platform_settings SET value = to_jsonb(CAST(:prompt AS text)) "
                "WHERE key = :key"
            ),
            {"prompt": prompt, "key": PROMPT_KEY},
        )


def stored_prompt(engine: Engine) -> str | None:
    """Read the stored prompt's text, or None if it isn't stored."""
    with engine.connect() as connection:
        prompt: str | None = connection.execute(
            text("SELECT value #>> '{}' FROM platform_settings WHERE key = :key"),
            {"key": PROMPT_KEY},
        ).scalar_one_or_none()
    return prompt


def reload_prompt(engine: Engine) -> None:
    """Run the helper as a migration replacing the previous seed prompt would."""
    with engine.begin() as connection:
        reload_prompt_unless_edited(
            connection, PROMPT_KEY, prompt_hash(PREVIOUS_SEED_PROMPT)
        )


def test_a_prompt_still_at_the_previous_seed_reloads_from_the_new_seed(
    engine: Engine, caplog: pytest.LogCaptureFixture
) -> None:
    new_seed_prompt = stored_prompt(engine)
    store_prompt(engine, PREVIOUS_SEED_PROMPT)

    with caplog.at_level(logging.WARNING):
        reload_prompt(engine)

    assert stored_prompt(engine) is None
    assert caplog.text == ""
    seed_platform_settings(engine, SEED_FILE)
    assert stored_prompt(engine) == new_seed_prompt


def test_a_prompt_an_admin_edited_is_kept_and_a_warning_names_it(
    engine: Engine, caplog: pytest.LogCaptureFixture
) -> None:
    store_prompt(engine, ADMIN_PROMPT)

    with caplog.at_level(logging.WARNING):
        reload_prompt(engine)

    assert stored_prompt(engine) == ADMIN_PROMPT
    assert PROMPT_KEY in caplog.text
    seed_platform_settings(engine, SEED_FILE)
    assert stored_prompt(engine) == ADMIN_PROMPT


def test_a_prompt_not_stored_yet_is_left_alone_without_a_warning(
    engine: Engine, caplog: pytest.LogCaptureFixture
) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM platform_settings WHERE key = :key"), {"key": PROMPT_KEY}
        )

    with caplog.at_level(logging.WARNING):
        reload_prompt(engine)

    assert stored_prompt(engine) is None
    assert caplog.text == ""


def test_a_previous_seed_hash_that_is_not_a_prompt_hash_is_refused(
    engine: Engine,
) -> None:
    store_prompt(engine, ADMIN_PROMPT)

    with engine.begin() as connection, pytest.raises(ValueError, match=PROMPT_KEY):
        reload_prompt_unless_edited(connection, PROMPT_KEY, "1b761f35…")

    assert stored_prompt(engine) == ADMIN_PROMPT


def test_the_seed_prompt_hash_is_the_hash_of_the_text_the_seed_loads() -> None:
    seed_yaml = f"other_setting: 4\n{PROMPT_KEY}: |\n  {PREVIOUS_SEED_PROMPT}"

    assert seed_prompt_hash(seed_yaml, PROMPT_KEY) == prompt_hash(PREVIOUS_SEED_PROMPT)


def test_the_seed_prompt_hash_refuses_a_setting_the_seed_does_not_hold() -> None:
    with pytest.raises(KeyError):
        seed_prompt_hash("other_setting: 4\n", PROMPT_KEY)
