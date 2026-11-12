from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    LargeBinary,
    MetaData,
    Table,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import text

EMBEDDING_SIZE = 384

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
    Column("ended_at", DateTime(timezone=True)),
    Column("processed_at", DateTime(timezone=True)),
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

helplines = Table(
    "helplines",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("country", Text),
    Column("name", Text, nullable=False),
    Column("number", Text, nullable=False),
    Column("hours", Text),
    Column("sort_order", Integer, nullable=False),
    Index(
        "helplines_one_international_fallback",
        text("(country IS NULL)"),
        unique=True,
        postgresql_where=text("country IS NULL"),
    ),
)

safeguard_events = Table(
    "safeguard_events",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("risk_type", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, index=True),
    Column("helplines_country", Text),
)

memory_categories = Table(
    "memory_categories",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("name", Text, nullable=False, unique=True),
    Column("description", Text, nullable=False),
    Column("always_include", Boolean, nullable=False),
    Column("archived", Boolean, nullable=False, server_default="false"),
    Column("sort_order", Integer, nullable=False),
)

memory_items = Table(
    "memory_items",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "category_id",
        Uuid,
        ForeignKey("memory_categories.id"),
        nullable=False,
    ),
    Column("position", BigInteger, Identity(), nullable=False, unique=True),
    Column("content", Text, nullable=False),
    Column("source", Text, nullable=False),
    Column(
        "source_conversation_id",
        Uuid,
        ForeignKey("conversations.id", ondelete="SET NULL"),
    ),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

conversation_summaries = Table(
    "conversation_summaries",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "conversation_id",
        Uuid,
        ForeignKey("conversations.id", ondelete="SET NULL"),
        unique=True,
    ),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("summary", Text, nullable=False),
    Column("mood", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

knowledge_documents = Table(
    "knowledge_documents",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("title", Text, nullable=False),
    Column("source", Text, nullable=False),
    Column("tradition", Text, nullable=False),
    Column("file_name", Text, nullable=False),
    Column("file_type", Text, nullable=False),
    Column("content", LargeBinary, nullable=False),
    Column("text", Text),
    Column("text_edited", Boolean, nullable=False, server_default="false"),
    Column("status", Text, nullable=False),
    Column("failure_reason", Text),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

knowledge_chunks = Table(
    "knowledge_chunks",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "document_id",
        Uuid,
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("position", Integer, nullable=False),
    Column("text", Text, nullable=False),
    Column("embedding", Vector(EMBEDDING_SIZE), nullable=False),
)
