"""Model Call Log: one row per model call, grouped by trace (ADR-0010).

Revision ID: 0027
Revises: 0026
Create Date: 2026-11-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0027"
down_revision: str | None = "0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the model call table. `content` is filled only for full content."""
    op.create_table(
        "model_calls",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "position", sa.BigInteger(), sa.Identity(), nullable=False, unique=True
        ),
        sa.Column("trace_id", sa.Uuid(), nullable=False),
        sa.Column("trace_kind", sa.Text(), nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("tokens_in", sa.Integer(), nullable=False),
        sa.Column("tokens_out", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text()),
        sa.Column(
            "tools_called",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("content", postgresql.JSONB()),
    )
    op.create_index("ix_model_calls_trace_id", "model_calls", ["trace_id"])
    op.create_index("ix_model_calls_user_id", "model_calls", ["user_id"])
    op.create_index("ix_model_calls_started_at", "model_calls", ["started_at"])


def downgrade() -> None:
    """Drop the model call table."""
    op.drop_table("model_calls")
