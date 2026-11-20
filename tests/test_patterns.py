import importlib
import json
from datetime import timedelta
from types import ModuleType
from typing import Any
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import Pattern, PatternReaction, PatternState
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import auth_headers, connect_telegram, owner_headers
from tests.test_features import maya_id
from tests.test_life_threads import end_conversation, new_thread
from tests.test_model_call_log import list_traces, open_trace
from tests.test_moves_migration import downgrade_to
from tests.test_older_summaries import set_settings

PROJECT = new_thread(
    title="Side project",
    story="Building an app at night; stopped eating properly while on it.",
    people=("app",),
)
MUM = new_thread(
    title="Mum's visit",
    story="Mum is staying for two weeks; they snapped at her while busy.",
    people=("mum",),
)
GOES_QUIET = "When something grabs them, everything else goes quiet."


def pattern_keeping_answer(patterns: list[dict[str, Any]]) -> str:
    """Build the JSON the Pattern keeping model answers with."""
    return json.dumps({"patterns": patterns})


def evidence(thread: int, line: str, day: str | None = None) -> dict[str, Any]:
    """Build one piece of evidence as the keeping model writes it."""
    entry: dict[str, Any] = {"thread": thread, "line": line}
    if day is not None:
        entry["day"] = day
    return entry


def patterns_of(engine: Engine, user_id: str) -> list[Pattern]:
    """List a User's Patterns through the Pattern repository."""
    return build_postgres_repositories(engine).patterns.list_for_user(UUID(user_id))


def test_two_threads_showing_the_same_way_of_acting_start_a_suspected_pattern(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_pattern_keeping(
        pattern_keeping_answer(
            [
                {
                    "pattern": GOES_QUIET,
                    "evidence": [
                        evidence(1, "Skipped meals for days while on the app."),
                        evidence(2, "Snapped at mum because the app had them."),
                    ],
                }
            ]
        )
    )

    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "the app has me, I forgot to eat and snapped at mum",
        [PROJECT, MUM],
    )

    [pattern] = patterns_of(client.engine, maya_id(client, auth_verifier))
    assert pattern.pattern == GOES_QUIET
    assert pattern.state == PatternState.SUSPECTED
    assert [(item.thread_title, item.line) for item in pattern.evidence] == [
        ("Side project", "Skipped meals for days while on the app."),
        ("Mum's visit", "Snapped at mum because the app had them."),
    ]


GUITAR = new_thread(
    title="Learning guitar",
    story="Practising guitar every night; stopped eating properly again.",
    people=("guitar",),
)


def start_goes_quiet_pattern(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    """Have a Conversation whose end starts the side project and mum's visit
    Threads (the project settled) and a suspected Pattern linking them."""
    chat_model.script_pattern_keeping(
        pattern_keeping_answer(
            [
                {
                    "pattern": GOES_QUIET,
                    "evidence": [
                        evidence(1, "Skipped meals for days while on the app."),
                        evidence(2, "Snapped at mum because the app had them."),
                    ],
                }
            ]
        )
    )
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "the app has me, I forgot to eat and snapped at mum",
        [{**PROJECT, "open": False}, MUM],
    )


def test_keeping_is_given_the_touched_and_closest_threads_however_old_and_the_patterns(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    set_settings(client, auth_verifier, {"pattern_keeping_threads": 1})
    start_goes_quiet_pattern(client, chat_model, clock, scheduler, seeded_settings)
    clock.advance(timedelta(days=300))

    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "guitar every night, forgot to eat again",
        [GUITAR],
    )

    seen = chat_model.pattern_keeping_calls[-1].history[0].text
    assert "Life Threads this Conversation touched:\n[1] Learning guitar (open" in seen
    assert (
        "Their other Life Threads closest in meaning:\n[2] Side project (settled"
        in seen
    )
    assert "[3]" not in seen
    assert f"Patterns kept so far:\n[1] (suspected) {GOES_QUIET} Evidence:" in seen


def test_days_within_retention_reach_keeping_as_messages_and_older_ones_as_summaries(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_goes_quiet_pattern(client, chat_model, clock, scheduler, seeded_settings)
    clock.advance(timedelta(days=seeded_settings["message_retention_days"] + 10))
    chat_model.script_pattern_keeping(
        pattern_keeping_answer(
            [
                {
                    "pattern": 1,
                    "evidence": [evidence(1, "Forgot to eat while learning guitar.")],
                }
            ]
        )
    )
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "guitar every night, forgot to eat again",
        [GUITAR],
    )
    clock.advance(timedelta(days=5))

    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "my guitar teacher says I practise too much",
        [
            {
                "thread": 1,
                "story": "Practising guitar every night; teacher says ease up.",
            }
        ],
    )

    seen = chat_model.pattern_keeping_calls[-1].history[0].text
    days = seen.split("The days behind that evidence:\n")[1].split(
        "The Conversation, on "
    )[0]
    guitar_day, project_day = days.strip().split("\n\n")
    assert ", the messages:\n" in guitar_day
    assert "guitar every night, forgot to eat again" in guitar_day
    assert project_day.endswith(", the Day Summary:\nTalked about family.")


def end_with_pattern_answer(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    pattern_entry: dict[str, Any],
) -> None:
    """A day later, have a Conversation touching the guitar Thread whose
    Pattern keeping answer is the given entry."""
    clock.advance(timedelta(days=1))
    chat_model.script_pattern_keeping(pattern_keeping_answer([pattern_entry]))
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "guitar every night, forgot to eat again",
        [GUITAR],
    )


def test_a_pattern_is_confirmed_or_closed_by_how_the_user_took_it_and_stays_closed(
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

    end_with_pattern_answer(*have_pattern_answer, {"pattern": 1, "state": "confirmed"})
    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.state == PatternState.SUSPECTED

    end_with_pattern_answer(
        *have_pattern_answer, {"pattern": 1, "reaction": "agreed", "state": "confirmed"}
    )
    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.state == PatternState.CONFIRMED
    assert pattern.last_reaction == PatternReaction.AGREED
    assert pattern.last_offered_at == clock.now()

    end_with_pattern_answer(
        *have_pattern_answer,
        {"pattern": 1, "reaction": "pushed_back", "state": "closed"},
    )
    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.state == PatternState.CLOSED

    end_with_pattern_answer(
        *have_pattern_answer,
        {
            "pattern": 1,
            "reaction": "agreed",
            "state": "confirmed",
            "evidence": [evidence(1, "Forgot to eat while learning guitar.")],
        },
    )
    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.state == PatternState.CLOSED
    assert pattern.last_reaction == PatternReaction.PUSHED_BACK
    assert len(pattern.evidence) == 2


def test_with_user_memory_off_no_pattern_is_started_or_changed(
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
    client.patch(
        "/api/me",
        json={"user_memory_enabled": False},
        headers=auth_headers(auth_verifier, "user_maya"),
    )
    calls_before = len(chat_model.pattern_keeping_calls)

    end_with_pattern_answer(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        {"pattern": 1, "reaction": "agreed", "state": "confirmed"},
    )

    assert len(chat_model.pattern_keeping_calls) == calls_before
    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.state == PatternState.SUSPECTED


def test_deleting_a_linked_thread_drops_its_evidence_and_the_pattern_once_none_is_left(
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
    headers = auth_headers(auth_verifier, "user_maya")
    start_goes_quiet_pattern(client, chat_model, clock, scheduler, seeded_settings)
    threads = client.get("/api/life-threads", headers=headers).json()["threads"]
    thread_ids = {thread["title"]: thread["id"] for thread in threads}

    client.delete(f"/api/life-threads/{thread_ids['Side project']}", headers=headers)

    [pattern] = patterns_of(client.engine, user_id)
    assert [item.thread_title for item in pattern.evidence] == ["Mum's visit"]

    client.delete(f"/api/life-threads/{thread_ids["Mum's visit"]}", headers=headers)

    assert patterns_of(client.engine, user_id) == []


def test_pattern_keeping_is_the_last_core_service_with_its_limits_and_hints(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    services = client.get("/api/admin/core-services", headers=admin).json()
    set_settings(
        client,
        auth_verifier,
        {
            "pattern_keeping_prompt": "Find what recurs.",
            "pattern_keeping_model": services["model_choices"][0],
            "pattern_keeping_thinking": False,
            "pattern_keeping_threads": 5,
            "pattern_keeping_days": 20,
        },
    )

    pattern_keeping = services["services"][-1]
    assert pattern_keeping["name"] == "Pattern keeping"
    assert pattern_keeping["prompt_key"] == "pattern_keeping_prompt"
    assert [limit["label"] for limit in pattern_keeping["limits"]] == [
        "Closest Threads to include",
        "Days of evidence to include",
    ]
    settings = client.get("/api/admin/settings", headers=admin).json()["settings"]
    assert settings["pattern_keeping_threads"]["value"] == 5
    assert settings["pattern_keeping_days"]["value"] == 20
    assert settings["pattern_keeping_prompt"]["value"] == "Find what recurs."
    assert settings["pattern_keeping_days"]["hint"] == (
        "How many days behind the evidence Pattern keeping reads, as messages or "
        "Day Summaries."
    )


def test_admins_see_only_how_many_confirmed_patterns_a_user_has_and_the_keeping_step(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_goes_quiet_pattern(client, chat_model, clock, scheduler, seeded_settings)
    end_with_pattern_answer(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        {"pattern": 1, "reaction": "agreed", "state": "confirmed"},
    )
    admin = owner_headers(client, auth_verifier)

    users = client.get("/api/admin/users", headers=admin)
    traces = list_traces(client, admin, step="patterns")

    [maya] = [row for row in users.json()["users"] if row["role"] == "user"]
    assert maya["confirmed_pattern_count"] == 1
    assert "grabs" not in users.text
    assert len(traces) == 2
    opened = open_trace(client, admin, traces[0]["trace_id"])
    [keeping] = [call for call in opened["calls"] if call["step"] == "patterns"]
    assert keeping["content"] is None


def test_a_new_pattern_the_user_agreed_with_in_the_same_conversation_starts_confirmed(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
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

    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "the app has me, I forgot to eat and snapped at mum",
        [PROJECT, MUM],
    )

    [pattern] = patterns_of(client.engine, maya_id(client, auth_verifier))
    assert pattern.state == PatternState.CONFIRMED
    assert pattern.last_reaction == PatternReaction.AGREED


def test_evidence_is_dated_to_the_day_the_conversation_started(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    started_on = clock.now().date()
    clock.advance(timedelta(hours=23, minutes=55) - timedelta(hours=clock.now().hour))
    chat_model.script_pattern_keeping(
        pattern_keeping_answer(
            [
                {
                    "pattern": GOES_QUIET,
                    "evidence": [
                        evidence(1, "Skipped meals for days while on the app."),
                        evidence(2, "Snapped at mum because the app had them."),
                    ],
                }
            ]
        )
    )

    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "the app has me, I forgot to eat and snapped at mum",
        [PROJECT, MUM],
    )

    assert clock.now().date() > started_on
    seen = chat_model.pattern_keeping_calls[-1].history[0].text
    assert f"The Conversation, on {started_on.day} Nov 2026:\n" in seen
    [pattern] = patterns_of(client.engine, maya_id(client, auth_verifier))
    assert {item.day for item in pattern.evidence} == {started_on}


def patterns_migration() -> ModuleType:
    """Load the Patterns migration module."""
    return importlib.import_module(
        "companion.adapters.postgres.migrations.versions.0067_patterns"
    )


def stored_curiosity_prompt(engine: Engine) -> str | None:
    """Read the stored Curiosity keeping prompt; None if it will reload."""
    with engine.connect() as connection:
        prompt: str | None = connection.execute(
            text(
                "SELECT value #>> '{}' FROM platform_settings "
                "WHERE key = 'curiosity_keeping_prompt'"
            )
        ).scalar_one_or_none()
    return prompt


def store_curiosity_prompt(engine: Engine, prompt: str) -> None:
    """Store the given Curiosity keeping prompt."""
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE platform_settings SET value = to_jsonb(CAST(:prompt AS text)) "
                "WHERE key = 'curiosity_keeping_prompt'"
            ),
            {"prompt": prompt},
        )


def test_the_curiosity_keeping_prompt_never_makes_a_curiosity_to_check_a_pattern(
    seeded_settings: dict[str, Any],
) -> None:
    prompt = " ".join(seeded_settings["curiosity_keeping_prompt"].split())

    assert "a pattern you notice" not in prompt
    assert "Never write one to check something that keeps showing up" in prompt


def test_the_migration_reloads_the_curiosity_prompt_still_matching_the_old_seed(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0066")
    try:
        store_curiosity_prompt(
            engine, patterns_migration().OLD_CURIOSITY_KEEPING_PROMPT
        )
    finally:
        migrate(database_url)

    assert stored_curiosity_prompt(engine) is None


def test_the_migration_keeps_a_curiosity_prompt_an_admin_edited(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0066")
    try:
        store_curiosity_prompt(engine, "Admin's own Curiosity prompt.")
    finally:
        migrate(database_url)

    assert stored_curiosity_prompt(engine) == "Admin's own Curiosity prompt."


def test_a_pattern_is_confirmed_even_when_no_thread_changed_in_the_conversation(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_goes_quiet_pattern(client, chat_model, clock, scheduler, seeded_settings)
    clock.advance(timedelta(days=1))
    chat_model.script_pattern_keeping(
        pattern_keeping_answer(
            [{"pattern": 1, "reaction": "agreed", "state": "confirmed"}]
        )
    )

    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "yes, that is me: when the app grabs me everything else goes quiet",
        [],
    )

    [pattern] = patterns_of(client.engine, maya_id(client, auth_verifier))
    assert pattern.state == PatternState.CONFIRMED
    seen = chat_model.pattern_keeping_calls[-1].history[0].text
    closest = seen.split("Their other Life Threads closest in meaning:\n")[1]
    assert "Side project (" in closest.split("Patterns kept so far:")[0]


def test_a_brushed_off_view_never_closes_a_pattern(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_goes_quiet_pattern(client, chat_model, clock, scheduler, seeded_settings)

    end_with_pattern_answer(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        {"pattern": 1, "reaction": "brushed_off", "state": "closed"},
    )

    [pattern] = patterns_of(client.engine, maya_id(client, auth_verifier))
    assert pattern.state == PatternState.SUSPECTED
    assert pattern.last_reaction == PatternReaction.BRUSHED_OFF
