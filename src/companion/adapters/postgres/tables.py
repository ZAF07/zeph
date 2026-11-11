from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Identity,
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
    Column("name", Text),
    Column("onboarding_reasons", JSONB, nullable=False, server_default="[]"),
    Column("onboarding_note", Text),
    Column("country", Text),
    Column("time_zone", Text),
    Column("ai_notice_acknowledged_at", DateTime(timezone=True)),
    Column("user_memory_enabled", Boolean, nullable=False, server_default="true"),
    Column("onboarding_completed_at", DateTime(timezone=True)),
    Column("role", Text, nullable=False, server_default="user"),
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

conversations = Table(
    "conversations",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("last_message_at", DateTime(timezone=True), nullable=False),
)

conversation_messages = Table(
    "conversation_messages",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "conversation_id",
        Uuid,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("position", BigInteger, Identity(), nullable=False, unique=True),
    Column("direction", Text, nullable=False),
    Column("kind", Text, nullable=False),
    Column("content", Text, nullable=False),
    Column("sent_at", DateTime(timezone=True), nullable=False),
)

platform_settings = Table(
    "platform_settings",
    metadata,
    Column("key", Text, primary_key=True),
    Column("value", JSONB, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("updated_by", Uuid, ForeignKey("users.id", ondelete="SET NULL")),
)
