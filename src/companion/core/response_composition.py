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
    RESPONSE_THINKING,
)
from companion.core.ports import Repositories
from companion.core.reply_tools import (
    NO_GUIDANCE,
    ReplyContext,
    ReplyGuidance,
    ReplyOffer,
    ReplyToolProvider,
)
from companion.core.usage import UsageRecordingChatModel

BLANK_LINE = re.compile(r"\n\s*\n")
PRIORITY_ORDER = (
    "Everything below is in order of priority. When two things clash, the "
    "higher one wins:\n"
    "1. Safety, privacy and their own boundaries.\n"
    "2. What they just asked or need right now.\n"
    "3. Today's guidance: what they need from you, the Moves and how to make "
    "them.\n"
    "4. What you remember about them, used accurately. Never state something "
    "you only suspect as fact.\n"
    "5. Your voice, as described at the top.\n"
    "6. Optional extras: a Check-in, something you've been wondering about "
    "them, Knowledge passages, a sticker, a photo of theirs. Leave out any "
    "that doesn't fit what they need right now."
)
BOUNDARIES_HEADING = "## 1. Safety, privacy and their boundaries"
ASKED_NOW_HEADING = "## 2. What they just asked or need right now"
ANSWER_THE_QUESTION = (
    "If their message asks you something directly, answer it first, before "
    "anything else."
)
GUIDANCE_HEADING = "## 3. Today's guidance"
MEMORY_HEADING = "## 4. What you remember"
OPTIONAL_EXTRAS_HEADING = (
    "## 6. Optional extras: use one only if it fits what they need right now"
)


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


def write_instructions(
    voice: str,
    response_prompt: str,
    boundaries: Sequence[str],
    asked_now: Sequence[str],
    guidance: str,
    memory: str,
    optional_extras: Sequence[str],
) -> str:
    """Write the reply's instructions in their priority order.

    The voice and response prompt come first, then the priority order with
    its clash rule, then one section per level that has something in it.
    The "what they just asked" section always tells the reply to answer a
    direct question first.

    Args:
        voice: The Persona.
        response_prompt: The Admin-set response prompt.
        boundaries: What keeps them safe and respects their boundaries,
            e.g. Threads to leave alone or a data deletion note.
        asked_now: The tools' instructions and notes on what they may ask for.
        guidance: Today's guidance from the Understanding; "" if none.
        memory: The User Memory that matters; "" if none.
        optional_extras: The extras the reply may leave out, e.g. a
            Woven-in Check-in, Curiosities or Knowledge passages.

    Returns:
        The instructions.
    """
    levels = (
        (BOUNDARIES_HEADING, list(boundaries)),
        (ASKED_NOW_HEADING, [ANSWER_THE_QUESTION, *asked_now]),
        (GUIDANCE_HEADING, [guidance]),
        (MEMORY_HEADING, [memory]),
        (OPTIONAL_EXTRAS_HEADING, list(optional_extras)),
    )
    parts = [voice, response_prompt, PRIORITY_ORDER]
    for heading, sections in levels:
        filled = [section for section in sections if section]
        if filled:
            parts.append("\n\n".join([heading, *filled]))
    return "\n\n".join(part for part in parts if part)


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
        guidance: ReplyGuidance = NO_GUIDANCE,
        optional_offers: Sequence[ReplyOffer] = (),
    ) -> ComposedReply:
        """Compose a reply to the Conversation's newest message.

        The instructions follow a strict priority order (see
        `write_instructions`): the Persona and response prompt, then safety
        and the User's boundaries, what they just asked, what the
        Understanding found they need, what the Companion remembers, and
        last the optional extras the reply may leave out. The model gets
        every earlier message in the Conversation. Each tool provider offers
        its tools and instructions, and a sticker or Shared Photo a tool
        picks is sent with the reply, after any fixed text a tool asked to
        close the reply with. When a Feature doesn't work for the User, the
        instructions say so, so the reply can tell them plainly.

        Args:
            conversation_id: The Conversation to reply in.
            snapshot: The User being replied to, as read when the reply started.
            memory: The User Memory that matters for this message; "" if none.
            knowledge: The Knowledge passages that may fit; "" if none.
            data_deletion_note: Tells the reply this Message cancelled the
                User's request to delete their data, and why; "" if it didn't.
            shared_photo_ids: The User's Shared Photos that matter for the
                message, which the reply may send one of; empty if none.
            guidance: What the Understanding adds, by priority.
            optional_offers: Optional extras with their own tools, such as a
                Woven-in Check-in, whose instructions go last.

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
        instructions = write_instructions(
            voice=settings.get(PERSONA),
            response_prompt=settings.get(RESPONSE_PROMPT),
            boundaries=(data_deletion_note, guidance.boundaries),
            asked_now=(
                *(offer.instructions for offer in offers),
                self._features.unavailable_note(
                    snapshot.unavailable_features, settings
                ),
            ),
            guidance=guidance.plan,
            memory=memory,
            optional_extras=(
                *(offer.instructions for offer in optional_offers),
                guidance.curiosities,
                knowledge,
            ),
        )
        offers += optional_offers
        history = to_chat_history(
            self._repositories.conversations.list_messages(conversation_id)
        )
        reply = self._chat_model.generate(
            snapshot=snapshot,
            step=ModelStep.REPLY,
            model=settings.get(RESPONSE_MODEL),
            thinking=settings.get(RESPONSE_THINKING),
            instructions=instructions,
            history=history,
            tools=[tool for offer in offers for tool in offer.tools],
        )
        reply_parts = split_into_messages(reply)
        reply_parts += [offer.closing_text for offer in offers if offer.closing_text]
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
