"""User Memory: Memory Categories, Memory Items, Conversation Summaries.

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add Conversation ending and the User Memory tables."""
    op.add_column("conversations", sa.Column("ended_at", sa.DateTime(timezone=True)))
    op.add_column(
        "conversations", sa.Column("processed_at", sa.DateTime(timezone=True))
    )
    op.create_table(
        "memory_categories",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("always_include", sa.Boolean, nullable=False),
        sa.Column("archived", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer, nullable=False),
    )
    op.create_table(
        "memory_items",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "category_id",
            sa.Uuid,
            sa.ForeignKey("memory_categories.id"),
            nullable=False,
        ),
        sa.Column(
            "position", sa.BigInteger, sa.Identity(), nullable=False, unique=True
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column(
            "source_conversation_id",
            sa.Uuid,
            sa.ForeignKey("conversations.id", ondelete="SET NULL"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "conversation_summaries",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "conversation_id",
            sa.Uuid,
            sa.ForeignKey("conversations.id", ondelete="SET NULL"),
            unique=True,
        ),
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("mood", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Drop the User Memory tables and Conversation ending."""
    op.drop_table("conversation_summaries")
    op.drop_table("memory_items")
    op.drop_table("memory_categories")
    op.drop_column("conversations", "processed_at")
    op.drop_column("conversations", "ended_at")
