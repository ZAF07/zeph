"""Eval Run Variants made live, and the Needs a run used.

Eval Runs keep the live Needs when they started; Variants keep who made
their Setting Overrides live, when, and which were applied or left out.

Revision ID: 0045
Revises: 0044
Create Date: 2026-11-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0045"
down_revision: str | None = "0044"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the Needs snapshot and the Make Live columns."""
    op.add_column(
        "eval_runs",
        sa.Column(
            "needs_snapshot", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
    )
    op.add_column(
        "eval_variants",
        sa.Column(
            "made_live_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
    )
    op.add_column(
        "eval_variants", sa.Column("made_live_at", sa.DateTime(timezone=True))
    )
    op.add_column(
        "eval_variants",
        sa.Column(
            "applied_keys", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
    )
    op.add_column(
        "eval_variants",
        sa.Column(
            "left_out_keys", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
    )


def downgrade() -> None:
    """Remove the Needs snapshot and the Make Live columns."""
    for column in ("left_out_keys", "applied_keys", "made_live_at", "made_live_by"):
        op.drop_column("eval_variants", column)
    op.drop_column("eval_runs", "needs_snapshot")
