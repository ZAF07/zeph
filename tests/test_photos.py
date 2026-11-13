import logging
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import ChannelPhoto, MessageDirection, PhotoImage
from tests.fakes import (
    PHOTO_TOKENS_IN,
    PHOTO_TOKENS_OUT,
    TOKENS_IN_PER_CALL,
    TOKENS_OUT_PER_CALL,
    FakeAuthVerifier,
    FakeChatChannel,
    FakePhotoViewer,
    ScriptedChatModel,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_file_update,
    telegram_message_update,
    telegram_photo_update,
)
from tests.test_safeguard import use_simple_crisis_reply
from tests.test_usage_limits import usage_rows
from tests.test_web_search import change_settings

CAT = "A ginger cat asleep on a sunny windowsill next to a small cactus."
TWENTY_MEGABYTES = 20 * 1024 * 1024


def send_photo_and_reply(
    client: TestClient,
    chat_model: ScriptedChatModel,
    update: dict[str, Any],
    reply: str = "what a sleepy cat",
) -> str:
    """Send a photo update and return the newest message the reply was given."""
    chat_model.script(reply)
    assert send_to_webhook(client, update) == 200
    return chat_model.calls[-1].history[-1].text


def test_a_photo_with_a_caption_reaches_the_reply_and_safeguard_as_its_description(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    cat_photo = PhotoImage(content=b"cat-jpeg", media_type="image/jpeg")
    chat_channel.photos["file-photo-cat"] = cat_photo
    photo_viewer.script(CAT)

    newest_message = send_photo_and_reply(
        client, chat_model, telegram_photo_update("meet Biscuit")
    )

    assert newest_message == f"[photo: {CAT}] meet Biscuit"
    assert chat_model.safeguard_calls[-1].history[-1].text.endswith(newest_message)
    [look] = photo_viewer.calls
    assert look.photo == cat_photo
    assert look.model == seeded_settings["photo_model"]
    assert look.instructions == seeded_settings["photo_description_prompt"]
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["what a sleepy cat"]


def test_a_photo_without_a_caption_gets_a_real_reply_about_the_photo(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    photo_viewer.script(CAT)

    newest_message = send_photo_and_reply(client, chat_model, telegram_photo_update())

    assert newest_message == f"[photo: {CAT}]"
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["what a sleepy cat"]


def test_the_saved_message_keeps_the_photos_telegram_ids(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    photo_viewer.script(CAT)

    send_photo_and_reply(client, chat_model, telegram_photo_update("meet Biscuit"))

    repositories = build_postgres_repositories(engine)
    [user] = [overview.user for overview in repositories.users.list_overviews()]
    conversation = repositories.conversations.get_latest_for_user(user.id)
    assert conversation is not None
    [incoming] = [
        message
        for message in repositories.conversations.list_messages(conversation.id)
        if message.direction == MessageDirection.INCOMING
    ]
    assert incoming.content == f"[photo: {CAT}] meet Biscuit"
    assert incoming.photos == (ChannelPhoto("file-photo-cat", "photo-cat"),)


@pytest.mark.parametrize("mime_type", ["image/jpeg", "image/png", "image/webp"])
def test_an_image_sent_as_a_file_is_read_as_a_photo(
    mime_type: str,
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    photo_viewer.script(CAT)

    newest_message = send_photo_and_reply(
        client, chat_model, telegram_file_update(mime_type, file_unique_id="scan")
    )

    assert newest_message == f"[photo: {CAT}]"
    assert chat_channel.downloaded_photos == ["file-scan"]


@pytest.mark.parametrize(
    "content",
    [
        {"animation": {"file_id": "g1"}, "document": {"mime_type": "image/gif"}},
        {"document": {"file_id": "g2", "mime_type": "image/gif"}},
        {"video": {"file_id": "v1", "duration": 4}},
        {"document": {"file_id": "d1", "mime_type": "application/pdf"}},
    ],
    ids=["gif", "gif-file", "video", "pdf"],
)
def test_gifs_videos_and_other_files_still_get_the_unsupported_reply(
    content: dict[str, Any],
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    assert send_to_webhook(client, telegram_message_update(content)) == 200

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        seeded_settings["unsupported_message_reply"]
    ]
    assert photo_viewer.calls == []
    assert chat_model.calls == []


def test_the_unsupported_reply_no_longer_says_photos_cant_be_opened(
    seeded_settings: dict[str, Any],
) -> None:
    assert "photo" not in seeded_settings["unsupported_message_reply"]


def test_a_failed_download_is_retried_the_set_number_of_times(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_channel.photo_download_failures = [TimeoutError(), TimeoutError()]
    photo_viewer.script(CAT)

    newest_message = send_photo_and_reply(client, chat_model, telegram_photo_update())

    assert newest_message == f"[photo: {CAT}]"
    assert chat_channel.downloaded_photos == ["file-photo-cat"] * 3


def test_a_failed_look_is_retried_too(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    photo_viewer.script(RuntimeError("model down"), CAT)

    newest_message = send_photo_and_reply(client, chat_model, telegram_photo_update())

    assert newest_message == f"[photo: {CAT}]"
    assert len(photo_viewer.calls) == 2


def test_a_photo_that_still_fails_is_marked_as_not_come_through_and_logged(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    caplog: pytest.LogCaptureFixture,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    note = "Say honestly the photo didn't come through; ask them to resend."
    change_settings(
        client, admin, {"photo_retry_count": 1, "photo_not_viewed_note": note}
    )
    photo_viewer.script(RuntimeError("model down"), RuntimeError("model down"))

    with caplog.at_level(logging.ERROR):
        newest_message = send_photo_and_reply(
            client,
            chat_model,
            telegram_photo_update("look!"),
            "it didn't load, resend?",
        )

    assert newest_message == f"[photo that didn't come through. {note}] look!"
    assert len(photo_viewer.calls) == 2
    assert "Could not view a photo" in caplog.text


def test_an_image_file_over_twenty_megabytes_is_not_downloaded_or_viewed(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    huge_file = telegram_file_update("image/png", file_size=TWENTY_MEGABYTES + 1)

    newest_message = send_photo_and_reply(client, chat_model, huge_file)

    note = seeded_settings["photo_not_viewed_note"]
    assert newest_message == f"[photo that didn't come through. {note}]"
    assert chat_channel.downloaded_photos == []
    assert photo_viewer.calls == []


def test_a_worrying_photo_with_no_caption_gets_the_crisis_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    admin = owner_headers(client, auth_verifier)
    use_simple_crisis_reply(client, admin)
    connect_telegram(client, auth_verifier, chat_channel)
    goodbye_note = "A handwritten note: 'I'm sorry. Goodbye.' beside a pile of pills."
    photo_viewer.script(goodbye_note)
    chat_model.script_safeguard("suicide_or_self_harm")

    assert send_to_webhook(client, telegram_photo_update()) == 200

    assert goodbye_note in chat_model.safeguard_calls[-1].history[-1].text
    [crisis_reply] = chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)
    assert crisis_reply.startswith("I'm an AI. Please reach out:")
    assert chat_model.calls == []


def test_a_photo_counts_as_one_message_and_its_tokens_go_into_usage(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)

    send_photo_and_reply(client, chat_model, telegram_photo_update("hi"))

    [row] = [row for row in usage_rows(client, admin) if row["message_count"]]
    assert row["message_count"] == 1
    model_calls = len(chat_model.call_order)
    assert row["tokens_in"] == model_calls * TOKENS_IN_PER_CALL + PHOTO_TOKENS_IN
    assert row["tokens_out"] == model_calls * TOKENS_OUT_PER_CALL + PHOTO_TOKENS_OUT
