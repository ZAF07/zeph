"""Check-in Schedule: why a Check-in is held back, and Admin Setting Changes.

Users keep why their due Check-in is held back right now and until when,
and when an Admin last changed each of their settings.

Revision ID: 0046
Revises: 0045
Create Date: 2026-11-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0046"
down_revision: str | None = "0045"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the held-back reason and until, and the changed-by-an-Admin marks."""
    op.add_column("users", sa.Column("check_in_held_back_reason", sa.Text()))
    op.add_column(
        "users",
        sa.Column("check_in_held_back_until", sa.DateTime(timezone=True)),
    )
    op.add_column(
        "users",
        sa.Column(
            "settings_changed_by_admin",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    """Remove the held-back reason and until, and the changed-by-an-Admin marks."""
    op.drop_column("users", "settings_changed_by_admin")
    op.drop_column("users", "check_in_held_back_until")
    op.drop_column("users", "check_in_held_back_reason")
