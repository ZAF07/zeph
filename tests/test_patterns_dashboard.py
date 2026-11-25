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
from tests.test_pattern_sharing import (
    APPROVED_WORDING,
    PREDICTION,
    predictions_of,
    ready_to_share,
    share,
)
from tests.test_pattern_tagging import observations_of
from tests.test_patterns import (
    GOES_QUIET,
    MUM,
    PROJECT,
    patterns_of,
)
from tests.test_ready_gate import belonging
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


def told_belonging(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> str:
    """Have Zeph tell Maya her Pattern of CONF.AVOID.BELONG; return her User ID."""
    user_id = ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    share(client, chat_model, clock)
    return user_id


def set_state(engine: Engine, pattern_id: UUID, state: PatternState) -> None:
    """Put a Pattern in a state straight in the database."""
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE patterns SET state = :state WHERE id = :id"),
            {"state": state.value, "id": pattern_id},
        )


def test_a_user_sees_a_pattern_zeph_told_them_with_quotes_by_thread_and_prediction(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = told_belonging(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    told_at = clock.now()
    days = {
        observation.quote: observation.day.isoformat()
        for observation in observations_of(client.engine, user_id)
    }

    [shown] = patterns_shown(client, maya_headers(auth_verifier))

    assert shown == {
        "id": str(belonging(client.engine, user_id).id),
        "state": "shared",
        "pattern": (
            "You seem to protect closeness by keeping disagreements small, even "
            "when they matter to you."
        ),
        "where_it_shows": [
            {"shows_with": ["family", "friend"], "not_with": ["partner"]}
        ],
        "told_at": shown["told_at"],
        "quote_groups": [
            {
                "life_thread": "Falling-out with Mei",
                "quotes": [
                    {
                        "quote": "I said yes to Mei again",
                        "day": days["I said yes to Mei again"],
                    }
                ],
            },
            {
                "life_thread": "New manager at work",
                "quotes": [
                    {
                        "quote": "Then I stewed on it all night",
                        "day": days["Then I stewed on it all night"],
                    }
                ],
            },
            {
                "life_thread": None,
                "quotes": [
                    {
                        "quote": "I just went along with it",
                        "day": days["I just went along with it"],
                    }
                ],
            },
        ],
        "predictions": [
            {"wording": PREDICTION, "made_at": shown["told_at"], "outcome": None}
        ],
    }
    assert datetime.fromisoformat(shown["told_at"]) == told_at


def test_each_pattern_zeph_told_them_shows_and_no_other_is_returned(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = told_belonging(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    headers = maya_headers(auth_verifier)
    pattern_id = belonging(client.engine, user_id).id
    keep_pattern(client.engine, user_id, HIDDEN, PatternState.UNMATCHED, [])

    states_shown = {}
    for state in PatternState:
        set_state(client.engine, pattern_id, state)
        states_shown[state.value] = [
            pattern["state"] for pattern in patterns_shown(client, headers)
        ]

    assert states_shown == {
        "noticed": [],
        "suspected": [],
        "ready": [],
        "shared": ["shared"],
        "confirmed": ["confirmed"],
        "contested": ["contested"],
        "closed": ["closed"],
        "unmatched": [],
    }

    with client.engine.begin() as connection:
        connection.execute(text("UPDATE patterns SET shared_at = NULL"))
    set_state(client.engine, pattern_id, PatternState.CLOSED)

    assert patterns_shown(client, headers) == []


def test_deleting_a_pattern_removes_it_with_its_quotes_and_asks_for_a_new_portrait(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = told_belonging(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    headers = maya_headers(auth_verifier)
    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )
    [shown] = patterns_shown(client, headers)
    portraits_before = len(chat_model.portrait_calls)

    deleted = client.delete(f"/api/patterns/{shown['id']}", headers=headers)
    deleted_again = client.delete(f"/api/patterns/{shown['id']}", headers=headers)
    chat_model.script_portrait(REWRITTEN)
    scheduler.tick()

    assert deleted.status_code == 204
    assert deleted_again.status_code == 404
    assert patterns_shown(client, headers) == []
    assert patterns_of(client.engine, user_id) == []
    assert observations_of(client.engine, user_id) == []
    assert predictions_of(client.engine, user_id) == []
    assert client.get("/api/kept-quotes", headers=headers).json()["quotes"] == []
    assert len(chat_model.portrait_calls) == portraits_before + 1
    assert APPROVED_WORDING not in chat_model.portrait_calls[-1].history[0].text
    portrait = client.get("/api/user-portrait", headers=headers).json()["portrait"]
    assert portrait["text"] == REWRITTEN


def test_a_user_cannot_delete_a_pattern_never_told_or_another_users_pattern(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    pattern_id = belonging(client.engine, user_id).id
    stranger = auth_headers(auth_verifier, "user_stranger")

    while_ready = client.delete(
        f"/api/patterns/{pattern_id}", headers=maya_headers(auth_verifier)
    )
    share(client, chat_model, clock)
    as_stranger = client.delete(f"/api/patterns/{pattern_id}", headers=stranger)

    assert while_ready.status_code == 404
    assert as_stranger.status_code == 404
    assert patterns_shown(client, stranger) == []
    assert belonging(client.engine, user_id).state == PatternState.SHARED
    assert len(observations_of(client.engine, user_id)) == 4


def test_with_user_memory_off_a_user_still_sees_and_deletes_patterns(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    told_belonging(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    headers = maya_headers(auth_verifier)
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)

    [shown] = patterns_shown(client, headers)
    deleted = client.delete(f"/api/patterns/{shown['id']}", headers=headers)

    assert deleted.status_code == 204
    assert patterns_shown(client, headers) == []


def test_a_pattern_with_no_pattern_type_never_reaches_the_portrait(
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
        client.engine, user_id, HIDDEN, PatternState.UNMATCHED, shared_evidence
    )
    keep_pattern(client.engine, user_id, CLOSED, PatternState.CLOSED, shared_evidence)
    clock.advance(timedelta(days=1))

    end_conversation_with_portrait(
        client, chat_model, clock, scheduler, seeded_settings
    )

    given = chat_model.portrait_calls[-1].history[0].text
    assert "Patterns they agreed with:\nNone yet." in given
    assert GOES_QUIET not in given
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
