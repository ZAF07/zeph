"""Woven-in Check-ins.

Check-ins keep whether they were woven into a reply, and the Model Call Log
keeps the shape of each woven-in Check-in decision. A Check-in held back
mid-Conversation now waits to be woven in.

Revision ID: 0049
Revises: 0048
Create Date: 2026-11-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0049"
down_revision: str | None = "0048"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add woven in and the Check-in shape, and rename the held-back reason."""
    op.add_column(
        "check_ins",
        sa.Column("woven_in", sa.Boolean(), nullable=False, server_default="false"),
    )
    for table in ("model_calls", "eval_model_calls"):
        op.add_column(table, sa.Column("check_in_shape", postgresql.JSONB()))
    op.execute(
        "UPDATE users SET check_in_held_back_reason = 'waiting_to_be_woven_in' "
        "WHERE check_in_held_back_reason = 'in_conversation'"
    )


def downgrade() -> None:
    """Remove woven in and the Check-in shape, and rename the held-back reason back."""
    op.execute(
        "UPDATE users SET check_in_held_back_reason = 'in_conversation' "
        "WHERE check_in_held_back_reason = 'waiting_to_be_woven_in'"
    )
    for table in ("model_calls", "eval_model_calls"):
        op.drop_column(table, "check_in_shape")
    op.drop_column("check_ins", "woven_in")
