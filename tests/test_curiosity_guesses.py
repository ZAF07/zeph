from datetime import timedelta
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
from tests.telegram_helpers import auth_headers, connect_telegram, owner_headers
from tests.test_curiosities import (
    bring_up_curiosity,
    end_conversation,
    new_curiosity,
    reply_instructions,
    stored_curiosities,
    understanding_sees,
)
from tests.test_curiosity_check_in import (
    check_in_model_saw,
    set_up_user_with_due_curiosities,
    wondering_answer,
)
from tests.test_features import maya_id, switch_for_user
from tests.test_moves_migration import downgrade_to

MUM = "Is your mum back home in Singapore now?"
MUM_WHY = "They said she went back to Singapore this morning."
MUM_GUESS = "their mum lives in Singapore"
MUM_GUESS_SHOWN = (
    f"A guess, not known: {MUM_GUESS} (how sure: medium). "
    "Check it gently; never state it as fact."
)


def mum_guess(how_sure: Any = "medium", **source: int) -> dict[str, Any]:
    """Build the mum guess as the keeping model writes it."""
    return {
        **new_curiosity(ask=MUM, why=MUM_WHY, not_before=None, **source),
        "guess": MUM_GUESS,
        "how_sure": how_sure,
    }


def mum_guess_is_waiting(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    """End a Conversation that hints at where their mum lives, keeping a guess."""
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "mum spent the week with me in Malaysia, she's back to Singapore today",
        [mum_guess()],
    )
    clock.advance(timedelta(days=1))


def test_a_guess_from_the_keeping_step_is_saved_with_how_sure_zeph_is(
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
        "mum spent the week with me in Malaysia, she's back to Singapore today",
        [
            mum_guess(),
            {**mum_guess(how_sure="very"), "ask": "Odd how sure?"},
            new_curiosity(ask="How was the week with her?", not_before=None),
        ],
    )
    rows = {row["question"]: row for row in stored_curiosities(engine)}

    assert rows[MUM]["guess"] == MUM_GUESS
    assert rows[MUM]["how_sure"] == "medium"
    assert rows["Odd how sure?"]["how_sure"] == "low"
    assert rows["How was the week with her?"]["guess"] is None
    assert rows["How was the week with her?"]["how_sure"] is None


def test_an_answered_waiting_guess_is_closed_by_the_keeping_step(
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
    mum_guess_is_waiting(client, chat_model, clock, scheduler, seeded_settings)

    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "mum's flat in Singapore is right by the sea",
        [{"curiosity": 1, "close": True}],
    )
    keeper_saw = chat_model.curiosity_keeping_calls[-1].history[0].text
    [row] = stored_curiosities(engine)

    assert (
        f"[1] (waiting; any day; sensitivity low) {MUM} Why: {MUM_WHY} "
        f"Guess (how sure: medium): {MUM_GUESS}"
    ) in keeper_saw
    assert row["state"] == "closed"


def test_a_waiting_guess_can_be_updated_with_how_sure_zeph_now_is(
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
    mum_guess_is_waiting(client, chat_model, clock, scheduler, seeded_settings)

    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "flying to Singapore to see mum next month",
        [{"curiosity": 1, "how_sure": "high"}],
    )
    [row] = stored_curiosities(engine)

    assert row["guess"] == MUM_GUESS
    assert row["how_sure"] == "high"
    assert row["state"] == "waiting"


def test_a_due_guess_is_shown_to_the_understanding_as_a_guess_to_check_gently(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    mum_guess_is_waiting(client, chat_model, clock, scheduler, seeded_settings)

    seen = understanding_sees(client, chat_model, "talked to mum last night")

    assert f"[1] {MUM} Why: {MUM_WHY} Sensitivity: low. {MUM_GUESS_SHOWN}" in seen


def test_a_raised_guess_tells_the_reply_to_check_it_never_state_it(
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
    mum_guess_is_waiting(client, chat_model, clock, scheduler, seeded_settings)

    bring_up_curiosity(chat_model, 1)
    instructions = reply_instructions(client, chat_model, "talked to mum last night")
    bring_up_curiosity(chat_model, 1)
    plain = reply_instructions(client, chat_model, "anyway")
    [row] = stored_curiosities(engine)

    assert (
        f"- {MUM} Open with it. Why you wonder: {MUM_WHY} {MUM_GUESS_SHOWN}"
    ) in instructions
    assert "A guess, not known" not in plain
    assert row["state"] == "raised"


def test_a_curiosity_check_in_asks_a_guess_as_a_gentle_check(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    set_up_user_with_due_curiosities(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        curiosities=[mum_guess()],
    )
    chat_model.script(wondering_answer("is your mum back in Singapore now?", 1))

    scheduler.tick()
    saw = check_in_model_saw(chat_model)
    [row] = stored_curiosities(engine)

    assert f"1. {MUM} Why: {MUM_WHY} Sensitivity: low. {MUM_GUESS_SHOWN}" in saw
    assert row["state"] == "raised"


def test_no_guesses_are_made_while_user_memory_or_curiosities_do_not_work(
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
    headers = auth_headers(auth_verifier, "user_maya")
    admin = owner_headers(client, auth_verifier)

    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)
    mum_guess_is_waiting(client, chat_model, clock, scheduler, seeded_settings)
    client.patch("/api/me", json={"user_memory_enabled": True}, headers=headers)
    switch_for_user(client, admin, maya_id(client, auth_verifier), "curiosities", "off")
    mum_guess_is_waiting(client, chat_model, clock, scheduler, seeded_settings)

    assert chat_model.curiosity_keeping_calls == []
    assert stored_curiosities(engine) == []


def test_delete_my_data_and_deleting_the_source_memory_item_remove_guesses(
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
    headers = auth_headers(auth_verifier, "user_maya")
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "mum's back to Singapore today",
        [mum_guess(memory_item=1)],
        operations=[
            {
                "action": "add",
                "category": "Life details",
                "content": "Their mum visited for a week",
            }
        ],
    )
    [item] = client.get("/api/memory-items", headers=headers).json()["groups"][0][
        "items"
    ]
    client.delete(f"/api/memory-items/{item['id']}", headers=headers)
    after_item = stored_curiosities(engine)
    mum_guess_is_waiting(client, chat_model, clock, scheduler, seeded_settings)
    before_delete = stored_curiosities(engine)

    client.delete("/api/me/data", headers=headers)

    assert after_item == []
    assert [row["guess"] for row in before_delete] == [MUM_GUESS]
    assert stored_curiosities(engine) == []


def test_the_guesses_migration_adds_empty_columns_and_reloads_the_keeping_prompt(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0057")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = to_jsonb('Old prompt'::text) "
                    "WHERE key = 'curiosity_keeping_prompt'"
                )
            )
    finally:
        migrate(database_url)

    with engine.connect() as connection:
        prompt = connection.execute(
            text(
                "SELECT value FROM platform_settings "
                "WHERE key = 'curiosity_keeping_prompt'"
            )
        ).all()
        columns = connection.execute(
            text(
                "SELECT column_name, is_nullable FROM information_schema.columns "
                "WHERE table_name = 'curiosities' "
                "AND column_name IN ('guess', 'how_sure') ORDER BY column_name"
            )
        ).all()
    assert prompt == []
    assert columns == [("guess", "YES"), ("how_sure", "YES")]


def test_the_seeded_keeping_prompt_explains_guesses(
    seeded_settings: dict[str, Any],
) -> None:
    prompt = seeded_settings["curiosity_keeping_prompt"]

    assert '"guess"' in prompt
    assert '"how_sure": "low" | "medium" | "high"' in prompt
