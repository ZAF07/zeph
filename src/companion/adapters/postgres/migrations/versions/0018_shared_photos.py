"""Shared Photos: photos that matter to a User, kept in their User Memory.

Revision ID: 0018
Revises: 0017
Create Date: 2026-11-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add Shared Photos, and reload the memory processing prompt.

    The stored memory processing prompt doesn't ask which photos to keep,
    so the old row is removed and the new seed value loads on the next start.
    """
    op.create_table(
        "shared_photos",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("file_id", sa.Text, nullable=False),
        sa.Column("file_unique_id", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("note", sa.Text, nullable=False),
        sa.Column("caption", sa.Text, nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "conversation_id",
            sa.Uuid,
            sa.ForeignKey("conversations.id", ondelete="SET NULL"),
        ),
    )
    op.execute("DELETE FROM platform_settings WHERE key = 'memory_processing_prompt'")


def downgrade() -> None:
    """Remove Shared Photos and reload the old memory processing prompt."""
    op.execute("DELETE FROM platform_settings WHERE key = 'memory_processing_prompt'")
    op.drop_table("shared_photos")
