from companion.core.models import IncomingMessage
from companion.core.telegram_connection import TelegramConnectionService


class IncomingMessageHandler:
    """Decides what to do with each message people send the Companion."""

    def __init__(self, telegram_connections: TelegramConnectionService) -> None:
        """Set up the handler.

        Args:
            telegram_connections: Handles `/start <token>` messages.
        """
        self._telegram_connections = telegram_connections

    def handle(self, message: IncomingMessage) -> None:
        """Handle one incoming message.

        Only `/start <token>` is handled for now; conversation arrives in a
        later slice.

        Args:
            message: The incoming message.
        """
        if self._telegram_connections.is_start_command(message):
            self._telegram_connections.handle_start(message)
