"""The Reply Plan takes over deciding; the Understanding only reads (ADR-0021).

Adds a Reply Plan saved with each answered Message, holding the Need, Moves
and "asked why" the reply followed, which the Understanding no longer
decides, so those columns leave the Understandings. Old Understandings keep
their saved form; no Reply Plans are made for them. The Model Call Log gets
a Reply Plan shape on both its tables. The Understanding prompt reloads from
the seed on next start, even where an Admin edited it, because the old one
asks the Understanding to pick Needs, Moves and Life Threads.

Revision ID: 0067
Revises: 0066
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0067"
down_revision: str | None = "0066"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DECISION_COLUMNS = (
    "need",
    "lead_move",
    "support_move",
    "next_move",
    "next_move_why",
    "asked_why",
)


def upgrade() -> None:
    """Create the Reply Plan table and move the decisions out of Understandings."""
    op.create_table(
        "reply_plans",
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
        sa.Column("lead_move", sa.Text()),
        sa.Column("support_move", sa.Text()),
        sa.Column("next_move", sa.Text()),
        sa.Column("next_move_why", sa.Text()),
        sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("asked_why", sa.Boolean(), nullable=False),
        sa.Column("made_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reply_plans_user_id", "reply_plans", ["user_id"])
    op.create_index(
        "ix_reply_plans_conversation_id", "reply_plans", ["conversation_id"]
    )
    op.create_index("ix_reply_plans_message_id", "reply_plans", ["message_id"])
    for column in DECISION_COLUMNS:
        op.drop_column("understandings", column)
    for table in ("model_calls", "eval_model_calls"):
        op.add_column(
            table,
            sa.Column("reply_plan_shape", postgresql.JSONB(none_as_null=True)),
        )
    op.get_bind().execute(
        sa.text("DELETE FROM platform_settings WHERE key = 'understanding_prompt'")
    )


def downgrade() -> None:
    """Drop the Reply Plans and give Understandings their decision columns back.

    Old Understandings get the Need "unknown" and no Moves; the new prompt
    stays.
    """
    for table in ("model_calls", "eval_model_calls"):
        op.drop_column(table, "reply_plan_shape")
    op.add_column(
        "understandings",
        sa.Column("need", sa.Text(), nullable=False, server_default="unknown"),
    )
    op.add_column("understandings", sa.Column("lead_move", sa.Text()))
    op.add_column("understandings", sa.Column("support_move", sa.Text()))
    op.add_column("understandings", sa.Column("next_move", sa.Text()))
    op.add_column("understandings", sa.Column("next_move_why", sa.Text()))
    op.add_column(
        "understandings",
        sa.Column("asked_why", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.drop_table("reply_plans")
