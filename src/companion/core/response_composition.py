import re
from uuid import UUID

from companion.core.models import ChatLine, ChatRole, MessageDirection
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

    def compose(self, conversation_id: UUID) -> list[str]:
        """Compose a reply to the Conversation's newest message.

        Uses the Persona, response prompt and model from platform settings,
        and gives the model every earlier message in the Conversation.

        Args:
            conversation_id: The Conversation to reply in.

        Returns:
            The reply as one or more short messages.

        Raises:
            EmptyReplyError: If the model's reply has no text.
        """
        settings = self._repositories.platform_settings
        instructions = f"{settings.get('persona')}\n\n{settings.get('response_prompt')}"
        messages = self._repositories.conversations.list_messages(conversation_id)
        history = [
            ChatLine(
                role=ChatRole.USER
                if message.direction == MessageDirection.INCOMING
                else ChatRole.COMPANION,
                text=message.content,
            )
            for message in messages
        ]
        reply = self._chat_model.generate(
            model=settings.get("response_model"),
            instructions=instructions,
            history=history,
        )
        reply_parts = split_into_messages(reply)
        if not reply_parts:
            raise EmptyReplyError
        return reply_parts
