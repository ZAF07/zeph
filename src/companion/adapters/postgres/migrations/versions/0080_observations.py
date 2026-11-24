"""Observations: quoted evidence for or against a Pattern Type (ADR-0027).

Adds the Observation table, part of User Memory. An Observation keeps the
User's quote itself, with no link to its message, so Message Retention
never deletes it; it goes with its User, its Conversation (Delete My Data)
and its Life Thread. Pattern tagging calls also keep how many Observations
were tagged and dropped, in the Model Call Log and in Eval traces. The
tagging prompt, model and thinking switch come from the seed on next start.

Revision ID: 0080
Revises: 0079
Create Date: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0080"
down_revision: str | None = "0079"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the Observation table and the tagging shape of a model call."""
    op.create_table(
        "observations",
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
        sa.Column(
            "conversation_id",
            sa.Uuid,
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pattern_type_id", sa.Text, nullable=False),
        sa.Column("pattern_type_version", sa.Text, nullable=False),
        sa.Column("sign_id", sa.Text, nullable=False),
        sa.Column("direction", sa.Text, nullable=False),
        sa.Column("quote", sa.Text, nullable=False),
        sa.Column("context", sa.Text, nullable=False),
        sa.Column("day", sa.Date, nullable=False),
        sa.Column(
            "life_thread_id",
            sa.Uuid,
            sa.ForeignKey("life_threads.id", ondelete="CASCADE"),
        ),
        sa.Column("about", sa.Text, nullable=False),
        sa.Column("relationship", sa.Text),
        sa.Column("power", sa.Text),
        sa.Column("setting", sa.Text),
        sa.Column("stance", sa.Text),
        sa.Column("evidence_kind", sa.Text, nullable=False),
        sa.Column("second_pattern_type_id", sa.Text),
        sa.Column("second_pattern_type_version", sa.Text),
        sa.Column("situational", sa.Boolean, nullable=False),
        sa.Column("tagged_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("user_id", "conversation_id", "life_thread_id"):
        op.create_index(f"ix_observations_{column}", "observations", [column])
    for table in ("model_calls", "eval_model_calls"):
        op.add_column(table, sa.Column("tagging_shape", postgresql.JSONB()))


def downgrade() -> None:
    """Remove the tagging shape and the Observation table."""
    for table in ("model_calls", "eval_model_calls"):
        op.drop_column(table, "tagging_shape")
    op.drop_table("observations")
