"""Steady Due Times and the "a few times a day" Check-in Frequency.

Users keep the Due Time a Held-back Check-in was first due at, so the next
Due Time keeps their rhythm. The stored gaps by frequency gain "a few times
a day" (6 hours) where it is missing, since reading the gaps fails when a
frequency is missing.

Revision ID: 0047
Revises: 0046
Create Date: 2026-11-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0047"
down_revision: str | None = "0046"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the held-back Due Time and the missing "a few times a day" gap."""
    op.add_column(
        "users",
        sa.Column("check_in_held_back_due_at", sa.DateTime(timezone=True)),
    )
    op.execute(
        "UPDATE platform_settings "
        "SET value = jsonb_build_object('a_few_times_a_day', 6) || value "
        "WHERE key = 'check_in_hours_between' "
        "AND NOT value ? 'a_few_times_a_day'"
    )


def downgrade() -> None:
    """Remove the held-back Due Time and the "a few times a day" gap."""
    op.execute(
        "UPDATE platform_settings SET value = value - 'a_few_times_a_day' "
        "WHERE key = 'check_in_hours_between'"
    )
    op.drop_column("users", "check_in_held_back_due_at")
