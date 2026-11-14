import json
from datetime import UTC, datetime, timedelta
from typing import Any

import yaml
from fastapi.testclient import TestClient

from tests.conftest import CHECK_IN_KINDS_SEED_FILE
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    auth_headers,
    connect_telegram,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_onboarding import onboarding_answers
from tests.test_post_conversation import (
    have_conversation,
    processing_answer,
    quiet_gap,
)

ONE_DAY = timedelta(days=1)


def send_answer(message: str, kind: str = "A casual hello") -> str:
    """Build the Check-in model's JSON answer for sending a Check-in."""
    return json.dumps({"decision": "send", "kind": kind, "message": message})


def skip_answer(reason: str) -> str:
    """Build the Check-in model's JSON answer for skipping a Check-in."""
    return json.dumps({"decision": "skip", "reason": reason})


def set_up_user_with_check_ins(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    **overrides: Any,
) -> dict[str, str]:
    """Connect Telegram and onboard with Check-ins on "most days" in Singapore.

    The clock starts at 09:00 UTC (17:00 in Singapore), so the first Check-in
    is due a day later at the same time, outside the seeded quiet hours.
    """
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    answers = onboarding_answers(
        **{"check_ins_enabled": True, "check_in_frequency": "most_days", **overrides}
    )
    assert (
        client.put("/api/onboarding", json=answers, headers=headers).status_code == 200
    )
    return headers


def seeded_check_in_kinds() -> list[str]:
    """The names of the seeded Check-in Kinds that send no Shared Photo."""
    kinds: list[dict[str, Any]] = yaml.safe_load(CHECK_IN_KINDS_SEED_FILE.read_text())
    return [kind["name"] for kind in kinds if not kind.get("sends_shared_photo")]


def recent_check_ins(
    client: TestClient, headers: dict[str, str]
) -> list[dict[str, Any]]:
    """List the User's recent Check-ins through the Dashboard API."""
    recent: list[dict[str, Any]] = client.get("/api/check-ins", headers=headers).json()[
        "recent"
    ]
    return recent


def test_a_due_user_gets_a_casual_hello_written_by_the_check_in_model(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)

    chat_model.script(send_answer("hey Maya, how's your thursday going?"))
    clock.advance(ONE_DAY - timedelta(minutes=1))
    scheduler.tick()
    assert chat_channel.sent == []

    clock.advance(timedelta(minutes=1))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey Maya, how's your thursday going?"
    ]
    [call] = chat_model.calls
    assert call.model == seeded_settings["check_in_model"]
    assert seeded_settings["check_in_prompt"] in call.instructions
    assert seeded_settings["persona"] in call.instructions
    [line] = call.history
    assert "A casual hello" in line.text
    assert "Maya" in line.text
    assert "Thursday, 17:00" in line.text
    assert recent_check_ins(client, headers) == [
        {
            "id": recent_check_ins(client, headers)[0]["id"],
            "outcome": "sent",
            "kind": "A casual hello",
            "decided_at": "2026-11-12T09:00:00Z",
            "status": "sent",
            "skipped_for_daily_limit": False,
        }
    ]


def test_the_next_check_in_waits_for_the_frequency_gap(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    clock.advance(ONE_DAY)
    chat_model.script(send_answer("hey, how's it going?"), send_answer("hi again 👋"))
    scheduler.tick()

    clock.advance(ONE_DAY - timedelta(minutes=5))
    scheduler.tick()
    assert len(chat_channel.sent) == 1

    clock.advance(timedelta(minutes=5))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey, how's it going?",
        "hi again 👋",
    ]
    assert [check_in["status"] for check_in in recent_check_ins(client, headers)] == [
        "sent",
        "no_reply",
    ]


def test_no_check_in_is_sent_during_quiet_hours_in_the_users_time_zone(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_check_ins(
        client,
        auth_verifier,
        chat_channel,
        quiet_hours_start="16:00",
        quiet_hours_end="19:00",
    )
    chat_model.script(send_answer("evening! how was today?"))

    clock.advance(ONE_DAY)
    scheduler.tick()
    clock.advance(timedelta(hours=1, minutes=59))
    scheduler.tick()
    assert chat_channel.sent == []

    clock.advance(timedelta(minutes=1))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["evening! how was today?"]


def test_quiet_hours_follow_the_users_own_time_zone(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_check_ins(
        client,
        auth_verifier,
        chat_channel,
        country="US",
        time_zone="America/New_York",
        quiet_hours_start="08:00",
        quiet_hours_end="10:00",
    )

    clock.advance(ONE_DAY)
    chat_model.script(send_answer("up early? hope you're doing ok"))
    scheduler.tick()

    assert clock.now() == datetime(2026, 11, 12, 9, 0, tzinfo=UTC)
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "up early? hope you're doing ok"
    ]
    assert "Thursday, 04:00" in chat_model.calls[0].history[0].text


def test_quiet_hours_can_run_past_midnight(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_check_ins(
        client,
        auth_verifier,
        chat_channel,
        quiet_hours_start="15:00",
        quiet_hours_end="07:30",
    )
    chat_model.script(send_answer("good morning ☀️"))

    clock.advance(ONE_DAY)
    scheduler.tick()
    clock.advance(timedelta(hours=14, minutes=29))
    scheduler.tick()
    assert chat_channel.sent == []

    clock.advance(timedelta(minutes=1))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["good morning ☀️"]


def test_no_check_in_is_sent_with_check_ins_off(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    client.patch("/api/check-ins", json={"enabled": False}, headers=headers)
    chat_model.script(send_answer("hey, how are you?"))

    clock.advance(timedelta(weeks=2))
    scheduler.tick()

    assert chat_channel.sent == []


def test_no_check_in_is_sent_while_paused_and_one_is_sent_once_the_pause_ends(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    client.put("/api/check-ins/pause", json={"length": "week"}, headers=headers)
    chat_model.script(send_answer("hey, been a little while. how are you?"))

    for _ in range(6):
        clock.advance(ONE_DAY)
        scheduler.tick()
    clock.advance(ONE_DAY - timedelta(minutes=1))
    scheduler.tick()
    assert chat_channel.sent == []

    clock.advance(timedelta(minutes=1))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey, been a little while. how are you?"
    ]
    assert client.get("/api/check-ins", headers=headers).json()["frequency"] == (
        "most_days"
    )


def test_no_check_in_is_sent_while_paused_until_resumed(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    client.put(
        "/api/check-ins/pause", json={"length": "until_resumed"}, headers=headers
    )
    chat_model.script(send_answer("hi! nice to hear from you again"))

    clock.advance(timedelta(weeks=4))
    scheduler.tick()
    assert chat_channel.sent == []

    client.delete("/api/check-ins/pause", headers=headers)
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hi! nice to hear from you again"
    ]


def test_no_check_in_is_sent_in_the_middle_of_a_conversation(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    clock.advance(ONE_DAY - timedelta(minutes=10))
    chat_model.script("oh nice!")
    send_to_webhook(client, telegram_text_update("just got back from a run"))
    chat_channel.sent.clear()
    chat_model.script(send_answer("hey, how's the rest of your day?"))

    clock.advance(timedelta(minutes=10))
    scheduler.tick()

    assert chat_channel.sent == []
    quiet_gap = timedelta(minutes=seeded_settings["conversation_quiet_gap_minutes"])
    clock.advance(quiet_gap)
    chat_model.script_processing(
        '{"summary": "Went for a run.", "mood": "good", "memory_operations": []}'
    )
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey, how's the rest of your day?"
    ]


def test_a_failing_check_in_model_sends_nothing_and_tries_again_next_tick(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    clock.advance(ONE_DAY)
    chat_model.script(RuntimeError("model down"), send_answer("hey there 🙂"))

    scheduler.tick()
    assert chat_channel.sent == []
    assert recent_check_ins(client, headers) == []

    clock.advance(timedelta(minutes=5))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey there 🙂"]


def test_a_reply_to_a_check_in_starts_a_conversation_handled_like_any_other(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    clock.advance(ONE_DAY)
    chat_model.script(send_answer("hey Maya, how did the presentation go?"))
    scheduler.tick()
    chat_channel.sent.clear()

    clock.advance(timedelta(hours=3))
    chat_model.script("that's brilliant, well done!")
    send_to_webhook(client, telegram_text_update("it went really well actually!"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "that's brilliant, well done!"
    ]
    reply_call = chat_model.calls[-1]
    assert [line.text for line in reply_call.history] == [
        "hey Maya, how did the presentation go?",
        "it went really well actually!",
    ]
    assert [line.role for line in reply_call.history] == ["companion", "user"]
    assert len(chat_model.safeguard_calls) == 1
    assert recent_check_ins(client, headers)[0]["status"] == "replied"


def test_only_the_first_message_after_a_check_in_counts_as_its_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    clock.advance(ONE_DAY)
    chat_model.script(send_answer("hey, how are you?"))
    scheduler.tick()
    chat_model.script("glad to hear it")
    send_to_webhook(client, telegram_text_update("good thanks"))

    quiet_gap = timedelta(minutes=seeded_settings["conversation_quiet_gap_minutes"])
    clock.advance(quiet_gap + timedelta(minutes=1))
    chat_model.script_processing(
        '{"summary": "Said hi.", "mood": "fine", "memory_operations": []}'
    )
    scheduler.tick()
    chat_model.script("oh what about?")
    send_to_webhook(client, telegram_text_update("random thought"))

    assert [line.text for line in chat_model.calls[-1].history] == ["random thought"]


def test_a_message_long_after_an_ignored_check_in_is_not_its_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    headers = set_up_user_with_check_ins(
        client, auth_verifier, chat_channel, check_in_frequency="weekly"
    )
    clock.advance(timedelta(weeks=1))
    chat_model.script(send_answer("hey, how's your week been?"))
    scheduler.tick()
    assert recent_check_ins(client, headers)[0]["status"] == "sent"

    window = timedelta(hours=seeded_settings["check_in_reply_window_hours"])
    clock.advance(window)
    assert recent_check_ins(client, headers)[0]["status"] == "no_reply"
    chat_model.script("oh hey, what's up?")
    send_to_webhook(client, telegram_text_update("random question for you"))

    assert [line.text for line in chat_model.calls[-1].history] == [
        "random question for you"
    ]
    assert recent_check_ins(client, headers)[0]["status"] == "no_reply"


def test_the_check_in_model_chooses_the_kind_from_recent_summaries_and_memory_items(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "big interview on friday, so nervous",
        processing_answer(
            summary="Nervous about a job interview on Friday.",
            mood="anxious",
            operations=[
                {"action": "add", "category": "Goals", "content": "Wants a new job"}
            ],
        ),
    )
    chat_channel.sent.clear()
    chat_model.script(send_answer("hey, how did the interview go?", kind="a follow-up"))

    clock.advance(ONE_DAY)
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey, how did the interview go?"
    ]
    [line] = chat_model.calls[-1].history
    for kind in seeded_check_in_kinds():
        assert kind in line.text
    assert "Nervous about a job interview on Friday." in line.text
    assert "Wants a new job" in line.text
    assert recent_check_ins(client, headers)[0]["kind"] == "A follow-up"


def test_a_skip_is_recorded_and_the_next_attempt_moves_to_the_following_slot(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_model.script(skip_answer("They asked for some space this week."))

    clock.advance(ONE_DAY)
    scheduler.tick()

    assert chat_channel.sent == []
    [skipped] = recent_check_ins(client, headers)
    assert skipped == {
        "id": skipped["id"],
        "outcome": "skipped",
        "kind": None,
        "decided_at": "2026-11-12T09:00:00Z",
        "status": "skipped",
        "skipped_for_daily_limit": False,
    }
    clock.advance(ONE_DAY - timedelta(minutes=1))
    scheduler.tick()
    assert len(chat_model.calls) == 1

    chat_model.script(send_answer("hey, hope the week's been kind to you"))
    clock.advance(timedelta(minutes=1))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey, hope the week's been kind to you"
    ]


def send_check_ins(
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    count: int,
    gap: timedelta = ONE_DAY,
) -> None:
    """Let a gap pass and send a casual-hello Check-in, `count` times."""
    for number in range(count):
        chat_model.script(send_answer(f"hey, just saying hi #{number}"))
        clock.advance(gap)
        scheduler.tick()


def test_after_the_ignore_threshold_one_would_you_like_fewer_message_pauses_check_ins(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    threshold = seeded_settings["check_in_ignore_threshold"]
    send_check_ins(chat_model, clock, scheduler, threshold)
    model_calls = len(chat_model.calls)

    clock.advance(ONE_DAY)
    scheduler.tick()

    sent = chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)
    assert len(sent) == threshold + 1
    assert sent[-1] == seeded_settings["check_in_fewer_message"]
    assert len(chat_model.calls) == model_calls
    check_ins = client.get("/api/check-ins", headers=headers).json()
    assert check_ins["paused"] is True
    assert check_ins["paused_until"] is None
    assert check_ins["recent"][0]["outcome"] == "asked_about_fewer"

    clock.advance(timedelta(weeks=2))
    scheduler.tick()
    assert len(chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)) == threshold + 1


def test_a_reply_to_a_check_in_resets_the_ignored_count(
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
    send_check_ins(chat_model, clock, scheduler, threshold)
    chat_model.script("aw, glad you're ok")
    send_to_webhook(client, telegram_text_update("sorry, busy week! all good"))
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(processing_answer())
    scheduler.tick()
    send_check_ins(chat_model, clock, scheduler, threshold - 1)
    chat_channel.sent.clear()

    chat_model.script(send_answer("hey, how's your weekend shaping up?"))
    clock.advance(ONE_DAY)
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey, how's your weekend shaping up?"
    ]


def test_with_user_memory_off_only_kinds_allowed_without_user_memory_are_chosen(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(
        client, auth_verifier, chat_channel, user_memory_enabled=False
    )
    chat_model.script(
        send_answer("hey, how did that thing go?", kind="A follow-up"),
        send_answer("hey Maya, how's your day going?"),
    )

    clock.advance(ONE_DAY)
    scheduler.tick()

    assert chat_channel.sent == []
    [line] = chat_model.calls[-1].history
    assert "A casual hello" in line.text
    assert "A present-moment pause" in line.text
    assert "A follow-up" not in line.text
    assert "A thought to reflect on" not in line.text
    assert "New job, running on autopilot." not in line.text

    clock.advance(timedelta(minutes=5))
    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey Maya, how's your day going?"
    ]
    assert recent_check_ins(client, headers)[0]["kind"] == "A casual hello"


def test_with_user_memory_turned_off_later_check_ins_still_use_existing_memory(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)
    chat_model.script(send_answer("hey Maya, how's the new job?"))

    clock.advance(ONE_DAY)
    scheduler.tick()

    [line] = chat_model.calls[-1].history
    assert "New job, running on autopilot." in line.text
    assert "User Memory is off" not in line.text
    assert "A follow-up" not in line.text


def test_an_answer_that_is_not_a_decision_sends_nothing_and_is_tried_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_model.script(
        "hey, how are you?",
        send_answer("hi!", kind="A kind nobody added"),
        send_answer("   "),
        send_answer("hey, how are you doing today?"),
    )
    clock.advance(ONE_DAY)

    for _ in range(3):
        scheduler.tick()
        clock.advance(timedelta(minutes=5))
    assert chat_channel.sent == []
    assert recent_check_ins(client, headers) == []

    scheduler.tick()
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey, how are you doing today?"
    ]


def test_settings_changed_while_the_model_decides_are_kept(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_model.before_next_reply = lambda: client.patch(
        "/api/check-ins",
        json={"frequency": "weekly", "quiet_hours_end": "09:00"},
        headers=headers,
    )
    chat_model.script(skip_answer("They seem busy this week."))

    clock.advance(ONE_DAY)
    scheduler.tick()

    check_ins = client.get("/api/check-ins", headers=headers).json()
    assert check_ins["frequency"] == "weekly"
    assert check_ins["quiet_hours_end"] == "09:00:00"


def test_a_message_long_after_a_check_in_still_resets_the_ignored_count(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    set_up_user_with_check_ins(
        client, auth_verifier, chat_channel, check_in_frequency="weekly"
    )
    threshold = seeded_settings["check_in_ignore_threshold"]
    one_week = timedelta(weeks=1)
    send_check_ins(chat_model, clock, scheduler, threshold, gap=one_week)
    clock.advance(timedelta(days=3))
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "hey, sorry I went quiet",
        processing_answer(),
    )
    chat_channel.sent.clear()

    chat_model.script(send_answer("hey, how's the week going?"))
    clock.advance(timedelta(days=4))
    scheduler.tick()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hey, how's the week going?"
    ]
