import logging
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import ChannelPhoto, MessageDirection, PhotoImage
from tests.fakes import (
    PHOTO_TOKENS_IN,
    PHOTO_TOKENS_OUT,
    TOKENS_IN_PER_CALL,
    TOKENS_OUT_PER_CALL,
    ChatModelCall,
    FakeAuthVerifier,
    FakeChatChannel,
    FakePhotoViewer,
    FakeTimer,
    ScriptedChatModel,
    ToolCall,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_album_video_update,
    telegram_file_update,
    telegram_message_update,
    telegram_photo_update,
    telegram_text_update,
)
from tests.test_safeguard import use_simple_crisis_reply
from tests.test_usage_limits import usage_rows
from tests.test_web_search import change_settings

CAT = "A ginger cat asleep on a sunny windowsill next to a small cactus."
TWENTY_MEGABYTES = 20 * 1024 * 1024
POT_QUESTION = "What colour is the pot the cactus is in?"
POT_ANSWER = "The pot is terracotta orange with a chipped rim."
DOG = "A black dog chasing a red ball across a park lawn."
BIRD = "A robin perched on a snowy fence post."
FOX = "A red fox curled up asleep in long grass."


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


def send_album(
    client: TestClient,
    timer: FakeTimer,
    chat_model: ScriptedChatModel,
    photo_count: int,
    caption_on: int = 2,
    reply: str = "what a lovely bunch",
) -> str:
    """Send an album's photos, let its wait end and return the newest message
    the reply was given.

    The photo numbered `caption_on` carries the caption "our trip".
    """
    for number in range(1, photo_count + 1):
        update = telegram_photo_update(
            "our trip" if number == caption_on else None,
            file_unique_id=f"photo-{number}",
            album_id="album-1",
        )
        assert send_to_webhook(client, update) == 200
    chat_model.script(reply)
    timer.run_waiting()
    return chat_model.calls[-1].history[-1].text


def ask_about_photo_tools(call: ChatModelCall) -> list[Any]:
    """List the ask_about_photo tools a reply call was offered."""
    return [tool for tool in call.tools if tool.name == "ask_about_photo"]


def ask_about_the_photo(
    client: TestClient,
    chat_model: ScriptedChatModel,
    arguments: dict[str, Any],
    reply: str = "it's terracotta",
) -> ChatModelCall:
    """Send a follow-up question whose reply calls ask_about_photo once."""
    chat_model.script(ToolCall("ask_about_photo", arguments), reply)
    assert send_to_webhook(client, telegram_text_update("what colour is the pot?"))
    return chat_model.calls[-1]


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


def test_the_saved_message_keeps_the_photos_telegram_ids_description_and_caption(
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
    assert incoming.photos == (
        ChannelPhoto(
            "file-photo-cat",
            "photo-cat",
            viewed=True,
            description=CAT,
            caption="meet Biscuit",
        ),
    )


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


def test_a_follow_up_question_looks_at_the_photo_again_and_the_answer_reaches_the_reply(
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
    photo_viewer.script(CAT, POT_ANSWER)
    send_photo_and_reply(client, chat_model, telegram_photo_update("meet Biscuit"))

    call = ask_about_the_photo(
        client, chat_model, {"photo": 1, "question": POT_QUESTION}
    )

    _, look_again = photo_viewer.calls
    assert look_again.photo == cat_photo
    assert look_again.model == seeded_settings["photo_model"]
    assert look_again.instructions.startswith(
        seeded_settings["photo_description_prompt"]
    )
    assert look_again.instructions.endswith(POT_QUESTION)
    [tool_result] = call.tool_results
    assert POT_ANSWER in tool_result
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)[-1] == "it's terracotta"


def test_the_tool_lists_the_conversations_viewed_photos_under_the_admin_description(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    photo_viewer.script(CAT, DOG)
    send_photo_and_reply(client, chat_model, telegram_photo_update("meet Biscuit"))
    send_photo_and_reply(
        client, chat_model, telegram_photo_update(file_unique_id="photo-dog")
    )

    [tool] = ask_about_photo_tools(chat_model.calls[-1])

    description = seeded_settings["ask_about_photo_tool_description"]
    assert tool.description.startswith(description)
    assert f"1. {CAT}" in tool.description
    assert f"2. {DOG}" in tool.description
    assert set(tool.parameters["required"]) == {"photo", "question"}


def test_the_tool_description_says_to_use_it_only_when_the_description_cant_answer(
    seeded_settings: dict[str, Any],
) -> None:
    description = seeded_settings["ask_about_photo_tool_description"].lower()

    assert "only" in description
    assert "description" in description


def test_the_tool_looks_at_the_photo_with_the_number_it_was_given(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    send_photo_and_reply(client, chat_model, telegram_photo_update())
    send_photo_and_reply(
        client, chat_model, telegram_photo_update(file_unique_id="photo-dog")
    )

    ask_about_the_photo(client, chat_model, {"photo": 2, "question": "Is it happy?"})

    assert chat_channel.downloaded_photos[-1] == "file-photo-dog"


def test_ask_about_photo_is_not_offered_without_viewed_photos(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("hey!")
    assert send_to_webhook(client, telegram_text_update("hi there"))
    no_photos = chat_model.calls[-1]
    photo_viewer.script(*[RuntimeError("model down")] * 3)
    send_photo_and_reply(client, chat_model, telegram_photo_update(), "resend?")
    failed_photo = chat_model.calls[-1]

    assert ask_about_photo_tools(no_photos) == []
    assert ask_about_photo_tools(failed_photo) == []


def test_a_failed_look_again_is_retried_then_reported_to_the_reply_in_plain_words(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    caplog: pytest.LogCaptureFixture,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    change_settings(client, admin, {"photo_retry_count": 1})
    photo_viewer.script(CAT, RuntimeError("model down"), RuntimeError("model down"))
    send_photo_and_reply(client, chat_model, telegram_photo_update())

    with caplog.at_level(logging.ERROR):
        call = ask_about_the_photo(
            client,
            chat_model,
            {"photo": 1, "question": POT_QUESTION},
            "I couldn't look again, sorry",
        )

    assert len(photo_viewer.calls) == 3
    [tool_result] = call.tool_results
    assert "couldn't look at the photo again" in tool_result.lower()
    assert "Could not look at a photo again" in caplog.text
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)[-1] == (
        "I couldn't look again, sorry"
    )


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        ({"photo": 5, "question": POT_QUESTION}, "no photo with that number"),
        ({"photo": "cat", "question": POT_QUESTION}, "no photo with that number"),
        ({"photo": 1, "question": "  "}, "needs a question"),
    ],
)
def test_an_unknown_photo_or_missing_question_is_said_plainly_without_a_look(
    arguments: dict[str, Any],
    expected: str,
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    send_photo_and_reply(client, chat_model, telegram_photo_update())

    call = ask_about_the_photo(client, chat_model, arguments)

    [tool_result] = call.tool_results
    assert expected in tool_result.lower()
    assert len(photo_viewer.calls) == 1


def test_a_look_again_puts_its_tokens_into_usage(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    send_photo_and_reply(client, chat_model, telegram_photo_update())

    ask_about_the_photo(client, chat_model, {"photo": 1, "question": POT_QUESTION})

    [row] = [row for row in usage_rows(client, admin) if row["message_count"]]
    model_calls = len(chat_model.call_order)
    assert row["tokens_in"] == model_calls * TOKENS_IN_PER_CALL + 2 * PHOTO_TOKENS_IN


def test_an_edited_tool_description_is_offered_and_shows_on_the_photo_viewing_card(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    edited = "Look again only for small details the description left out."
    change_settings(client, admin, {"ask_about_photo_tool_description": edited})

    send_photo_and_reply(client, chat_model, telegram_photo_update())

    [tool] = ask_about_photo_tools(chat_model.calls[-1])
    assert tool.description.startswith(edited)
    services = client.get("/api/admin/core-services", headers=admin).json()
    [photo_viewing] = [
        service
        for service in services["services"]
        if service["name"] == "Photo viewing"
    ]
    assert photo_viewing["extra_prompts"] == [
        {
            "key": "ask_about_photo_tool_description",
            "label": "ask_about_photo tool description",
            "hint": None,
        },
        {
            "key": "send_photo_tool_description",
            "label": "send_photo tool description",
            "hint": None,
        },
    ]


def test_an_album_gets_one_reply_that_covers_every_photo_with_the_caption(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    timer: FakeTimer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    photo_viewer.script(DOG, BIRD, FOX)

    newest_message = send_album(client, timer, chat_model, photo_count=3)

    assert newest_message == (
        f"[photo 1: {DOG}] [photo 2: {BIRD}] [photo 3: {FOX}] our trip"
    )
    assert chat_model.safeguard_calls[-1].history[-1].text.endswith(newest_message)
    assert len(chat_model.calls) == 1
    assert chat_channel.downloaded_photos == [
        "file-photo-1",
        "file-photo-2",
        "file-photo-3",
    ]
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["what a lovely bunch"]


def test_nothing_is_answered_until_the_album_wait_after_the_last_photo_ends(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    timer: FakeTimer,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    change_settings(client, admin, {"photo_album_wait_seconds": 4})

    for number in (1, 2):
        update = telegram_photo_update(
            file_unique_id=f"photo-{number}", album_id="album-1"
        )
        assert send_to_webhook(client, update) == 200

    assert chat_model.calls == []
    assert photo_viewer.calls == []
    [first_wait, second_wait] = timer.waits
    assert first_wait == second_wait
    assert first_wait[1] == 4


def test_an_album_over_the_cap_describes_only_the_first_photos_and_mentions_the_rest(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    timer: FakeTimer,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    change_settings(client, admin, {"photo_album_max_photos": 2})
    photo_viewer.script(DOG, BIRD)

    newest_message = send_album(client, timer, chat_model, photo_count=5, caption_on=4)

    assert len(photo_viewer.calls) == 2
    assert newest_message.startswith(f"[photo 1: {DOG}] [photo 2: {BIRD}] our trip")
    assert "3 more photos that you didn't look at" in newest_message
    assert "only the first 2" in newest_message
    assert "mention" in newest_message.lower()


def test_one_photo_over_the_cap_is_named_in_the_singular(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    change_settings(client, admin, {"photo_album_max_photos": 2})

    newest_message = send_album(client, timer, chat_model, photo_count=3)

    assert "1 more photo that you didn't look at" in newest_message


def test_an_album_counts_as_one_message(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    timer: FakeTimer,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)

    send_album(client, timer, chat_model, photo_count=3)

    [row] = [row for row in usage_rows(client, admin) if row["message_count"]]
    assert row["message_count"] == 1
    assert row["tokens_in"] == (
        len(chat_model.call_order) * TOKENS_IN_PER_CALL + 3 * PHOTO_TOKENS_IN
    )


def test_an_album_photo_that_fails_is_marked_while_the_others_are_described(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    timer: FakeTimer,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    note = "Say it didn't come through."
    change_settings(
        client, admin, {"photo_retry_count": 0, "photo_not_viewed_note": note}
    )
    photo_viewer.script(DOG, RuntimeError("model down"))

    newest_message = send_album(client, timer, chat_model, photo_count=2)

    assert newest_message == (
        f"[photo 1: {DOG}] [photo 2 that didn't come through. {note}] our trip"
    )


def test_two_albums_sent_together_get_a_reply_each(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    timer: FakeTimer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    photo_viewer.script(DOG, BIRD)
    for album in ("album-1", "album-2"):
        update = telegram_photo_update(file_unique_id=album, album_id=album)
        assert send_to_webhook(client, update) == 200
    chat_model.script("nice dog", "nice bird")

    timer.run_waiting()

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["nice dog", "nice bird"]


def test_ask_about_photo_lists_each_album_photo_by_its_own_description(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    timer: FakeTimer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    photo_viewer.script(DOG, BIRD, FOX)
    send_album(client, timer, chat_model, photo_count=3)

    ask_about_the_photo(client, chat_model, {"photo": 2, "question": "Is it cold?"})

    [tool] = ask_about_photo_tools(chat_model.calls[-1])
    assert f"1. {DOG}\n2. {BIRD}\n3. {FOX}" in tool.description
    assert chat_channel.downloaded_photos[-1] == "file-photo-2"


def test_a_photo_saved_without_its_description_is_listed_by_its_message_text(
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
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE conversation_messages SET photos = "
                "jsonb_build_array((photos->0) - 'description') "
                "WHERE photos != '[]'::jsonb"
            )
        )

    ask_about_the_photo(client, chat_model, {"photo": 1, "question": POT_QUESTION})

    [tool] = ask_about_photo_tools(chat_model.calls[-1])
    assert f"1. [photo: {CAT}] meet Biscuit" in tool.description


def test_a_video_in_an_album_joins_the_one_reply_and_its_caption_is_kept(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    timer: FakeTimer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    photo_viewer.script(DOG)
    send_to_webhook(client, telegram_album_video_update("our trip", message_id=11))
    send_to_webhook(
        client,
        telegram_photo_update(file_unique_id="photo-1", album_id="album-1"),
    )
    chat_model.script("lovely")

    timer.run_waiting()

    assert chat_model.calls[-1].history[-1].text == f"[photo: {DOG}] [video] our trip"
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["lovely"]


def test_an_album_of_videos_alone_gets_one_unsupported_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
    timer: FakeTimer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    send_to_webhook(client, telegram_album_video_update(message_id=11))
    send_to_webhook(client, telegram_album_video_update(message_id=12))

    timer.run_waiting()

    assert chat_model.calls == []
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        seeded_settings["unsupported_message_reply"]
    ]


def test_an_album_of_videos_with_a_caption_gets_one_reply_to_the_caption(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    timer: FakeTimer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    send_to_webhook(client, telegram_album_video_update("our trip", message_id=11))
    send_to_webhook(client, telegram_album_video_update(message_id=12))
    chat_model.script("sounds fun")

    timer.run_waiting()

    assert chat_model.calls[-1].history[-1].text == "[video] [video] our trip"
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["sounds fun"]


def test_album_photos_are_numbered_in_the_order_they_were_sent(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    timer: FakeTimer,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    for number, message_id in ((2, 12), (1, 11)):
        update = telegram_photo_update(
            file_unique_id=f"photo-{number}", album_id="album-1", message_id=message_id
        )
        send_to_webhook(client, update)
    chat_model.script("nice")

    timer.run_waiting()

    assert chat_channel.downloaded_photos == ["file-photo-1", "file-photo-2"]
