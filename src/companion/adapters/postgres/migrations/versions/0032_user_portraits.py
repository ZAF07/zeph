"""User Portraits, and what was offered in each Conversation Summary.

Also reloads the post-conversation processing and Understanding prompts from
the seed on next start, so they ask for the mood arc and what was offered,
and explain the Portrait.

Revision ID: 0032
Revises: 0031
Create Date: 2026-11-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0032"
down_revision: str | None = "0031"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RELOADED_PROMPTS = "('memory_processing_prompt', 'understanding_prompt')"


def upgrade() -> None:
    """Create the User Portrait table, add `offered` and reload two prompts."""
    op.create_table(
        "user_portraits",
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("text", sa.Text()),
        sa.Column("written_at", sa.DateTime(timezone=True)),
        sa.Column("rewrite_requested_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_user_portraits_rewrite_requested_at",
        "user_portraits",
        ["rewrite_requested_at"],
        postgresql_where=sa.text("rewrite_requested_at IS NOT NULL"),
    )
    op.add_column(
        "conversation_summaries",
        sa.Column("offered", sa.Text(), nullable=False, server_default=""),
    )
    op.execute(f"DELETE FROM platform_settings WHERE key IN {RELOADED_PROMPTS}")


def downgrade() -> None:
    """Drop the User Portrait table and `offered`, and reload two prompts."""
    op.drop_column("conversation_summaries", "offered")
    op.drop_table("user_portraits")
    op.execute(f"DELETE FROM platform_settings WHERE key IN {RELOADED_PROMPTS}")
