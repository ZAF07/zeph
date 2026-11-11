from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    MetaData,
    Table,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("auth_id", Text, nullable=False, unique=True),
    Column("email", Text),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

telegram_connections = Table(
    "telegram_connections",
    metadata,
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("telegram_user_id", BigInteger, nullable=False, unique=True),
    Column("telegram_chat_id", BigInteger, nullable=False),
    Column("telegram_username", Text),
    Column("connected_at", DateTime(timezone=True), nullable=False),
)

connection_tokens = Table(
    "connection_tokens",
    metadata,
    Column("token", Text, primary_key=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("used_at", DateTime(timezone=True)),
    Column("rejected_at", DateTime(timezone=True)),
)

platform_settings = Table(
    "platform_settings",
    metadata,
    Column("key", Text, primary_key=True),
    Column("value", JSONB, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
