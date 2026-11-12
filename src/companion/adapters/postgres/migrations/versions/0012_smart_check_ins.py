"""Smart Check-ins.

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Record skipped Check-ins and their reasons, and reload the Check-in prompt.

    Every Check-in so far was sent. The stored Check-in prompt asked for a
    plain message; the new one asks for a decision, so the old row is
    removed and the new seed value loads on the next start.
    """
    op.add_column(
        "check_ins",
        sa.Column("outcome", sa.Text, nullable=False, server_default="sent"),
    )
    op.alter_column("check_ins", "outcome", server_default=None)
    op.add_column("check_ins", sa.Column("skip_reason", sa.Text))
    op.alter_column("check_ins", "message", nullable=True)
    op.alter_column("check_ins", "sent_at", new_column_name="decided_at")
    op.execute("DELETE FROM platform_settings WHERE key = 'check_in_prompt'")


def downgrade() -> None:
    """Go back to sent Check-ins only and the plain-message Check-in prompt.

    Skips and "would you like fewer?" messages are dropped, and the stored
    Check-in prompt is removed so the old seed value loads again.
    """
    op.execute("DELETE FROM check_ins WHERE outcome <> 'sent'")
    op.execute("DELETE FROM platform_settings WHERE key = 'check_in_prompt'")
    op.alter_column("check_ins", "decided_at", new_column_name="sent_at")
    op.alter_column("check_ins", "message", nullable=False)
    op.drop_column("check_ins", "skip_reason")
    op.drop_column("check_ins", "outcome")
