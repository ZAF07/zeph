"""User roles, and who last saved each platform setting.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the role column to users and updated_by to platform_settings."""
    op.add_column(
        "users",
        sa.Column("role", sa.Text, nullable=False, server_default="user"),
    )
    op.add_column(
        "platform_settings",
        sa.Column(
            "updated_by",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
    )


def downgrade() -> None:
    """Remove the role and updated_by columns."""
    op.drop_column("platform_settings", "updated_by")
    op.drop_column("users", "role")
