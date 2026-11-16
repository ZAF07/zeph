"""Check in Now: an Admin's request waiting on a User, and who asked for a Check-in.

Users keep a waiting Check in Now and the Admin who asked. Check-ins keep
the Admin who asked for one with Check in Now.

Revision ID: 0048
Revises: 0047
Create Date: 2026-11-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0048"
down_revision: str | None = "0047"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the waiting Check in Now on Users and who asked on Check-ins."""
    op.add_column(
        "users",
        sa.Column(
            "check_in_now_requested_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
    )
    op.add_column(
        "users",
        sa.Column("check_in_now_requested_at", sa.DateTime(timezone=True)),
    )
    op.add_column(
        "check_ins",
        sa.Column(
            "requested_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
    )


def downgrade() -> None:
    """Remove the waiting Check in Now and who asked."""
    op.drop_column("check_ins", "requested_by")
    op.drop_column("users", "check_in_now_requested_at")
    op.drop_column("users", "check_in_now_requested_by")
