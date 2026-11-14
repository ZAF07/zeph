import logging
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.model_call_log import ModelCallLog, ModelCallRequest
from companion.core.models import (
    ChatLine,
    ChatRole,
    ModelAnswer,
    ModelCallTraceDetails,
    ModelStep,
    WebSearchResult,
)
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    FakeTimer,
    FakeWebSearch,
    ScriptedChatModel,
    ToolCall,
)
from tests.telegram_helpers import (
    OWNER_TELEGRAM_USER_ID,
    auth_headers,
    connect_owner_telegram,
    connect_telegram,
    owner_headers,
    post_to_webhook,
    send_to_webhook,
    telegram_photo_update,
    telegram_text_update,
)
from tests.test_check_in_sending import send_check_ins, set_up_user_with_check_ins
from tests.test_post_conversation import have_conversation, processing_answer
from tests.test_reply_tools import add_user, snapshot_for

SECRET_WORDS = "my secret plan about the lighthouse"
SEARCH_RESULT = WebSearchResult(
    title="Lighthouses", url="https://example.com/lighthouses", content="Tall."
)


def list_traces(
    client: TestClient, headers: dict[str, str], **filters: Any
) -> list[dict[str, Any]]:
    """List Model Call Log traces through the Admin API."""
    response = client.get("/api/admin/model-calls", params=filters, headers=headers)
    assert response.status_code == 200
    traces: list[dict[str, Any]] = response.json()["traces"]
    return traces


def open_trace(
    client: TestClient, headers: dict[str, str], trace_id: str
) -> dict[str, Any]:
    """Open one Model Call Log trace through the Admin API."""
    response = client.get(f"/api/admin/model-calls/{trace_id}", headers=headers)
    assert response.status_code == 200
    trace: dict[str, Any] = response.json()
    return trace


def stored_model_calls(engine: Engine) -> list[str]:
    """Read every stored Model Call Log row as text, every column included."""
    with engine.connect() as connection:
        return list(
            connection.execute(text("SELECT model_calls::text FROM model_calls"))
            .scalars()
            .all()
        )


def test_a_plain_users_message_makes_a_trace_with_no_content(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    web_search: FakeWebSearch,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    web_search.results = [SEARCH_RESULT]
    chat_model.script(
        ToolCall("web_search", {"query": "lighthouse"}), "that sounds lovely"
    )

    send_to_webhook(client, telegram_text_update(SECRET_WORDS))

    admin = owner_headers(client, auth_verifier)
    [trace] = list_traces(client, admin)
    assert trace["kind"] == "message"
    assert trace["has_content"] is False
    opened = open_trace(client, admin, trace["trace_id"])
    steps = [call["step"] for call in opened["calls"]]
    assert steps == ["safeguard", "understanding", "reply"]
    reply = opened["calls"][-1]
    assert reply["model"]
    assert reply["tokens_in"] > 0
    assert reply["tokens_out"] > 0
    assert reply["duration_ms"] >= 0
    assert reply["error"] is None
    assert reply["tools_called"] == ["web_search"]
    assert all(call["content"] is None for call in opened["calls"])
    assert "lighthouse" not in str(opened)
    stored = stored_model_calls(engine)
    assert len(stored) == 3
    assert not any("lighthouse" in row for row in stored)


def test_an_admins_own_message_keeps_full_content_with_tool_calls(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    web_search: FakeWebSearch,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    web_search.results = [SEARCH_RESULT]
    chat_model.script(
        ToolCall("web_search", {"query": "lighthouse"}), "that sounds lovely"
    )

    send_to_webhook(client, telegram_text_update(SECRET_WORDS, OWNER_TELEGRAM_USER_ID))

    [trace] = list_traces(client, admin)
    assert trace["has_content"] is True
    reply = open_trace(client, admin, trace["trace_id"])["calls"][-1]
    content = reply["content"]
    assert content["instructions"]
    assert content["history"][-1] == {"role": "user", "text": SECRET_WORDS}
    assert "web_search" in [tool["name"] for tool in content["tools_offered"]]
    [tool_call] = content["tool_calls"]
    assert tool_call["name"] == "web_search"
    assert tool_call["arguments"] == {"query": "lighthouse"}
    assert "Lighthouses" in tool_call["result"]
    assert content["response"] == "that sounds lovely"


def test_texts_sent_in_a_row_make_one_trace_for_their_message(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("oh no, what happened?")

    post_to_webhook(client, telegram_text_update("ugh"))
    post_to_webhook(client, telegram_text_update("bad day"))
    timer.end_message_waits()

    admin = owner_headers(client, auth_verifier)
    [trace] = list_traces(client, admin)
    assert trace["steps"] == ["safeguard", "safeguard", "understanding", "reply"]


def test_a_failing_model_call_shows_its_error(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script(TimeoutError("the model took too long"))

    send_to_webhook(client, telegram_text_update(SECRET_WORDS))

    admin = owner_headers(client, auth_verifier)
    [trace] = list_traces(client, admin)
    assert trace["error_count"] == 1
    reply = open_trace(client, admin, trace["trace_id"])["calls"][-1]
    assert reply["step"] == "reply"
    assert reply["error"] == "TimeoutError"


def test_a_photo_is_part_of_its_messages_trace(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("what a lovely desk")

    send_to_webhook(client, telegram_photo_update(caption="my new desk"))

    admin = owner_headers(client, auth_verifier)
    [trace] = list_traces(client, admin)
    assert "photo" in trace["steps"]


def test_check_ins_and_conversation_end_make_their_own_traces(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "I started a new job",
        processing_answer(summary="Started a new job."),
    )
    send_check_ins(chat_model, clock, scheduler, count=1)

    admin = owner_headers(client, auth_verifier)
    kinds = [trace["kind"] for trace in list_traces(client, admin)]
    assert sorted(kinds) == ["check_in", "conversation_end", "message"]
    [check_in] = list_traces(client, admin, step="check_in")
    assert check_in["steps"] == ["check_in"]
    [conversation_end] = list_traces(client, admin, step="conversation_end")
    assert conversation_end["kind"] == "conversation_end"


def test_traces_can_be_filtered_by_user_days_and_errors(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    chat_model.script("hello there")
    send_to_webhook(client, telegram_text_update("hi"))
    clock.advance(timedelta(days=3))
    chat_model.script("hi back", RuntimeError("down"))
    send_to_webhook(client, telegram_text_update("hey", OWNER_TELEGRAM_USER_ID))
    send_to_webhook(client, telegram_text_update("again", OWNER_TELEGRAM_USER_ID))

    maya_id = client.get(
        "/api/me", headers=auth_headers(auth_verifier, "user_maya")
    ).json()["id"]
    [maya_trace] = list_traces(client, admin, user_id=maya_id)
    assert maya_trace["user_id"] == maya_id
    assert len(list_traces(client, admin, days=1)) == 2
    [failed] = list_traces(client, admin, errors_only=True)
    assert failed["error_count"] == 1
    assert len(list_traces(client, admin)) == 3


def test_opening_a_trace_that_does_not_exist_is_not_found(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    response = client.get(
        "/api/admin/model-calls/00000000-0000-0000-0000-000000000000",
        headers=admin,
    )

    assert response.status_code == 404


def test_plain_users_cannot_see_the_model_call_log(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    response = client.get(
        "/api/admin/model-calls", headers=auth_headers(auth_verifier, "user_maya")
    )

    assert response.status_code == 403


def test_message_retention_removes_old_entries(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "hi",
        processing_answer(summary="Said hi."),
    )
    assert stored_model_calls(engine)

    clock.advance(timedelta(days=seeded_settings["message_retention_days"] + 1))
    scheduler.tick()

    assert stored_model_calls(engine) == []


def record_one_call(
    engine: Engine,
    clock: FakeClock,
    content_for_everyone: bool,
    developer_logs: bool,
) -> ModelCallTraceDetails:
    """Record one plain User's model call straight into the Model Call Log."""
    repositories = build_postgres_repositories(engine)
    log = ModelCallLog(repositories, clock, content_for_everyone, developer_logs)
    snapshot = snapshot_for(add_user(repositories))
    log.record(
        snapshot,
        ModelCallRequest(
            step=ModelStep.REPLY,
            model="deepseek-chat",
            instructions="Be kind.",
            history=(ChatLine(ChatRole.USER, SECRET_WORDS),),
            tools=(),
        ),
        clock.now(),
        ModelAnswer(text="that sounds lovely", reasoning="They seem excited."),
    )
    return log.open_trace(snapshot.trace.id)


def test_an_eval_run_keeps_full_content_for_every_user(
    engine: Engine, clock: FakeClock
) -> None:
    trace = record_one_call(
        engine, clock, content_for_everyone=True, developer_logs=False
    )

    [call] = trace.calls
    assert call.content is not None
    assert call.content.history == (ChatLine(ChatRole.USER, SECRET_WORDS),)
    assert call.content.reasoning == "They seem excited."


def test_developer_logs_get_full_content_but_storage_does_not(
    engine: Engine, clock: FakeClock, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="companion.core.model_call_log")

    trace = record_one_call(
        engine, clock, content_for_everyone=False, developer_logs=True
    )

    assert trace.calls[0].content is None
    assert SECRET_WORDS in caplog.text
    assert "They seem excited." in caplog.text


def test_without_developer_logs_nothing_is_logged(
    engine: Engine, clock: FakeClock, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="companion.core.model_call_log")

    record_one_call(engine, clock, content_for_everyone=False, developer_logs=False)

    assert SECRET_WORDS not in caplog.text
