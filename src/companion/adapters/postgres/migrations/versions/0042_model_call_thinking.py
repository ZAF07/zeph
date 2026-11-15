"""Whether each Model Call Log call was asked to think.

Revision ID: 0042
Revises: 0041
Create Date: 2026-11-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0042"
down_revision: str | None = "0041"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the thinking column; earlier calls read as thinking off."""
    op.add_column(
        "model_calls",
        sa.Column("thinking", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    """Drop the thinking column."""
    op.drop_column("model_calls", "thinking")
