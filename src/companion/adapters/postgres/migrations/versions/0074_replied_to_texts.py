"""Replied-to Texts are kept with the User's texts.

Adds a nullable column to the saved messages for the earlier text a User's
text replies to. Existing messages are left as they are, with none.

Revision ID: 0074
Revises: 0073
Create Date: 2026-11-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0074"
down_revision: str | None = "0073"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the Replied-to Text column to the saved messages."""
    op.add_column(
        "conversation_messages",
        sa.Column("replied_to", JSONB(none_as_null=True), nullable=True),
    )


def downgrade() -> None:
    """Drop the Replied-to Text column."""
    op.drop_column("conversation_messages", "replied_to")
