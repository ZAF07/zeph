"""Move Outcomes: what the Companion learned about how each Move went (ADR-0016).

Adds the Move Outcome table, part of User Memory, and reloads the User
Portrait prompt from the seed on next start, so the Portrait draws on what
has helped and what hasn't.

Revision ID: 0051
Revises: 0050
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0051"
down_revision: str | None = "0050"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the Move Outcome table and reload the Portrait prompt."""
    op.create_table(
        "move_outcomes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "position",
            sa.BigInteger(),
            sa.Identity(),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("move", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("situation", sa.Text(), nullable=False),
        sa.Column("feeling", sa.Text(), nullable=False),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("why", sa.Text(), nullable=False),
        sa.Column("made_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("embedding", Vector(384)),
    )
    op.create_index("ix_move_outcomes_user_id", "move_outcomes", ["user_id"])
    op.execute("DELETE FROM platform_settings WHERE key = 'portrait_prompt'")


def downgrade() -> None:
    """Drop the Move Outcome table and reload the Portrait prompt."""
    op.drop_table("move_outcomes")
    op.execute("DELETE FROM platform_settings WHERE key = 'portrait_prompt'")
