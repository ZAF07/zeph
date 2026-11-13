"""Features: each Feature's switch for one User, when it isn't "default".

Revision ID: 0016
Revises: 0015
Create Date: 2026-11-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the per-User switches; they go when the User's account goes."""
    op.create_table(
        "user_feature_switches",
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("feature", sa.Text, primary_key=True),
        sa.Column("is_on", sa.Boolean, nullable=False),
        sa.Column(
            "changed_by", sa.Uuid, sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Remove the per-User switches."""
    op.drop_table("user_feature_switches")
