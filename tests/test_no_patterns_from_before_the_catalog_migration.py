from datetime import date, datetime
from typing import Any
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from companion.adapters.postgres.database import migrate
from companion.adapters.postgres.repositories import build_postgres_repositories
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


def test_a_suspected_pattern_kept_before_the_catalog_became_unmatched(
    client: TestClient, auth_verifier: FakeAuthVerifier, database_url: str
) -> None:
    user_id = maya_id(client, auth_verifier)

    downgrade_to(database_url, "0091")
    try:
        with client.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO patterns (id, user_id, pattern, state, started_at, "
                    "updated_at) VALUES (:id, :user_id, :pattern, 'suspected', "
                    "now(), now())"
                ),
                {"id": OLD_ID, "user_id": user_id, "pattern": HIDDEN},
            )
    finally:
        migrate(database_url)

    [pattern] = patterns_of(client.engine, user_id)
    assert (pattern.id, pattern.pattern, pattern.state) == (
        OLD_ID,
        HIDDEN,
        PatternState.UNMATCHED,
    )


def test_the_migration_deletes_old_confirmed_and_closed_patterns_only(
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
    [unmatched_before] = patterns_of(client.engine, user_id)
    threads = threads_by_title(client.engine, user_id)
    lines = [
        (date(2026, 11, 2), threads["Side project"], "Worked through the weekend."),
        (date(2026, 11, 3), threads["Mum's visit"], "Tidied while mum talked."),
    ]

    downgrade_to(database_url, "0096")
    try:
        keep_pattern(
            client.engine,
            user_id,
            EARNS_REST,
            PatternState.CONFIRMED,
            lines,
            datetime(2026, 11, 12, 20, 0),
        )
        keep_pattern(client.engine, user_id, CLOSED, PatternState.CLOSED, lines)
        with client.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO patterns (id, user_id, pattern_type_id, state, "
                    "started_at, updated_at) VALUES (gen_random_uuid(), :user_id, "
                    "'ACH.ABSORB.PULL', 'closed', now(), now())"
                ),
                {"user_id": user_id},
            )
            connection.execute(
                text(
                    "INSERT INTO user_portraits (user_id, text, written_at) "
                    "VALUES (:user_id, 'Rest has to be earned.', now()) "
                    "ON CONFLICT (user_id) DO UPDATE "
                    "SET rewrite_requested_at = NULL"
                ),
                {"user_id": user_id},
            )
            connection.execute(
                text(
                    "INSERT INTO platform_settings (key, value, updated_at) "
                    "VALUES ('pattern_pushed_back_wait_days', '30', now()) "
                    "ON CONFLICT (key) DO NOTHING"
                )
            )
    finally:
        migrate(database_url)

    assert patterns_of(client.engine, user_id) == [unmatched_before]
    assert unmatched_before.pattern == GOES_QUIET
    assert len(unmatched_before.evidence) == 2
    assert patterns_shown(client, maya_headers(auth_verifier)) == []
    with client.engine.connect() as connection:
        of_pattern_types = connection.execute(
            text(
                "SELECT pattern_type_id, state FROM patterns "
                "WHERE pattern_type_id IS NOT NULL"
            )
        ).all()
        evidence_left = connection.execute(
            text("SELECT count(*) FROM pattern_evidence")
        ).scalar_one()
        wait_setting = connection.execute(
            text(
                "SELECT 1 FROM platform_settings "
                "WHERE key = 'pattern_pushed_back_wait_days'"
            )
        ).first()
    assert [tuple(row) for row in of_pattern_types] == [("ACH.ABSORB.PULL", "closed")]
    assert evidence_left == 2
    rewrites = build_postgres_repositories(client.engine).user_portraits
    assert [str(asked) for asked in rewrites.list_rewrite_requests()] == [user_id]
    assert wait_setting is None
    columns = {
        column["name"] for column in inspect(client.engine).get_columns("patterns")
    }
    assert not columns & {"last_offered_at", "last_reaction"}
