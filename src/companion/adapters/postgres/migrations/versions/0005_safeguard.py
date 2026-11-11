"""Helplines and Safeguard Events.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the helplines and safeguard_events tables."""
    op.create_table(
        "helplines",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("country", sa.Text),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("number", sa.Text, nullable=False),
        sa.Column("hours", sa.Text),
        sa.Column("sort_order", sa.Integer, nullable=False),
    )
    op.create_index(
        "helplines_one_international_fallback",
        "helplines",
        [sa.text("(country IS NULL)")],
        unique=True,
        postgresql_where=sa.text("country IS NULL"),
    )
    op.create_table(
        "safeguard_events",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("risk_type", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("helplines_country", sa.Text),
    )


def downgrade() -> None:
    """Drop the helplines and safeguard_events tables."""
    op.drop_table("safeguard_events")
    op.drop_table("helplines")
