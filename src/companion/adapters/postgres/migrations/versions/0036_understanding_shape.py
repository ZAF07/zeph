"""The shape of each Understanding in the Model Call Log.

Revision ID: 0036
Revises: 0035
Create Date: 2026-11-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0036"
down_revision: str | None = "0035"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add `understanding_shape` to the Model Call Log."""
    op.add_column(
        "model_calls",
        sa.Column("understanding_shape", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    """Drop `understanding_shape` from the Model Call Log."""
    op.drop_column("model_calls", "understanding_shape")
