from datetime import UTC, datetime
from uuid import uuid4

from companion.core.models import (
    ChatLine,
    ChatRole,
    ConversationMessage,
    MessageDirection,
    MessageKind,
)
from companion.core.response_composition import to_chat_history
from companion.core.transcripts import split_off_latest_message

CONVERSATION_ID = uuid4()


def saved(direction: MessageDirection, content: str) -> ConversationMessage:
    """Build a saved text message in the Conversation."""
    return ConversationMessage(
        id=uuid4(),
        conversation_id=CONVERSATION_ID,
        direction=direction,
        kind=MessageKind.TEXT,
        content=content,
        sent_at=datetime(2026, 11, 14, 9, 0, tzinfo=UTC),
    )


CONVERSATION = [
    saved(MessageDirection.INCOMING, "morning"),
    saved(MessageDirection.OUTGOING, "morning! how'd you sleep?"),
    saved(MessageDirection.INCOMING, "badly"),
    saved(MessageDirection.INCOMING, "big day today"),
]


def test_the_users_texts_in_a_row_are_one_line_of_chat_history() -> None:
    assert to_chat_history(CONVERSATION) == [
        ChatLine(role=ChatRole.USER, text="morning"),
        ChatLine(role=ChatRole.COMPANION, text="morning! how'd you sleep?"),
        ChatLine(role=ChatRole.USER, text="badly\nbig day today"),
    ]


def test_the_latest_message_is_every_text_after_the_companions_last_reply() -> None:
    earlier, latest_text = split_off_latest_message(CONVERSATION)

    assert earlier == CONVERSATION[:2]
    assert latest_text == "badly\nbig day today"


def test_a_conversation_ending_with_the_companion_has_no_latest_message() -> None:
    earlier, latest_text = split_off_latest_message(CONVERSATION[:2])

    assert earlier == CONVERSATION[:2]
    assert latest_text == ""
