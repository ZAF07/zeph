"""Pending auth account deletions: Clerk accounts still to delete.

Revision ID: 0019
Revises: 0018
Create Date: 2026-11-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the list of auth provider accounts still to delete.

    It holds only the auth ID and when it was added, so no personal data is
    kept once a User has deleted their account.
    """
    op.create_table(
        "pending_auth_account_deletions",
        sa.Column("auth_id", sa.Text, primary_key=True),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Remove the list of auth provider accounts still to delete."""
    op.drop_table("pending_auth_account_deletions")
