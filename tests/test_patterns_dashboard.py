import importlib
from datetime import date, datetime, timedelta
from types import ModuleType
from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import (
    Pattern,
    PatternEvidence,
    PatternReaction,
    PatternState,
    PatternToSave,
)
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import auth_headers, connect_telegram
from tests.test_features import maya_id
from tests.test_life_threads import end_conversation
from tests.test_moves_migration import downgrade_to
from tests.test_patterns import (
    GOES_QUIET,
    MUM,
    PROJECT,
    end_with_pattern_answer,
    evidence,
    pattern_keeping_answer,
    patterns_of,
    start_goes_quiet_pattern,
)
from tests.test_user_portrait import REWRITTEN, end_conversation_with_portrait

EARNS_REST = (
    "Treats rest as something to be earned, and feels behind whenever they stop."
)
WORST_FIRST = "Names the worst version of a plan first, before anyone else can."
HIDDEN = "Keeps busy so they never have to sit with a hard feeling."
CLOSED = "Only feels calm when the house is spotless."


def patterns_shown(client: TestClient, headers: dict[str, str]) -> list[Any]:
    """Read the User's Patterns through the Dashboard API."""
    response = client.get("/api/patterns", headers=headers)
    assert response.status_code == 200
    shown: list[Any] = response.json()["patterns"]
    return shown


def maya_headers(auth_verifier: FakeAuthVerifier) -> dict[str, str]:
    """Build the Dashboard API headers for the User the tests talk as."""
    return auth_headers(auth_verifier, "user_maya")


def threads_by_title(engine: Engine, user_id: str) -> dict[str, UUID]:
    """Find a User's Life Thread IDs by title."""
    threads = build_postgres_repositories(engine).life_threads.list_for_user(
        UUID(user_id)
    )
    return {thread.title: thread.id for thread in threads}


def keep_pattern(
    engine: Engine,
    user_id: str,
    pattern_text: str,
    state: PatternState,
    evidence_lines: list[tuple[date, UUID, str]],
    confirmed_at: datetime | None = None,
) -> UUID:
    """Save a Pattern with the given state and evidence straight to the database."""
    now = datetime(2026, 11, 1, 12, 0)
    pattern = Pattern(
        id=uuid4(),
        user_id=UUID(user_id),
        pattern=pattern_text,
        state=state,
        evidence=tuple(
            PatternEvidence(
                id=uuid4(), day=day, thread_id=thread_id, thread_title="", line=line
            )
            for day, thread_id, line in evidence_lines
        ),
        started_at=now,
        updated_at=now,
        confirmed_at=confirmed_at,
    )
    build_postgres_repositories(engine).patterns.save_many(
        [PatternToSave(pattern=pattern, embedding=None)], []
    )
    return pattern.id


def keep_threads(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    """Have a Conversation whose end starts the side project and mum's visit Threads."""
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "the app has me, I forgot to eat and snapped at mum",
        [PROJECT, MUM],
    )


def test_a_user_sees_only_confirmed_patterns_newest_agreed_first_with_evidence(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    keep_threads(client, chat_model, clock, scheduler, seeded_settings)
    threads = threads_by_title(client.engine, user_id)
    project, mum = threads["Side project"], threads["Mum's visit"]
    keep_pattern(
        client.engine,
        user_id,
        WORST_FIRST,
        PatternState.CONFIRMED,
        [
            (date(2026, 10, 28), project, "Listed what could go wrong first."),
            (date(2026, 11, 9), mum, "Called the trip reckless before mum could."),
        ],
        confirmed_at=datetime(2026, 11, 9, 20, 0),
    )
    keep_pattern(
        client.engine,
        user_id,
        EARNS_REST,
        PatternState.CONFIRMED,
        [
            (date(2026, 11, 2), mum, "Felt guilty taking an afternoon off."),
            (date(2026, 11, 12), project, "Worked through the weekend."),
        ],
        confirmed_at=datetime(2026, 11, 12, 20, 0),
    )
    hidden_patterns = [
        (HIDDEN, PatternState.SUSPECTED),
        (CLOSED, PatternState.CLOSED),
    ]
    for pattern_text, state in hidden_patterns:
        keep_pattern(
            client.engine,
            user_id,
            pattern_text,
            state,
            [
                (date(2026, 11, 3), project, "Cleaned at midnight."),
                (date(2026, 11, 4), mum, "Tidied while mum talked."),
            ],
        )

    shown = patterns_shown(client, maya_headers(auth_verifier))

    assert [pattern["pattern"] for pattern in shown] == [EARNS_REST, WORST_FIRST]
    assert set(shown[0]) == {"id", "pattern", "agreed_at", "evidence"}
    assert shown[0]["agreed_at"].startswith("2026-11-12T20:00:00")
    assert shown[0]["evidence"] == [
        {
            "day": "2026-11-12",
            "thread": "Side project",
            "line": "Worked through the weekend.",
        },
        {
            "day": "2026-11-02",
            "thread": "Mum's visit",
            "line": "Felt guilty taking an afternoon off.",
        },
    ]


def test_agreeing_with_a_pattern_records_the_day_and_a_later_reaction_keeps_it(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    start_goes_quiet_pattern(client, chat_model, clock, scheduler, seeded_settings)
    have_pattern_answer = (client, chat_model, clock, scheduler, seeded_settings)
    [suspected] = patterns_of(client.engine, user_id)
    assert suspected.confirmed_at is None

    end_with_pattern_answer(
        *have_pattern_answer, {"pattern": 1, "reaction": "agreed", "state": "confirmed"}
    )
    agreed_at = clock.now()
    end_with_pattern_answer(
        *have_pattern_answer, {"pattern": 1, "reaction": "brushed_off"}
    )

    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.state == PatternState.CONFIRMED
    assert pattern.last_reaction == PatternReaction.BRUSHED_OFF
    assert pattern.confirmed_at == agreed_at
    [shown] = patterns_shown(client, maya_headers(auth_verifier))
    assert datetime.fromisoformat(shown["agreed_at"]) == agreed_at


def test_a_new_pattern_agreed_with_at_once_is_dated_and_agreeing_again_keeps_the_day(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    chat_model.script_pattern_keeping(
        pattern_keeping_answer(
            [
                {
                    "pattern": GOES_QUIET,
                    "evidence": [
                        evidence(1, "Skipped meals for days while on the app."),
                        evidence(2, "Snapped at mum because the app had them."),
                    ],
                    "reaction": "agreed",
                    "state": "confirmed",
                }
            ]
        )
    )
    keep_threads(client, chat_model, clock, scheduler, seeded_settings)
    [started_confirmed] = patterns_of(client.engine, user_id)
    agreed_at = started_confirmed.confirmed_at

    end_with_pattern_answer(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        {"pattern": 1, "reaction": "agreed", "state": "confirmed"},
    )

    assert agreed_at is not None
    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.last_offered_at == clock.now()
    assert pattern.confirmed_at == agreed_at < clock.now()


def test_deleting_a_pattern_removes_it_and_rewrites_the_portrait_without_it(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    headers = maya_headers(auth_verifier)
    end_conversation_with_portrait(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        threads=[PROJECT, MUM],
    )
    threads = threads_by_title(client.engine, user_id)
    keep_pattern(
        client.engine,
        user_id,
        GOES_QUIET,
        PatternState.CONFIRMED,
        [
            (date(2026, 11, 2), threads["Side project"], "Skipped meals."),
            (date(2026, 11, 3), threads["Mum's visit"], "Snapped at mum."),
        ],
        confirmed_at=datetime(2026, 11, 3, 20, 0),
    )
    [shown] = patterns_shown(client, headers)

    deleted = client.delete(f"/api/patterns/{shown['id']}", headers=headers)
    deleted_again = client.delete(f"/api/patterns/{shown['id']}", headers=headers)
    chat_model.script_portrait(REWRITTEN)
    scheduler.tick()

    assert deleted.status_code == 204
    assert deleted_again.status_code == 404
    assert patterns_shown(client, headers) == []
    assert patterns_of(client.engine, user_id) == []
    assert GOES_QUIET not in chat_model.portrait_calls[-1].history[0].text
    portrait = client.get("/api/user-portrait", headers=headers).json()["portrait"]
    assert portrait["text"] == REWRITTEN


def test_a_user_cannot_delete_a_suspected_or_another_users_pattern(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    keep_threads(client, chat_model, clock, scheduler, seeded_settings)
    threads = threads_by_title(client.engine, user_id)
    shared_evidence = [
        (date(2026, 11, 2), threads["Side project"], "Skipped meals."),
        (date(2026, 11, 3), threads["Mum's visit"], "Snapped at mum."),
    ]
    suspected_id = keep_pattern(
        client.engine, user_id, HIDDEN, PatternState.SUSPECTED, shared_evidence
    )
    confirmed_id = keep_pattern(
        client.engine,
        user_id,
        GOES_QUIET,
        PatternState.CONFIRMED,
        shared_evidence,
        confirmed_at=datetime(2026, 11, 3, 20, 0),
    )
    stranger = auth_headers(auth_verifier, "user_stranger")

    as_maya = client.delete(
        f"/api/patterns/{suspected_id}", headers=maya_headers(auth_verifier)
    )
    as_stranger = client.delete(f"/api/patterns/{confirmed_id}", headers=stranger)

    assert as_maya.status_code == 404
    assert as_stranger.status_code == 404
    assert patterns_shown(client, stranger) == []
    assert len(patterns_of(client.engine, user_id)) == 2


def test_with_user_memory_off_a_user_still_sees_and_deletes_patterns(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    headers = maya_headers(auth_verifier)
    keep_threads(client, chat_model, clock, scheduler, seeded_settings)
    threads = threads_by_title(client.engine, user_id)
    keep_pattern(
        client.engine,
        user_id,
        GOES_QUIET,
        PatternState.CONFIRMED,
        [
            (date(2026, 11, 2), threads["Side project"], "Skipped meals."),
            (date(2026, 11, 3), threads["Mum's visit"], "Snapped at mum."),
        ],
        confirmed_at=datetime(2026, 11, 3, 20, 0),
    )
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)

    [shown] = patterns_shown(client, headers)
    deleted = client.delete(f"/api/patterns/{shown['id']}", headers=headers)

    assert deleted.status_code == 204
    assert patterns_shown(client, headers) == []


def test_the_portrait_is_written_from_confirmed_patterns_only(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    keep_threads(client, chat_model, clock, scheduler, seeded_settings)
    threads = threads_by_title(client.engine, user_id)
    shared_evidence = [
        (date(2026, 11, 2), threads["Side project"], "Skipped meals."),
        (date(2026, 11, 3), threads["Mum's visit"], "Snapped at mum."),
    ]
    keep_pattern(
        client.engine,
        user_id,
        GOES_QUIET,
        PatternState.CONFIRMED,
        shared_evidence,
        confirmed_at=datetime(2026, 11, 3, 20, 0),
    )
    keep_pattern(
        client.engine, user_id, HIDDEN, PatternState.SUSPECTED, shared_evidence
    )
    keep_pattern(client.engine, user_id, CLOSED, PatternState.CLOSED, shared_evidence)
    clock.advance(timedelta(days=1))

    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )

    given = chat_model.portrait_calls[-1].history[0].text
    assert f"Patterns they agreed with:\n- {GOES_QUIET}" in given
    assert HIDDEN not in given
    assert CLOSED not in given
    assert "patterns they agreed with" in seeded_settings["portrait_prompt"].lower()


def confirmed_at_migration() -> ModuleType:
    """Load the migration that adds when a Pattern was confirmed."""
    return importlib.import_module(
        "companion.adapters.postgres.migrations.versions.0069_pattern_confirmed_at"
    )


def store_old_texts(engine: Engine, portrait_prompt: str, hero_lead: str) -> None:
    """Store the given Portrait prompt and Memories hero line."""
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE platform_settings SET value = to_jsonb(CAST(:prompt AS text)) "
                "WHERE key = 'portrait_prompt'"
            ),
            {"prompt": portrait_prompt},
        )
        connection.execute(
            text("UPDATE copy_slots SET text = :lead WHERE key = 'memories.hero.lead'"),
            {"lead": hero_lead},
        )


def stored_texts(engine: Engine) -> tuple[str | None, str | None]:
    """Read the stored Portrait prompt and Memories hero line; None if reloading."""
    with engine.connect() as connection:
        prompt = connection.execute(
            text(
                "SELECT value #>> '{}' FROM platform_settings "
                "WHERE key = 'portrait_prompt'"
            )
        ).scalar_one_or_none()
        lead = connection.execute(
            text("SELECT text FROM copy_slots WHERE key = 'memories.hero.lead'")
        ).scalar_one_or_none()
    return prompt, lead


def test_the_migration_reloads_the_portrait_prompt_and_hero_line_still_on_the_old_seed(
    engine: Engine, database_url: str
) -> None:
    migration = confirmed_at_migration()
    downgrade_to(database_url, "0068")
    try:
        store_old_texts(
            engine, migration.OLD_PORTRAIT_PROMPT, migration.OLD_MEMORIES_HERO_LEAD
        )
    finally:
        migrate(database_url)

    assert stored_texts(engine) == (None, None)


def test_the_migration_keeps_a_portrait_prompt_and_hero_line_an_admin_edited(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0068")
    try:
        store_old_texts(engine, "Admin's own Portrait prompt.", "Admin's own line.")
    finally:
        migrate(database_url)

    assert stored_texts(engine) == ("Admin's own Portrait prompt.", "Admin's own line.")


def test_the_migration_dates_confirmed_patterns_to_when_they_were_last_offered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    database_url: str,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    start_goes_quiet_pattern(client, chat_model, clock, scheduler, seeded_settings)
    end_with_pattern_answer(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        {"pattern": 1, "reaction": "agreed", "state": "confirmed"},
    )

    downgrade_to(database_url, "0068")
    migrate(database_url)

    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.confirmed_at == pattern.last_offered_at
