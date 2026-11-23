"""Zeph can reply to a specific text.

Adds a nullable column to the saved messages for the chat channel's ID of
each User text, so a reply can point at it. Existing messages are left as
they are, with none. The response prompt reloads from the seed on next
start, even where an Admin edited it, because the old one never says how
to reply to a text.

Revision ID: 0077
Revises: 0076
Create Date: 2026-11-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0077"
down_revision: str | None = "0076"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the chat message ID column and drop the stored response prompt."""
    op.add_column(
        "conversation_messages",
        sa.Column("chat_message_id", sa.BigInteger(), nullable=True),
    )
    op.get_bind().execute(
        sa.text("DELETE FROM platform_settings WHERE key = 'response_prompt'")
    )


def downgrade() -> None:
    """Drop the chat message ID column; the response prompt stays as it is."""
    op.drop_column("conversation_messages", "chat_message_id")
