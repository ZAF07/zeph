"""When each User was told about Pattern noticing (ADR-0027).

No quote is kept as evidence for a User until they have pressed "Got it"
on the Dashboard notice saying what changed. Every User starts untold, so
existing Users are told before their first Observation. No User data is
removed.

Revision ID: 0084
Revises: 0083
Create Date: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0084"
down_revision: str | None = "0083"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add when the User was told about Pattern noticing."""
    op.add_column(
        "users",
        sa.Column("pattern_noticing_told_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    """Remove when the User was told about Pattern noticing."""
    op.drop_column("users", "pattern_noticing_told_at")
