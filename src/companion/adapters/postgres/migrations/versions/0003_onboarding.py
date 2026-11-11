"""User profile and onboarding fields.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the onboarding and preference columns to users."""
    op.add_column("users", sa.Column("name", sa.Text))
    op.add_column(
        "users",
        sa.Column(
            "onboarding_reasons",
            JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column("users", sa.Column("onboarding_note", sa.Text))
    op.add_column("users", sa.Column("country", sa.Text))
    op.add_column("users", sa.Column("time_zone", sa.Text))
    op.add_column(
        "users", sa.Column("ai_notice_acknowledged_at", sa.DateTime(timezone=True))
    )
    op.add_column(
        "users",
        sa.Column(
            "user_memory_enabled",
            sa.Boolean,
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "users", sa.Column("onboarding_completed_at", sa.DateTime(timezone=True))
    )


def downgrade() -> None:
    """Remove the onboarding and preference columns from users."""
    for column in (
        "onboarding_completed_at",
        "user_memory_enabled",
        "ai_notice_acknowledged_at",
        "time_zone",
        "country",
        "onboarding_note",
        "onboarding_reasons",
        "name",
    ):
        op.drop_column("users", column)
