import secrets
from dataclasses import dataclass
from uuid import UUID

from companion.core.models import (
    ConnectionToken,
    ConnectionTokenStatus,
    IncomingMessage,
    TelegramConnection,
    User,
)
from companion.core.platform_settings import (
    CONNECTION_TOKEN_INVALID_REPLY,
    CONNECTION_TOKEN_TTL,
    DASHBOARD_URL_PLACEHOLDER,
    ONBOARDING_UNFINISHED_REPLY,
    TELEGRAM_CONNECTED_ELSEWHERE_REPLY,
    WELCOME_MESSAGE,
)
from companion.core.ports import ChatChannel, Clock, Repositories

TOKEN_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
START_COMMAND = "/start"


class OnboardingNotFinishedError(Exception):
    """Raised when a User who hasn't finished onboarding asks to connect Telegram."""

    def __init__(self) -> None:
        """Set the message the Dashboard shows."""
        super().__init__("Finish onboarding before connecting Telegram.")


@dataclass(frozen=True)
class TelegramConnectionStatus:
    """What the Dashboard shows about a User's Telegram Connection.

    Attributes:
        connection: The User's Telegram Connection, if they have one.
        latest_token: The newest connection token they asked for, if any.
        latest_token_status: That token's status right now, if there is one.
    """

    connection: TelegramConnection | None
    latest_token: ConnectionToken | None
    latest_token_status: ConnectionTokenStatus | None


def generate_token_code() -> str:
    """Make a random, easy-to-type code like "7Q2K-ZEPH".

    Returns:
        A new code made of two groups of four characters.
    """
    characters = "".join(secrets.choice(TOKEN_ALPHABET) for _ in range(8))
    return f"{characters[:4]}-{characters[4:]}"


class TelegramConnectionService:
    """Issues connection tokens and makes Telegram Connections from `/start`."""

    def __init__(
        self,
        repositories: Repositories,
        chat_channel: ChatChannel,
        clock: Clock,
        dashboard_url: str,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where Users, connections, tokens and settings are stored.
            chat_channel: Sends replies to the person in Telegram.
            clock: Tells the current time.
            dashboard_url: The Dashboard's address, put into replies that send
                people back there.
        """
        self._repositories = repositories
        self._chat_channel = chat_channel
        self._clock = clock
        self._dashboard_url = dashboard_url

    def create_token(self, user: User) -> ConnectionToken:
        """Issue a new one-time connection token for a User.

        Args:
            user: The User asking to connect Telegram.

        Returns:
            The new token.

        Raises:
            OnboardingNotFinishedError: If the User hasn't finished onboarding;
                no token is made.
        """
        if not user.has_finished_onboarding:
            raise OnboardingNotFinishedError()
        settings = self._repositories.platform_settings.load()
        lifetime = settings.get(CONNECTION_TOKEN_TTL)
        now = self._clock.now()
        token = ConnectionToken(
            user_id=user.id,
            token=generate_token_code(),
            created_at=now,
            expires_at=now + lifetime,
            used_at=None,
            rejected_at=None,
        )
        self._repositories.connection_tokens.add(token)
        return token

    def get_status(self, user_id: UUID) -> TelegramConnectionStatus:
        """Describe a User's Telegram Connection and newest token.

        Args:
            user_id: The User to look up.

        Returns:
            The connection status.
        """
        connection = self._repositories.telegram_connections.get_by_user(user_id)
        latest_token = self._repositories.connection_tokens.get_latest_for_user(user_id)
        latest_token_status = (
            latest_token.status_at(self._clock.now()) if latest_token else None
        )
        return TelegramConnectionStatus(
            connection=connection,
            latest_token=latest_token,
            latest_token_status=latest_token_status,
        )

    def is_start_command(self, message: IncomingMessage) -> bool:
        """Tell whether a message is a `/start` command.

        Args:
            message: The incoming message.

        Returns:
            True if the message starts with `/start`.
        """
        first_word = message.text.strip().split(" ", 1)[0]
        return first_word == START_COMMAND

    def handle_start(self, message: IncomingMessage) -> None:
        """Connect Telegram from a `/start <token>` message and reply.

        Sends the seeded welcome message on success, and again if the account
        that used the token sends it again (e.g. Telegram retrying an update).
        Replies pointing back to the Dashboard when the token is missing,
        unknown, expired or used by someone else, or when the Telegram account
        already belongs to another User. Links nothing and leaves the token
        unused when its User hasn't finished onboarding. A User with
        Check-ins on who was held back for having no Telegram Connection is
        due again from now.

        Args:
            message: The `/start` message.
        """
        settings = self._repositories.platform_settings.load()
        token = self._find_token(message.text)
        now = self._clock.now()
        if token is None:
            self._reply(message, settings.get(CONNECTION_TOKEN_INVALID_REPLY))
            return

        existing = self._repositories.telegram_connections.get_by_telegram_user(
            message.sender_id
        )
        token_status = token.status_at(now)
        already_connected_by_this_token = (
            token_status == ConnectionTokenStatus.USED
            and existing is not None
            and existing.user_id == token.user_id
        )
        if already_connected_by_this_token:
            self._reply(message, settings.get(WELCOME_MESSAGE))
            return

        if token_status != ConnectionTokenStatus.ACTIVE:
            self._reply(message, settings.get(CONNECTION_TOKEN_INVALID_REPLY))
            return

        if not self._has_finished_onboarding(token.user_id):
            self._reply(message, settings.get(ONBOARDING_UNFINISHED_REPLY))
            return

        if existing is not None and existing.user_id != token.user_id:
            self._repositories.connection_tokens.mark_rejected(token.token, now)
            self._reply(message, settings.get(TELEGRAM_CONNECTED_ELSEWHERE_REPLY))
            return

        if not self._repositories.connection_tokens.claim(token.token, now):
            self._reply(message, settings.get(CONNECTION_TOKEN_INVALID_REPLY))
            return

        self._repositories.telegram_connections.save(
            TelegramConnection(
                user_id=token.user_id,
                telegram_user_id=message.sender_id,
                telegram_chat_id=message.chat_id,
                telegram_username=message.sender_username,
                connected_at=now,
            )
        )
        self._repositories.check_ins.set_due_now_unless_due_later(token.user_id, now)
        self._reply(message, settings.get(WELCOME_MESSAGE))

    def _has_finished_onboarding(self, user_id: UUID) -> bool:
        """Tell whether a User has finished onboarding.

        Args:
            user_id: The User to check.

        Returns:
            True if the User exists and has finished onboarding.
        """
        user = self._repositories.users.get(user_id)
        return user is not None and user.has_finished_onboarding

    def _find_token(self, start_text: str) -> ConnectionToken | None:
        """Look up the token named in a `/start <token>` message.

        Args:
            start_text: The full message text.

        Returns:
            The token, or None if the message names none or it is unknown.
        """
        parts = start_text.strip().split()
        if len(parts) < 2:
            return None
        return self._repositories.connection_tokens.get(parts[1].upper())

    def _reply(self, message: IncomingMessage, template: str) -> None:
        """Send a reply, filling in the Dashboard address.

        Args:
            message: The message being answered.
            template: The reply text; `{dashboard_url}` is replaced.
        """
        text = template.replace(DASHBOARD_URL_PLACEHOLDER, self._dashboard_url)
        self._chat_channel.send_text(message.chat_id, text)
