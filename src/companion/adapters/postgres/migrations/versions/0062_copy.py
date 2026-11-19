"""Copy: the website's words, one row per fixed slot (ADR-0019).

Kept apart from platform settings. Slots are loaded from the Copy seed file
on start, so this only makes the table.

Revision ID: 0062
Revises: 0061
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision: str = "0062"
down_revision: str | None = "0061"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the Copy slots table."""
    op.create_table(
        "copy_slots",
        sa.Column("key", sa.Text, primary_key=True),
        sa.Column("tab", sa.Text, nullable=False),
        sa.Column("tab_name", sa.Text, nullable=False),
        sa.Column("tab_order", sa.Integer, nullable=False),
        sa.Column("slot_order", sa.Integer, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("max_length", sa.Integer, nullable=False),
        sa.Column("placeholders", ARRAY(sa.Text), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "updated_by", sa.Uuid, sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
    )


def downgrade() -> None:
    """Remove the Copy slots table."""
    op.drop_table("copy_slots")
