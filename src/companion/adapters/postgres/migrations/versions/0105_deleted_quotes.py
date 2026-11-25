"""A quote a User deleted is never kept again.

Adds `deleted_quotes`: one record per quote a User deleted from "Things
you said that Zeph kept", or that went with a Pattern or Life Thread they
deleted. It holds the User, the Conversation and a hash of the quote,
never the words. The tagging checks drop an Observation whose quote is on
it, so tagging a day again can't bring a deleted quote back. No User data
is removed.

Revision ID: 0105
Revises: 0104
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0105"
down_revision: str | None = "0104"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the record of deleted quotes."""
    op.create_table(
        "deleted_quotes",
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "conversation_id",
            sa.Uuid,
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("quote_hash", sa.Text, primary_key=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Remove the record; a deleted quote can be kept again."""
    op.drop_table("deleted_quotes")
