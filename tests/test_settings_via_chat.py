from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine

from tests.fakes import (
    ChatModelCall,
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    FakeTimer,
    ScriptedChatModel,
    ToolCall,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    post_to_webhook,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_check_in_sending import set_up_user_with_check_ins
from tests.test_data_deletion import (
    assert_treated_as_unknown_telegram_user,
    rows_per_table,
    set_up_user_with_every_kind_of_data,
    user_data_tables,
)
from tests.test_post_conversation import memory_contents

SETTINGS_TOOLS = [
    "pause_check_ins",
    "resume_check_ins",
    "change_check_in_frequency",
    "change_quiet_hours",
    "turn_user_memory_on_or_off",
    "turn_photo_viewing_on_or_off",
    "list_memories",
    "forget_memory",
    "change_time_zone",
    "start_deleting_my_data",
]


def reply_call(
    client: TestClient,
    chat_model: ScriptedChatModel,
    text: str,
    *script: str | ToolCall,
) -> ChatModelCall:
    """Send a Telegram message and return the reply call the model received."""
    chat_model.calls.clear()
    chat_model.script(*script)
    assert send_to_webhook(client, telegram_text_update(text)) == 200
    [call] = chat_model.calls
    return call


def check_ins(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    """Get the User's Check-in settings through the Dashboard API."""
    body: dict[str, Any] = client.get("/api/check-ins", headers=headers).json()
    return body


def me(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    """Get the signed-in User through the Dashboard API."""
    body: dict[str, Any] = client.get("/api/me", headers=headers).json()
    return body


def tables_a_reply_leaves_alone(engine: Engine) -> list[str]:
    """List the per-User tables a cancelled Delete My Data must not change.

    The Model Call Log is left out: every reply adds to it.
    """
    return [table for table in user_data_tables(engine) if table != "model_calls"]


def test_settings_tools_are_offered_with_their_instructions(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)

    call = reply_call(client, chat_model, "hi", "hey")

    offered = [tool.name for tool in call.tools]
    assert [name for name in offered if name in SETTINGS_TOOLS] == SETTINGS_TOOLS
    instructions = seeded_settings["reply_settings_instructions"]
    assert instructions in call.instructions
    assert "ask" in instructions
    assert "Dashboard" in instructions


def test_pausing_check_ins_in_chat_saves_the_pause_and_marks_it_changed_in_chat(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    now = clock.now()

    call = reply_call(
        client,
        chat_model,
        "can you give me a week off from check-ins?",
        ToolCall("pause_check_ins", {"length": "week"}),
        "Done, I've paused Check-ins for a week.",
    )

    settings = check_ins(client, headers)
    assert settings["paused"] is True
    assert settings["paused_until"] == (now + timedelta(days=7)).isoformat().replace(
        "+00:00", "Z"
    )
    [result] = call.tool_results
    assert "paused" in result
    assert "Tell them plainly" in result
    assert me(client, headers)["changed_in_chat"] == {
        "check_in_pause": now.isoformat().replace("+00:00", "Z")
    }
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "Done, I've paused Check-ins for a week."
    ]


def test_resuming_check_ins_in_chat_ends_the_pause(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    client.put(
        "/api/check-ins/pause", json={"length": "until_resumed"}, headers=headers
    )

    call = reply_call(
        client,
        chat_model,
        "ok you can start checking in again",
        ToolCall("resume_check_ins", {}),
        "Great, Check-ins are back on.",
    )

    assert check_ins(client, headers)["paused"] is False
    assert "resumed" in call.tool_results[0]
    assert "check_in_pause" in me(client, headers)["changed_in_chat"]


def test_pausing_when_check_ins_are_off_changes_nothing(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(
        client, auth_verifier, chat_channel, check_ins_enabled=False
    )

    call = reply_call(
        client,
        chat_model,
        "pause check-ins for a day",
        ToolCall("pause_check_ins", {"length": "day"}),
        "They're off already.",
    )

    settings = check_ins(client, headers)
    assert settings["enabled"] is False
    assert settings["paused"] is False
    assert "Nothing changed" in call.tool_results[0]
    assert me(client, headers)["changed_in_chat"] == {}


def test_changing_frequency_and_quiet_hours_in_chat(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)

    call = reply_call(
        client,
        chat_model,
        "check in once a week at most, and not after 9pm",
        ToolCall("change_check_in_frequency", {"frequency": "weekly"}),
        ToolCall("change_quiet_hours", {"start": "21:00"}),
        "Done: once a week at most, and quiet from 9pm.",
    )

    settings = check_ins(client, headers)
    assert settings["frequency"] == "weekly"
    assert settings["quiet_hours_start"] == "21:00:00"
    assert settings["quiet_hours_end"] == "07:30:00"
    frequency_result, quiet_hours_result = call.tool_results
    assert "once a week" in frequency_result
    assert "21:00" in quiet_hours_result
    assert set(me(client, headers)["changed_in_chat"]) == {
        "check_in_frequency",
        "quiet_hours",
    }


def test_unclear_quiet_hours_change_nothing(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)

    call = reply_call(
        client,
        chat_model,
        "make quiet hours later",
        ToolCall("change_quiet_hours", {"start": "late"}),
        "What time should they start?",
    )

    assert check_ins(client, headers)["quiet_hours_start"] == "22:00:00"
    assert "Nothing changed" in call.tool_results[0]
    assert me(client, headers)["changed_in_chat"] == {}


def test_turning_user_memory_off_and_on_in_chat(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)

    off = reply_call(
        client,
        chat_model,
        "stop remembering things about me",
        ToolCall("turn_user_memory_on_or_off", {"on": False}),
        "Okay, memory is off.",
    )
    assert me(client, headers)["user_memory_enabled"] is False
    assert "off" in off.tool_results[0]

    reply_call(
        client,
        chat_model,
        "actually turn memory back on",
        ToolCall("turn_user_memory_on_or_off", {"on": True}),
        "Memory's back on.",
    )
    assert me(client, headers)["user_memory_enabled"] is True
    assert "user_memory" in me(client, headers)["changed_in_chat"]


def test_forgetting_a_named_memory_item_in_chat(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    before = memory_contents(client, headers)
    assert before["Life details"] == ["Goes by Maya"]
    listed = reply_call(
        client, chat_model, "what do you remember?", ToolCall("list_memories", {}), "."
    ).tool_results[0]
    [number] = [
        line.split(".")[0] for line in listed.splitlines() if "Goes by Maya" in line
    ]

    call = reply_call(
        client,
        chat_model,
        "forget my name",
        ToolCall("list_memories", {}),
        ToolCall("forget_memory", {"number": int(number)}),
        "Done, I've forgotten that.",
    )

    forgotten = call.tool_results[1]
    assert "Goes by Maya" in forgotten
    after = memory_contents(client, headers)
    assert "Life details" not in after
    assert after["Goals"] == before["Goals"]


def test_forgetting_without_listing_or_with_a_wrong_number_changes_nothing(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    before = memory_contents(client, headers)

    call = reply_call(
        client,
        chat_model,
        "forget that",
        ToolCall("forget_memory", {"number": 1}),
        ToolCall("list_memories", {}),
        ToolCall("forget_memory", {"number": 99}),
        "Which one should I forget?",
    )

    not_listed, _, wrong_number = call.tool_results
    assert "list_memories" in not_listed
    assert "Nothing changed" in wrong_number
    assert memory_contents(client, headers) == before


def test_changing_time_zone_in_chat(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)

    call = reply_call(
        client,
        chat_model,
        "I've moved to London",
        ToolCall("change_time_zone", {"time_zone": "Atlantis/Lost"}),
        ToolCall("change_time_zone", {"time_zone": "Europe/London"}),
        "Got it, your time zone is London now.",
    )

    unknown, changed = call.tool_results
    assert "Nothing changed" in unknown
    assert "Europe/London" in changed
    assert me(client, headers)["time_zone"] == "Europe/London"
    assert "time_zone" in me(client, headers)["changed_in_chat"]


def test_a_dashboard_change_clears_the_changed_in_chat_mark(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    reply_call(
        client,
        chat_model,
        "quiet from 9pm and I'm in London now",
        ToolCall("change_quiet_hours", {"start": "21:00"}),
        ToolCall("change_time_zone", {"time_zone": "Europe/London"}),
        "Done.",
    )

    client.patch("/api/check-ins", json={"quiet_hours_end": "08:00"}, headers=headers)

    assert me(client, headers)["changed_in_chat"].keys() == {"time_zone"}


def test_delete_my_data_in_chat_only_deletes_after_the_confirmation_word(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    headers, user_id = set_up_user_with_every_kind_of_data(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    word = seeded_settings["data_deletion_confirmation_word"]

    call = reply_call(
        client,
        chat_model,
        "please delete all my data",
        ToolCall("start_deleting_my_data", {}),
        f"Reply {word} to confirm.",
    )
    assert f'"{word}"' in call.tool_results[0]
    assert "on its own, with nothing after it" in call.tool_results[0]
    data_tables = user_data_tables(engine)
    assert all(
        count > 0 for count in rows_per_table(engine, user_id, data_tables).values()
    )

    chat_channel.sent.clear()
    chat_model.calls.clear()
    assert send_to_webhook(client, telegram_text_update(f"  {word}  ")) == 200

    assert chat_model.calls == []
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        seeded_settings["data_deleted_reply"]
    ]
    assert rows_per_table(engine, user_id, data_tables) == dict.fromkeys(data_tables, 0)
    assert me(client, headers)["name"] == "Maya"
    assert_treated_as_unknown_telegram_user(
        client, chat_channel, chat_model, seeded_settings
    )


def test_any_other_reply_cancels_delete_my_data(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    _, user_id = set_up_user_with_every_kind_of_data(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    word = seeded_settings["data_deletion_confirmation_word"]
    reply_call(
        client,
        chat_model,
        "delete my data",
        ToolCall("start_deleting_my_data", {}),
        f"Reply {word} to confirm.",
    )
    before = rows_per_table(engine, user_id, tables_a_reply_leaves_alone(engine))

    cancelled = reply_call(
        client, chat_model, f"hmm, {word.lower()} everything? no wait", "Okay."
    )
    later = reply_call(client, chat_model, word, "Hm?")

    assert (
        rows_per_table(engine, user_id, tables_a_reply_leaves_alone(engine)) == before
    )
    cancel_note = seeded_settings["reply_data_deletion_cancelled_note"]
    word_not_alone_note = seeded_settings["reply_data_deletion_word_not_alone_note"]
    assert cancel_note in cancelled.instructions
    assert word_not_alone_note not in cancelled.instructions
    assert cancel_note not in later.instructions


def test_the_word_with_another_text_in_one_message_cancels_and_says_why(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    timer: FakeTimer,
    seeded_settings: dict[str, Any],
) -> None:
    _, user_id = set_up_user_with_every_kind_of_data(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    word = seeded_settings["data_deletion_confirmation_word"]
    reply_call(
        client,
        chat_model,
        "delete my data",
        ToolCall("start_deleting_my_data", {}),
        f"Reply {word} to confirm.",
    )
    before = rows_per_table(engine, user_id, user_data_tables(engine))
    chat_model.script("Nothing was deleted.")

    for text in (word, "bye for good"):
        assert post_to_webhook(client, telegram_text_update(text)) == 200
    timer.end_message_waits()

    assert rows_per_table(engine, user_id, user_data_tables(engine)) == before
    instructions = chat_model.calls[-1].instructions
    assert seeded_settings["reply_data_deletion_word_not_alone_note"] in instructions
    assert seeded_settings["reply_data_deletion_cancelled_note"] not in instructions


def test_a_crisis_message_never_runs_a_settings_tool(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_model.script_safeguard("suicide_or_self_harm")
    chat_model.script(ToolCall("pause_check_ins", {"length": "week"}), "unused")

    send_to_webhook(
        client,
        telegram_text_update("pause everything, I don't want to be here anymore"),
    )

    assert chat_model.calls == []
    assert check_ins(client, headers)["paused"] is False
    assert me(client, headers)["changed_in_chat"] == {}


def test_a_crisis_message_cancels_a_pending_delete_my_data(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    _, user_id = set_up_user_with_every_kind_of_data(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    word = seeded_settings["data_deletion_confirmation_word"]
    reply_call(
        client,
        chat_model,
        "delete my data",
        ToolCall("start_deleting_my_data", {}),
        f"Reply {word} to confirm.",
    )
    chat_model.script_safeguard("suicide_or_self_harm")
    send_to_webhook(client, telegram_text_update("I want to end it all"))
    before = rows_per_table(engine, user_id, tables_a_reply_leaves_alone(engine))

    reply_call(client, chat_model, word, "Hm?")

    assert (
        rows_per_table(engine, user_id, tables_a_reply_leaves_alone(engine)) == before
    )


def test_saving_the_profile_without_changing_the_time_zone_keeps_its_mark(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    reply_call(
        client,
        chat_model,
        "I'm in London now, and stop remembering things",
        ToolCall("change_time_zone", {"time_zone": "Europe/London"}),
        ToolCall("turn_user_memory_on_or_off", {"on": False}),
        "Done.",
    )

    client.patch(
        "/api/me",
        json={
            "name": "Maya L",
            "country": "SG",
            "time_zone": "Europe/London",
            "user_memory_enabled": False,
        },
        headers=headers,
    )

    assert me(client, headers)["changed_in_chat"].keys() == {
        "time_zone",
        "user_memory",
    }


def test_turning_check_ins_off_on_the_dashboard_clears_the_pause_mark(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    reply_call(
        client,
        chat_model,
        "week off please",
        ToolCall("pause_check_ins", {"length": "week"}),
        "Done.",
    )

    client.patch("/api/check-ins", json={"enabled": False}, headers=headers)

    assert me(client, headers)["changed_in_chat"] == {}
