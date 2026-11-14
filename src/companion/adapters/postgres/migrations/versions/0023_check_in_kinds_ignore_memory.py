"""Check-in Kinds ignore User Memory: drop "allowed without User Memory".

Revision ID: 0023
Revises: 0022
Create Date: 2026-11-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop the "allowed without User Memory" flag from Check-in Kinds.

    User Memory off only stops learning, so every Kind can be sent either way.
    """
    op.drop_column("check_in_kinds", "allowed_without_user_memory")


def downgrade() -> None:
    """Bring the flag back, with every Kind allowed without User Memory."""
    op.add_column(
        "check_in_kinds",
        sa.Column(
            "allowed_without_user_memory",
            sa.Boolean,
            nullable=False,
            server_default=sa.true(),
        ),
    )
