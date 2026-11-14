from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import Engine

from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_check_in_sending import set_up_user_with_check_ins, skip_answer
from tests.test_post_conversation import processing_answer
from tests.test_user_snapshot import add_due_users, reads_by_table

SETTINGS_TABLE = ("platform_settings",)


def test_a_reply_reads_the_platform_settings_once(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_model.script("hey, good to hear from you")

    with reads_by_table(engine, SETTINGS_TABLE) as reads:
        send_to_webhook(client, telegram_text_update("hi Zeph"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)[-1] == (
        "hey, good to hear from you"
    )
    assert reads == {"platform_settings": 1}


def test_a_tick_reads_the_platform_settings_once(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_model.script("hey, good to hear from you")
    send_to_webhook(client, telegram_text_update("hi Zeph"))
    clock.advance(timedelta(hours=2))
    add_due_users(engine, clock, 3)
    chat_model.script_processing(processing_answer())
    chat_model.script(*[skip_answer("not now")] * 3)

    with reads_by_table(engine, SETTINGS_TABLE) as reads:
        scheduler.tick()

    assert len(chat_model.processing_calls) == 1
    assert len(chat_model.calls) == 4
    assert reads == {"platform_settings": 1}
