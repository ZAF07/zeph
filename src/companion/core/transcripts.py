from companion.core.memory_retrieval import format_day
from companion.core.models import (
    ConversationMessage,
    MessageDirection,
    MessageKind,
    RepliedToSender,
    RepliedToText,
)

REPLIED_TO_KIND_NAMES = {
    MessageKind.TEXT: "text",
    MessageKind.STICKER: "sticker",
    MessageKind.PHOTO: "photo",
    MessageKind.UNSUPPORTED: "message",
}


def replied_to_note(
    replied_to: RepliedToText, time_zone: str | None, read_by_companion: bool
) -> str:
    """Write what a User's text replies to, to go before the text.

    Args:
        replied_to: The Replied-to Text.
        time_zone: The User's IANA time zone; UTC if they have none.
        read_by_companion: True when the Companion itself reads it, as in
            the Reply's chat history, so its texts are "your" texts; False
            for a transcript, where they are "the Companion's".

    Returns:
        E.g. '(replying to the Companion's text from 3 Nov 2026, "have you
        told your mum?")', or "their own" for the User's own text.
    """
    if replied_to.sender == RepliedToSender.USER:
        owner = "their own"
    elif read_by_companion:
        owner = "your"
    else:
        owner = "the Companion's"
    kind = REPLIED_TO_KIND_NAMES[replied_to.kind]
    day = format_day(replied_to.sent_at, time_zone)
    said = f', "{replied_to.text}"' if replied_to.text else ""
    return f"(replying to {owner} {kind} from {day}{said})"


def readable_content(
    message: ConversationMessage,
    time_zone: str | None,
    read_by_companion: bool = False,
) -> str:
    """Write a saved message's content with what it replies to, if anything.

    Args:
        message: The saved message.
        time_zone: The User's IANA time zone; UTC if they have none.
        read_by_companion: Whether the Companion itself reads it; see
            `replied_to_note`.

    Returns:
        The content, after a note on the Replied-to Text when it has one.
    """
    if message.replied_to is None:
        return message.content
    note = replied_to_note(message.replied_to, time_zone, read_by_companion)
    return f"{note} {message.content}"


def to_transcript_lines(
    messages: list[ConversationMessage], time_zone: str | None
) -> str:
    """Write messages as transcript lines for a model to read, not answer.

    Args:
        messages: The messages, oldest first.
        time_zone: The User's IANA time zone, for when a Replied-to Text was
            sent; UTC if they have none.

    Returns:
        One "Person: ..." or "Companion: ..." line per message, a text's
        Replied-to Text noted before it.
    """
    speakers = {
        MessageDirection.INCOMING: "Person",
        MessageDirection.OUTGOING: "Companion",
    }
    return "\n".join(
        f"{speakers[message.direction]}: {readable_content(message, time_zone)}"
        for message in messages
    )


def split_off_latest_message(
    messages: list[ConversationMessage],
) -> tuple[list[ConversationMessage], str]:
    """Split a Conversation into what came before the latest Message and its text.

    The User's messages in a row at the end are one Message, sent before
    they paused.

    Args:
        messages: The Conversation so far, oldest first.

    Returns:
        The earlier messages, and the latest Message's texts one per line;
        "" if the Conversation doesn't end with a message from the User.
    """
    latest_start = len(messages)
    while (
        latest_start > 0
        and messages[latest_start - 1].direction == MessageDirection.INCOMING
    ):
        latest_start -= 1
    latest_text = "\n".join(message.content for message in messages[latest_start:])
    return messages[:latest_start], latest_text
