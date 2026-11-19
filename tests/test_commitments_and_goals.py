import importlib
from datetime import date
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
from companion.main import MEMORY_CATEGORIES_SEED_FILE
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import connect_telegram
from tests.test_curiosities import end_conversation, new_curiosity, stored_curiosities
from tests.test_moves_migration import downgrade_to

CALL_MUM_FOLLOW_UP = "Did you get to call your mum?"
CALL_MUM_WHY = "They agreed to call their mum tonight after the argument."
CHANGED_PROMPT_KEYS = (
    "memory_processing_prompt",
    "life_thread_keeping_prompt",
    "curiosity_keeping_prompt",
)


def one_line(prompt: str) -> str:
    """Join a prompt's lines so a phrase can be found across line breaks."""
    return " ".join(prompt.split())


def commitments_migration() -> ModuleType:
    """Load the commitments, goals and one home migration module."""
    return importlib.import_module(
        "companion.adapters.postgres.migrations.versions."
        "0065_commitments_goals_one_home"
    )


def stored_prompts(engine: Engine) -> dict[str, str]:
    """Read the stored values of the prompts this issue changes."""
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT key, value #>> '{}' FROM platform_settings "
                "WHERE key = ANY(:keys)"
            ),
            {"keys": list(CHANGED_PROMPT_KEYS)},
        ).all()
    return {key: value for key, value in rows}


def challenges_description(engine: Engine) -> str:
    """Read the stored Challenges Memory Category description."""
    with engine.connect() as connection:
        description: str = connection.execute(
            text("SELECT description FROM memory_categories WHERE name = 'Challenges'")
        ).scalar_one()
    return description


def store_prompts_and_challenges_description(
    engine: Engine, prompts: dict[str, str], challenges: str
) -> None:
    """Store the given prompt values and Challenges description."""
    with engine.begin() as connection:
        for key, value in prompts.items():
            connection.execute(
                text(
                    "UPDATE platform_settings "
                    "SET value = to_jsonb(CAST(:value AS text)) WHERE key = :key"
                ),
                {"key": key, "value": value},
            )
        connection.execute(
            text(
                "UPDATE memory_categories SET description = :description "
                "WHERE name = 'Challenges'"
            ),
            {"description": challenges},
        )


def test_the_thread_keeping_prompt_keeps_agreed_commitments_with_dates_and_outcomes(
    seeded_settings: dict[str, Any],
) -> None:
    prompt = one_line(seeded_settings["life_thread_keeping_prompt"])

    assert "commitment they agreed to" in prompt
    assert "with the day it was due" in prompt
    assert "once they say how it went" in prompt
    assert "Zeph only suggested is not a commitment" in prompt


def test_the_curiosity_keeping_prompt_follows_up_a_commitment_after_its_day(
    seeded_settings: dict[str, Any],
) -> None:
    prompt = one_line(seeded_settings["curiosity_keeping_prompt"])

    assert "A commitment they agreed to" in prompt
    assert "not_before at least the day after it was due" in prompt


def test_a_commitment_follow_up_from_the_keeping_step_is_saved_with_its_day(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "ok you're right, I'll call mum tonight and say sorry",
        [
            new_curiosity(
                ask=CALL_MUM_FOLLOW_UP,
                why=CALL_MUM_WHY,
                not_before="2026-11-12",
                sensitivity="medium",
            )
        ],
    )
    keeper_instructions = one_line(chat_model.curiosity_keeping_calls[-1].instructions)
    [row] = stored_curiosities(engine)

    assert "A commitment they agreed to" in keeper_instructions
    assert (row["question"], row["not_before"]) == (
        CALL_MUM_FOLLOW_UP,
        date(2026, 11, 12),
    )


def test_the_memory_processing_prompt_keeps_goals_shown_plainly(
    seeded_settings: dict[str, Any],
) -> None:
    prompt = one_line(seeded_settings["memory_processing_prompt"])

    assert "in the Goals category when they show it plainly" in prompt
    assert 'even if they never say "my goal is"' in prompt


def test_the_memory_and_thread_prompts_state_the_one_home_rule(
    seeded_settings: dict[str, Any],
) -> None:
    for key in ("memory_processing_prompt", "life_thread_keeping_prompt"):
        prompt = one_line(seeded_settings[key])

        assert "Each thing learned has one home" in prompt
        assert "a single fact about them is a Memory Item" in prompt
        assert "a story that goes on across Conversations is a Life Thread" in prompt
        assert "what keeps showing up across their stories is left for Patterns" in (
            prompt
        )


def test_the_seeded_challenges_description_drops_patterns() -> None:
    categories = yaml.safe_load(Path(MEMORY_CATEGORIES_SEED_FILE).read_text())
    [challenges] = [c for c in categories if c["name"] == "Challenges"]

    assert "pattern" not in challenges["description"].lower()
    assert challenges["description"] == (
        commitments_migration().NEW_CHALLENGES_DESCRIPTION
    )


def test_the_migration_reloads_prompts_and_wording_still_matching_the_old_seed(
    engine: Engine, database_url: str
) -> None:
    migration = commitments_migration()
    downgrade_to(database_url, "0064")
    try:
        store_prompts_and_challenges_description(
            engine, migration.OLD_PROMPTS, migration.OLD_CHALLENGES_DESCRIPTION
        )
    finally:
        migrate(database_url)

    assert stored_prompts(engine) == {}
    assert challenges_description(engine) == migration.NEW_CHALLENGES_DESCRIPTION


def test_the_migration_keeps_prompts_and_wording_an_admin_edited(
    engine: Engine, database_url: str
) -> None:
    edited_prompts = {key: f"Admin's own {key}" for key in CHANGED_PROMPT_KEYS}
    downgrade_to(database_url, "0064")
    try:
        store_prompts_and_challenges_description(
            engine, edited_prompts, "Admin's own Challenges wording."
        )
    finally:
        migrate(database_url)

    assert stored_prompts(engine) == edited_prompts
    assert challenges_description(engine) == "Admin's own Challenges wording."
