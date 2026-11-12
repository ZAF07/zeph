"""Settings via chat: when each setting was changed in chat, and data deletion asks.

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the settings changed in chat and the pending data deletion to Users."""
    op.add_column(
        "users",
        sa.Column(
            "settings_changed_in_chat", JSONB, nullable=False, server_default="{}"
        ),
    )
    op.add_column(
        "users",
        sa.Column("data_deletion_requested_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    """Remove the settings changed in chat and the pending data deletion."""
    op.drop_column("users", "data_deletion_requested_at")
    op.drop_column("users", "settings_changed_in_chat")
