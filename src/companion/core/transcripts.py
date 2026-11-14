from companion.core.models import ConversationMessage, MessageDirection


def to_transcript_lines(messages: list[ConversationMessage]) -> str:
    """Write messages as transcript lines for a model to read, not answer.

    Args:
        messages: The messages, oldest first.

    Returns:
        One "Person: ..." or "Companion: ..." line per message.
    """
    speakers = {
        MessageDirection.INCOMING: "Person",
        MessageDirection.OUTGOING: "Companion",
    }
    return "\n".join(
        f"{speakers[message.direction]}: {message.content}" for message in messages
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
