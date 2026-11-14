"""Older Conversation Summaries found by meaning: each Summary gets an embedding.

Summaries written before this have none and are only found as the newest few.
Also reloads the Understanding prompt from the seed on next start, so it
explains look_up_past.

Revision ID: 0029
Revises: 0028
Create Date: 2026-11-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0029"
down_revision: str | None = "0028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the Summary embedding and reload the Understanding prompt."""
    op.add_column(
        "conversation_summaries",
        sa.Column("embedding", Vector(384), nullable=True),
    )
    op.execute("DELETE FROM platform_settings WHERE key = 'understanding_prompt'")


def downgrade() -> None:
    """Drop the Summary embedding and reload the Understanding prompt."""
    op.drop_column("conversation_summaries", "embedding")
    op.execute("DELETE FROM platform_settings WHERE key = 'understanding_prompt'")
