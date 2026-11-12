from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from companion.core.knowledge_retrieval import KnowledgeRetrieval
from companion.core.memory_retrieval import MemoryRetrieval
from companion.core.models import (
    Conversation,
    ConversationMessage,
    MessageDirection,
    MessageKind,
)
from companion.core.ports import (
    ChatChannel,
    Clock,
    PlatformSettingsRepository,
    Repositories,
)
from companion.core.response_composition import ResponseComposer
from companion.core.safeguard import Safeguard
from companion.core.stickers import sticker_message_text
from companion.core.timing import check_in_reply_window, is_open, quiet_gap
from companion.core.usage import UsageLimiter


def typing_pause_seconds(text: str, settings: PlatformSettingsRepository) -> float:
    """Work out how long to show typing before sending a message.

    Longer messages take longer to "type", within the range set by Admins.

    Args:
        text: The message about to be sent.
        settings: Holds the typing pace and its lower and upper limits.

    Returns:
        The pause in seconds.
    """
    pause = len(text) * settings.get("typing_seconds_per_character")
    shortest = settings.get("min_typing_seconds")
    longest = settings.get("max_typing_seconds")
    return float(min(max(pause, shortest), longest))


class ConversationService:
    """Saves messages into Conversations and sends the Companion's replies."""

    def __init__(
        self, repositories: Repositories, chat_channel: ChatChannel, clock: Clock
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where Conversations and settings are stored.
            chat_channel: Sends messages to the User.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._chat_channel = chat_channel
        self._clock = clock

    def record_incoming(
        self,
        user_id: UUID,
        chat_id: int,
        text: str,
        kind: MessageKind = MessageKind.TEXT,
    ) -> UUID:
        """Save a User's message and show that the Companion is typing.

        The message joins the User's open Conversation, or starts a new one if
        the quiet gap has passed since the last message.

        Args:
            user_id: The User who sent it.
            chat_id: The chat it came from.
            text: The message as the Companion reads it.
            kind: What kind of message it is.

        Returns:
            The ID of the Conversation the message was added to.
        """
        conversation_id = self._open_conversation_id(user_id)
        self._save(conversation_id, MessageDirection.INCOMING, text, kind)
        self._chat_channel.show_typing(chat_id)
        return conversation_id

    def deliver_reply(
        self,
        conversation_id: UUID,
        chat_id: int,
        reply_parts: list[str],
        sticker_id: UUID | None = None,
    ) -> None:
        """Send the Companion's reply, one short message at a time.

        Before each message the Companion shows typing for a while, as a
        person would. Each message is saved as soon as it is sent. The
        sticker, if any, goes last; it is skipped if it was removed from the
        Sticker Library meanwhile.

        Args:
            conversation_id: The Conversation being answered.
            chat_id: The chat to send to.
            reply_parts: The short messages that make up the reply, in order.
            sticker_id: The Sticker Library sticker to send after them.
        """
        settings = self._repositories.platform_settings
        for part in reply_parts:
            self._chat_channel.show_typing(chat_id)
            self._clock.sleep(typing_pause_seconds(part, settings))
            self._chat_channel.send_text(chat_id, part)
            self._save(conversation_id, MessageDirection.OUTGOING, part)
        sticker = self._repositories.stickers.get(sticker_id) if sticker_id else None
        if sticker is not None:
            self._chat_channel.send_sticker(chat_id, sticker.file_id)
            self._save(
                conversation_id,
                MessageDirection.OUTGOING,
                sticker_message_text(sticker.emoji),
                MessageKind.STICKER,
            )

    def deliver_at_once(self, conversation_id: UUID, chat_id: int, text: str) -> None:
        """Send one message straight away, without a typing pause, and save it.

        Used for the Crisis Reply, which must never wait, and the daily
        limit reply.

        Args:
            conversation_id: The Conversation being answered.
            chat_id: The chat to send to.
            text: The message, sent whole even if it has blank lines.
        """
        self._chat_channel.send_text(chat_id, text)
        self._save(conversation_id, MessageDirection.OUTGOING, text)

    def _open_conversation_id(self, user_id: UUID) -> UUID:
        """Find the User's open Conversation, or start a new one.

        A Conversation is open until it is ended or the quiet gap passes. A
        new Conversation started within the reply window of the User's
        newest Check-in answers it: it starts with that Check-in, so the
        reply has it as context, and the Check-in is marked replied.

        Args:
            user_id: The User.

        Returns:
            The open Conversation's ID.
        """
        settings = self._repositories.platform_settings
        now = self._clock.now()
        latest = self._repositories.conversations.get_latest_for_user(user_id)
        if latest is not None and is_open(latest, now, quiet_gap(settings)):
            return latest.id
        conversation = Conversation(
            id=uuid4(), user_id=user_id, started_at=now, last_message_at=now
        )
        self._repositories.conversations.add(conversation)
        check_in = self._repositories.check_ins.claim_reply(
            user_id, replied_at=now, sent_since=now - check_in_reply_window(settings)
        )
        if check_in is not None and check_in.message is not None:
            self._save(
                conversation.id,
                MessageDirection.OUTGOING,
                check_in.message,
                sent_at=check_in.decided_at,
            )
        return conversation.id

    def _save(
        self,
        conversation_id: UUID,
        direction: MessageDirection,
        text: str,
        kind: MessageKind = MessageKind.TEXT,
        sent_at: datetime | None = None,
    ) -> None:
        """Save one message to a Conversation.

        Args:
            conversation_id: The Conversation.
            direction: Who sent it.
            text: The message as the Companion reads it.
            kind: What kind of message it is.
            sent_at: When it was sent; now if not given.
        """
        self._repositories.conversations.add_message(
            ConversationMessage(
                id=uuid4(),
                conversation_id=conversation_id,
                direction=direction,
                kind=kind,
                content=text,
                sent_at=sent_at or self._clock.now(),
            )
        )


@dataclass(frozen=True)
class ConversationServices:
    """The core services the conversation engine runs, step by step.

    Attributes:
        conversations: Saves messages and sends replies.
        safeguard: Checks each message for crisis and writes the Crisis Reply.
        usage_limiter: Keeps each User within the daily message limit.
        memory_retrieval: Finds the User Memory that matters for a message.
        knowledge_retrieval: Finds the Knowledge that may fit a message.
        response_composer: Writes the Companion's reply.
    """

    conversations: ConversationService
    safeguard: Safeguard
    usage_limiter: UsageLimiter
    memory_retrieval: MemoryRetrieval
    knowledge_retrieval: KnowledgeRetrieval
    response_composer: ResponseComposer
