from datetime import timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
from companion.core.response_composition import OPTIONAL_EXTRAS_HEADING
from tests.conftest import INITIAL_ADMIN_EMAIL
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    FakeTimer,
    ScriptedChatModel,
    reply_plan_answer,
    understanding_answer,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    owner_headers,
    post_to_webhook,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_check_in_hold_back import maya_id, next_due_at
from tests.test_check_in_now import check_in_now
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
from tests.test_moves_migration import downgrade_to
from tests.test_post_conversation import processing_answer, quiet_gap

FOLLOW_UP_DESCRIPTION = "On something you shared, like a decision or a hard day."
NOTE = "Ask how the presentation to the board went."
CHECK_IN_DUE = "A Check-in with them is due."


def weave_plan(kind: object = "A follow-up", note: object = NOTE) -> str:
    """Build a Reply Plan form that weaves the due Check-in in."""
    return reply_plan_answer(check_in={"kind": kind, "note": note})


def plan_weaves_and_reply_brings_it_up(chat_model: ScriptedChatModel) -> None:
    """Have the next Reply Plan weave the Check-in in and the check say yes."""
    chat_model.script_reply_plan(weave_plan())
    chat_model.script_brought_up_check("yes")


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
    plan_weaves_and_reply_brings_it_up(chat_model)
    chat_model.script("ha, love that. how did the board presentation go?")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "ha, love that. how did the board presentation go?"
    ]
    assert chat_model.call_order[-4:] == [
        "understanding",
        "reply_plan",
        "reply",
        "brought_up_check",
    ]
    [check_call] = chat_model.brought_up_check_calls
    assert check_call.model == seeded_settings["check_in_model"]
    assert check_call.thinking is False
    [line] = check_call.history
    assert NOTE in line.text
    assert "ha, love that. how did the board presentation go?" in line.text
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


def test_a_due_check_in_reaches_the_reply_as_an_optional_extra_not_an_order(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    chat_model.script_reply_plan(weave_plan())
    chat_model.script("sounds tasty!")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    reply_call = chat_model.calls[-1]
    instructions = reply_call.instructions
    assert "Weave it into this reply" not in instructions
    assert "Bring it up only if it fits what they need right now" in instructions
    assert instructions.index(OPTIONAL_EXTRAS_HEADING) < instructions.index(NOTE)
    assert "bring_up_check_in" not in [tool.name for tool in reply_call.tools]


def test_a_check_in_the_reply_leaves_out_is_not_logged_and_stays_due(
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
    chat_model.script_reply_plan(weave_plan(), weave_plan())
    chat_model.script_brought_up_check("no", "yes")
    chat_model.script("sounds tasty!", "how did the board presentation go?")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["sounds tasty!"]
    assert admin_log(client, auth_verifier) == []
    assert recent_check_ins(client, headers) == []
    assert next_due_at(engine, maya_id(client, headers)) == due_at

    send_to_webhook(client, telegram_text_update("with feta"))

    assert len(chat_model.brought_up_check_calls) == 2
    [entry] = admin_log(client, auth_verifier)
    assert (entry["outcome"], entry["woven_in"]) == ("sent", True)


def test_a_check_in_the_check_cannot_judge_is_taken_back_and_stays_due(
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
    chat_model.script_reply_plan(weave_plan())
    chat_model.script_brought_up_check(RuntimeError("model down"))
    chat_model.script("how did the board presentation go?")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "how did the board presentation go?"
    ]
    assert recent_check_ins(client, headers) == []
    assert next_due_at(engine, maya_id(client, headers)) == due_at


def test_the_reply_plan_is_given_the_due_check_in_kinds_and_no_check_in_model_runs(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    chat_model.script("sounds tasty!")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    [line] = chat_model.reply_plan_calls[-1].history
    assert CHECK_IN_DUE in line.text
    assert "A casual hello" in line.text
    assert "A follow-up" in line.text
    assert "A look back at a photo" not in line.text
    assert "Something I've been wondering" not in line.text
    assert "now making a big salad" in line.text
    assert chat_model.brought_up_check_calls == []
    assert chat_model.call_order[-1] == "reply"


def assert_no_check_in_offered(
    client: TestClient, auth_verifier: FakeAuthVerifier, chat_model: ScriptedChatModel
) -> None:
    """Check the last Reply Plan was offered no Check-in and none was woven in."""
    [line] = chat_model.reply_plan_calls[-1].history
    assert CHECK_IN_DUE not in line.text
    assert NOTE not in chat_model.calls[-1].instructions
    assert chat_model.brought_up_check_calls == []
    assert admin_log(client, auth_verifier) == []


def test_no_check_in_is_offered_while_the_user_is_struggling(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    chat_model.script_understanding(understanding_answer(struggling=True))
    chat_model.script_reply_plan(weave_plan())
    chat_model.script("I'm here. that sounds really hard.")

    send_to_webhook(client, telegram_text_update("my mum is in hospital again"))

    assert_no_check_in_offered(client, auth_verifier, chat_model)
    assert recent_check_ins(client, headers) == []


def test_no_check_in_is_offered_while_check_ins_are_paused(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    pause_check_ins(client, headers, "day")
    chat_model.script_reply_plan(weave_plan())
    chat_model.script("sounds tasty!")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    assert_no_check_in_offered(client, auth_verifier, chat_model)


def test_no_check_in_is_offered_before_the_due_time(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    clock.advance(ONE_DAY - timedelta(minutes=5))
    chat_model.script_reply_plan(weave_plan())
    chat_model.script("oh nice!")

    send_to_webhook(client, telegram_text_update("just got back from a run"))

    assert_no_check_in_offered(client, auth_verifier, chat_model)


def test_no_check_in_is_offered_with_check_ins_off_by_an_admin(
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
    chat_model.script_reply_plan(weave_plan())
    chat_model.script("sounds tasty!")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    assert_no_check_in_offered(client, auth_verifier, chat_model)


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
    plan_weaves_and_reply_brings_it_up(chat_model)
    chat_model.script("how did the board presentation go?")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    [entry] = admin_log(client, auth_verifier)
    assert entry["woven_in"] is True


@pytest.mark.parametrize(
    "answer",
    [
        reply_plan_answer(),
        weave_plan(kind="A look back at a photo"),
        weave_plan(kind="Not a Kind at all"),
        weave_plan(note=""),
        weave_plan(kind=3),
        reply_plan_answer(check_in="A follow-up"),
        "sure, let's do it",
        RuntimeError("model down"),
    ],
    ids=[
        "none",
        "a fixed-behaviour Kind",
        "unknown Kind",
        "no note",
        "Kind not text",
        "not an object",
        "no JSON",
        "fails",
    ],
)
def test_no_check_in_or_an_unusable_one_weaves_nothing_and_it_stays_due(
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
    chat_model.script_reply_plan(answer)
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
    plan_weaves_and_reply_brings_it_up(chat_model)
    chat_model.script("how did the board presentation go?")
    send_to_webhook(client, telegram_text_update("now making a big salad"))
    chat_model.script("so glad!")
    send_to_webhook(client, telegram_text_update("it went great"))
    chat_channel.sent.clear()

    chat_model.script_processing(processing_answer())
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    scheduler.tick()

    assert len(chat_model.brought_up_check_calls) == 1
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
    plan_weaves_and_reply_brings_it_up(chat_model)
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
    plan_weaves_and_reply_brings_it_up(chat_model)
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
    plan_weaves_and_reply_brings_it_up(chat_model)
    chat_model.script("how did the board presentation go?")
    chat_channel.text_send_failures.append(ConnectionError("telegram is down"))

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    assert recent_check_ins(client, headers) == []
    assert next_due_at(engine, maya_id(client, headers)) == due_at


def test_a_woven_in_check_in_for_a_reply_started_over_is_taken_back_and_stays_due(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    timer: FakeTimer,
    engine: Engine,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    due_at = next_due_at(engine, maya_id(client, headers))
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    plan_weaves_and_reply_brings_it_up(chat_model)
    chat_model.script("how did the board presentation go?", "yum, enjoy")
    chat_model.before_next_reply = lambda: post_to_webhook(
        client, telegram_text_update("with some pasta")
    )

    send_to_webhook(client, telegram_text_update("now making a big salad"))
    timer.end_message_waits()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["yum, enjoy"]
    assert recent_check_ins(client, headers) == []
    assert next_due_at(engine, maya_id(client, headers)) == due_at


def test_a_reply_that_fails_after_its_first_part_keeps_the_woven_in_check_in(
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
    plan_weaves_and_reply_brings_it_up(chat_model)
    chat_model.script("how did the board presentation go?\n\nand how's the salad?")
    send_text = chat_channel.send_text

    def fail_the_second_part(
        chat_id: int, text: str, reply_to_message_id: int | None = None
    ) -> None:
        if text == "and how's the salad?":
            raise ConnectionError("telegram is down")
        send_text(chat_id, text, reply_to_message_id)

    monkeypatch.setattr(chat_channel, "send_text", fail_the_second_part)

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    assert "how did the board presentation go?" in chat_channel.texts_sent_to(
        TELEGRAM_CHAT_ID
    )
    [recent] = recent_check_ins(client, headers)
    assert recent["kind"] == "A follow-up"
    assert due_at is not None
    assert next_due_at(engine, maya_id(client, headers)) == due_at + ONE_DAY


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
    chat_model.script_reply_plan(weave_plan())
    chat_model.script("sounds tasty!")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["sounds tasty!"]
    assert NOTE not in chat_model.calls[-1].instructions
    assert recent_check_ins(client, headers) == []
    assert next_due_at(engine, maya_id(client, headers)) == due_at


def test_the_model_call_log_shows_the_check_in_choice_and_check_as_shapes_only(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    plan_weaves_and_reply_brings_it_up(chat_model)
    chat_model.script("how did the board presentation go?")
    send_to_webhook(client, telegram_text_update("now making a big salad"))
    admin = owner_headers(client, auth_verifier)

    newest = list_traces(client, admin)[0]
    trace = open_trace(client, admin, newest["trace_id"])

    assert newest["kind"] == "message"
    [plan_call] = [call for call in trace["calls"] if call["step"] == "reply_plan"]
    assert plan_call["reply_plan_shape"]["check_in_kinds_offered"] == 4
    assert plan_call["reply_plan_shape"]["check_in_kind"] == "A follow-up"
    [call] = [call for call in trace["calls"] if call["step"] == "check_in"]
    assert call["content"] is None
    assert call["check_in_shape"] == {"kind": "A follow-up", "brought_up": True}
    assert NOTE not in str(trace)


def test_a_shape_saved_by_the_old_check_in_model_shows_no_shape(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    engine: Engine,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    open_a_conversation_until_due(client, chat_model, chat_channel, clock)
    plan_weaves_and_reply_brings_it_up(chat_model)
    chat_model.script("how did the board presentation go?")
    send_to_webhook(client, telegram_text_update("now making a big salad"))
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE model_calls SET check_in_shape = jsonb_build_object("
                "'kinds_offered', 4, 'woven_in', true, 'kind', 'A follow-up') "
                "WHERE step = 'check_in'"
            )
        )
    admin = owner_headers(client, auth_verifier)

    trace = open_trace(client, admin, list_traces(client, admin)[0]["trace_id"])

    [call] = [call for call in trace["calls"] if call["step"] == "check_in"]
    assert call["check_in_shape"] is None


def test_the_woven_in_check_in_prompt_is_gone_from_the_settings(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
) -> None:
    admin = owner_headers(client, auth_verifier)

    services = client.get("/api/admin/core-services", headers=admin).json()
    settings = client.get("/api/admin/settings", headers=admin).json()
    response = client.patch(
        "/api/admin/settings",
        json={"values": {"woven_check_in_prompt": "Weave it in, maybe."}},
        headers=admin,
    )

    assert "woven_check_in_prompt" not in str(services)
    assert "woven_check_in_prompt" not in str(settings)
    assert response.status_code != 200


def chat_then_check_in_now(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> tuple[dict[str, str], dict[str, str], UUID]:
    """Chat long before the Due Time, then ask for a Check in Now.

    Returns:
        Maya's headers, the Admin's headers and Maya's ID.
    """
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    maya = maya_id(client, headers)
    clock.advance(timedelta(hours=1))
    chat_model.script("oh nice!")
    send_to_webhook(client, telegram_text_update("just got back from a run"))
    check_in_now(client, admin, [maya])
    chat_channel.sent.clear()
    return headers, admin, maya


def test_a_check_in_now_mid_conversation_is_woven_into_the_reply_and_logged(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    engine: Engine,
) -> None:
    _, admin, maya = chat_then_check_in_now(
        client, auth_verifier, chat_channel, chat_model, clock
    )
    plan_weaves_and_reply_brings_it_up(chat_model)
    chat_model.script("ha, love that. how did the board presentation go?")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "ha, love that. how did the board presentation go?"
    ]
    assert NOTE in chat_model.calls[-1].instructions
    [entry] = admin_log(client, auth_verifier)
    assert (entry["outcome"], entry["woven_in"], entry["requested_by"]) == (
        "sent",
        True,
        INITIAL_ADMIN_EMAIL,
    )
    assert only_entry(client, admin)["check_in_now_waiting"] is False
    assert as_json_time(next_due_at(engine, maya) - ONE_DAY) == entry["decided_at"]


def test_a_check_in_now_is_woven_in_past_the_pause_and_the_feature_switch(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    headers, admin, maya = chat_then_check_in_now(
        client, auth_verifier, chat_channel, chat_model, clock
    )
    pause_check_ins(client, headers, "week")
    response = client.put(
        f"/api/admin/users/{maya}/features/check_ins",
        json={"switch": "off"},
        headers=admin,
    )
    assert response.status_code == 200, response.text
    plan_weaves_and_reply_brings_it_up(chat_model)
    chat_model.script("how did the board presentation go?")

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    [entry] = admin_log(client, auth_verifier)
    assert (entry["woven_in"], entry["requested_by"]) == (True, INITIAL_ADMIN_EMAIL)
    assert client.get("/api/check-ins", headers=headers).json()["paused"] is True


def test_a_check_in_now_is_never_woven_in_while_the_user_is_struggling(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    _, admin, _ = chat_then_check_in_now(
        client, auth_verifier, chat_channel, chat_model, clock
    )
    chat_model.script_understanding(understanding_answer(struggling=True))
    chat_model.script_reply_plan(weave_plan())
    chat_model.script("I'm here. that sounds really hard.")

    send_to_webhook(client, telegram_text_update("my mum is in hospital again"))

    assert_no_check_in_offered(client, auth_verifier, chat_model)
    assert only_entry(client, admin)["check_in_now_waiting"] is True


def test_a_check_in_now_not_woven_in_goes_out_on_its_own_after_the_conversation(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    engine: Engine,
    seeded_settings: dict[str, Any],
) -> None:
    _, admin, maya = chat_then_check_in_now(
        client, auth_verifier, chat_channel, chat_model, clock
    )
    chat_model.script("sounds tasty!")
    send_to_webhook(client, telegram_text_update("now making a big salad"))
    scheduler.tick()
    assert only_entry(client, admin)["check_in_now_waiting"] is True
    chat_channel.sent.clear()

    chat_model.script(send_answer("hey, how was the salad?"))
    chat_model.script_processing(processing_answer())
    clock.advance(quiet_gap(seeded_settings))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey, how was the salad?"]
    [entry] = admin_log(client, auth_verifier)
    assert (entry["woven_in"], entry["requested_by"]) == (False, INITIAL_ADMIN_EMAIL)
    assert only_entry(client, admin)["check_in_now_waiting"] is False
    assert next_due_at(engine, maya) == clock.now() + ONE_DAY


def test_a_woven_in_check_in_now_whose_reply_fails_to_send_keeps_waiting(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    _, admin, _ = chat_then_check_in_now(
        client, auth_verifier, chat_channel, chat_model, clock
    )
    plan_weaves_and_reply_brings_it_up(chat_model)
    chat_model.script("how did the board presentation go?")
    chat_channel.text_send_failures.append(ConnectionError("telegram is down"))

    send_to_webhook(client, telegram_text_update("now making a big salad"))

    assert admin_log(client, auth_verifier) == []
    assert only_entry(client, admin)["check_in_now_waiting"] is True


def weave_in_while_the_tick_decides(
    client: TestClient, chat_model: ScriptedChatModel
) -> None:
    """Have the User's message weave the Check-in in during the tick's model call."""

    def user_sends_a_message() -> None:
        plan_weaves_and_reply_brings_it_up(chat_model)
        send_to_webhook(client, telegram_text_update("now making a big salad"))

    chat_model.script("how did the board presentation go?")
    chat_model.script(send_answer("hey, how was your day?"))
    chat_model.before_next_reply = user_sends_a_message


def test_a_check_in_woven_in_while_the_tick_decides_it_is_sent_once(
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
    chat_model.script_processing(processing_answer())
    clock.advance(quiet_gap(seeded_settings))
    weave_in_while_the_tick_decides(client, chat_model)

    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "how did the board presentation go?"
    ]
    [entry] = admin_log(client, auth_verifier)
    assert entry["woven_in"] is True
    assert due_at is not None
    assert next_due_at(engine, maya_id(client, headers)) == due_at + ONE_DAY


def test_a_check_in_now_woven_in_while_the_tick_decides_it_is_sent_once(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    engine: Engine,
    seeded_settings: dict[str, Any],
) -> None:
    _, admin, maya = chat_then_check_in_now(
        client, auth_verifier, chat_channel, chat_model, clock
    )
    chat_model.script_processing(processing_answer())
    clock.advance(quiet_gap(seeded_settings))
    weave_in_while_the_tick_decides(client, chat_model)

    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "how did the board presentation go?"
    ]
    [entry] = admin_log(client, auth_verifier)
    assert (entry["woven_in"], entry["requested_by"]) == (True, INITIAL_ADMIN_EMAIL)
    assert only_entry(client, admin)["check_in_now_waiting"] is False
    assert as_json_time(next_due_at(engine, maya) - ONE_DAY) == entry["decided_at"]


def test_the_migration_removes_the_woven_in_prompt_and_reloads_the_reply_plan_prompt(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0070")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO platform_settings (key, value, updated_at) "
                    "VALUES ('woven_check_in_prompt', to_jsonb('Old'::text), now()) "
                    "ON CONFLICT (key) DO NOTHING"
                )
            )
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = to_jsonb('Edited'::text) "
                    "WHERE key = 'reply_plan_prompt'"
                )
            )
    finally:
        migrate(database_url)

    with engine.connect() as connection:
        left = connection.execute(
            text(
                "SELECT key FROM platform_settings WHERE key IN "
                "('woven_check_in_prompt', 'reply_plan_prompt')"
            )
        ).all()
    assert left == []
