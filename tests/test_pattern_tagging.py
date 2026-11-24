import json
from datetime import timedelta
from typing import Any
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import Engine

from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import (
    EvidenceKind,
    Observation,
    ObservationDirection,
    Relationship,
)
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import auth_headers, connect_telegram, owner_headers
from tests.test_features import maya_id, switch_for_everyone, switch_for_user
from tests.test_life_threads import end_conversation, new_thread
from tests.test_message_retention import message_contents, retention
from tests.test_model_call_log import list_traces, open_trace, stored_model_calls

TEXT = "I said yes to Mei again, it's fine honestly. Then I stewed on it all night"
MEI = new_thread(
    title="Falling-out with Mei",
    story="They keep saying yes to their sister Mei and resenting it.",
    people=("Mei", "sister"),
)
CONTEXT_LINE = "Agreed to help Mei move again, then resented it all night."


def observation_entry(**changes: Any) -> dict[str, Any]:
    """One Observation as the tagging model writes it, with some fields changed."""
    return {
        "pattern_types": ["CONF.AVOID.BELONG"],
        "sign": "I2",
        "direction": "for",
        "quote": "I said yes to Mei again",
        "context": CONTEXT_LINE,
        "about": "Mei, their sister",
        "thread": 1,
        "relationship": "family",
        "power": "equal",
        "setting": "home",
        "stance": "neutral",
        "evidence": "real_story",
        **changes,
    }


def tagging_answer(*entries: dict[str, Any]) -> str:
    """Build the JSON the tagging model answers with."""
    return json.dumps({"observations": list(entries)})


def observations_of(engine: Engine, user_id: str) -> list[Observation]:
    """List a User's Observations through the Observation repository."""
    return build_postgres_repositories(engine).observations.list_for_user(UUID(user_id))


def turn_noticing_on(client: TestClient, auth_verifier: FakeAuthVerifier) -> str:
    """Turn Pattern noticing on for Maya only, tell her, and return her User ID."""
    user_id = maya_id(client, auth_verifier)
    switch_for_user(
        client,
        owner_headers(client, auth_verifier),
        user_id,
        "pattern_noticing",
        "on",
    )
    tell_about_noticing(client, auth_verifier)
    return user_id


def tell_about_noticing(client: TestClient, auth_verifier: FakeAuthVerifier) -> None:
    """Have Maya press "Got it" on the Pattern noticing notice."""
    response = client.post(
        "/api/me/pattern-noticing-told",
        headers=auth_headers(auth_verifier, "user_maya"),
    )
    assert response.status_code == 200


def end_tagged_conversation(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    *entries: dict[str, Any],
) -> None:
    """Have a Conversation about Mei whose tagging writes the given Observations."""
    chat_model.script_pattern_tagging(tagging_answer(*entries))
    end_conversation(client, chat_model, clock, scheduler, seeded_settings, TEXT, [MEI])


def test_with_pattern_noticing_on_a_conversation_end_keeps_the_valid_observations(
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
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        observation_entry(),
        observation_entry(quote="I said no to Mei"),
    )

    [observation] = observations_of(client.engine, user_id)
    [thread] = build_postgres_repositories(client.engine).life_threads.list_for_user(
        UUID(user_id)
    )
    assert observation.quote == "I said yes to Mei again"
    assert observation.context == CONTEXT_LINE
    assert observation.pattern_type_id == "CONF.AVOID.BELONG"
    assert observation.pattern_type_version == "0.2.0"
    assert (observation.sign_id, observation.direction) == (
        "I2",
        ObservationDirection.FOR,
    )
    assert observation.thread_id == thread.id
    assert observation.about == "Mei, their sister"
    assert observation.tags.relationship == Relationship.FAMILY
    assert observation.evidence_kind == EvidenceKind.REAL_STORY
    assert observation.day == clock.now().date()
    assert (observation.unclear, observation.situational) == (False, False)


def test_tagging_runs_after_life_threads_and_before_pattern_keeping_and_sees_it_all(
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

    end_tagged_conversation(client, chat_model, clock, scheduler, seeded_settings)

    order = chat_model.call_order
    assert (
        order.index("thread_keeping")
        < order.index("pattern_tagging")
        < order.index("pattern_keeping")
    )
    [call] = chat_model.pattern_tagging_calls
    seen = call.history[0].text
    assert call.instructions == seeded_settings["pattern_tagging_prompt"]
    assert call.model == seeded_settings["pattern_tagging_model"]
    assert "Life Threads this Conversation touched:\n[1] Falling-out with Mei" in seen
    assert "CONF.AVOID.BELONG: Conflict avoidance to preserve belonging" in seen
    assert "- I2 (strong): Reports agreeing in the moment" in seen
    assert "ACH.WORTH.PERF: Performance-contingent self-worth" in seen
    assert "relationship: partner, family, friend" in seen
    assert f"Person: {TEXT}" in seen


def test_unclear_and_situational_observations_are_saved_as_such(
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
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        observation_entry(pattern_types=["CONF.AVOID.BELONG", "ACH.WORTH.PERF"]),
        observation_entry(
            quote="Then I stewed on it all night", relationship="stranger"
        ),
    )

    unclear, situational = observations_of(client.engine, user_id)
    assert unclear.unclear
    assert (
        unclear.second_pattern_type_id,
        unclear.second_pattern_type_version,
    ) == ("ACH.WORTH.PERF", "0.1.0")
    assert not unclear.situational
    assert situational.situational
    assert not situational.unclear


def test_the_model_call_log_shows_how_many_were_tagged_and_dropped_never_words(
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
        observation_entry(sign="I9"),
        observation_entry(quote="mm, I hear you"),
    )

    admin = owner_headers(client, auth_verifier)
    [trace] = list_traces(client, admin, step="pattern_tagging")
    [call] = [
        call
        for call in open_trace(client, admin, trace["trace_id"])["calls"]
        if call["step"] == "pattern_tagging"
    ]
    assert call["tagging_shape"] == {"tagged": 3, "dropped": 2}
    assert call["content"] is None
    assert not any(
        "I said yes to Mei again" in row or CONTEXT_LINE in row
        for row in stored_model_calls(client.engine)
    )


def test_observations_stay_after_message_retention_deletes_their_messages(
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

    clock.advance(retention(seeded_settings) + timedelta(days=1))
    scheduler.tick()

    assert message_contents(client.engine) == []
    assert [
        observation.quote for observation in observations_of(client.engine, user_id)
    ] == ["I said yes to Mei again"]


def test_with_pattern_noticing_off_tagging_does_not_run_and_nothing_is_deleted(
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
    switch_for_user(
        client,
        owner_headers(client, auth_verifier),
        user_id,
        "pattern_noticing",
        "default",
    )
    clock.advance(timedelta(days=1))

    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, observation_entry()
    )

    assert len(chat_model.pattern_tagging_calls) == 1
    assert len(observations_of(client.engine, user_id)) == 1


def test_pattern_noticing_is_off_for_everyone_to_start(
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

    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, observation_entry()
    )

    assert chat_model.pattern_tagging_calls == []
    assert observations_of(client.engine, user_id) == []


def test_pattern_noticing_on_for_everyone_tags_every_user(
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
    switch_for_everyone(
        client, owner_headers(client, auth_verifier), "pattern_noticing", True
    )
    tell_about_noticing(client, auth_verifier)

    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, observation_entry()
    )

    assert len(observations_of(client.engine, user_id)) == 1


def test_with_user_memory_off_tagging_does_not_run_and_nothing_is_deleted(
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
    client.patch(
        "/api/me",
        json={"user_memory_enabled": False},
        headers=auth_headers(auth_verifier, "user_maya"),
    )
    clock.advance(timedelta(days=1))

    chat_model.script("mm, I hear you")
    end_tagged_conversation(
        client, chat_model, clock, scheduler, seeded_settings, observation_entry()
    )

    assert len(chat_model.pattern_tagging_calls) == 1
    assert len(observations_of(client.engine, user_id)) == 1


def test_deleting_a_life_thread_removes_its_observations(
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
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        observation_entry(),
        observation_entry(quote="Then I stewed on it all night", thread=None),
    )
    headers = auth_headers(auth_verifier, "user_maya")
    [thread] = client.get("/api/life-threads", headers=headers).json()["threads"]

    response = client.delete(f"/api/life-threads/{thread['id']}", headers=headers)

    assert response.status_code == 204
    assert [
        observation.quote for observation in observations_of(client.engine, user_id)
    ] == ["Then I stewed on it all night"]


def test_delete_my_data_removes_every_observation(
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
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        observation_entry(),
        observation_entry(quote="Then I stewed on it all night", thread=None),
    )

    response = client.delete(
        "/api/me/data", headers=auth_headers(auth_verifier, "user_maya")
    )

    assert response.status_code == 204
    assert observations_of(client.engine, user_id) == []


def test_account_deletion_removes_every_observation(
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

    response = client.delete(
        "/api/me", headers=auth_headers(auth_verifier, "user_maya")
    )

    assert response.status_code == 204
    assert observations_of(client.engine, user_id) == []


def test_a_failing_tagging_call_leaves_the_other_conversation_end_steps_running(
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
    chat_model.script_pattern_tagging(RuntimeError("model down"))

    end_conversation(client, chat_model, clock, scheduler, seeded_settings, TEXT, [MEI])

    assert observations_of(client.engine, user_id) == []
    assert len(chat_model.pattern_keeping_calls) == 1


def test_an_unreadable_answer_is_asked_again_once(
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
    chat_model.script_pattern_tagging("not json", tagging_answer(observation_entry()))

    end_conversation(client, chat_model, clock, scheduler, seeded_settings, TEXT, [MEI])

    assert len(chat_model.pattern_tagging_calls) == 2
    assert len(observations_of(client.engine, user_id)) == 1


def test_replies_are_not_given_observations(
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
    clock.advance(timedelta(days=1))
    calls_before = len(chat_model.calls)
    plans_before = len(chat_model.reply_plan_calls)

    chat_model.script("hey")
    end_conversation(
        client, chat_model, clock, scheduler, seeded_settings, "Mei called", [MEI]
    )

    reply_steps = [
        *chat_model.calls[calls_before:],
        *chat_model.reply_plan_calls[plans_before:],
        *chat_model.understanding_calls,
    ]
    assert reply_steps
    assert not any(
        CONTEXT_LINE in line.text or "CONF.AVOID.BELONG" in call.instructions
        for call in reply_steps
        for line in call.history
    )


def test_the_tagging_prompt_model_and_thinking_are_settings_in_core_services(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    services = client.get("/api/admin/core-services", headers=admin).json()
    settings = client.get("/api/admin/settings", headers=admin).json()["settings"]

    [service] = [
        service
        for service in services["services"]
        if service["name"] == "Pattern tagging"
    ]
    assert (
        service["prompt_key"],
        service["model_key"],
        service["thinking_key"],
    ) == (
        "pattern_tagging_prompt",
        "pattern_tagging_model",
        "pattern_tagging_thinking",
    )
    for key in (
        "pattern_tagging_prompt",
        "pattern_tagging_model",
        "pattern_tagging_thinking",
    ):
        assert settings[key]["hint"]
