"""Patterns come to mind in replies.

Adds the table of Patterns that came to mind in each Conversation, so one
found by an early message still reaches the Reply Plan later on. It goes
with its Conversation and with its Pattern. The Reply Plan prompt reloads
from the seed on next start, even where an Admin edited it, because the old
one never sees Patterns. The Pattern a Reply Plan used or offered is saved
in its form, and the Model Call Log's shapes are JSON, so no column changes.

Revision ID: 0073
Revises: 0072
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0073"
down_revision: str | None = "0072"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the Patterns in mind table and drop the stored Reply Plan prompt."""
    op.create_table(
        "patterns_in_mind",
        sa.Column(
            "conversation_id",
            sa.Uuid(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "pattern_id",
            sa.Uuid(),
            sa.ForeignKey("patterns.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("came_to_mind_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_patterns_in_mind_pattern_id", "patterns_in_mind", ["pattern_id"]
    )
    op.get_bind().execute(
        sa.text("DELETE FROM platform_settings WHERE key = 'reply_plan_prompt'")
    )


def downgrade() -> None:
    """Drop the Patterns in mind table; the Reply Plan prompt stays as it is."""
    op.drop_index("ix_patterns_in_mind_pattern_id", table_name="patterns_in_mind")
    op.drop_table("patterns_in_mind")
