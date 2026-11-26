"""A Prediction keeps which of its Pattern Type's wordings it was given from.

Adds `predictions.wording_number`. A Pattern Type now has several
Prediction wordings, each testing a different side of the Pattern; code
gives one the Pattern hasn't had, and confirming by Predictions counts
each wording once. A Prediction given before this has no number and
counts as its own test. No User data is removed.

Revision ID: 0108
Revises: 0107
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0108"
down_revision: str | None = "0107"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the number of the wording a Prediction was given from."""
    op.add_column("predictions", sa.Column("wording_number", sa.Integer))


def downgrade() -> None:
    """Remove it; a new Prediction may repeat the last again."""
    op.drop_column("predictions", "wording_number")
