from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Identity,
    Index,
    Integer,
    LargeBinary,
    MetaData,
    Table,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
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
    Column("directness", Text, nullable=False, server_default="balanced"),
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
    Column("check_in_held_back_reason", Text),
    Column("check_in_held_back_until", DateTime(timezone=True)),
    Column("check_in_held_back_due_at", DateTime(timezone=True)),
    Column(
        "check_in_now_requested_by", Uuid, ForeignKey("users.id", ondelete="SET NULL")
    ),
    Column("check_in_now_requested_at", DateTime(timezone=True)),
    Column("settings_changed_in_chat", JSONB, nullable=False, server_default="{}"),
    Column("settings_changed_by_admin", JSONB, nullable=False, server_default="{}"),
    Column("data_deletion_requested_at", DateTime(timezone=True)),
    Column("pattern_noticing_told_at", DateTime(timezone=True)),
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
    Column("sticker", JSONB(none_as_null=True)),
    Column("replied_to", JSONB(none_as_null=True)),
    Column("chat_message_id", BigInteger),
)

platform_settings = Table(
    "platform_settings",
    metadata,
    Column("key", Text, primary_key=True),
    Column("value", JSONB, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("updated_by", Uuid, ForeignKey("users.id", ondelete="SET NULL")),
)

copy_slots = Table(
    "copy_slots",
    metadata,
    Column("key", Text, primary_key=True),
    Column("tab", Text, nullable=False),
    Column("tab_name", Text, nullable=False),
    Column("tab_order", Integer, nullable=False),
    Column("slot_order", Integer, nullable=False),
    Column("name", Text, nullable=False),
    Column("text", Text, nullable=False),
    Column("max_length", Integer, nullable=False),
    Column("placeholders", ARRAY(Text), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("updated_by", Uuid, ForeignKey("users.id", ondelete="SET NULL")),
)

pattern_types = Table(
    "pattern_types",
    metadata,
    Column("pattern_type_id", Text, primary_key=True),
    Column("version", Text, primary_key=True),
    Column("content", JSONB, nullable=False),
    Column("is_current", Boolean, nullable=False),
    Column("loaded_at", DateTime(timezone=True), nullable=False),
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

needs = Table(
    "needs",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("name", Text, nullable=False, unique=True),
    Column("when_it_fits", Text, nullable=False),
    Column("how_to_reply", Text, nullable=False),
    Column("sort_order", Integer, nullable=False),
    Column("is_fallback", Boolean, nullable=False, server_default="false"),
    Column("curiosities", Text, nullable=False, server_default="only_if_it_fits"),
    Index(
        "needs_one_fallback",
        "is_fallback",
        unique=True,
        postgresql_where=text("is_fallback"),
    ),
)

moves = Table(
    "moves",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("name", Text, nullable=False),
    Column("when_it_fits", Text, nullable=False),
    Column("how_to_do_it", Text, nullable=False),
    Column("sort_order", Integer, nullable=False),
    Column("needed_feature", Text, nullable=True),
    Column("asks_a_question", Boolean, nullable=False, server_default="false"),
    Index("moves_name_ignoring_case", text("lower(name)"), unique=True),
)

need_ruled_out_moves = Table(
    "need_ruled_out_moves",
    metadata,
    Column(
        "need_id",
        Uuid,
        ForeignKey("needs.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "move_id",
        Uuid,
        ForeignKey("moves.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)

understandings = Table(
    "understandings",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("position", BigInteger, Identity(), nullable=False, unique=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "conversation_id",
        Uuid,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "message_id",
        Uuid,
        ForeignKey("conversation_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("form", JSONB, nullable=False),
    Column("is_fallback", Boolean, nullable=False, server_default="false"),
    Column("made_at", DateTime(timezone=True), nullable=False),
)

reply_plans = Table(
    "reply_plans",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("position", BigInteger, Identity(), nullable=False, unique=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "conversation_id",
        Uuid,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "message_id",
        Uuid,
        ForeignKey("conversation_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("form", JSONB, nullable=False),
    Column("need", Text, nullable=False),
    Column("lead_move", Text),
    Column("support_move", Text),
    Column("next_move", Text),
    Column("next_move_why", Text),
    Column("is_fallback", Boolean, nullable=False, server_default="false"),
    Column("asked_why", Boolean, nullable=False),
    Column("made_at", DateTime(timezone=True), nullable=False),
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

day_summaries = Table(
    "day_summaries",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("day", Date, nullable=False),
    Column("summary", Text, nullable=False),
    Column("mood", Text, nullable=False),
    Column("written_at", DateTime(timezone=True), nullable=False),
    Column("embedding", Vector(EMBEDDING_SIZE)),
    Column("offered", Text, nullable=False, server_default=""),
    UniqueConstraint("user_id", "day"),
)

life_threads = Table(
    "life_threads",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("title", Text, nullable=False),
    Column("story", Text, nullable=False),
    Column("people", ARRAY(Text), nullable=False),
    Column("name_keys", ARRAY(Text), nullable=False),
    Column("is_open", Boolean, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("last_raised_at", DateTime(timezone=True)),
    Column(
        "last_raised_conversation_id",
        Uuid,
        ForeignKey("conversations.id", ondelete="SET NULL"),
        index=True,
    ),
    Column("last_reaction", Text),
    Column("embedding", Vector(EMBEDDING_SIZE)),
    Index("life_threads_name_keys", "name_keys", postgresql_using="gin"),
)

life_threads_in_mind = Table(
    "life_threads_in_mind",
    metadata,
    Column(
        "conversation_id",
        Uuid,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "life_thread_id",
        Uuid,
        ForeignKey("life_threads.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    Column("came_to_mind_at", DateTime(timezone=True), nullable=False),
)

user_portraits = Table(
    "user_portraits",
    metadata,
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("text", Text),
    Column("written_at", DateTime(timezone=True)),
    Column("rewrite_requested_at", DateTime(timezone=True)),
    Index(
        "ix_user_portraits_rewrite_requested_at",
        "rewrite_requested_at",
        postgresql_where=text("rewrite_requested_at IS NOT NULL"),
    ),
)

curiosities = Table(
    "curiosities",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("position", BigInteger, Identity(), nullable=False, unique=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("question", Text, nullable=False),
    Column("why", Text, nullable=False),
    Column("not_before", Date),
    Column("sensitivity", Text, nullable=False),
    Column("state", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column(
        "source_memory_item_id",
        Uuid,
        ForeignKey("memory_items.id", ondelete="CASCADE"),
        index=True,
    ),
    Column(
        "source_life_thread_id",
        Uuid,
        ForeignKey("life_threads.id", ondelete="CASCADE"),
        index=True,
    ),
    Column("raised_at", DateTime(timezone=True)),
    Column(
        "raised_conversation_id",
        Uuid,
        ForeignKey("conversations.id", ondelete="SET NULL"),
        index=True,
    ),
    Column("reaction", Text),
    Column("guess", Text),
    Column("how_sure", Text),
    Column("aim", Text, nullable=False),
    Column(
        "exploration_id",
        Uuid,
        ForeignKey("explorations.id", ondelete="CASCADE"),
        index=True,
    ),
    Column(
        "source_observation_id",
        Uuid,
        ForeignKey("observations.id", ondelete="CASCADE"),
        index=True,
    ),
    Index("ix_curiosities_user_id_state", "user_id", "state"),
)

move_outcomes = Table(
    "move_outcomes",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("position", BigInteger, Identity(), nullable=False, unique=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("move", Text, nullable=False),
    Column("role", Text, nullable=False),
    Column("situation", Text, nullable=False),
    Column("feeling", Text, nullable=False),
    Column("result", Text, nullable=False),
    Column("why", Text, nullable=False),
    Column("made_at", DateTime(timezone=True), nullable=False),
    Column("embedding", Vector(EMBEDDING_SIZE)),
)

patterns = Table(
    "patterns",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("pattern", Text),
    Column("pattern_type_id", Text),
    Column("state", Text, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("last_offered_at", DateTime(timezone=True)),
    Column("last_reaction", Text),
    Column("confirmed_at", DateTime(timezone=True)),
    Column("matched_pattern_type_id", Text),
    Column("embedding", Vector(EMBEDDING_SIZE)),
    UniqueConstraint(
        "user_id", "pattern_type_id", name="uq_patterns_user_id_pattern_type_id"
    ),
)

pattern_moves = Table(
    "pattern_moves",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("position", BigInteger, Identity(), nullable=False, unique=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("pattern_id", Uuid, nullable=False),
    Column("pattern_type_id", Text, nullable=False),
    Column("from_state", Text),
    Column("to_state", Text, nullable=False),
    Column("cause", Text, nullable=False),
    Column("conversation_id", Uuid),
    Column("points", Float, nullable=False),
    Column("situations", Integer, nullable=False),
    Column("moved_at", DateTime(timezone=True), nullable=False),
)

pattern_evidence = Table(
    "pattern_evidence",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("position", BigInteger, Identity(), nullable=False, unique=True),
    Column(
        "pattern_id",
        Uuid,
        ForeignKey("patterns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "life_thread_id",
        Uuid,
        ForeignKey("life_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("day", Date, nullable=False),
    Column("line", Text, nullable=False),
)

observations = Table(
    "observations",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("position", BigInteger, Identity(), nullable=False, unique=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "conversation_id",
        Uuid,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("pattern_type_id", Text, nullable=False),
    Column("pattern_type_version", Text, nullable=False),
    Column("sign_id", Text, nullable=False),
    Column("direction", Text, nullable=False),
    Column("quote", Text, nullable=False),
    Column("context", Text, nullable=False),
    Column("day", Date, nullable=False),
    Column(
        "life_thread_id",
        Uuid,
        ForeignKey("life_threads.id", ondelete="CASCADE"),
        index=True,
    ),
    Column("about", Text, nullable=False),
    Column("relationship", Text),
    Column("power", Text),
    Column("setting", Text),
    Column("stance", Text),
    Column("evidence_kind", Text, nullable=False),
    Column("second_pattern_type_id", Text),
    Column("second_pattern_type_version", Text),
    Column("situational", Boolean, nullable=False),
    Column("tagged_at", DateTime(timezone=True), nullable=False),
)

explorations = Table(
    "explorations",
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
        "pattern_id",
        Uuid,
        ForeignKey("patterns.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    ),
    Column("pattern_type_id", Text, nullable=False),
    Column("state", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("rested_at", DateTime(timezone=True)),
    Column("woke_at", DateTime(timezone=True)),
)

exploration_tries = Table(
    "exploration_tries",
    metadata,
    Column(
        "curiosity_id",
        Uuid,
        ForeignKey("curiosities.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "exploration_id",
        Uuid,
        ForeignKey("explorations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("need", Text, nullable=False),
    Column("way", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column(
        "observation_id",
        Uuid,
        ForeignKey("observations.id", ondelete="SET NULL"),
    ),
    Column("part_of_life", Text),
    Column("outcome", Text),
    Column(
        "thought_experiment_id",
        Uuid,
        ForeignKey("thought_experiments.id"),
        index=True,
    ),
)

thought_experiments = Table(
    "thought_experiments",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("wording", Text, nullable=False),
    Column("pattern_type_id", Text, nullable=False),
    Column("other_pattern_type_id", Text, nullable=False),
    Column("sensitivity", Text, nullable=False),
    Column("starter", Boolean, nullable=False),
    Column("is_on", Boolean, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("archived_at", DateTime(timezone=True)),
    Column("seed_key", Text, unique=True),
)

patterns_in_mind = Table(
    "patterns_in_mind",
    metadata,
    Column(
        "conversation_id",
        Uuid,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "pattern_id",
        Uuid,
        ForeignKey("patterns.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    Column("came_to_mind_at", DateTime(timezone=True), nullable=False),
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
    Column("when_it_helps", Text, nullable=False, server_default=""),
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

personal_stickers = Table(
    "personal_stickers",
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
    Column("emoji", Text),
    Column("set_name", Text),
    Column("preview_file_id", Text),
    Column("note", Text, nullable=False),
    Column("kept_at", DateTime(timezone=True), nullable=False),
    Column("last_used_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("user_id", "file_unique_id"),
)

check_in_kinds = Table(
    "check_in_kinds",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("name", Text, nullable=False, unique=True),
    Column("description", Text, nullable=False),
    Column("sort_order", Integer, nullable=False),
    Column("sends_shared_photo", Boolean, nullable=False),
    Column("raises_curiosity", Boolean, nullable=False),
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
    Column("curiosity_id", Uuid, ForeignKey("curiosities.id", ondelete="SET NULL")),
    Column("requested_by", Uuid, ForeignKey("users.id", ondelete="SET NULL")),
    Column("woven_in", Boolean, nullable=False, server_default="false"),
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

model_calls = Table(
    "model_calls",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("position", BigInteger, Identity(), nullable=False, unique=True),
    Column("trace_id", Uuid, nullable=False, index=True),
    Column("trace_kind", Text, nullable=False),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("step", Text, nullable=False),
    Column("model", Text, nullable=False),
    Column("thinking", Boolean, nullable=False, server_default="false"),
    Column("started_at", DateTime(timezone=True), nullable=False, index=True),
    Column("duration_ms", Integer, nullable=False),
    Column("tokens_in", Integer, nullable=False),
    Column("tokens_out", Integer, nullable=False),
    Column("error", Text),
    Column("tools_called", JSONB, nullable=False, server_default="[]"),
    Column("content", JSONB(none_as_null=True)),
    Column("understanding_shape", JSONB(none_as_null=True)),
    Column("check_in_shape", JSONB(none_as_null=True)),
    Column("reply_plan_shape", JSONB(none_as_null=True)),
    Column("tagging_shape", JSONB(none_as_null=True)),
)

eval_cases = Table(
    "eval_cases",
    metadata,
    Column("key", Text, primary_key=True),
    Column("position", BigInteger, Identity(), nullable=False, unique=True),
    Column("eval", Text, nullable=False, index=True),
    Column("content", JSONB, nullable=False),
    Column("archived", Boolean, nullable=False, server_default="false"),
    Column("edited", Boolean, nullable=False, server_default="false"),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("created_by", Uuid, ForeignKey("users.id", ondelete="SET NULL")),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("updated_by", Uuid, ForeignKey("users.id", ondelete="SET NULL")),
)

eval_images = Table(
    "eval_images",
    metadata,
    Column("name", Text, primary_key=True),
    Column("content", LargeBinary, nullable=False),
    Column("media_type", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

eval_judge_settings = Table(
    "eval_judge_settings",
    metadata,
    Column("key", Text, primary_key=True),
    Column("value", JSONB, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("updated_by", Uuid, ForeignKey("users.id", ondelete="SET NULL")),
)

eval_runs = Table(
    "eval_runs",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("position", BigInteger, Identity(), nullable=False, unique=True),
    Column("started_by", Uuid, ForeignKey("users.id", ondelete="SET NULL")),
    Column("started_from", Text, nullable=False),
    Column("state", Text, nullable=False, index=True),
    Column("evals", JSONB, nullable=False),
    Column("repeats", Integer, nullable=False, server_default="1"),
    Column("queued_at", DateTime(timezone=True), nullable=False),
    Column("started_at", DateTime(timezone=True)),
    Column("finished_at", DateTime(timezone=True)),
    Column("settings_snapshot", JSONB(none_as_null=True)),
    Column("judge_snapshot", JSONB(none_as_null=True)),
    Column("cases_snapshot", JSONB(none_as_null=True)),
    Column("case_keys", JSONB, nullable=False, server_default="[]"),
    Column("cancel_requested", Boolean, nullable=False, server_default="false"),
    Column("token_limit", Integer),
    Column("rerun_of", Uuid, ForeignKey("eval_runs.id", ondelete="SET NULL")),
    Column("needs_snapshot", JSONB, nullable=False, server_default="[]"),
    Column("moves_snapshot", JSONB, nullable=False, server_default="[]"),
)

eval_variants = Table(
    "eval_variants",
    metadata,
    Column(
        "run_id",
        Uuid,
        ForeignKey("eval_runs.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("letter", Text, primary_key=True),
    Column("setting_overrides", JSONB, nullable=False, server_default="{}"),
    Column("made_live_by", Uuid, ForeignKey("users.id", ondelete="SET NULL")),
    Column("made_live_at", DateTime(timezone=True)),
    Column("applied_keys", JSONB, nullable=False, server_default="[]"),
    Column("left_out_keys", JSONB, nullable=False, server_default="[]"),
)

eval_case_results = Table(
    "eval_case_results",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("position", BigInteger, Identity(), nullable=False, unique=True),
    Column(
        "run_id",
        Uuid,
        ForeignKey("eval_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("variant", Text, nullable=False),
    Column("try_number", Integer, nullable=False),
    Column("case_key", Text, nullable=False, index=True),
    Column("eval", Text, nullable=False),
    Column("case_content", JSONB, nullable=False),
    Column("outcome", Text, nullable=False),
    Column("checks", JSONB, nullable=False),
    Column("facts", JSONB, nullable=False),
    Column("notes", JSONB, nullable=False),
    Column("error", Text, nullable=False, server_default=""),
    Column("tokens_in", Integer, nullable=False),
    Column("tokens_out", Integer, nullable=False),
    Column("duration_ms", Integer, nullable=False),
    Column("finished_at", DateTime(timezone=True), nullable=False),
    Column("tokens_by_model", JSONB, nullable=False, server_default="{}"),
)

eval_model_calls = Table(
    "eval_model_calls",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("position", BigInteger, Identity(), nullable=False, unique=True),
    Column(
        "case_result_id",
        Uuid,
        ForeignKey("eval_case_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("made_up_user_id", Uuid, nullable=False),
    Column("trace_id", Uuid, nullable=False),
    Column("trace_kind", Text, nullable=False),
    Column("step", Text, nullable=False),
    Column("model", Text, nullable=False),
    Column("thinking", Boolean, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("duration_ms", Integer, nullable=False),
    Column("tokens_in", Integer, nullable=False),
    Column("tokens_out", Integer, nullable=False),
    Column("error", Text),
    Column("tools_called", JSONB, nullable=False),
    Column("content", JSONB(none_as_null=True)),
    Column("understanding_shape", JSONB(none_as_null=True)),
    Column("check_in_shape", JSONB(none_as_null=True)),
    Column("reply_plan_shape", JSONB(none_as_null=True)),
    Column("tagging_shape", JSONB(none_as_null=True)),
)
