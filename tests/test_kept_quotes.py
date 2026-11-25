import threading
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.features import FeatureService
from companion.core.models import CatalogPatternType, PatternMoveCause, PatternState
from companion.core.pattern_catalog import PatternCatalogService
from companion.core.pattern_scoring import PatternScorer
from companion.core.ports import Repositories
from companion.core.ready_gate import ReadyKeeper
from companion.core.user_memory import UserMemoryService
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import auth_headers, connect_telegram, owner_headers
from tests.test_features import maya_id, switch_for_user
from tests.test_pattern_states import (
    MEI_STORY,
    WORK_STORY,
    moves_of,
    patterns_of,
    states_and_causes,
)
from tests.test_pattern_states import (
    end_tagged_conversation as end_conversation_in_two_threads,
)
from tests.test_pattern_tagging import (
    CONTEXT_LINE,
    end_tagged_conversation,
    observation_entry,
    observations_of,
    turn_noticing_on,
)

STEWED = observation_entry(
    quote="Then I stewed on it all night", context="Lay awake angry after."
)
MAYA = "user_maya"


def kept_quotes(client: TestClient, auth_verifier: FakeAuthVerifier) -> Any:
    """List Maya's kept quotes as the Memories page reads them."""
    response = client.get("/api/kept-quotes", headers=auth_headers(auth_verifier, MAYA))
    assert response.status_code == 200
    return response.json()["quotes"]


def test_kept_quotes_are_listed_newest_first_with_their_line_and_day_and_no_pattern(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    turn_noticing_on(client, auth_verifier)
    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, observation_entry()
    )
    clock.advance(timedelta(days=2))
    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, STEWED
    )

    quotes = kept_quotes(client, auth_verifier)

    assert [(quote["quote"], quote["context"]) for quote in quotes] == [
        ("Then I stewed on it all night", "Lay awake angry after."),
        ("I said yes to Mei again", CONTEXT_LINE),
    ]
    assert quotes[0]["day"] > quotes[1]["day"]
    assert set(quotes[0]) == {"id", "quote", "context", "day"}
    response = client.get("/api/kept-quotes", headers=auth_headers(auth_verifier, MAYA))
    assert "CONF" not in response.text
    assert "pattern" not in response.text.lower()


def test_deleting_a_kept_quote_removes_it_and_scores_its_pattern_again_at_once(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_noticing_on(client, auth_verifier)
    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, observation_entry()
    )
    [quote] = kept_quotes(client, auth_verifier)
    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.state == PatternState.NOTICED

    response = client.delete(
        f"/api/kept-quotes/{quote['id']}", headers=auth_headers(auth_verifier, MAYA)
    )

    assert response.status_code == 204
    assert kept_quotes(client, auth_verifier) == []
    assert observations_of(client.engine, user_id) == []
    assert patterns_of(client.engine, user_id) == []
    assert len(moves_of(client.engine, user_id)) == 1


def test_a_deleted_quote_moves_its_pattern_back_and_logs_why(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_noticing_on(client, auth_verifier)
    end_conversation_in_two_threads(
        client, chat_model, clock, scheduler, seeded_settings, MEI_STORY, WORK_STORY
    )
    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.state == PatternState.SUSPECTED
    work = next(
        quote
        for quote in kept_quotes(client, auth_verifier)
        if quote["quote"] == WORK_STORY["quote"]
    )

    client.delete(
        f"/api/kept-quotes/{work['id']}", headers=auth_headers(auth_verifier, MAYA)
    )

    [pattern] = patterns_of(client.engine, user_id)
    assert pattern.state == PatternState.NOTICED
    assert states_and_causes(moves_of(client.engine, user_id))[-1] == (
        "suspected",
        "noticed",
        "observations_deleted",
    )


def test_a_user_can_not_delete_a_quote_that_is_not_theirs(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_noticing_on(client, auth_verifier)
    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, observation_entry()
    )
    [quote] = kept_quotes(client, auth_verifier)

    someone_else = client.delete(
        f"/api/kept-quotes/{quote['id']}", headers=owner_headers(client, auth_verifier)
    )
    unknown = client.delete(
        f"/api/kept-quotes/{uuid4()}", headers=auth_headers(auth_verifier, MAYA)
    )

    assert (someone_else.status_code, unknown.status_code) == (404, 404)
    assert len(observations_of(client.engine, user_id)) == 1


def test_kept_quotes_are_listed_and_deletable_with_user_memory_off(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_noticing_on(client, auth_verifier)
    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, observation_entry()
    )
    headers = auth_headers(auth_verifier, MAYA)
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)

    [quote] = kept_quotes(client, auth_verifier)
    response = client.delete(f"/api/kept-quotes/{quote['id']}", headers=headers)

    assert response.status_code == 204
    assert observations_of(client.engine, user_id) == []


class CatalogThatDeletesMeanwhile(PatternCatalogService):
    """The real catalog, which starts deleting a quote while scoring is under way.

    Scoring reads the catalog after the User's Observations and before saving,
    so the deletion starts in the middle of it. The deletion is given a second
    to finish before scoring goes on, which it only can if nothing makes it
    wait for scoring.
    """

    def __init__(self, repositories: Repositories, start_deleting: Any) -> None:
        """Wrap the real catalog and remember how to start the deletion."""
        super().__init__(repositories.pattern_catalog)
        self._start_deleting = start_deleting
        self.deletion: threading.Thread | None = None

    def catalog(self) -> list[CatalogPatternType]:
        """Start the deletion once, give it a moment, then read the catalog."""
        if self.deletion is None:
            self.deletion = threading.Thread(target=self._start_deleting)
            self.deletion.start()
            self.deletion.join(timeout=1)
        return super().catalog()


def test_a_quote_deleted_while_a_conversation_end_scores_does_not_come_back(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_noticing_on(client, auth_verifier)
    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, observation_entry()
    )
    [quote] = kept_quotes(client, auth_verifier)
    repositories = build_postgres_repositories(client.engine)
    user_memory = UserMemoryService(
        repositories,
        FeatureService(repositories, clock, "http://dashboard"),
        PatternCatalogService(repositories.pattern_catalog),
        PatternScorer(
            repositories, PatternCatalogService(repositories.pattern_catalog), clock
        ),
        ReadyKeeper(
            repositories, PatternCatalogService(repositories.pattern_catalog), clock
        ),
        clock,
    )
    with repositories.transaction() as transaction:
        transaction.repositories.patterns.save_moves(
            [], [], [pattern.id for pattern in patterns_of(client.engine, user_id)], []
        )
    catalog = CatalogThatDeletesMeanwhile(
        repositories,
        lambda: user_memory.delete_kept_quote(UUID(user_id), UUID(quote["id"])),
    )
    user = repositories.users.get(UUID(user_id))
    assert user is not None

    PatternScorer(repositories, catalog, clock).score(
        user,
        repositories.platform_settings.load(),
        PatternMoveCause.CONVERSATION_TAGGED,
        uuid4(),
    )
    assert catalog.deletion is not None
    catalog.deletion.join()

    assert observations_of(client.engine, user_id) == []
    assert patterns_of(client.engine, user_id) == []


def test_admins_see_only_how_many_kept_quotes_a_user_has(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    turn_noticing_on(client, auth_verifier)
    end_tagged_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        observation_entry(),
        STEWED,
    )

    response = client.get(
        "/api/admin/users", headers=owner_headers(client, auth_verifier)
    )

    [maya] = [row for row in response.json()["users"] if row["role"] == "user"]
    [owner] = [row for row in response.json()["users"] if row["role"] == "admin"]
    assert (maya["kept_quote_count"], owner["kept_quote_count"]) == (2, 0)
    assert "said yes" not in response.text
    assert "stewed" not in response.text
    assert "Lay awake" not in response.text


def shows_notice(client: TestClient, headers: dict[str, str]) -> bool:
    """Say whether the Dashboard is told to show the Pattern noticing notice."""
    shown: bool = client.get("/api/me", headers=headers).json()[
        "show_pattern_noticing_notice"
    ]
    return shown


def test_the_notice_shows_while_pattern_noticing_works_until_the_user_says_got_it(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
) -> None:
    headers = auth_headers(auth_verifier, MAYA)
    user_id = maya_id(client, auth_verifier)
    assert not shows_notice(client, headers)
    switch_for_user(
        client, owner_headers(client, auth_verifier), user_id, "pattern_noticing", "on"
    )
    assert shows_notice(client, headers)

    response = client.post("/api/me/pattern-noticing-told", headers=headers)

    assert response.status_code == 200
    assert response.json()["show_pattern_noticing_notice"] is False
    assert not shows_notice(client, headers)


def test_no_quote_is_kept_until_the_user_has_been_told(
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
    switch_for_user(
        client, owner_headers(client, auth_verifier), user_id, "pattern_noticing", "on"
    )

    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, observation_entry()
    )

    assert chat_model.pattern_tagging_calls == []
    assert observations_of(client.engine, user_id) == []

    client.post(
        "/api/me/pattern-noticing-told", headers=auth_headers(auth_verifier, MAYA)
    )
    clock.advance(timedelta(days=1))
    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, observation_entry()
    )

    assert len(observations_of(client.engine, user_id)) == 1
    assert states_and_causes(moves_of(client.engine, user_id)) == [
        (None, "noticed", "conversation_tagged")
    ]
