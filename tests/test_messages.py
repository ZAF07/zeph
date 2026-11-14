import threading

from fastapi.testclient import TestClient

from tests.fakes import FakeAuthVerifier, FakeChatChannel, FakeTimer, ScriptedChatModel
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    connect_telegram,
    owner_headers,
    post_to_webhook,
    send_to_webhook,
    telegram_photo_update,
    telegram_text_update,
)
from tests.test_safeguard import use_simple_crisis_reply
from tests.test_usage_limits import usage_rows
from tests.test_web_search import change_settings


def post_texts(client: TestClient, *texts: str) -> None:
    """Post the connected User's texts in a row, all within the Message wait."""
    for text in texts:
        assert post_to_webhook(client, telegram_text_update(text)) == 200


def test_texts_sent_in_a_row_get_one_reply_that_sees_them_as_one_message(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("oh no, what happened?")

    post_texts(client, "hey", "rough day", "my boss yelled at me")

    assert chat_model.calls == []
    timer.end_message_waits()
    [reply_call] = chat_model.calls
    assert reply_call.history[-1].text == "hey\nrough day\nmy boss yelled at me"
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["oh no, what happened?"]


def test_the_safeguard_checks_each_text_as_it_arrives_without_waiting(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    post_texts(client, "hey", "rough day")

    assert len(chat_model.safeguard_calls) == 2
    assert "rough day" in chat_model.safeguard_calls[-1].history[-1].text


def test_a_text_after_the_wait_starts_a_new_message(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("hi you", "ha, tell me more")

    send_to_webhook(client, telegram_text_update("hey"))
    send_to_webhook(client, telegram_text_update("guess what"))

    assert len(chat_model.calls) == 2
    assert chat_model.calls[-1].history[-1].text == "guess what"
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "hi you",
        "ha, tell me more",
    ]


def test_the_wait_is_the_admins_message_wait_setting(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    timer: FakeTimer,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    change_settings(client, admin, {"message_wait_seconds": 7})

    post_texts(client, "hey", "you there?")

    [first_wait, second_wait] = timer.waits
    assert first_wait == second_wait
    assert first_wait[1] == 7


def test_a_crisis_text_gets_the_crisis_reply_at_once_and_the_rest_is_not_answered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
) -> None:
    admin = owner_headers(client, auth_verifier)
    use_simple_crisis_reply(client, admin)
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_safeguard("none", "suicide_or_self_harm")

    post_texts(client, "hey", "i don't want to be here anymore")

    [crisis_reply] = chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)
    assert crisis_reply.startswith("I'm an AI. Please reach out:")
    timer.end_message_waits()
    assert chat_model.calls == []
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [crisis_reply]


def test_a_message_of_several_texts_counts_once_toward_the_daily_limit(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("oh no")

    post_texts(client, "hey", "rough day", "my boss yelled at me")
    timer.end_message_waits()

    [row] = [row for row in usage_rows(client, admin) if row["message_count"]]
    assert row["message_count"] == 1


def test_a_text_and_an_album_sent_together_get_one_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("what a view")

    post_texts(client, "look where i am")
    for number in (1, 2):
        update = telegram_photo_update(
            file_unique_id=f"photo-{number}", album_id="album-1", message_id=10 + number
        )
        assert post_to_webhook(client, update) == 200
    timer.end_message_waits()

    [reply_call] = chat_model.calls
    assert reply_call.history[-1].text.startswith("look where i am\n[photo 1:")
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["what a view"]


def test_a_text_sent_while_a_reply_is_written_starts_a_new_message_answered_after(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("first reply", "second reply")
    late_text = threading.Thread(target=post_texts, args=(client, "two"))
    chat_model.before_next_reply = late_text.start

    send_to_webhook(client, telegram_text_update("one"))
    late_text.join()
    timer.end_message_waits()

    first_call, second_call = chat_model.calls
    assert first_call.history[-1].text == "one"
    assert [line.text for line in second_call.history] == [
        "one",
        "first reply",
        "two",
    ]
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "first reply",
        "second reply",
    ]
