"""Photos: each message keeps the Telegram IDs of the photos it came with.

Revision ID: 0017
Revises: 0016
Create Date: 2026-11-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add each message's photos, and reload the unsupported message reply.

    The stored unsupported reply says photos can't be opened. Admins can't
    edit it, so the old row is removed and the new seed value loads on the
    next start.
    """
    op.add_column(
        "conversation_messages",
        sa.Column("photos", JSONB, nullable=False, server_default="[]"),
    )
    op.execute("DELETE FROM platform_settings WHERE key = 'unsupported_message_reply'")


def downgrade() -> None:
    """Remove each message's photos and reload the old unsupported reply."""
    op.execute("DELETE FROM platform_settings WHERE key = 'unsupported_message_reply'")
    op.drop_column("conversation_messages", "photos")
