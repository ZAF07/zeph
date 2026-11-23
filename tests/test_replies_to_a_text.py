from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import CompanionTestClient
from tests.fakes import FakeAuthVerifier, FakeChatChannel, ScriptedChatModel, SentText
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    connect_telegram,
    post_to_webhook,
    send_to_webhook,
    telegram_reply_update,
    telegram_text_update,
)

WORK = "work was rough"
MUM = "also mum called"
CAT = "oh and the cat's sick"


def send_three_threads(client: TestClient) -> None:
    """Send three texts as one Message, with chat IDs 101, 102 and 103."""
    for message_id, text in ((101, WORK), (102, MUM), (103, CAT)):
        assert (
            post_to_webhook(client, telegram_text_update(text, message_id=message_id))
            == 200
        )
    assert isinstance(client, CompanionTestClient)
    client.timer.end_message_waits()


def test_a_marked_part_goes_out_as_a_reply_to_that_text_of_the_message(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("[re 1] ugh, what happened at work?\n\npoor cat, is it the vet?")

    send_three_threads(client)

    assert chat_channel.sent == [
        SentText(TELEGRAM_CHAT_ID, "ugh, what happened at work?", 101),
        SentText(TELEGRAM_CHAT_ID, "poor cat, is it the vet?"),
    ]


def test_the_reply_sees_the_messages_texts_numbered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("oh no, all at once")

    send_three_threads(client)

    assert chat_model.calls[-1].history[-1].text == (
        f"[1] {WORK}\n[2] {MUM}\n[3] {CAT}"
    )


def test_a_numbered_text_keeps_what_it_replies_to(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("ok")
    post_to_webhook(client, telegram_text_update(WORK, message_id=101))
    reply = telegram_reply_update("not yet", {"text": "told your mum?"})

    send_to_webhook(client, reply)

    assert chat_model.calls[-1].history[-1].text == (
        f"[1] {WORK}\n"
        '[2] (replying to your text from 3 Nov 2025, "told your mum?") not yet'
    )


def test_a_single_text_message_is_not_numbered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("oh no")

    send_to_webhook(client, telegram_text_update(WORK, message_id=101))

    assert chat_model.calls[-1].history[-1].text == WORK


def test_a_marker_naming_no_text_of_the_message_is_dropped(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("[re 7] ugh, work\n\n[re 0] and mum?")

    send_three_threads(client)

    assert chat_channel.sent == [
        SentText(TELEGRAM_CHAT_ID, "ugh, work"),
        SentText(TELEGRAM_CHAT_ID, "and mum?"),
    ]


def test_a_third_marker_is_dropped_and_its_part_sent_normally(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("[re 1] ugh, work\n\n[RE 2] and mum?\n\n[re 1] and the boss!")

    send_three_threads(client)

    assert chat_channel.sent == [
        SentText(TELEGRAM_CHAT_ID, "ugh, work", 101),
        SentText(TELEGRAM_CHAT_ID, "and mum?", 102),
        SentText(TELEGRAM_CHAT_ID, "and the boss!"),
    ]


def test_a_marker_in_a_reply_to_an_earlier_message_points_at_nothing(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("oh no")
    send_to_webhook(client, telegram_text_update(WORK, message_id=101))
    chat_model.script("[re 2] glad she called")

    send_to_webhook(client, telegram_text_update(MUM, message_id=102))

    assert chat_channel.sent[-1] == SentText(TELEGRAM_CHAT_ID, "glad she called")


def test_the_seeded_reply_prompt_says_when_and_how_to_reply_to_a_text(
    seeded_settings: dict[str, Any],
) -> None:
    prompt = seeded_settings["response_prompt"]

    assert "[re 2]" in prompt
    assert "at most two" in prompt


def test_a_marker_naming_the_latest_text_is_dropped(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("[ re 3 ] poor cat\n\n[ re 2 ] glad she called")

    send_three_threads(client)

    assert chat_channel.sent == [
        SentText(TELEGRAM_CHAT_ID, "poor cat"),
        SentText(TELEGRAM_CHAT_ID, "glad she called", 102),
    ]


def test_a_single_text_messages_reply_has_no_reply_links(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("[re 1] oh no, what happened?")

    send_to_webhook(client, telegram_text_update(WORK, message_id=101))

    assert chat_channel.sent == [SentText(TELEGRAM_CHAT_ID, "oh no, what happened?")]
