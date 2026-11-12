"""Basic Check-ins.

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add Check-in settings to users and the Check-in tables."""
    op.add_column(
        "users",
        sa.Column(
            "check_ins_enabled", sa.Boolean, nullable=False, server_default="false"
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "check_in_frequency",
            sa.Text,
            nullable=False,
            server_default="few_times_a_week",
        ),
    )
    op.add_column(
        "users",
        sa.Column("quiet_hours_start", sa.Time, nullable=False, server_default="22:00"),
    )
    op.add_column(
        "users",
        sa.Column("quiet_hours_end", sa.Time, nullable=False, server_default="07:30"),
    )
    op.add_column(
        "users",
        sa.Column(
            "check_ins_paused", sa.Boolean, nullable=False, server_default="false"
        ),
    )
    op.add_column(
        "users", sa.Column("check_ins_paused_until", sa.DateTime(timezone=True))
    )
    op.add_column(
        "users", sa.Column("check_in_next_due_at", sa.DateTime(timezone=True))
    )
    op.create_table(
        "check_in_kinds",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("allowed_without_user_memory", sa.Boolean, nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False),
    )
    op.create_table(
        "check_ins",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "kind_id",
            sa.Uuid,
            sa.ForeignKey("check_in_kinds.id", ondelete="SET NULL"),
        ),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("replied_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    """Drop the Check-in tables and the users' Check-in settings."""
    op.drop_table("check_ins")
    op.drop_table("check_in_kinds")
    for column in (
        "check_in_next_due_at",
        "check_ins_paused_until",
        "check_ins_paused",
        "quiet_hours_end",
        "quiet_hours_start",
        "check_in_frequency",
        "check_ins_enabled",
    ):
        op.drop_column("users", column)
