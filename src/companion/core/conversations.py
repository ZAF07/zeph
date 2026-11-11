from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID, uuid4

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

    def record_incoming(self, user_id: UUID, chat_id: int, text: str) -> UUID:
        """Save a User's message and show that the Companion is typing.

        The message joins the User's open Conversation, or starts a new one if
        the quiet gap has passed since the last message.

        Args:
            user_id: The User who sent it.
            chat_id: The chat it came from.
            text: The message text.

        Returns:
            The ID of the Conversation the message was added to.
        """
        conversation_id = self._open_conversation_id(user_id)
        self._save(conversation_id, MessageDirection.INCOMING, text)
        self._chat_channel.show_typing(chat_id)
        return conversation_id

    def deliver_reply(
        self, conversation_id: UUID, chat_id: int, reply_parts: list[str]
    ) -> None:
        """Send the Companion's reply, one short message at a time.

        Before each message the Companion shows typing for a while, as a
        person would. Each message is saved as soon as it is sent.

        Args:
            conversation_id: The Conversation being answered.
            chat_id: The chat to send to.
            reply_parts: The short messages that make up the reply, in order.
        """
        settings = self._repositories.platform_settings
        for part in reply_parts:
            self._chat_channel.show_typing(chat_id)
            self._clock.sleep(typing_pause_seconds(part, settings))
            self._chat_channel.send_text(chat_id, part)
            self._save(conversation_id, MessageDirection.OUTGOING, part)

    def _open_conversation_id(self, user_id: UUID) -> UUID:
        """Find the User's open Conversation, or start a new one.

        Args:
            user_id: The User.

        Returns:
            The open Conversation's ID.
        """
        settings = self._repositories.platform_settings
        quiet_gap = timedelta(minutes=settings.get("conversation_quiet_gap_minutes"))
        now = self._clock.now()
        latest = self._repositories.conversations.get_latest_for_user(user_id)
        if latest is not None and now - latest.last_message_at < quiet_gap:
            return latest.id
        conversation = Conversation(
            id=uuid4(), user_id=user_id, started_at=now, last_message_at=now
        )
        self._repositories.conversations.add(conversation)
        return conversation.id

    def _save(
        self, conversation_id: UUID, direction: MessageDirection, text: str
    ) -> None:
        """Save one text message to a Conversation.

        Args:
            conversation_id: The Conversation.
            direction: Who sent it.
            text: The message text.
        """
        self._repositories.conversations.add_message(
            ConversationMessage(
                id=uuid4(),
                conversation_id=conversation_id,
                direction=direction,
                kind=MessageKind.TEXT,
                content=text,
                sent_at=self._clock.now(),
            )
        )


@dataclass(frozen=True)
class ConversationServices:
    """The core services the conversation engine runs, step by step.

    Attributes:
        conversations: Saves messages and sends replies.
        response_composer: Writes the Companion's reply.
    """

    conversations: ConversationService
    response_composer: ResponseComposer
