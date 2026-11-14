"""Understanding: Needs, and the Understanding saved with each answered Message.

Also drops the old memory picking entries from the Model Call Log, since the
Understanding call replaced that step.

Revision ID: 0028
Revises: 0027
Create Date: 2026-11-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the Need and Understanding tables."""
    op.create_table(
        "needs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("when_it_fits", sa.Text(), nullable=False),
        sa.Column("how_to_reply", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index(
        "needs_one_fallback",
        "needs",
        ["is_fallback"],
        unique=True,
        postgresql_where=sa.text("is_fallback"),
    )
    op.create_table(
        "understandings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "position", sa.BigInteger(), sa.Identity(), nullable=False, unique=True
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            sa.Uuid(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "message_id",
            sa.Uuid(),
            sa.ForeignKey("conversation_messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("form", postgresql.JSONB(), nullable=False),
        sa.Column("need", sa.Text(), nullable=False),
        sa.Column("asked_why", sa.Boolean(), nullable=False),
        sa.Column("made_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_understandings_user_id", "understandings", ["user_id"])
    op.create_index(
        "ix_understandings_conversation_id", "understandings", ["conversation_id"]
    )
    op.create_index("ix_understandings_message_id", "understandings", ["message_id"])
    op.execute("DELETE FROM model_calls WHERE step = 'memory_picking'")


def downgrade() -> None:
    """Drop the Need and Understanding tables."""
    op.drop_table("understandings")
    op.drop_table("needs")
