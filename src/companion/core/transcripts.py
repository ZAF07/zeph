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
