import re
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from companion.core.features import FeatureService
from companion.core.models import (
    ChatLine,
    ChatRole,
    ConversationMessage,
    LibrarySticker,
    MessageDirection,
    ModelStep,
    PersonalSticker,
    SharedPhoto,
    UserSnapshot,
)
from companion.core.platform_settings import (
    PERSONA,
    RESPONSE_MODEL,
    RESPONSE_PROMPT,
)
from companion.core.ports import Repositories
from companion.core.reply_tools import ReplyContext, ReplyToolProvider
from companion.core.usage import UsageRecordingChatModel

BLANK_LINE = re.compile(r"\n\s*\n")


class EmptyReplyError(Exception):
    """Raised when the chat model's reply has no text, sticker or photo."""


@dataclass(frozen=True)
class ComposedReply:
    """The Companion's reply, ready to send.

    Attributes:
        parts: The short text messages, in order; may be empty when the
            reply is just a sticker or a photo.
        sticker: The one sticker to send after the text, if any, from the
            Sticker Library or the User's Personal Stickers.
        shared_photo: The one Shared Photo of the User's to send back after
            the text, if any.
    """

    parts: list[str]
    sticker: LibrarySticker | PersonalSticker | None
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

    The User's messages in a row are one Message, so they become one line
    with each text on its own line.

    Args:
        messages: The messages, oldest first.

    Returns:
        One line per Message or Companion message, saying who said it.
    """
    history: list[ChatLine] = []
    for message in messages:
        if message.direction == MessageDirection.OUTGOING:
            history.append(ChatLine(role=ChatRole.COMPANION, text=message.content))
        elif history and history[-1].role == ChatRole.USER:
            history[-1] = ChatLine(
                role=ChatRole.USER, text=f"{history[-1].text}\n{message.content}"
            )
        else:
            history.append(ChatLine(role=ChatRole.USER, text=message.content))
    return history


class ResponseComposer:
    """Writes the Companion's reply to the current Conversation."""

    def __init__(
        self,
        repositories: Repositories,
        chat_model: UsageRecordingChatModel,
        features: FeatureService,
        tool_providers: Sequence[ReplyToolProvider],
    ) -> None:
        """Set up the composer.

        Args:
            repositories: Where Conversations and settings are stored.
            chat_model: Generates the reply and records the tokens used.
            features: Names the Features the User doesn't have, so the
                reply can say so.
            tool_providers: Offer the tools the reply may call, each for one
                Feature, in the order the tools are offered.
        """
        self._repositories = repositories
        self._chat_model = chat_model
        self._features = features
        self._tool_providers = tool_providers

    def compose(
        self,
        conversation_id: UUID,
        snapshot: UserSnapshot,
        memory: str = "",
        knowledge: str = "",
        data_deletion_note: str = "",
        shared_photo_ids: Sequence[UUID] = (),
        reply_guidance: str = "",
    ) -> ComposedReply:
        """Compose a reply to the Conversation's newest message.

        Uses the Persona, response prompt and model from platform settings,
        then what the Understanding found the User needs, what the Companion
        remembers and the Knowledge that may fit, and
        gives the model every earlier message in the Conversation. Each tool
        provider offers its tools and instructions, and a sticker or Shared
        Photo a tool picks is sent with the reply. When a Feature doesn't
        work for the User, the instructions say so, so the reply can tell
        them plainly.

        Args:
            conversation_id: The Conversation to reply in.
            snapshot: The User being replied to, as read when the reply started.
            memory: The User Memory that matters for this message; "" if none.
            knowledge: The Knowledge passages that may fit; "" if none.
            data_deletion_note: Tells the reply this Message cancelled the
                User's request to delete their data, and why; "" if it didn't.
            shared_photo_ids: The User's Shared Photos that matter for the
                message, which the reply may send one of; empty if none.
            reply_guidance: What the Understanding adds: the Need's "how to
                reply", the nuance and mood; "" if none.

        Returns:
            The reply as short messages, an optional sticker and an optional
            Shared Photo.

        Raises:
            EmptyReplyError: If the reply has no text, sticker or photo.
        """
        settings = snapshot.settings
        context = ReplyContext(
            conversation_id=conversation_id, shared_photo_ids=tuple(shared_photo_ids)
        )
        offers = [
            provider.offer(snapshot, context) for provider in self._tool_providers
        ]
        instructions = f"{settings.get(PERSONA)}\n\n{settings.get(RESPONSE_PROMPT)}"
        sections = (
            reply_guidance,
            memory,
            knowledge,
            *(offer.instructions for offer in offers),
            self._features.unavailable_note(snapshot.unavailable_features, settings),
            data_deletion_note,
        )
        for section in sections:
            if section:
                instructions += f"\n\n{section}"
        history = to_chat_history(
            self._repositories.conversations.list_messages(conversation_id)
        )
        reply = self._chat_model.generate(
            snapshot=snapshot,
            step=ModelStep.REPLY,
            model=settings.get(RESPONSE_MODEL),
            instructions=instructions,
            history=history,
            tools=[tool for offer in offers for tool in offer.tools],
        )
        reply_parts = split_into_messages(reply)
        sticker: LibrarySticker | PersonalSticker | None = None
        shared_photo: SharedPhoto | None = None
        for offer in offers:
            if isinstance(offer.picked, SharedPhoto):
                shared_photo = offer.picked
            elif offer.picked is not None:
                sticker = offer.picked
        if not reply_parts and sticker is None and shared_photo is None:
            raise EmptyReplyError
        return ComposedReply(
            parts=reply_parts, sticker=sticker, shared_photo=shared_photo
        )
