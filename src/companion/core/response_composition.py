import re
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from companion.core.chat_settings import SettingsTools
from companion.core.features import FeatureService
from companion.core.models import (
    ChatLine,
    ChatRole,
    ConversationMessage,
    LibrarySticker,
    MessageDirection,
    SharedPhoto,
)
from companion.core.photos import PhotoTools, SendPhotoTools
from companion.core.ports import Repositories
from companion.core.stickers import StickerTools
from companion.core.usage import UsageRecordingChatModel
from companion.core.web_search import WebSearchTools

BLANK_LINE = re.compile(r"\n\s*\n")
DELETION_CANCELLED_NOTE_SETTING = "reply_data_deletion_cancelled_note"


class EmptyReplyError(Exception):
    """Raised when the chat model's reply has no text, sticker or photo."""


@dataclass(frozen=True)
class ComposedReply:
    """The Companion's reply, ready to send.

    Attributes:
        parts: The short text messages, in order; may be empty when the
            reply is just a sticker or a photo.
        sticker: The one sticker to send after the text, if any.
        shared_photo: The one Shared Photo of the User's to send back after
            the text, if any.
    """

    parts: list[str]
    sticker: LibrarySticker | None
    shared_photo: SharedPhoto | None = None


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


class ResponseComposer:
    """Writes the Companion's reply to the current Conversation."""

    def __init__(
        self,
        repositories: Repositories,
        chat_model: UsageRecordingChatModel,
        features: FeatureService,
        web_search_tools: WebSearchTools,
        settings_tools: SettingsTools,
        sticker_tools: StickerTools,
        photo_tools: PhotoTools,
        send_photo_tools: SendPhotoTools,
    ) -> None:
        """Set up the composer.

        Args:
            repositories: Where Conversations and settings are stored.
            chat_model: Generates the reply and records the tokens used.
            features: Names the Features the User doesn't have, so the
                reply can say so.
            web_search_tools: Offers the web tools the reply may call.
            settings_tools: Offers the tools that change the User's settings.
            sticker_tools: Offers the Sticker Library to the reply.
            photo_tools: Offers a look again at the Conversation's photos.
            send_photo_tools: Offers to send one of the User's Shared Photos
                back.
        """
        self._repositories = repositories
        self._chat_model = chat_model
        self._features = features
        self._web_search_tools = web_search_tools
        self._settings_tools = settings_tools
        self._sticker_tools = sticker_tools
        self._photo_tools = photo_tools
        self._send_photo_tools = send_photo_tools

    def compose(
        self,
        conversation_id: UUID,
        user_id: UUID,
        memory: str = "",
        knowledge: str = "",
        data_deletion_cancelled: bool = False,
        shared_photo_ids: Sequence[UUID] = (),
    ) -> ComposedReply:
        """Compose a reply to the Conversation's newest message.

        Uses the Persona, response prompt and model from platform settings,
        then what the Companion remembers and the Knowledge that may fit, and
        gives the model every earlier message in the Conversation. The model
        may search the web and read pages when web search is offered, change
        the User's settings when they ask, pick one sticker from the
        Sticker Library when Stickers works for them, look again at a photo
        from the Conversation when its description can't answer, and send
        back one of the User's Shared Photos that matter for the message. When
        a Feature doesn't work for the User, the instructions say so, so the
        reply can tell them plainly.

        Args:
            conversation_id: The Conversation to reply in.
            user_id: The User being replied to.
            memory: The User Memory that matters for this message; "" if none.
            knowledge: The Knowledge passages that may fit; "" if none.
            data_deletion_cancelled: True if this message cancelled the
                User's request to delete their data, so the reply says so.
            shared_photo_ids: The User's Shared Photos that matter for the
                message, which the reply may send one of; empty if none.

        Returns:
            The reply as short messages, an optional sticker and an optional
            Shared Photo.

        Raises:
            EmptyReplyError: If the reply has no text, sticker or photo.
        """
        settings = self._repositories.platform_settings
        instructions = f"{settings.get('persona')}\n\n{settings.get('response_prompt')}"
        web_search = self._web_search_tools.offer(user_id)
        settings_tools = self._settings_tools.offer(user_id)
        sticker_choice = self._sticker_tools.offer(user_id)
        photo_tools = self._photo_tools.offer(user_id, conversation_id)
        send_photo_choice = self._send_photo_tools.offer(user_id, shared_photo_ids)
        cancelled_note = (
            settings.get(DELETION_CANCELLED_NOTE_SETTING)
            if data_deletion_cancelled
            else ""
        )
        sections = (
            memory,
            knowledge,
            web_search.instructions,
            settings_tools.instructions,
            self._features.unavailable_note(user_id),
            cancelled_note,
        )
        for section in sections:
            if section:
                instructions += f"\n\n{section}"
        history = to_chat_history(
            self._repositories.conversations.list_messages(conversation_id)
        )
        reply = self._chat_model.generate(
            user_id=user_id,
            model=settings.get("response_model"),
            instructions=instructions,
            history=history,
            tools=[
                *web_search.tools,
                *settings_tools.tools,
                *sticker_choice.tools,
                *photo_tools,
                *send_photo_choice.tools,
            ],
        )
        reply_parts = split_into_messages(reply)
        if (
            not reply_parts
            and sticker_choice.picked is None
            and send_photo_choice.picked is None
        ):
            raise EmptyReplyError
        return ComposedReply(
            parts=reply_parts,
            sticker=sticker_choice.picked,
            shared_photo=send_photo_choice.picked,
        )
