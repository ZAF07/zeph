"""Life Threads: each User's ongoing stories, found by name or by meaning.

Also reloads the Understanding prompt from the seed on next start, so it
explains the reminded Threads, bring_up, left_alone and threads_touched.

Revision ID: 0030
Revises: 0029
Create Date: 2026-11-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0030"
down_revision: str | None = "0029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the Life Thread table and reload the Understanding prompt."""
    op.create_table(
        "life_threads",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("story", sa.Text(), nullable=False),
        sa.Column("people", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("name_keys", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("is_open", sa.Boolean(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_raised_at", sa.DateTime(timezone=True)),
        sa.Column(
            "last_raised_conversation_id",
            sa.Uuid(),
            sa.ForeignKey("conversations.id", ondelete="SET NULL"),
        ),
        sa.Column("last_reaction", sa.Text()),
        sa.Column("embedding", Vector(384)),
    )
    op.create_index("ix_life_threads_user_id", "life_threads", ["user_id"])
    op.create_index(
        "ix_life_threads_last_raised_conversation_id",
        "life_threads",
        ["last_raised_conversation_id"],
    )
    op.create_index(
        "life_threads_name_keys",
        "life_threads",
        ["name_keys"],
        postgresql_using="gin",
    )
    op.execute("DELETE FROM platform_settings WHERE key = 'understanding_prompt'")


def downgrade() -> None:
    """Drop the Life Thread table and reload the Understanding prompt."""
    op.drop_table("life_threads")
    op.execute("DELETE FROM platform_settings WHERE key = 'understanding_prompt'")
