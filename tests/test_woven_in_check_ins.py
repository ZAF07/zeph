import json
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import UserPortrait
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
    understanding_answer,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_check_in_hold_back import maya_id, next_due_at
from tests.test_check_in_rhythm import change_check_ins, pause_check_ins
from tests.test_check_in_schedule import as_json_time, only_entry
from tests.test_check_in_sending import (
    ONE_DAY,
    recent_check_ins,
    send_answer,
    send_check_ins,
    set_up_user_with_check_ins,
)
from tests.test_model_call_log import list_traces, open_trace
from tests.test_post_conversation import processing_answer, quiet_gap
from tests.test_web_search import change_settings

FOLLOW_UP_DESCRIPTION = "On something you shared, like a decision or a hard day."
NOTE = "Ask how the presentation to the board went."


def weave_answer(kind: str = "A follow-up", note: str = NOTE) -> str:
    """Build the Check-in model's JSON answer for weaving a Check-in in."""
    return json.dumps({"decision": "weave_in", "kind": kind, "note": note})


def open_a_conversation_until_due(
    client: TestClient,
    chat_model: ScriptedChatModel,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
) -> None:
    """Chat five minutes before the first Due Time, then let it come."""
    clock.advance(ONE_DAY - timedelta(minutes=5))
    chat_model.script("oh nice!")
    send_to_webhook(client, telegram_text_update("just got back from a run"))
    clock.advance(timedelta(minutes=5))
    chat_channel.sent.clear()


def admin_log(client: TestClient, auth_verifier: FakeAuthVerifier) -> list[Any]:
    """List the Admins' Check-in log for the last week."""
    admin = owner_headers(client, auth_verifier)
    response = client.get("/api/admin/check-ins", params={"days": 7}, headers=admin)
    assert response.status_code == 200, response.text
    entries: list[Any] = response.json()["entries"]
    return entries


def test_a_check_in_due_mid_conversation_is_woven_into_the_reply_and_logged(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    engine: Engine,
    seeded_settings: dict[str, Any],
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    due_at = next_due_at(engine, maya_id(client, headers))
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    chat_model.script_woven_check_in(weave_answer())
    chat_model.script("ha, love that. how did the board presentation go?")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "ha, love that. how did the board presentation go?"
    ]
    [woven_call] = chat_model.woven_check_in_calls
    assert woven_call.model == seeded_settings["check_in_model"]
    assert woven_call.thinking == seeded_settings["check_in_thinking"]
    assert seeded_settings["persona"] in woven_call.instructions
    reply_instructions = chat_model.calls[-1].instructions
    assert FOLLOW_UP_DESCRIPTION in reply_instructions
    assert NOTE in reply_instructions
    [entry] = admin_log(client, auth_verifier)
    assert (entry["outcome"], entry["kind"], entry["woven_in"]) == (
        "sent",
        "A follow-up",
        True,
    )
    [recent] = recent_check_ins(client, headers)
    assert (recent["outcome"], recent["kind"]) == ("sent", "A follow-up")
    assert due_at is not None
    assert next_due_at(engine, maya_id(client, headers)) == due_at + ONE_DAY
    admin = owner_headers(client, auth_verifier)
    assert only_entry(client, admin)["held_back"] is None


def test_the_woven_in_call_is_given_the_conversation_understanding_and_portrait(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    engine: Engine,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    build_postgres_repositories(engine).user_portraits.save(
        UserPortrait(
            user_id=maya_id(client, headers),
            text="Maya is a nurse who unwinds by baking on weekends.",
            written_at=clock.now(),
        )
    )
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    chat_model.script_understanding(
        understanding_answer(mood="cheerful and chatty", nuance="Light catch-up.")
    )
    chat_model.script("sounds tasty!")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    [woven_call] = chat_model.woven_check_in_calls
    [line] = woven_call.history
    assert "just got back from a run" in line.text
    assert "now making a big salad" in line.text
    assert "oh nice!" in line.text
    assert "cheerful and chatty" in line.text
    assert "Maya is a nurse who unwinds by baking on weekends." in line.text
    assert "A casual hello" in line.text
    assert "A follow-up" in line.text
    assert "A look back at a photo" not in line.text
    assert "Something I've been wondering" not in line.text
    assert "Thursday, 17:00" in line.text


def test_no_woven_in_call_is_made_while_the_user_is_struggling(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    chat_model.script_understanding(understanding_answer(struggling=True))
    chat_model.script("I'm here. that sounds really hard.")

    send_to_webhook(client, telegram_text_update("my mum is in hospital again"))

    assert chat_model.woven_check_in_calls == []
    assert recent_check_ins(client, headers) == []


def test_no_woven_in_call_is_made_while_check_ins_are_paused(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    pause_check_ins(client, headers, "day")
    chat_model.script("sounds tasty!")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    assert chat_model.woven_check_in_calls == []


def test_no_woven_in_call_is_made_before_the_due_time(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    clock.advance(ONE_DAY - timedelta(minutes=5))
    chat_model.script("oh nice!")

    send_to_webhook(client, telegram_text_update("just got back from a run"))

    assert chat_model.woven_check_in_calls == []


def test_no_woven_in_call_is_made_with_check_ins_off_by_an_admin(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    response = client.put(
        "/api/admin/features/check_ins",
        json={"on": False},
        headers=owner_headers(client, auth_verifier),
    )
    assert response.status_code == 200, response.text
    chat_model.script("sounds tasty!")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    assert chat_model.woven_check_in_calls == []


def test_a_check_in_can_be_woven_in_during_quiet_hours(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    change_check_ins(
        client, headers, {"quiet_hours_start": "16:00", "quiet_hours_end": "18:00"}
    )
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    chat_model.script_woven_check_in(weave_answer())
    chat_model.script("how did the board presentation go?")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    [entry] = admin_log(client, auth_verifier)
    assert entry["woven_in"] is True


@pytest.mark.parametrize(
    "answer",
    [
        json.dumps({"decision": "not_now"}),
        weave_answer(kind="A look back at a photo"),
        weave_answer(kind="Not a Kind at all"),
        weave_answer(note=""),
        "sure, let's do it",
        RuntimeError("model down"),
    ],
    ids=[
        "not now",
        "a fixed-behaviour Kind",
        "unknown Kind",
        "no note",
        "no JSON",
        "fails",
    ],
)
def test_not_now_or_an_unusable_answer_weaves_nothing_and_it_stays_due(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    engine: Engine,
    answer: str | Exception,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    due_at = next_due_at(engine, maya_id(client, headers))
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    chat_model.script_woven_check_in(answer)
    chat_model.script("sounds tasty!")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["sounds tasty!"]
    assert NOTE not in chat_model.calls[-1].instructions
    assert recent_check_ins(client, headers) == []
    assert next_due_at(engine, maya_id(client, headers)) == due_at


def test_when_no_reply_weaves_it_in_it_waits_then_goes_out_after_the_conversation(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    engine: Engine,
    seeded_settings: dict[str, Any],
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    due_at = next_due_at(engine, maya_id(client, headers))
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    chat_model.script("sounds tasty!")
    send_to_webhook(client, telegram_text_update("now making a big salad"))
    conversation_ends_at = clock.now() + quiet_gap(seeded_settings)
    chat_channel.sent.clear()

    scheduler.tick()

    admin = owner_headers(client, auth_verifier)
    assert chat_channel.sent == []
    assert only_entry(client, admin)["held_back"] == {
        "reason": "waiting_to_be_woven_in",
        "until": as_json_time(conversation_ends_at),
    }
    assert next_due_at(engine, maya_id(client, headers)) == due_at

    chat_model.script(send_answer("hey, how was the salad?"))
    chat_model.script_processing(processing_answer())
    clock.advance(quiet_gap(seeded_settings))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey, how was the salad?"]
    [entry] = admin_log(client, auth_verifier)
    assert entry["woven_in"] is False


def test_a_woven_in_check_in_is_not_woven_in_again_nor_sent_on_its_own(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    chat_model.script_woven_check_in(weave_answer())
    chat_model.script("how did the board presentation go?")
    send_to_webhook(client, telegram_text_update("now making a big salad"))
    chat_model.script("so glad!")
    send_to_webhook(client, telegram_text_update("it went great"))
    chat_channel.sent.clear()

    chat_model.script_processing(processing_answer())
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    scheduler.tick()

    assert len(chat_model.woven_check_in_calls) == 1
    assert chat_channel.sent == []
    assert len(admin_log(client, auth_verifier)) == 1


def test_the_users_next_message_counts_as_the_woven_in_check_ins_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    chat_model.script_woven_check_in(weave_answer())
    chat_model.script("how did the board presentation go?")
    send_to_webhook(client, telegram_text_update("now making a big salad"))
    assert recent_check_ins(client, headers)[0]["status"] == "sent"

    chat_model.script("so glad!")
    send_to_webhook(client, telegram_text_update("it went great"))

    assert recent_check_ins(client, headers)[0]["status"] == "replied"
    assert [line.text for line in chat_model.calls[-1].history] == [
        "just got back from a run",
        "oh nice!",
        "now making a big salad",
        "how did the board presentation go?",
        "it went great",
    ]


def test_woven_in_check_ins_never_count_toward_the_ignore_threshold(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    threshold = seeded_settings["check_in_ignore_threshold"]
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    chat_model.script_woven_check_in(weave_answer())
    chat_model.script("how did the board presentation go?")
    send_to_webhook(client, telegram_text_update("now making a big salad"))
    chat_model.script_processing(processing_answer())
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    scheduler.tick()
    send_check_ins(chat_model, clock, scheduler, threshold - 1)
    chat_channel.sent.clear()

    chat_model.script(send_answer("hey, how's your weekend shaping up?"))
    clock.advance(ONE_DAY)
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey, how's your weekend shaping up?"
    ]


def test_a_reply_that_fails_to_send_logs_no_check_in_and_it_stays_due(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    engine: Engine,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    due_at = next_due_at(engine, maya_id(client, headers))
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    chat_model.script_woven_check_in(weave_answer())
    chat_model.script("how did the board presentation go?")
    chat_channel.text_send_failures.append(ConnectionError("telegram is down"))

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    assert recent_check_ins(client, headers) == []
    assert next_due_at(engine, maya_id(client, headers)) == due_at


def test_a_woven_in_check_in_whose_save_fails_is_not_woven_in(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    due_at = next_due_at(engine, maya_id(client, headers))
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)

    def fail(*args: Any, **kwargs: Any) -> bool:
        raise ConnectionError("the database dropped")

    monkeypatch.setattr(
        "companion.adapters.postgres.repositories.PostgresCheckInRepository.add_woven_in",
        fail,
    )
    chat_model.script_woven_check_in(weave_answer())
    chat_model.script("sounds tasty!")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["sounds tasty!"]
    assert NOTE not in chat_model.calls[-1].instructions
    assert recent_check_ins(client, headers) == []
    assert next_due_at(engine, maya_id(client, headers)) == due_at


def test_the_model_call_log_shows_the_woven_in_step_with_its_shape_only(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    chat_model.script_woven_check_in(weave_answer())
    chat_model.script("how did the board presentation go?")
    send_to_webhook(client, telegram_text_update("now making a big salad"))
    admin = owner_headers(client, auth_verifier)

    newest = list_traces(client, admin)[0]
    trace = open_trace(client, admin, newest["trace_id"])

    assert newest["kind"] == "message"
    [call] = [call for call in trace["calls"] if call["step"] == "check_in"]
    assert call["content"] is None
    assert call["check_in_shape"] == {
        "kinds_offered": 4,
        "woven_in": True,
        "kind": "A follow-up",
    }
    assert NOTE not in str(trace)


def test_the_woven_in_check_in_prompt_is_editable_by_admins(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    services = client.get("/api/admin/core-services", headers=admin).json()
    [check_ins] = [
        service for service in services["services"] if service["name"] == "Check-ins"
    ]
    assert "woven_check_in_prompt" in str(check_ins)
    change_settings(client, admin, {"woven_check_in_prompt": "Weave it in, maybe."})
    chat_model.woven_check_in_prompt = "Weave it in, maybe."
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    chat_model.script("sounds tasty!")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    [woven_call] = chat_model.woven_check_in_calls
    assert woven_call.instructions.endswith("Weave it in, maybe.")
