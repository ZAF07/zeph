"""Patterns of Pattern Types, scored by code, and the log of their moves (ADR-0024).

A Pattern may now be of a Pattern Type: it gets the Pattern Type's ID (one
Pattern per User and Pattern Type) and needs no written pattern, since its
evidence is its Observations. Every Pattern kept under the old rules is
left exactly as it was, with no Pattern Type. Adds the append-only log of
Pattern moves; a move stays when its Pattern is deleted and goes only with
its User (Delete My Data deletes it too). The scoring numbers come from the
seed on next start. No User data is removed.

Revision ID: 0083
Revises: 0082
Create Date: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0083"
down_revision: str | None = "0082"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Let a Pattern be of a Pattern Type, and add the move log."""
    op.add_column("patterns", sa.Column("pattern_type_id", sa.Text))
    op.alter_column("patterns", "pattern", nullable=True)
    op.create_unique_constraint(
        "uq_patterns_user_id_pattern_type_id",
        "patterns",
        ["user_id", "pattern_type_id"],
    )
    op.create_table(
        "pattern_moves",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "position", sa.BigInteger, sa.Identity(), nullable=False, unique=True
        ),
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pattern_id", sa.Uuid, nullable=False),
        sa.Column("pattern_type_id", sa.Text, nullable=False),
        sa.Column("from_state", sa.Text),
        sa.Column("to_state", sa.Text, nullable=False),
        sa.Column("cause", sa.Text, nullable=False),
        sa.Column("conversation_id", sa.Uuid),
        sa.Column("points", sa.Float, nullable=False),
        sa.Column("situations", sa.Integer, nullable=False),
        sa.Column("moved_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_pattern_moves_user_id", "pattern_moves", ["user_id"])


def downgrade() -> None:
    """Remove the move log and every Pattern of a Pattern Type."""
    op.drop_table("pattern_moves")
    op.execute("DELETE FROM patterns WHERE pattern_type_id IS NOT NULL")
    op.drop_constraint("uq_patterns_user_id_pattern_type_id", "patterns")
    op.alter_column("patterns", "pattern", nullable=False)
    op.drop_column("patterns", "pattern_type_id")
