"""Daily usage: web searches per User per day.

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the daily usage table."""
    op.create_table(
        "daily_usage",
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("day", sa.Date, primary_key=True),
        sa.Column("web_search_count", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """Drop the daily usage table."""
    op.drop_table("daily_usage")
