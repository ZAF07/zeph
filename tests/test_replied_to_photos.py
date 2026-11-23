from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from tests.fakes import (
    PHOTO_TOKENS_IN,
    PHOTO_TOKENS_OUT,
    TOKENS_IN_PER_CALL,
    TOKENS_OUT_PER_CALL,
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakePhotoViewer,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import (
    OWNER_TELEGRAM_USER_ID,
    TELEGRAM_CHAT_ID,
    auth_headers,
    connect_owner_telegram,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_file_update,
    telegram_reply_to_photo_update,
    telegram_reply_update,
    telegram_text_update,
)
from tests.test_message_retention import retention
from tests.test_model_call_log import list_traces, newest_call
from tests.test_photo_viewing import not_looked_at, turn_photo_viewing_off
from tests.test_photos import CAT
from tests.test_post_conversation import processing_answer
from tests.test_recent_messages import given_text, newest_reply_steps
from tests.test_usage_limits import usage_rows

REPLIED_PHOTO = "(replying to their own photo from 3 Nov 2025"
SEEN_PHOTO = f'{REPLIED_PHOTO}, "my cat", [photo: {CAT}]) so cute'


def saved_replied_to(engine: Engine) -> list[dict[str, Any]]:
    """List the Replied-to Texts the saved messages keep, oldest first."""
    with engine.connect() as connection:
        return list(
            connection.execute(
                text(
                    "SELECT replied_to FROM conversation_messages "
                    "WHERE replied_to IS NOT NULL ORDER BY position"
                )
            ).scalars()
        )


def test_a_reply_to_a_photo_gets_its_description_in_the_understanding_plan_and_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    photo_viewer.script(CAT)
    chat_model.script("that windowsill nap looks perfect")

    send_to_webhook(client, telegram_reply_to_photo_update("so cute", "my cat"))

    understanding, reply_plan, reply = newest_reply_steps(chat_model)
    for call in (understanding, reply_plan):
        assert f"Person: {SEEN_PHOTO}" in given_text(call)
    assert reply.history[-1].text == SEEN_PHOTO
    assert chat_channel.downloaded_photos == ["file-old-cat"]
    assert chat_model.safeguard_calls[-1].history[0].text.endswith(SEEN_PHOTO)


def test_the_look_uses_the_photo_model_and_description_prompt(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("aw")

    send_to_webhook(client, telegram_reply_to_photo_update("so cute", "my cat"))

    [look] = photo_viewer.calls
    assert look.model == seeded_settings["photo_model"]
    assert look.instructions == seeded_settings["photo_description_prompt"]


def test_the_description_is_kept_so_later_replies_still_see_it(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    photo_viewer.script(CAT)
    chat_model.script("aw", "ha, classic")
    send_to_webhook(client, telegram_reply_to_photo_update("so cute", "my cat"))

    send_to_webhook(client, telegram_text_update("he does it every day"))

    [kept] = saved_replied_to(engine)
    assert kept["photo_note"] == f"[photo: {CAT}]"
    assert "photo" not in kept
    reply = newest_reply_steps(chat_model)[-1]
    assert any(line.text == SEEN_PHOTO for line in reply.history)
    assert len(photo_viewer.calls) == 1


def test_with_photo_viewing_off_only_the_safeguard_reads_the_description(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    turn_photo_viewing_off(client, auth_verifier, "by_the_user")
    photo_viewer.script(CAT)
    chat_model.script("aw")

    send_to_webhook(client, telegram_reply_to_photo_update("so cute", "my cat"))

    assert chat_model.safeguard_calls[-1].history[0].text.endswith(SEEN_PHOTO)
    off = f'{REPLIED_PHOTO}, "my cat", {not_looked_at(seeded_settings)}) so cute'
    understanding, reply_plan, reply = newest_reply_steps(chat_model)
    for call in (understanding, reply_plan):
        assert f"Person: {off}" in given_text(call)
        assert CAT not in given_text(call)
    assert reply.history[-1].text == off
    assert CAT not in str(saved_replied_to(engine))


def test_a_photo_that_cant_be_downloaded_falls_back_to_the_caption(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    tries = 1 + seeded_settings["photo_retry_count"]
    chat_channel.photo_download_failures = [RuntimeError("file is gone")] * tries
    chat_model.script("aw, what's his name?")

    send_to_webhook(client, telegram_reply_to_photo_update("so cute", "my cat"))

    assert len(chat_channel.downloaded_photos) == tries
    for call in newest_reply_steps(chat_model):
        assert f'{REPLIED_PHOTO}, "my cat") so cute' in given_text(call)
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["aw, what's his name?"]


def test_a_photo_that_cant_be_looked_at_falls_back_to_the_caption(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    tries = 1 + seeded_settings["photo_retry_count"]
    photo_viewer.script(*[RuntimeError("model down")] * tries)
    chat_model.script("aw")

    send_to_webhook(client, telegram_reply_to_photo_update("so cute"))

    reply = newest_reply_steps(chat_model)[-1]
    assert reply.history[-1].text == f"{REPLIED_PHOTO}) so cute"
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["aw"]


def test_an_image_file_too_big_to_download_is_not_looked_at(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    file = telegram_file_update("image/png", file_size=30 * 1024 * 1024)
    chat_model.script("nice")

    send_to_webhook(
        client,
        telegram_reply_update(
            "this one",
            {"document": file["message"]["document"]},
            from_companion=False,
        ),
    )

    assert chat_channel.downloaded_photos == []
    assert photo_viewer.calls == []
    reply = newest_reply_steps(chat_model)[-1]
    assert reply.history[-1].text == f"{REPLIED_PHOTO}) this one"


def test_a_reply_to_a_text_or_sticker_looks_at_no_photo(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    sticker = {"file_id": "file-hug", "file_unique_id": "hug", "emoji": "🤗"}
    chat_model.script("ok")

    send_to_webhook(client, telegram_reply_update("thanks", {"sticker": sticker}))

    assert chat_channel.downloaded_photos == []
    assert photo_viewer.calls == []


def test_the_looks_tokens_go_into_usage(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("aw")

    send_to_webhook(client, telegram_reply_to_photo_update("so cute", "my cat"))

    [row] = [row for row in usage_rows(client, admin) if row["message_count"]]
    model_calls = len(chat_model.call_order)
    assert row["tokens_in"] == model_calls * TOKENS_IN_PER_CALL + PHOTO_TOKENS_IN
    assert row["tokens_out"] == model_calls * TOKENS_OUT_PER_CALL + PHOTO_TOKENS_OUT


def test_the_look_shows_in_the_model_call_log_with_the_understanding_and_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    photo_viewer.script(CAT)
    chat_model.script("aw")
    update = telegram_reply_to_photo_update("so cute", "my cat")
    update["message"]["from"]["id"] = OWNER_TELEGRAM_USER_ID
    update["message"]["chat"]["id"] = OWNER_TELEGRAM_USER_ID

    send_to_webhook(client, update)

    [trace] = list_traces(client, admin)
    assert "photo" in trace["steps"]
    understanding = newest_call(client, admin, "understanding")
    reply = newest_call(client, admin, "reply")
    assert f"[photo: {CAT}]" in understanding["content"]["history"][0]["text"]
    assert reply["content"]["history"][-1]["text"] == SEEN_PHOTO


def test_delete_my_data_removes_the_description_with_the_text(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    photo_viewer.script(CAT)
    chat_model.script("aw")
    send_to_webhook(client, telegram_reply_to_photo_update("so cute", "my cat"))
    assert len(saved_replied_to(engine)) == 1

    response = client.delete(
        "/api/me/data", headers=auth_headers(auth_verifier, "user_maya")
    )

    assert response.status_code == 204
    assert saved_replied_to(engine) == []


def test_message_retention_removes_the_description_with_the_text(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    photo_viewer.script(CAT)
    chat_model.script("aw")
    send_to_webhook(client, telegram_reply_to_photo_update("so cute", "my cat"))
    assert len(saved_replied_to(engine)) == 1

    clock.advance(retention(seeded_settings) + timedelta(days=1))
    chat_model.script_processing(processing_answer())
    scheduler.tick()

    assert saved_replied_to(engine) == []
