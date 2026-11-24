from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text

from companion.adapters.postgres.database import migrate
from companion.core.models import PatternState
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import connect_telegram
from tests.test_features import maya_id
from tests.test_moves_migration import downgrade_to
from tests.test_patterns import GOES_QUIET, patterns_of, start_goes_quiet_pattern
from tests.test_patterns_dashboard import (
    CLOSED,
    EARNS_REST,
    HIDDEN,
    keep_pattern,
    maya_headers,
    patterns_shown,
    threads_by_title,
)

OLD_ID = UUID("0f6f2c7e-58a4-4d0b-9d0e-6f1f6f0a9f16")


def test_the_migration_keeps_every_old_pattern_and_makes_suspected_ones_unmatched(
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
    threads = threads_by_title(client.engine, user_id)
    lines = [
        (date(2026, 11, 2), threads["Side project"], "Worked through the weekend."),
        (date(2026, 11, 3), threads["Mum's visit"], "Tidied while mum talked."),
    ]
    agreed_at = datetime(2026, 11, 12, 20, 0)
    keep_pattern(
        client.engine, user_id, EARNS_REST, PatternState.CONFIRMED, lines, agreed_at
    )
    keep_pattern(client.engine, user_id, CLOSED, PatternState.CLOSED, lines)
    before = patterns_of(client.engine, user_id)
    shown_before = patterns_shown(client, maya_headers(auth_verifier))

    downgrade_to(database_url, "0090")
    try:
        with client.engine.begin() as connection:
            old_rows = connection.execute(
                text("SELECT pattern, state FROM patterns ORDER BY started_at, pattern")
            ).all()
            connection.execute(
                text(
                    "INSERT INTO patterns (id, user_id, pattern, state, started_at, "
                    "updated_at) VALUES (:id, :user_id, :pattern, 'suspected', "
                    "now(), now())"
                ),
                {"id": OLD_ID, "user_id": user_id, "pattern": HIDDEN},
            )
            connection.execute(
                text(
                    "INSERT INTO pattern_evidence (id, pattern_id, life_thread_id, "
                    "day, line) VALUES (:id, :pattern_id, :thread_id, "
                    "'2026-11-04', 'Cleaned at midnight.')"
                ),
                {
                    "id": uuid4(),
                    "pattern_id": OLD_ID,
                    "thread_id": threads["Side project"],
                },
            )
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = '\"Old keeping rules.\"' "
                    "WHERE key = 'pattern_keeping_prompt'"
                )
            )
    finally:
        migrate(database_url)

    assert {tuple(row) for row in old_rows} == {
        (GOES_QUIET, "suspected"),
        (EARNS_REST, "confirmed"),
        (CLOSED, "closed"),
    }
    every_pattern = patterns_of(client.engine, user_id)
    [inserted_old] = [item for item in every_pattern if item.id == OLD_ID]
    assert (inserted_old.pattern, inserted_old.state) == (
        HIDDEN,
        PatternState.UNMATCHED,
    )
    assert [item.line for item in inserted_old.evidence] == ["Cleaned at midnight."]
    after = [item for item in every_pattern if item.id != OLD_ID]
    assert after == before
    assert {pattern.pattern: pattern.state for pattern in after} == {
        GOES_QUIET: PatternState.UNMATCHED,
        EARNS_REST: PatternState.CONFIRMED,
        CLOSED: PatternState.CLOSED,
    }
    assert [len(pattern.evidence) for pattern in after] == [2, 2, 2]
    assert patterns_shown(client, maya_headers(auth_verifier)) == shown_before
    assert [pattern["pattern"] for pattern in shown_before] == [EARNS_REST]
    with client.engine.connect() as connection:
        stored_prompt = connection.execute(
            text("SELECT 1 FROM platform_settings WHERE key = 'pattern_keeping_prompt'")
        ).first()
    assert stored_prompt is None
