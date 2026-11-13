from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    LargeBinary,
    MetaData,
    Table,
    Text,
    Time,
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
    Column("photo_viewing_enabled", Boolean, nullable=False, server_default="true"),
    Column("onboarding_completed_at", DateTime(timezone=True)),
    Column("role", Text, nullable=False, server_default="user"),
    Column("check_ins_enabled", Boolean, nullable=False, server_default="false"),
    Column(
        "check_in_frequency",
        Text,
        nullable=False,
        server_default="few_times_a_week",
    ),
    Column("quiet_hours_start", Time, nullable=False, server_default="22:00"),
    Column("quiet_hours_end", Time, nullable=False, server_default="07:30"),
    Column("check_ins_paused", Boolean, nullable=False, server_default="false"),
    Column("check_ins_paused_until", DateTime(timezone=True)),
    Column("check_in_next_due_at", DateTime(timezone=True)),
    Column("settings_changed_in_chat", JSONB, nullable=False, server_default="{}"),
    Column("data_deletion_requested_at", DateTime(timezone=True)),
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
    Column("photos", JSONB, nullable=False, server_default="[]"),
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

shared_photos = Table(
    "shared_photos",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("file_id", Text, nullable=False),
    Column("file_unique_id", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("note", Text, nullable=False),
    Column("caption", Text, nullable=False),
    Column("sent_at", DateTime(timezone=True), nullable=False),
    Column(
        "conversation_id",
        Uuid,
        ForeignKey("conversations.id", ondelete="SET NULL"),
    ),
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

daily_usage = Table(
    "daily_usage",
    metadata,
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("day", Date, primary_key=True),
    Column("web_search_count", Integer, nullable=False, server_default=text("0")),
    Column("message_count", Integer, nullable=False, server_default=text("0")),
    Column("tokens_in", BigInteger, nullable=False, server_default=text("0")),
    Column("tokens_out", BigInteger, nullable=False, server_default=text("0")),
    Column(
        "message_limit_reached", Boolean, nullable=False, server_default=text("false")
    ),
    Column(
        "web_search_limit_reached",
        Boolean,
        nullable=False,
        server_default=text("false"),
    ),
)

stickers = Table(
    "stickers",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("position", BigInteger, Identity(), nullable=False, unique=True),
    Column("file_id", Text, nullable=False),
    Column("file_unique_id", Text, nullable=False, unique=True),
    Column("emoji", Text),
    Column("set_name", Text),
    Column("preview_file_id", Text),
    Column("note", Text, nullable=False, server_default=""),
    Column("added_at", DateTime(timezone=True), nullable=False),
)

check_in_kinds = Table(
    "check_in_kinds",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("name", Text, nullable=False, unique=True),
    Column("description", Text, nullable=False),
    Column("allowed_without_user_memory", Boolean, nullable=False),
    Column("sort_order", Integer, nullable=False),
    Column("sends_shared_photo", Boolean, nullable=False),
)

check_ins = Table(
    "check_ins",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("outcome", Text, nullable=False),
    Column("kind_id", Uuid, ForeignKey("check_in_kinds.id", ondelete="SET NULL")),
    Column("message", Text),
    Column("skip_reason", Text),
    Column("decided_at", DateTime(timezone=True), nullable=False),
    Column("replied_at", DateTime(timezone=True)),
    Column(
        "shared_photo_id", Uuid, ForeignKey("shared_photos.id", ondelete="SET NULL")
    ),
)

feature_switches = Table(
    "feature_switches",
    metadata,
    Column("feature", Text, primary_key=True),
    Column("is_on", Boolean, nullable=False),
    Column("changed_by", Uuid, ForeignKey("users.id", ondelete="SET NULL")),
    Column("changed_at", DateTime(timezone=True)),
)

user_feature_switches = Table(
    "user_feature_switches",
    metadata,
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("feature", Text, primary_key=True),
    Column("is_on", Boolean, nullable=False),
    Column("changed_by", Uuid, ForeignKey("users.id", ondelete="SET NULL")),
    Column("changed_at", DateTime(timezone=True), nullable=False),
)

pending_auth_account_deletions = Table(
    "pending_auth_account_deletions",
    metadata,
    Column("auth_id", Text, primary_key=True),
    Column("added_at", DateTime(timezone=True), nullable=False),
)
