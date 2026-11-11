import re
from uuid import UUID

from companion.core.models import (
    ChatLine,
    ChatRole,
    ConversationMessage,
    MessageDirection,
)
from companion.core.ports import ChatModel, Repositories

BLANK_LINE = re.compile(r"\n\s*\n")


class EmptyReplyError(Exception):
    """Raised when the chat model's reply has no text to send."""


def split_into_messages(reply: str) -> list[str]:
    """Split a reply into short messages wherever there is a blank line.

    Args:
        reply: The reply text from the chat model.

    Returns:
        The non-empty messages, in order.
    """
    parts = (part.strip() for part in BLANK_LINE.split(reply))
    return [part for part in parts if part]


def to_chat_history(messages: list[ConversationMessage]) -> list[ChatLine]:
    """Turn a Conversation's saved messages into history for the chat model.

    Args:
        messages: The messages, oldest first.

    Returns:
        One line per message, saying who said it.
    """
    return [
        ChatLine(
            role=ChatRole.USER
            if message.direction == MessageDirection.INCOMING
            else ChatRole.COMPANION,
            text=message.content,
        )
        for message in messages
    ]


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


class ResponseComposer:
    """Writes the Companion's reply to the current Conversation."""

    def __init__(self, repositories: Repositories, chat_model: ChatModel) -> None:
        """Set up the composer.

        Args:
            repositories: Where Conversations and settings are stored.
            chat_model: Generates the reply.
        """
        self._repositories = repositories
        self._chat_model = chat_model

    def compose(
        self, conversation_id: UUID, memory: str = "", knowledge: str = ""
    ) -> list[str]:
        """Compose a reply to the Conversation's newest message.

        Uses the Persona, response prompt and model from platform settings,
        then what the Companion remembers and the Knowledge that may fit, and
        gives the model every earlier message in the Conversation.

        Args:
            conversation_id: The Conversation to reply in.
            memory: The User Memory that matters for this message; "" if none.
            knowledge: The Knowledge passages that may fit; "" if none.

        Returns:
            The reply as one or more short messages.

        Raises:
            EmptyReplyError: If the model's reply has no text.
        """
        settings = self._repositories.platform_settings
        instructions = f"{settings.get('persona')}\n\n{settings.get('response_prompt')}"
        for section in (memory, knowledge):
            if section:
                instructions += f"\n\n{section}"
        history = to_chat_history(
            self._repositories.conversations.list_messages(conversation_id)
        )
        reply = self._chat_model.generate(
            model=settings.get("response_model"),
            instructions=instructions,
            history=history,
        )
        reply_parts = split_into_messages(reply)
        if not reply_parts:
            raise EmptyReplyError
        return reply_parts
