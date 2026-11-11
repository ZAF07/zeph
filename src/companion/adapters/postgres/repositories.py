from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Engine, Row, select, update
from sqlalchemy.dialects.postgresql import insert

from companion.adapters.postgres.tables import (
    connection_tokens,
    platform_settings,
    telegram_connections,
    users,
)
from companion.core.models import ConnectionToken, TelegramConnection, User
from companion.core.ports import Repositories


def _to_user(row: Row[Any]) -> User:
    """Turn a `users` row into a User.

    Args:
        row: The database row.

    Returns:
        The User.
    """
    return User(
        id=row.id, auth_id=row.auth_id, email=row.email, created_at=row.created_at
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


class PostgresUserRepository:
    """Stores Users in Postgres."""

    def __init__(self, engine: Engine) -> None:
        """Set up the repository.

        Args:
            engine: The database engine.
        """
        self._engine = engine

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
            )
            .on_conflict_do_nothing(index_elements=[users.c.auth_id])
        )
        with self._engine.begin() as connection:
            connection.execute(statement)
            row = connection.execute(
                select(users).where(users.c.auth_id == user.auth_id)
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
        platform_settings=PostgresPlatformSettingsRepository(engine),
    )
