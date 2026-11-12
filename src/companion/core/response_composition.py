import re
from dataclasses import dataclass
from uuid import UUID

from companion.core.models import (
    ChatLine,
    ChatRole,
    ConversationMessage,
    LibrarySticker,
    MessageDirection,
)
from companion.core.ports import ChatModel, Repositories
from companion.core.stickers import StickerTools
from companion.core.web_search import WebSearchTools

BLANK_LINE = re.compile(r"\n\s*\n")


class EmptyReplyError(Exception):
    """Raised when the chat model's reply has neither text nor a sticker."""


@dataclass(frozen=True)
class ComposedReply:
    """The Companion's reply, ready to send.

    Attributes:
        parts: The short text messages, in order; may be empty when the
            reply is just a sticker.
        sticker: The one sticker to send after the text, if any.
    """

    parts: list[str]
    sticker: LibrarySticker | None


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

    def __init__(
        self,
        repositories: Repositories,
        chat_model: ChatModel,
        web_search_tools: WebSearchTools,
        sticker_tools: StickerTools,
    ) -> None:
        """Set up the composer.

        Args:
            repositories: Where Conversations and settings are stored.
            chat_model: Generates the reply.
            web_search_tools: Offers the web tools the reply may call.
            sticker_tools: Offers the Sticker Library to the reply.
        """
        self._repositories = repositories
        self._chat_model = chat_model
        self._web_search_tools = web_search_tools
        self._sticker_tools = sticker_tools

    def compose(
        self,
        conversation_id: UUID,
        user_id: UUID,
        memory: str = "",
        knowledge: str = "",
    ) -> ComposedReply:
        """Compose a reply to the Conversation's newest message.

        Uses the Persona, response prompt and model from platform settings,
        then what the Companion remembers and the Knowledge that may fit, and
        gives the model every earlier message in the Conversation. The model
        may search the web and read pages when web search is offered, and may
        pick one sticker from the Sticker Library.

        Args:
            conversation_id: The Conversation to reply in.
            user_id: The User being replied to.
            memory: The User Memory that matters for this message; "" if none.
            knowledge: The Knowledge passages that may fit; "" if none.

        Returns:
            The reply as short messages and an optional sticker.

        Raises:
            EmptyReplyError: If the reply has neither text nor a sticker.
        """
        settings = self._repositories.platform_settings
        instructions = f"{settings.get('persona')}\n\n{settings.get('response_prompt')}"
        web_search = self._web_search_tools.offer(user_id)
        sticker_choice = self._sticker_tools.offer()
        for section in (memory, knowledge, web_search.instructions):
            if section:
                instructions += f"\n\n{section}"
        history = to_chat_history(
            self._repositories.conversations.list_messages(conversation_id)
        )
        reply = self._chat_model.generate(
            model=settings.get("response_model"),
            instructions=instructions,
            history=history,
            tools=[*web_search.tools, *sticker_choice.tools],
        )
        reply_parts = split_into_messages(reply)
        if not reply_parts and sticker_choice.picked is None:
            raise EmptyReplyError
        return ComposedReply(parts=reply_parts, sticker=sticker_choice.picked)
