"""Understandings record whether they were the fallback (ADR-0016).

A fallback Understanding neither makes nor drops a next Move, so the next
Move a Curiosity may come from is read past it. Existing Understandings are
taken as not the fallback.

Revision ID: 0056
Revises: 0055
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0056"
down_revision: str | None = "0055"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add whether each Understanding was the fallback."""
    op.add_column(
        "understandings",
        sa.Column("is_fallback", sa.Boolean, nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    """Remove whether each Understanding was the fallback."""
    op.drop_column("understandings", "is_fallback")
