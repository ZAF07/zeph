"""Personal Stickers: stickers kept from a User, to reply in their own stickers.

Revision ID: 0022
Revises: 0021
Create Date: 2026-11-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add Personal Stickers and the sticker on each message; reload the tool text.

    The stored sticker tool description doesn't mention a User's own
    stickers, so the old row is removed and the new seed value loads on the
    next start. Admins couldn't edit it before, so no edit is lost.
    """
    op.add_column("conversation_messages", sa.Column("sticker", JSONB))
    op.create_table(
        "personal_stickers",
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
        sa.Column("emoji", sa.Text),
        sa.Column("set_name", sa.Text),
        sa.Column("preview_file_id", sa.Text),
        sa.Column("note", sa.Text, nullable=False),
        sa.Column("kept_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "file_unique_id"),
    )
    op.execute("DELETE FROM platform_settings WHERE key = 'sticker_tool_description'")


def downgrade() -> None:
    """Remove Personal Stickers and the kept stickers on messages."""
    op.execute("DELETE FROM platform_settings WHERE key = 'sticker_tool_description'")
    op.drop_table("personal_stickers")
    op.drop_column("conversation_messages", "sticker")
