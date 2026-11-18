from datetime import date
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
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
from tests.test_user_portrait import end_conversation_with_portrait

BOSS_LOOK_BACK = "How are you feeling about the thing with your boss now?"
BOSS_WHY = "They vented about their boss taking credit; Zeph only listened."


def test_a_look_back_from_the_keeping_step_is_saved_with_its_day_and_sensitivity(
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
        "my boss took credit for my work AGAIN in the meeting, I'm so done",
        [
            new_curiosity(
                ask=BOSS_LOOK_BACK,
                why=BOSS_WHY,
                not_before="2026-11-12",
                sensitivity="medium",
            )
        ],
    )
    keeper_instructions = " ".join(
        chat_model.curiosity_keeping_calls[-1].instructions.split()
    )
    [row] = stored_curiosities(engine)

    assert "vented about where Zeph only listened" in keeper_instructions
    assert (row["question"], row["not_before"], row["sensitivity"]) == (
        BOSS_LOOK_BACK,
        date(2026, 11, 12),
        "medium",
    )


def test_the_seeded_keeping_prompt_asks_for_look_backs_a_day_later_at_least_medium(
    seeded_settings: dict[str, Any],
) -> None:
    prompt = " ".join(seeded_settings["curiosity_keeping_prompt"].split())

    assert "vented about where Zeph only listened" in prompt
    assert "not_before at least the next day" in prompt
    assert "sensitivity at least medium" in prompt


def test_the_portrait_is_written_from_what_zeph_is_sure_of_without_open_questions(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )
    [call] = chat_model.portrait_calls

    assert "open questions" not in call.instructions.lower()
    assert "fairly sure" in call.instructions


def test_the_look_backs_migration_reloads_the_keeping_and_portrait_prompts(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0058")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = to_jsonb('Old prompt'::text) "
                    "WHERE key IN ('curiosity_keeping_prompt', 'portrait_prompt')"
                )
            )
    finally:
        migrate(database_url)

    with engine.connect() as connection:
        prompts = connection.execute(
            text(
                "SELECT key FROM platform_settings "
                "WHERE key IN ('curiosity_keeping_prompt', 'portrait_prompt')"
            )
        ).all()
    assert prompts == []
