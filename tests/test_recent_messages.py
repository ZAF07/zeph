from datetime import date, timedelta
from typing import Any

from fastapi.testclient import TestClient

from companion.core.past_day import parse_day_argument
from companion.core.recent_messages import leave_out_past_cap
from companion.core.response_composition import MEMORY_HEADING
from tests.fakes import (
    ChatModelCall,
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
    ToolCall,
    reply_plan_answer,
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
from tests.test_day_summaries import live_in_singapore
from tests.test_model_call_log import newest_call
from tests.test_post_conversation import have_conversation, processing_answer

EARLIER_TEXT = "I'm moving flat on Saturday"
TEXT_LATER = "as I was saying, the movers cancelled"


def given_text(call: ChatModelCall) -> str:
    """Everything a model call was given: its instructions and every line."""
    lines = "\n".join(line.text for line in call.history)
    return f"{call.instructions}\n{lines}"


def newest_reply_steps(chat_model: ScriptedChatModel) -> list[ChatModelCall]:
    """The newest Understanding, Reply Plan and Reply calls."""
    return [
        chat_model.understanding_calls[-1],
        chat_model.reply_plan_calls[-1],
        chat_model.calls[-1],
    ]


def change_settings(
    client: TestClient, auth_verifier: FakeAuthVerifier, values: dict[str, Any]
) -> None:
    """Save Admin settings through the Admin API."""
    response = client.patch(
        "/api/admin/settings",
        json={"values": values},
        headers=owner_headers(client, auth_verifier),
    )
    assert response.status_code == 200, response.json()


def test_a_new_conversation_20_minutes_later_sees_the_previous_ones_messages(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_reply_plan(
        reply_plan_answer(where_we_are="planning the move, a bit anxious")
    )
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        EARLIER_TEXT,
        processing_answer(summary="Planning a move on Saturday."),
    )
    clock.advance(timedelta(minutes=3))
    chat_model.script("oh no!")

    send_to_webhook(client, telegram_text_update(TEXT_LATER))

    understanding, reply_plan, reply = newest_reply_steps(chat_model)
    for call in (understanding, reply_plan):
        assert f"Person: {EARLIER_TEXT}" in given_text(call)
        assert "Companion: mm, I hear you" in given_text(call)
        assert "New Conversation" in given_text(call)
    assert [line.text for line in reply.history] == [
        EARLIER_TEXT,
        "mm, I hear you",
        TEXT_LATER,
    ]
    assert "planning the move, a bit anxious" in given_text(reply_plan)


def test_a_message_at_00_10_sees_the_messages_from_23_50_the_day_before(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    live_in_singapore(client, auth_headers(auth_verifier, "user_maya"))
    clock.advance(timedelta(hours=6, minutes=50))
    chat_model.script("oh no, what happened?")
    send_to_webhook(client, telegram_text_update("can't sleep, big fight with Sam"))
    clock.advance(timedelta(minutes=20))
    chat_model.script_processing(processing_answer(summary="A late fight with Sam."))
    scheduler.tick()
    chat_model.script("still up?")

    send_to_webhook(client, telegram_text_update("he just texted me"))

    for call in newest_reply_steps(chat_model):
        assert "can't sleep, big fight with Sam" in given_text(call)


def test_messages_older_than_the_admin_set_window_are_not_given(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    change_settings(client, auth_verifier, {"recent_messages_hours": 2})
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "three hours ago",
        processing_answer(),
    )
    clock.advance(timedelta(hours=2, minutes=44))
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "an hour ago",
        processing_answer(),
    )
    clock.advance(timedelta(minutes=44))
    chat_model.script("hey")

    send_to_webhook(client, telegram_text_update("now"))

    for call in newest_reply_steps(chat_model):
        assert "an hour ago" in given_text(call)
        assert "three hours ago" not in given_text(call)


def test_past_the_cap_the_oldest_messages_are_replaced_by_their_day_summary(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    change_settings(client, auth_verifier, {"recent_messages_cap": 4})
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        EARLIER_TEXT,
        processing_answer(summary="Planning a move on Saturday."),
    )
    chat_model.script("what happened?", "oh no")
    send_to_webhook(client, telegram_text_update("ugh"))

    send_to_webhook(client, telegram_text_update(TEXT_LATER))

    understanding, reply_plan, reply = newest_reply_steps(chat_model)
    for call in (understanding, reply_plan, reply):
        assert EARLIER_TEXT not in given_text(call)
        assert "Planning a move on Saturday." in given_text(call)
    assert [line.text for line in reply.history] == [
        "mm, I hear you",
        "ugh",
        "what happened?",
        TEXT_LATER,
    ]


def test_the_reply_plan_reads_a_past_days_messages_with_the_past_day_tool(
    client: TestClient,
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
        EARLIER_TEXT,
        processing_answer(),
    )
    clock.advance(timedelta(days=3))
    chat_model.script_reply_plan(
        ToolCall("past_day", {"date": "2026-11-11"}), reply_plan_answer()
    )
    chat_model.script("you moved last week!")

    send_to_webhook(client, telegram_text_update("what did I say about the move?"))

    [result] = chat_model.reply_plan_calls[-1].tool_results
    assert result.startswith("2 messages from 11 Nov")
    assert f"Person: {EARLIER_TEXT}" in result
    assert "Companion: mm, I hear you" in result


def test_what_the_past_day_tool_read_reaches_the_reply_at_level_four(
    client: TestClient,
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
        EARLIER_TEXT,
        processing_answer(),
    )
    clock.advance(timedelta(days=3))
    chat_model.script_reply_plan(
        ToolCall("past_day", {"date": "2026-11-11"}),
        ToolCall("past_day", {"date": "2026-09-01"}),
        reply_plan_answer(),
    )
    chat_model.script("you said Saturday")

    send_to_webhook(client, telegram_text_update("what did I say about the move?"))

    [reply] = chat_model.calls[-1:]
    memory = reply.instructions.split(MEMORY_HEADING, 1)[1]
    assert f"Person: {EARLIER_TEXT}" in memory
    assert "No messages from 1 Sep" in memory
    assert EARLIER_TEXT not in reply.instructions.split(MEMORY_HEADING, 1)[0]


def test_the_past_day_tool_gives_no_messages_for_a_day_past_retention(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    change_settings(client, auth_verifier, {"message_retention_days": 2})
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        EARLIER_TEXT,
        processing_answer(),
    )
    clock.advance(timedelta(days=3))
    chat_model.script_reply_plan(
        ToolCall("past_day", {"date": "2026-11-11"}), reply_plan_answer()
    )
    chat_model.script("I don't have the exact words any more")

    send_to_webhook(client, telegram_text_update("what did I say about the move?"))

    [result] = chat_model.reply_plan_calls[-1].tool_results
    assert result.startswith("No messages from 11 Nov")
    assert EARLIER_TEXT not in result
    assert "Day Summary" in result
    assert "exact words" in result


def test_the_past_day_tool_call_shows_in_the_model_call_log(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    headers = connect_owner_telegram(client, auth_verifier, chat_channel)
    send = telegram_text_update("what did I say yesterday?", OWNER_TELEGRAM_USER_ID)
    chat_model.script_reply_plan(
        ToolCall("past_day", {"date": "2026-11-10"}), reply_plan_answer()
    )
    chat_model.script("nothing yesterday")

    send_to_webhook(client, send)

    reply_plan = newest_call(client, headers, "reply_plan")
    assert reply_plan["tools_called"] == ["past_day"]
    [tool_call] = reply_plan["content"]["tool_calls"]
    assert tool_call["arguments"] == {"date": "2026-11-10"}
    assert tool_call["result"].startswith("No messages from 10 Nov")


def test_the_window_settings_are_admin_editable_with_hints(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    response = client.get(
        "/api/admin/settings", headers=owner_headers(client, auth_verifier)
    )

    settings = response.json()["settings"]
    assert settings["recent_messages_hours"]["value"] == 24
    assert settings["recent_messages_cap"]["value"] > 0
    for key in ("recent_messages_hours", "recent_messages_cap"):
        assert settings[key]["hint"]


def test_the_past_day_tool_reads_only_dates_written_as_year_month_day() -> None:
    assert parse_day_argument("2026-11-12") == date(2026, 11, 12)
    for odd in ("12 Nov", "", None, 20261112, "2026-13-01"):
        assert parse_day_argument(odd) is None


def test_past_the_cap_only_the_newest_messages_are_kept() -> None:
    assert leave_out_past_cap([1, 2, 3, 4, 5], 3) == ([3, 4, 5], [1, 2])
    assert leave_out_past_cap([1, 2], 3) == ([1, 2], [])


def test_texts_left_unanswered_in_the_last_conversation_are_not_the_latest_message(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script(RuntimeError("the model is down"))
    send_to_webhook(client, telegram_text_update(EARLIER_TEXT))
    clock.advance(timedelta(minutes=20))
    chat_model.script_processing(processing_answer())
    scheduler.tick()
    chat_model.script("oh no!")

    send_to_webhook(client, telegram_text_update(TEXT_LATER))

    understanding, reply_plan, reply = newest_reply_steps(chat_model)
    for call in (understanding, reply_plan):
        earlier, latest = given_text(call).split("Latest message:")
        assert EARLIER_TEXT in earlier
        assert "--- New Conversation" in earlier
        assert EARLIER_TEXT not in latest
    assert [line.text for line in reply.history if line.role.value == "user"] == [
        EARLIER_TEXT,
        TEXT_LATER,
    ]
