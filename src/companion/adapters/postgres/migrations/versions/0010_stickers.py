"""Sticker Library.

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the stickers table."""
    op.create_table(
        "stickers",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "position", sa.BigInteger, sa.Identity(), nullable=False, unique=True
        ),
        sa.Column("file_id", sa.Text, nullable=False),
        sa.Column("file_unique_id", sa.Text, nullable=False, unique=True),
        sa.Column("emoji", sa.Text),
        sa.Column("set_name", sa.Text),
        sa.Column("preview_file_id", sa.Text),
        sa.Column("note", sa.Text, nullable=False, server_default=""),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Drop the stickers table."""
    op.drop_table("stickers")
