from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from companion.adapters.postgres.database import migrate
from companion.core.models import UnmatchedEntry, UnmatchedMark
from companion.core.unmatched_review import read_general_description, shown_mark
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeEmbedder,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import (
    OWNER_TELEGRAM_USER_ID,
    auth_headers,
    connect_owner_telegram,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_features import maya_id
from tests.test_life_threads import end_conversation, thread_keeping_answer
from tests.test_moves_migration import downgrade_to
from tests.test_patterns import (
    GOES_QUIET,
    MUM,
    PROJECT,
    evidence,
    pattern_keeping_answer,
    patterns_of,
)
from tests.test_post_conversation import processing_answer, quiet_gap

ROUTE = "/api/admin/unmatched-patterns"
ABSORBED = "Lets everything else slip while absorbed in something"
ABSORBED_AGAIN = "Lets everything else slip when absorbed in something"
JOKES = "Makes jokes when things turn serious"
SKIPPED_MEALS = "Skipped meals for days while on the app."
SNAPPED_AT_MUM = "Snapped at mum because the app had them."
BELONG = "CONF.AVOID.BELONG"


def unmatched_pattern(general: str | None, pattern: str = GOES_QUIET) -> dict[str, Any]:
    """Build a new unmatched Pattern as the keeping model writes it, with
    evidence from the first two Threads."""
    entry: dict[str, Any] = {
        "pattern": pattern,
        "evidence": [evidence(1, SKIPPED_MEALS), evidence(2, SNAPPED_AT_MUM)],
    }
    if general is not None:
        entry["general"] = general
    return entry


def maya_shows(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    *patterns: dict[str, Any],
) -> None:
    """Have a Conversation of Maya's whose end keeps the given Patterns."""
    chat_model.script_pattern_keeping(pattern_keeping_answer(list(patterns)))
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "the app has me, I forgot to eat and snapped at mum",
        [PROJECT, MUM],
    )


def owner_shows(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    *patterns: dict[str, Any],
) -> None:
    """Have a Conversation of the owner's whose end keeps the given Patterns."""
    chat_model.script_pattern_keeping(pattern_keeping_answer(list(patterns)))
    chat_model.script_thread_keeping(thread_keeping_answer([PROJECT, MUM]))
    chat_model.script("mm, I hear you")
    send_to_webhook(
        client,
        telegram_text_update(
            "work swallowed my week again", OWNER_TELEGRAM_USER_ID, "owner_tg"
        ),
    )
    clock.advance(quiet_gap(seeded_settings) + (quiet_gap(seeded_settings) / 15))
    chat_model.script_processing(processing_answer(summary="Work.", mood="tired"))
    scheduler.tick()


def listed(
    client: TestClient, admin: dict[str, str], mark: str | None = None
) -> list[dict[str, Any]]:
    """Fetch the unmatched entries, all of them or those with one mark."""
    response = client.get(ROUTE, params={"mark": mark} if mark else {}, headers=admin)
    assert response.status_code == 200, response.text
    entries: list[dict[str, Any]] = response.json()["entries"]
    return entries


def set_mark(
    client: TestClient,
    admin: dict[str, str],
    entry_id: str,
    mark: str,
    pattern_type_id: str | None = None,
) -> Any:
    """Mark an unmatched entry and return the response."""
    return client.put(
        f"{ROUTE}/{entry_id}/mark",
        json={"mark": mark, "pattern_type_id": pattern_type_id},
        headers=admin,
    )


def test_an_unmatched_pattern_is_listed_as_its_general_description_with_a_user_count(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    maya_shows(
        client, chat_model, clock, scheduler, seeded_settings, unmatched_pattern(JOKES)
    )

    [entry] = listed(client, owner_headers(client, auth_verifier))
    assert entry["description"] == JOKES
    assert entry["user_count"] == 1
    assert entry["mark"] == "to_review"
    assert entry["folded_into_pattern_type_id"] is None
    [pattern] = patterns_of(client.engine, maya_id(client, auth_verifier))
    assert pattern.general_description == JOKES


def test_an_entry_shows_only_the_general_wording_never_the_users_pattern_or_evidence(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    maya_shows(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        unmatched_pattern(ABSORBED),
        unmatched_pattern(None, pattern="Keeps choosing the app over mum."),
    )

    response = client.get(ROUTE, headers=owner_headers(client, auth_verifier))
    [entry] = response.json()["entries"]
    assert entry["description"] == ABSORBED
    assert set(entry) == {
        "id",
        "description",
        "user_count",
        "mark",
        "folded_into_pattern_type_id",
        "dropped_before",
    }
    for users_words in (
        GOES_QUIET,
        "Keeps choosing",
        SKIPPED_MEALS,
        SNAPPED_AT_MUM,
        "Side project",
        "Mum's visit",
        "Maya",
        maya_id(client, auth_verifier),
    ):
        assert users_words not in response.text
    with client.engine.connect() as connection:
        stored = connection.execute(text("SELECT * FROM unmatched_entries")).all()
    assert [row.description for row in stored] == [ABSORBED]
    assert "user_id" not in stored[0]._fields


@pytest.mark.parametrize(
    "written",
    [
        "Maya makes jokes when things turn serious",
        "Makes jokes like “it's fine” when things turn serious",
        'Says "it is fine" when things turn serious',
        "Made jokes at the hospital on 3 Nov",
        "Goes quiet whenever Priya calls",
        "Works late since joining Deloitte",
        "Goes quiet around Christmas",
        "Says 'it is fine' when things turn serious",
        "Says ‘it is fine’ when things turn serious",
        "Makes jokes. Then goes quiet",
        "maya makes jokes when things turn serious".capitalize(),
        "",
        "   ",
        17,
        None,
    ],
)
def test_a_description_with_the_users_name_a_quote_or_a_number_is_dropped(
    written: Any,
) -> None:
    assert read_general_description(written, "Maya") is None


def test_a_general_description_is_kept_trimmed() -> None:
    assert read_general_description(f"  {JOKES} ", "Maya") == JOKES
    assert read_general_description(JOKES, None) == JOKES
    assert read_general_description("Stays mayan about it", "Maya") is not None
    assert read_general_description("Finds joy in what others' plans are", "Joy") == (
        "Finds joy in what others' plans are"
    )
    assert read_general_description("Doesn't say what they will do", "Will") == (
        "Doesn't say what they will do"
    )
    assert read_general_description("Will not say no", "Will") is None


def test_a_pattern_whose_description_was_dropped_is_kept_and_asked_about_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    maya_shows(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        unmatched_pattern("Snapped at mum on 3 Nov"),
    )
    [pattern] = patterns_of(client.engine, maya_id(client, auth_verifier))
    assert pattern.general_description is None
    assert listed(client, admin) == []

    maya_shows(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        {"pattern": 1, "general": ABSORBED},
    )

    seen = chat_model.pattern_keeping_calls[-1].history[0].text
    assert "[1] (needs a general description) (unmatched)" in seen
    [entry] = listed(client, admin)
    assert (entry["description"], entry["user_count"]) == (ABSORBED, 1)
    [pattern] = patterns_of(client.engine, maya_id(client, auth_verifier))
    assert len(pattern.evidence) == 2


def test_a_general_description_once_kept_is_never_rewritten(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    maya_shows(
        client, chat_model, clock, scheduler, seeded_settings, unmatched_pattern(JOKES)
    )

    maya_shows(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        {"pattern": 1, "general": ABSORBED},
    )

    seen = chat_model.pattern_keeping_calls[-1].history[0].text
    assert "needs a general description" not in seen
    [entry] = listed(client, owner_headers(client, auth_verifier))
    assert entry["description"] == JOKES


def test_like_descriptions_from_different_users_are_one_entry_most_users_first(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    maya_shows(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        unmatched_pattern(JOKES, pattern="Jokes when it gets heavy."),
        unmatched_pattern(ABSORBED),
    )

    owner_shows(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        unmatched_pattern(ABSORBED_AGAIN, pattern="Work swallows everything."),
    )

    assert [
        (entry["description"], entry["user_count"]) for entry in listed(client, admin)
    ] == [(ABSORBED, 2), (JOKES, 1)]


def test_two_like_patterns_of_one_user_count_that_user_once(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    maya_shows(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        unmatched_pattern(ABSORBED),
        unmatched_pattern(ABSORBED_AGAIN, pattern="The app swallows everything."),
    )

    [entry] = listed(client, owner_headers(client, auth_verifier))
    assert (entry["description"], entry["user_count"]) == (ABSORBED, 1)


def test_a_description_that_cant_be_embedded_is_grouped_at_the_next_conversation_end(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    embedder: FakeEmbedder,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    embedder.failure = RuntimeError("embedder down")
    maya_shows(
        client, chat_model, clock, scheduler, seeded_settings, unmatched_pattern(JOKES)
    )
    assert listed(client, admin) == []
    embedder.failure = None

    maya_shows(client, chat_model, clock, scheduler, seeded_settings)

    [entry] = listed(client, admin)
    assert (entry["description"], entry["user_count"]) == (JOKES, 1)


def test_an_admin_marks_an_entry_and_filters_by_the_mark(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    maya_shows(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        unmatched_pattern(JOKES, pattern="Jokes when it gets heavy."),
        unmatched_pattern(ABSORBED),
        unmatched_pattern("Keeps promises made to strangers", pattern="Promises."),
    )
    ids = {entry["description"]: entry["id"] for entry in listed(client, admin)}

    folded = set_mark(client, admin, ids[JOKES], "folded", BELONG)
    new_type = set_mark(client, admin, ids[ABSORBED], "new_pattern_type", BELONG)

    assert folded.status_code == 200, folded.text
    assert folded.json()["mark"] == "folded"
    assert folded.json()["folded_into_pattern_type_id"] == BELONG
    assert new_type.json()["folded_into_pattern_type_id"] is None
    assert [entry["description"] for entry in listed(client, admin, "folded")] == [
        JOKES
    ]
    assert [
        entry["description"] for entry in listed(client, admin, "new_pattern_type")
    ] == [ABSORBED]
    assert [entry["description"] for entry in listed(client, admin, "to_review")] == [
        "Keeps promises made to strangers"
    ]
    assert listed(client, admin, "dropped") == []
    assert len(listed(client, admin)) == 3

    back = set_mark(client, admin, ids[JOKES], "to_review")

    assert back.json()["mark"] == "to_review"
    assert back.json()["folded_into_pattern_type_id"] is None
    assert len(listed(client, admin, "to_review")) == 2


def test_the_list_comes_with_the_pattern_types_an_entry_can_be_folded_into(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    response = client.get(ROUTE, headers=owner_headers(client, auth_verifier))

    pattern_types = response.json()["pattern_types"]
    assert BELONG in [choice["id"] for choice in pattern_types]
    assert pattern_types == sorted(pattern_types, key=lambda choice: choice["id"])


def test_a_mark_that_makes_no_sense_is_refused(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    maya_shows(
        client, chat_model, clock, scheduler, seeded_settings, unmatched_pattern(JOKES)
    )
    [entry] = listed(client, admin)

    assert set_mark(client, admin, entry["id"], "folded").status_code == 422
    assert set_mark(client, admin, entry["id"], "folded", "NOT.A.TYPE").status_code == (
        422
    )
    assert set_mark(client, admin, entry["id"], "kept").status_code == 422
    assert set_mark(client, admin, str(uuid4()), "dropped").status_code == 404
    assert listed(client, admin)[0]["mark"] == "to_review"


def test_a_dropped_entry_comes_back_only_when_it_appears_for_more_users(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    maya_shows(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        unmatched_pattern(ABSORBED),
    )
    [entry] = listed(client, admin)
    assert set_mark(client, admin, entry["id"], "dropped").status_code == 200

    maya_shows(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        unmatched_pattern(ABSORBED_AGAIN, pattern="The app swallows everything."),
    )

    assert listed(client, admin, "to_review") == []
    [dropped] = listed(client, admin, "dropped")
    assert (dropped["mark"], dropped["dropped_before"]) == ("dropped", False)

    owner_shows(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        unmatched_pattern(ABSORBED_AGAIN, pattern="Work swallows everything."),
    )

    assert listed(client, admin, "dropped") == []
    [back] = listed(client, admin, "to_review")
    assert (back["id"], back["user_count"]) == (entry["id"], 2)
    assert (back["mark"], back["dropped_before"]) == ("to_review", True)

    assert set_mark(client, admin, entry["id"], "dropped").status_code == 200
    assert listed(client, admin, "to_review") == []


def entry_marked(mark: UnmatchedMark, users_when_marked: int | None) -> UnmatchedEntry:
    """Build an unmatched entry with a mark made at some number of Users."""
    return UnmatchedEntry(
        id=uuid4(),
        description=JOKES,
        mark=mark,
        folded_into_pattern_type_id=None,
        users_when_marked=users_when_marked,
    )


def test_only_a_dropped_entry_with_more_users_reads_as_to_review_again() -> None:
    dropped = entry_marked(UnmatchedMark.DROPPED, 2)
    folded = entry_marked(UnmatchedMark.FOLDED, 2)

    assert shown_mark(dropped, 2) == UnmatchedMark.DROPPED
    assert shown_mark(dropped, 1) == UnmatchedMark.DROPPED
    assert shown_mark(dropped, 3) == UnmatchedMark.TO_REVIEW
    assert shown_mark(folded, 3) == UnmatchedMark.FOLDED


def test_a_pattern_the_matching_command_linked_or_a_deleted_one_is_not_counted(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    maya_shows(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        unmatched_pattern(ABSORBED),
    )
    owner_shows(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        unmatched_pattern(ABSORBED_AGAIN),
    )
    assert listed(client, admin)[0]["user_count"] == 2

    with client.engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE patterns SET matched_pattern_type_id = :pattern_type "
                "WHERE user_id = :user_id"
            ),
            {"pattern_type": BELONG, "user_id": maya_id(client, auth_verifier)},
        )
    assert listed(client, admin)[0]["user_count"] == 1

    with client.engine.begin() as connection:
        connection.execute(text("DELETE FROM patterns"))
    assert listed(client, admin) == []
    with client.engine.connect() as connection:
        kept = connection.execute(
            text("SELECT count(*) FROM unmatched_entries")
        ).scalar_one()
    assert kept == 1


def test_only_admins_can_reach_the_unmatched_entries(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    maya = auth_headers(auth_verifier, "user_maya")

    assert client.get(ROUTE, headers=maya).status_code == 403
    assert set_mark(client, maya, str(uuid4()), "dropped").status_code == 403
    assert client.get(ROUTE).status_code == 401


def test_the_migration_keeps_every_pattern_and_its_downgrade_only_drops_the_review(
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
    maya_shows(
        client, chat_model, clock, scheduler, seeded_settings, unmatched_pattern(JOKES)
    )

    downgrade_to(database_url, "0095")
    try:
        with client.engine.begin() as connection:
            columns = set(
                connection.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'patterns'"
                    )
                ).scalars()
            )
            old_rows = connection.execute(
                text(
                    "SELECT pattern, state, count(pattern_evidence.id) FROM patterns "
                    "JOIN pattern_evidence ON pattern_id = patterns.id "
                    "GROUP BY patterns.id"
                )
            ).all()
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = '\"Old keeping rules.\"' "
                    "WHERE key = 'pattern_keeping_prompt'"
                )
            )
    finally:
        migrate(database_url)

    assert not {"general_description", "unmatched_entry_id"} & columns
    assert [tuple(row) for row in old_rows] == [(GOES_QUIET, "unmatched", 2)]
    [pattern] = patterns_of(client.engine, maya_id(client, auth_verifier))
    assert (pattern.pattern, len(pattern.evidence)) == (GOES_QUIET, 2)
    assert pattern.general_description is None
    assert listed(client, owner_headers(client, auth_verifier)) == []
    with client.engine.connect() as connection:
        stored_prompt = connection.execute(
            text("SELECT 1 FROM platform_settings WHERE key = 'pattern_keeping_prompt'")
        ).first()
    assert stored_prompt is None
