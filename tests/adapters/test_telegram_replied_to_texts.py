from datetime import UTC, datetime

from companion.adapters.telegram.webhook import parse_update
from companion.core.models import (
    IncomingMessage,
    MessageKind,
    RepliedToSender,
    RepliedToText,
)
from tests.telegram_helpers import (
    telegram_message_update,
    telegram_reply_update,
    telegram_text_update,
)

REPLIED_AT = datetime(2025, 11, 3, 6, 30, tzinfo=UTC)


def parsed(update: dict[str, object]) -> IncomingMessage:
    """Parse an update that must be a message."""
    message = parse_update(update)
    assert message is not None
    return message


def test_a_reply_to_the_companions_text_reads_who_when_and_what_it_said() -> None:
    update = telegram_reply_update(
        "not yet, scared tbh",
        {"text": "have you told your mum about the job yet?"},
    )

    assert parsed(update).replied_to == RepliedToText(
        sender=RepliedToSender.COMPANION,
        sent_at=REPLIED_AT,
        kind=MessageKind.TEXT,
        text="have you told your mum about the job yet?",
    )


def test_a_reply_to_the_users_own_text_reads_as_theirs() -> None:
    update = telegram_reply_update(
        "like I said before", {"text": "I hate my commute"}, from_companion=False
    )

    replied_to = parsed(update).replied_to
    assert replied_to is not None
    assert replied_to.sender == RepliedToSender.USER


def test_a_highlighted_part_is_read_instead_of_the_whole_text() -> None:
    update = telegram_reply_update(
        "this bit",
        {"text": "work was rough. also mum called"},
        quote="also mum called",
    )

    replied_to = parsed(update).replied_to
    assert replied_to is not None
    assert replied_to.text == "also mum called"


def test_a_long_replied_to_text_is_cut_to_about_500_characters() -> None:
    update = telegram_reply_update("yes", {"text": "a" * 2000})

    replied_to = parsed(update).replied_to
    assert replied_to is not None
    assert replied_to.text == "a" * 500 + "…"


def test_a_reply_to_a_photo_reads_its_caption() -> None:
    photo = [{"file_id": "file-cat", "file_unique_id": "cat", "width": 9}]
    update = telegram_reply_update(
        "so cute", {"photo": photo, "caption": "my cat"}, from_companion=False
    )

    replied_to = parsed(update).replied_to
    assert replied_to is not None
    assert (replied_to.kind, replied_to.text) == (MessageKind.PHOTO, "my cat")


def test_a_reply_to_a_sticker_reads_its_emoji_and_keeps_the_replied_sticker() -> None:
    sticker = {"file_id": "file-laugh", "file_unique_id": "laugh", "emoji": "😂"}
    update = telegram_reply_update("haha", {"sticker": sticker})

    message = parsed(update)
    assert message.replied_to is not None
    assert (message.replied_to.kind, message.replied_to.text) == (
        MessageKind.STICKER,
        "😂",
    )
    assert message.replied_sticker is not None
    assert message.replied_sticker.file_unique_id == "laugh"


def test_a_reply_to_anything_else_is_read_as_another_kind() -> None:
    update = telegram_reply_update("listening now", {"voice": {"file_id": "v"}})

    replied_to = parsed(update).replied_to
    assert replied_to is not None
    assert (replied_to.kind, replied_to.text) == (MessageKind.UNSUPPORTED, "")


def test_a_sticker_or_photo_sent_as_a_reply_reads_what_it_replies_to() -> None:
    sticker = {"file_id": "file-hug", "file_unique_id": "hug", "emoji": "🤗"}
    photo = [{"file_id": "file-cat", "file_unique_id": "cat", "width": 9}]
    for content in ({"sticker": sticker}, {"photo": photo}):
        update = telegram_message_update(content)
        update["message"]["reply_to_message"] = telegram_reply_update(
            "", {"text": "rough day?"}
        )["message"]["reply_to_message"]

        replied_to = parsed(update).replied_to
        assert replied_to is not None
        assert replied_to.text == "rough day?"


def test_a_text_that_replies_to_nothing_has_no_replied_to_text() -> None:
    assert parsed(telegram_text_update("hello")).replied_to is None
