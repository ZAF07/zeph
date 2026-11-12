import logging
import threading
from collections import defaultdict
from uuid import UUID

from companion.core.models import (
    ConversationTurn,
    IncomingMessage,
    MessageKind,
    UserRole,
)
from companion.core.ports import ChatChannel, ConversationEngine, Repositories
from companion.core.stickers import StickerLibraryService, sticker_message_text
from companion.core.telegram_connection import TelegramConnectionService

logger = logging.getLogger(__name__)


def readable_text(message: IncomingMessage) -> str:
    """Write an incoming message the way the Companion reads it.

    Args:
        message: The incoming message.

    Returns:
        The text; "[sticker: 😂]" for a sticker; "[photo] caption" for
        something the Companion can't open that came with a caption.
    """
    if message.kind == MessageKind.STICKER:
        return sticker_message_text(message.sticker.emoji if message.sticker else None)
    if message.kind == MessageKind.UNSUPPORTED:
        return f"[{message.attachment or 'attachment'}] {message.text.strip()}"
    return message.text


class IncomingMessageHandler:
    """Decides what to do with each message people send the Companion.

    A User's messages are answered one at a time, so a reply always sees
    every earlier message, even when several arrive at once.
    """

    def __init__(
        self,
        telegram_connections: TelegramConnectionService,
        repositories: Repositories,
        conversation_engine: ConversationEngine,
        chat_channel: ChatChannel,
        sticker_library: StickerLibraryService,
        dashboard_url: str,
    ) -> None:
        """Set up the handler.

        Args:
            telegram_connections: Handles `/start <token>` messages.
            repositories: Where Users, Telegram Connections and settings are
                stored.
            conversation_engine: Answers connected Users' messages.
            chat_channel: Sends replies that need no Conversation.
            sticker_library: Adds the stickers Admins send.
            dashboard_url: The Dashboard's address, put into some replies.
        """
        self._telegram_connections = telegram_connections
        self._sticker_library = sticker_library
        self._repositories = repositories
        self._conversation_engine = conversation_engine
        self._chat_channel = chat_channel
        self._dashboard_url = dashboard_url
        self._turn_locks: defaultdict[UUID, threading.Lock] = defaultdict(
            threading.Lock
        )
        self._turn_locks_guard = threading.Lock()

    def handle(self, message: IncomingMessage) -> None:
        """Handle one incoming message.

        `/start <token>` makes a Telegram Connection. Anyone else without a
        Telegram Connection is pointed to the Dashboard to sign up. A sticker
        from an Admin goes into the Sticker Library. A voice note, photo or
        other message the Companion can't read gets the unsupported reply,
        unless it has a caption, which is answered instead. Any other message
        from a connected User is answered by the Companion; if that fails,
        they get a short fallback reply instead of silence.

        Args:
            message: The incoming message.
        """
        if self._telegram_connections.is_start_command(message):
            self._telegram_connections.handle_start(message)
            return

        connection = self._repositories.telegram_connections.get_by_telegram_user(
            message.sender_id
        )
        if connection is None:
            reply = self._repositories.platform_settings.get(
                "unknown_telegram_user_reply"
            )
            self._chat_channel.send_text(
                message.chat_id, reply.replace("{dashboard_url}", self._dashboard_url)
            )
            return

        settings = self._repositories.platform_settings
        sticker = message.sticker if message.kind == MessageKind.STICKER else None
        if sticker is not None and self._is_admin(connection.user_id):
            if self._sticker_library.add_sent_sticker(sticker):
                reply = settings.get("sticker_added_reply")
            else:
                reply = settings.get("sticker_already_in_library_reply")
            self._chat_channel.send_text(
                message.chat_id, reply.replace("{dashboard_url}", self._dashboard_url)
            )
            return
        if message.kind == MessageKind.UNSUPPORTED and not message.text.strip():
            self._chat_channel.send_text(
                message.chat_id, settings.get("unsupported_message_reply")
            )
            return

        turn = ConversationTurn(
            user_id=connection.user_id,
            chat_id=message.chat_id,
            text=readable_text(message),
            kind=message.kind,
        )
        with self._turn_lock_for(connection.user_id):
            try:
                self._conversation_engine.handle(turn)
            except Exception:
                logger.exception("Could not answer a message from a User")
                self._chat_channel.send_text(
                    message.chat_id,
                    self._repositories.platform_settings.get("reply_failed_message"),
                )

    def _is_admin(self, user_id: UUID) -> bool:
        """Tell whether a User is an Admin right now.

        Args:
            user_id: The User.

        Returns:
            True if they are an Admin.
        """
        user = self._repositories.users.get(user_id)
        return user is not None and user.role == UserRole.ADMIN

    def _turn_lock_for(self, user_id: UUID) -> threading.Lock:
        """Get the lock that keeps one User's turns from overlapping.

        Args:
            user_id: The User.

        Returns:
            That User's lock.
        """
        with self._turn_locks_guard:
            return self._turn_locks[user_id]
