"""Eval Runs keep the live Moves they started with (ADR-0014).

A Variant can change a Move's text, so a run keeps the live Moves to run
with and to compare with on Make Live. Older runs kept none.

Revision ID: 0057
Revises: 0056
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0057"
down_revision: str | None = "0056"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the live Moves each run started with."""
    op.add_column(
        "eval_runs",
        sa.Column(
            "moves_snapshot", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
    )


def downgrade() -> None:
    """Drop the Moves each run started with."""
    op.drop_column("eval_runs", "moves_snapshot")
