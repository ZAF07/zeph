"""Users, Telegram Connections, connection tokens and platform settings.

Revision ID: 0001
Revises:
Create Date: 2026-11-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the first tables and enable pgvector."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("auth_id", sa.Text, nullable=False, unique=True),
        sa.Column("email", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "telegram_connections",
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("telegram_user_id", sa.BigInteger, nullable=False, unique=True),
        sa.Column("telegram_chat_id", sa.BigInteger, nullable=False),
        sa.Column("telegram_username", sa.Text),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "connection_tokens",
        sa.Column("token", sa.Text, primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("rejected_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "platform_settings",
        sa.Column("key", sa.Text, primary_key=True),
        sa.Column("value", JSONB, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Drop the first tables."""
    op.drop_table("platform_settings")
    op.drop_table("connection_tokens")
    op.drop_table("telegram_connections")
    op.drop_table("users")
