from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Engine, Row, func, select, update
from sqlalchemy.dialects.postgresql import insert

from companion.adapters.postgres.tables import (
    connection_tokens,
    conversation_messages,
    conversations,
    platform_settings,
    telegram_connections,
    users,
)
from companion.core.models import (
    ConnectionToken,
    Conversation,
    ConversationMessage,
    MessageDirection,
    MessageKind,
    StoredSetting,
    TelegramConnection,
    User,
    UserOverview,
    UserRole,
)
from companion.core.ports import Repositories


def _to_user(row: Row[Any]) -> User:
    """Turn a `users` row into a User.

    Args:
        row: The database row.

    Returns:
        The User.
    """
    return User(
        id=row.id,
        auth_id=row.auth_id,
        email=row.email,
        created_at=row.created_at,
        name=row.name,
        onboarding_reasons=tuple(row.onboarding_reasons),
        onboarding_note=row.onboarding_note,
        country=row.country,
        time_zone=row.time_zone,
        ai_notice_acknowledged_at=row.ai_notice_acknowledged_at,
        user_memory_enabled=row.user_memory_enabled,
        onboarding_completed_at=row.onboarding_completed_at,
        role=UserRole(row.role),
    )


def _to_connection(row: Row[Any]) -> TelegramConnection:
    """Turn a `telegram_connections` row into a TelegramConnection.

    Args:
        row: The database row.

    Returns:
        The Telegram Connection.
    """
    return TelegramConnection(
        user_id=row.user_id,
        telegram_user_id=row.telegram_user_id,
        telegram_chat_id=row.telegram_chat_id,
        telegram_username=row.telegram_username,
        connected_at=row.connected_at,
    )


def _to_token(row: Row[Any]) -> ConnectionToken:
    """Turn a `connection_tokens` row into a ConnectionToken.

    Args:
        row: The database row.

    Returns:
        The connection token.
    """
    return ConnectionToken(
        user_id=row.user_id,
        token=row.token,
        created_at=row.created_at,
        expires_at=row.expires_at,
        used_at=row.used_at,
        rejected_at=row.rejected_at,
    )


def _to_conversation(row: Row[Any]) -> Conversation:
    """Turn a `conversations` row into a Conversation.

    Args:
        row: The database row.

    Returns:
        The Conversation.
    """
    return Conversation(
        id=row.id,
        user_id=row.user_id,
        started_at=row.started_at,
        last_message_at=row.last_message_at,
    )


def _to_message(row: Row[Any]) -> ConversationMessage:
    """Turn a `conversation_messages` row into a ConversationMessage.

    Args:
        row: The database row.

    Returns:
        The message.
    """
    return ConversationMessage(
        id=row.id,
        conversation_id=row.conversation_id,
        direction=MessageDirection(row.direction),
        kind=MessageKind(row.kind),
        content=row.content,
        sent_at=row.sent_at,
    )


class PostgresUserRepository:
    """Stores Users in Postgres."""

    def __init__(self, engine: Engine) -> None:
        """Set up the repository.

        Args:
            engine: The database engine.
        """
        self._engine = engine

    def get(self, user_id: UUID) -> User | None:
        """Find a User by our ID.

        Args:
            user_id: The User's ID.

        Returns:
            The User, or None if there is none.
        """
        with self._engine.connect() as connection:
            row = connection.execute(select(users).where(users.c.id == user_id)).first()
        return _to_user(row) if row else None

    def get_by_auth_id(self, auth_id: str) -> User | None:
        """Find a User by the auth provider's account ID.

        Args:
            auth_id: The auth provider's account ID.

        Returns:
            The User, or None if there is none.
        """
        with self._engine.connect() as connection:
            row = connection.execute(
                select(users).where(users.c.auth_id == auth_id)
            ).first()
        return _to_user(row) if row else None

    def add(self, user: User) -> User:
        """Save a new User, or return the existing one with the same auth ID.

        Args:
            user: The User to save.

        Returns:
            The saved User.
        """
        statement = (
            insert(users)
            .values(
                id=user.id,
                auth_id=user.auth_id,
                email=user.email,
                created_at=user.created_at,
                role=user.role.value,
            )
            .on_conflict_do_nothing(index_elements=[users.c.auth_id])
        )
        with self._engine.begin() as connection:
            connection.execute(statement)
            row = connection.execute(
                select(users).where(users.c.auth_id == user.auth_id)
            ).one()
        return _to_user(row)

    def update(self, user: User) -> User:
        """Save changes to an existing User's profile and preferences.

        Args:
            user: The User with their new values.

        Returns:
            The saved User.
        """
        statement = (
            update(users)
            .where(users.c.id == user.id)
            .values(
                name=user.name,
                onboarding_reasons=list(user.onboarding_reasons),
                onboarding_note=user.onboarding_note,
                country=user.country,
                time_zone=user.time_zone,
                ai_notice_acknowledged_at=user.ai_notice_acknowledged_at,
                user_memory_enabled=user.user_memory_enabled,
                onboarding_completed_at=user.onboarding_completed_at,
            )
            .returning(users)
        )
        with self._engine.begin() as connection:
            row = connection.execute(statement).one()
        return _to_user(row)

    def list_overviews(self) -> list[UserOverview]:
        """List every User with their activity counts, newest sign-up first.

        Returns:
            One overview per User.
        """
        conversation_count = (
            select(func.count())
            .select_from(conversations)
            .where(conversations.c.user_id == users.c.id)
            .scalar_subquery()
        )
        messages_sent = (
            select(func.count())
            .select_from(conversation_messages.join(conversations))
            .where(
                conversations.c.user_id == users.c.id,
                conversation_messages.c.direction == MessageDirection.INCOMING.value,
            )
            .scalar_subquery()
        )
        telegram_connected = (
            select(telegram_connections.c.user_id)
            .where(telegram_connections.c.user_id == users.c.id)
            .exists()
        )
        statement = select(
            users,
            telegram_connected.label("telegram_connected"),
            conversation_count.label("conversation_count"),
            messages_sent.label("messages_sent"),
        ).order_by(users.c.created_at.desc())
        with self._engine.connect() as connection:
            rows = connection.execute(statement).all()
        return [
            UserOverview(
                user=_to_user(row),
                telegram_connected=row.telegram_connected,
                conversation_count=row.conversation_count,
                messages_sent=row.messages_sent,
            )
            for row in rows
        ]

    def count_admins(self) -> int:
        """Count the Users who are Admins.

        Returns:
            How many Admins there are.
        """
        with self._engine.connect() as connection:
            admin_count = connection.execute(
                select(func.count())
                .select_from(users)
                .where(users.c.role == UserRole.ADMIN.value)
            ).scalar_one()
        return int(admin_count)

    def promote_to_admin(self, user_id: UUID) -> User:
        """Make a User an Admin.

        Args:
            user_id: The User's ID.

        Returns:
            The saved User.
        """
        with self._engine.begin() as connection:
            row = connection.execute(
                update(users)
                .where(users.c.id == user_id)
                .values(role=UserRole.ADMIN.value)
                .returning(users)
            ).one()
        return _to_user(row)

    def demote_unless_last_admin(self, user_id: UUID) -> User | None:
        """Make an Admin a plain User, in one step, unless they are the only one.

        The Admin rows are locked first, so a second demotion running at the
        same time waits and then sees this one.

        Args:
            user_id: The Admin's ID.

        Returns:
            The saved User, or None if they are the last Admin.
        """
        with self._engine.begin() as connection:
            admin_ids = (
                connection.execute(
                    select(users.c.id)
                    .where(users.c.role == UserRole.ADMIN.value)
                    .with_for_update()
                )
                .scalars()
                .all()
            )
            other_admins = [admin_id for admin_id in admin_ids if admin_id != user_id]
            if not other_admins:
                return None
            row = connection.execute(
                update(users)
                .where(users.c.id == user_id)
                .values(role=UserRole.USER.value)
                .returning(users)
            ).one()
        return _to_user(row)


class PostgresTelegramConnectionRepository:
    """Stores Telegram Connections in Postgres."""

    def __init__(self, engine: Engine) -> None:
        """Set up the repository.

        Args:
            engine: The database engine.
        """
        self._engine = engine

    def get_by_user(self, user_id: UUID) -> TelegramConnection | None:
        """Find a User's Telegram Connection.

        Args:
            user_id: The User's ID.

        Returns:
            The connection, or None if the User has none.
        """
        with self._engine.connect() as connection:
            row = connection.execute(
                select(telegram_connections).where(
                    telegram_connections.c.user_id == user_id
                )
            ).first()
        return _to_connection(row) if row else None

    def get_by_telegram_user(self, telegram_user_id: int) -> TelegramConnection | None:
        """Find the Telegram Connection for a Telegram account.

        Args:
            telegram_user_id: The Telegram account's ID.

        Returns:
            The connection, or None if the account is not connected.
        """
        with self._engine.connect() as connection:
            row = connection.execute(
                select(telegram_connections).where(
                    telegram_connections.c.telegram_user_id == telegram_user_id
                )
            ).first()
        return _to_connection(row) if row else None

    def save(self, connection: TelegramConnection) -> None:
        """Save a User's Telegram Connection, replacing any they had.

        Args:
            connection: The connection to save.
        """
        values = {
            "user_id": connection.user_id,
            "telegram_user_id": connection.telegram_user_id,
            "telegram_chat_id": connection.telegram_chat_id,
            "telegram_username": connection.telegram_username,
            "connected_at": connection.connected_at,
        }
        statement = (
            insert(telegram_connections)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[telegram_connections.c.user_id], set_=values
            )
        )
        with self._engine.begin() as db:
            db.execute(statement)


class PostgresConnectionTokenRepository:
    """Stores connection tokens in Postgres."""

    def __init__(self, engine: Engine) -> None:
        """Set up the repository.

        Args:
            engine: The database engine.
        """
        self._engine = engine

    def add(self, token: ConnectionToken) -> None:
        """Save a new connection token.

        Args:
            token: The token to save.
        """
        with self._engine.begin() as connection:
            connection.execute(
                insert(connection_tokens).values(
                    token=token.token,
                    user_id=token.user_id,
                    created_at=token.created_at,
                    expires_at=token.expires_at,
                    used_at=token.used_at,
                    rejected_at=token.rejected_at,
                )
            )

    def get(self, token: str) -> ConnectionToken | None:
        """Find a connection token by its code.

        Args:
            token: The code.

        Returns:
            The token, or None if there is none.
        """
        with self._engine.connect() as connection:
            row = connection.execute(
                select(connection_tokens).where(connection_tokens.c.token == token)
            ).first()
        return _to_token(row) if row else None

    def get_latest_for_user(self, user_id: UUID) -> ConnectionToken | None:
        """Find the newest connection token a User asked for.

        Args:
            user_id: The User's ID.

        Returns:
            The newest token, or None if the User has never asked for one.
        """
        with self._engine.connect() as connection:
            row = connection.execute(
                select(connection_tokens)
                .where(connection_tokens.c.user_id == user_id)
                .order_by(connection_tokens.c.created_at.desc())
                .limit(1)
            ).first()
        return _to_token(row) if row else None

    def claim(self, token: str, used_at: datetime) -> bool:
        """Mark a token used, in one step, only if it is still active.

        Args:
            token: The code.
            used_at: When it is being used.

        Returns:
            True if this call claimed the token; False if it was already used,
            refused or expired, so two requests can never both use one token.
        """
        with self._engine.begin() as connection:
            claimed = connection.execute(
                update(connection_tokens)
                .where(
                    connection_tokens.c.token == token,
                    connection_tokens.c.used_at.is_(None),
                    connection_tokens.c.rejected_at.is_(None),
                    connection_tokens.c.expires_at > used_at,
                )
                .values(used_at=used_at)
                .returning(connection_tokens.c.token)
            ).first()
        return claimed is not None

    def mark_rejected(self, token: str, rejected_at: datetime) -> None:
        """Record that a token was refused because the Telegram account is taken.

        Args:
            token: The code.
            rejected_at: When it was refused.
        """
        with self._engine.begin() as connection:
            connection.execute(
                update(connection_tokens)
                .where(connection_tokens.c.token == token)
                .values(rejected_at=rejected_at)
            )


class PostgresConversationRepository:
    """Stores Conversations and their messages in Postgres."""

    def __init__(self, engine: Engine) -> None:
        """Set up the repository.

        Args:
            engine: The database engine.
        """
        self._engine = engine

    def get_latest_for_user(self, user_id: UUID) -> Conversation | None:
        """Find a User's newest Conversation.

        Args:
            user_id: The User's ID.

        Returns:
            The newest Conversation, or None if the User has never had one.
        """
        with self._engine.connect() as connection:
            row = connection.execute(
                select(conversations)
                .where(conversations.c.user_id == user_id)
                .order_by(conversations.c.last_message_at.desc())
                .limit(1)
            ).first()
        return _to_conversation(row) if row else None

    def add(self, conversation: Conversation) -> None:
        """Save a new Conversation.

        Args:
            conversation: The Conversation to save.
        """
        with self._engine.begin() as connection:
            connection.execute(
                insert(conversations).values(
                    id=conversation.id,
                    user_id=conversation.user_id,
                    started_at=conversation.started_at,
                    last_message_at=conversation.last_message_at,
                )
            )

    def add_message(self, message: ConversationMessage) -> None:
        """Save a message and make it the Conversation's newest message.

        Args:
            message: The message to save.
        """
        with self._engine.begin() as connection:
            connection.execute(
                insert(conversation_messages).values(
                    id=message.id,
                    conversation_id=message.conversation_id,
                    direction=message.direction.value,
                    kind=message.kind.value,
                    content=message.content,
                    sent_at=message.sent_at,
                )
            )
            connection.execute(
                update(conversations)
                .where(conversations.c.id == message.conversation_id)
                .values(last_message_at=message.sent_at)
            )

    def list_messages(self, conversation_id: UUID) -> list[ConversationMessage]:
        """List a Conversation's messages in the order they were saved.

        Args:
            conversation_id: The Conversation's ID.

        Returns:
            The messages.
        """
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(conversation_messages)
                .where(conversation_messages.c.conversation_id == conversation_id)
                .order_by(conversation_messages.c.position)
            ).all()
        return [_to_message(row) for row in rows]


class PostgresPlatformSettingsRepository:
    """Reads platform settings from Postgres."""

    def __init__(self, engine: Engine) -> None:
        """Set up the repository.

        Args:
            engine: The database engine.
        """
        self._engine = engine

    def get(self, key: str) -> Any:
        """Read one setting.

        Args:
            key: The setting's key.

        Returns:
            The setting's value.

        Raises:
            KeyError: If the setting does not exist.
        """
        with self._engine.connect() as connection:
            row = connection.execute(
                select(platform_settings.c.value).where(platform_settings.c.key == key)
            ).first()
        if row is None:
            raise KeyError(key)
        return row.value

    def get_many(self, keys: Sequence[str]) -> list[StoredSetting]:
        """Read several settings with when and by whom they were last saved.

        Args:
            keys: The settings' keys.

        Returns:
            The settings that exist, in the order of `keys`.
        """
        statement = (
            select(
                platform_settings.c.key,
                platform_settings.c.value,
                platform_settings.c.updated_at,
                func.coalesce(users.c.name, users.c.email).label("updated_by_name"),
            )
            .select_from(platform_settings.outerjoin(users))
            .where(platform_settings.c.key.in_(keys))
        )
        with self._engine.connect() as connection:
            rows = {row.key: row for row in connection.execute(statement).all()}
        return [
            StoredSetting(
                key=key,
                value=rows[key].value,
                updated_at=rows[key].updated_at,
                updated_by_name=rows[key].updated_by_name,
            )
            for key in keys
            if key in rows
        ]

    def save_many(
        self, values: Mapping[str, Any], updated_at: datetime, updated_by: UUID
    ) -> None:
        """Save new values for several settings in one step.

        Args:
            values: The new value for each setting key.
            updated_at: When they are being saved.
            updated_by: The Admin saving them.
        """
        with self._engine.begin() as connection:
            for key, value in values.items():
                connection.execute(
                    update(platform_settings)
                    .where(platform_settings.c.key == key)
                    .values(value=value, updated_at=updated_at, updated_by=updated_by)
                )


def build_postgres_repositories(engine: Engine) -> Repositories:
    """Build every repository on one Postgres engine.

    Args:
        engine: The database engine.

    Returns:
        The repositories.
    """
    return Repositories(
        users=PostgresUserRepository(engine),
        telegram_connections=PostgresTelegramConnectionRepository(engine),
        connection_tokens=PostgresConnectionTokenRepository(engine),
        conversations=PostgresConversationRepository(engine),
        platform_settings=PostgresPlatformSettingsRepository(engine),
    )
