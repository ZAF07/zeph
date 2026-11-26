"""Admins review what the Companion keeps noticing that fits no Pattern Type.

An unmatched Pattern can now keep a general description: the way of acting
in words that could be true of anyone. Like descriptions, from any Users,
are grouped under one row of the new `unmatched_entries`, which holds no
User ID and nothing a User said; an Admin marks each one. The Pattern
keeping prompt is reloaded from the seed on next start, even where an Admin
edited it, since the step now writes the general description. The grouping
bar comes from the seed on next start. No User data is removed.

Revision ID: 0096
Revises: 0095
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0096"
down_revision: str | None = "0095"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add unmatched entries and let a Pattern keep its general description."""
    op.create_table(
        "unmatched_entries",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("mark", sa.Text, nullable=False),
        sa.Column("folded_into_pattern_type_id", sa.Text),
        sa.Column("users_when_marked", sa.Integer),
        sa.Column("marked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute(
        "CREATE INDEX ix_unmatched_entries_embedding ON unmatched_entries "
        "USING hnsw (embedding vector_cosine_ops)"
    )
    op.add_column("patterns", sa.Column("general_description", sa.Text))
    op.add_column(
        "patterns",
        sa.Column(
            "unmatched_entry_id",
            sa.Uuid,
            sa.ForeignKey("unmatched_entries.id", ondelete="SET NULL"),
        ),
    )
    op.create_index(
        "ix_patterns_unmatched_entry_id", "patterns", ["unmatched_entry_id"]
    )
    op.execute("DELETE FROM platform_settings WHERE key = 'pattern_keeping_prompt'")


def downgrade() -> None:
    """Remove unmatched entries and the general descriptions.

    Every Pattern and its evidence stays. The Pattern keeping prompt is
    reloaded from the seed again, and the grouping bar is removed.
    """
    op.drop_index("ix_patterns_unmatched_entry_id", "patterns")
    op.drop_column("patterns", "unmatched_entry_id")
    op.drop_column("patterns", "general_description")
    op.drop_table("unmatched_entries")
    op.execute(
        "DELETE FROM platform_settings WHERE key IN "
        "('pattern_keeping_prompt', 'unmatched_grouping_closeness_percent')"
    )
