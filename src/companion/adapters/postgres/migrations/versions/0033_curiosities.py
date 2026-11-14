"""Curiosities: things the Companion wants to ask each User later.

Also reloads the Understanding prompt from the seed on next start, so it
explains Curiosities in bring_up.

Revision ID: 0033
Revises: 0032
Create Date: 2026-11-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0033"
down_revision: str | None = "0032"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the Curiosity table and reload the Understanding prompt.

    Deleting the Memory Item or Life Thread a Curiosity came from deletes
    the Curiosity.
    """
    op.create_table(
        "curiosities",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "position", sa.BigInteger(), sa.Identity(), nullable=False, unique=True
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("why", sa.Text(), nullable=False),
        sa.Column("not_before", sa.Date()),
        sa.Column("sensitivity", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "source_memory_item_id",
            sa.Uuid(),
            sa.ForeignKey("memory_items.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "source_life_thread_id",
            sa.Uuid(),
            sa.ForeignKey("life_threads.id", ondelete="CASCADE"),
        ),
        sa.Column("raised_at", sa.DateTime(timezone=True)),
        sa.Column(
            "raised_conversation_id",
            sa.Uuid(),
            sa.ForeignKey("conversations.id", ondelete="SET NULL"),
        ),
        sa.Column("reaction", sa.Text()),
    )
    op.create_index("ix_curiosities_user_id_state", "curiosities", ["user_id", "state"])
    op.create_index(
        "ix_curiosities_source_memory_item_id",
        "curiosities",
        ["source_memory_item_id"],
    )
    op.create_index(
        "ix_curiosities_source_life_thread_id",
        "curiosities",
        ["source_life_thread_id"],
    )
    op.create_index(
        "ix_curiosities_raised_conversation_id",
        "curiosities",
        ["raised_conversation_id"],
    )
    op.execute("DELETE FROM platform_settings WHERE key = 'understanding_prompt'")


def downgrade() -> None:
    """Drop the Curiosity table and reload the Understanding prompt."""
    op.drop_table("curiosities")
    op.execute("DELETE FROM platform_settings WHERE key = 'understanding_prompt'")
