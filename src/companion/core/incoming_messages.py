import logging
import threading
from collections import defaultdict
from uuid import UUID

from companion.core.models import ConversationTurn, IncomingMessage
from companion.core.ports import ChatChannel, ConversationEngine, Repositories
from companion.core.telegram_connection import TelegramConnectionService

logger = logging.getLogger(__name__)


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
        dashboard_url: str,
    ) -> None:
        """Set up the handler.

        Args:
            telegram_connections: Handles `/start <token>` messages.
            repositories: Where Telegram Connections and settings are stored.
            conversation_engine: Answers connected Users' messages.
            chat_channel: Sends the reply to people without a connection.
            dashboard_url: The Dashboard's address, put into that reply.
        """
        self._telegram_connections = telegram_connections
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
        Telegram Connection is pointed to the Dashboard to sign up. A connected
        User's message is answered by the Companion; if that fails, they get
        a short fallback reply instead of silence.

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

        turn = ConversationTurn(
            user_id=connection.user_id, chat_id=message.chat_id, text=message.text
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

    def _turn_lock_for(self, user_id: UUID) -> threading.Lock:
        """Get the lock that keeps one User's turns from overlapping.

        Args:
            user_id: The User.

        Returns:
            That User's lock.
        """
        with self._turn_locks_guard:
            return self._turn_locks[user_id]
