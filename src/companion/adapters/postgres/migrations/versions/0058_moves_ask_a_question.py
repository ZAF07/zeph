"""A Move may ask a question (ADR-0016).

Adds each Move's "asks a question" setting, off for the existing Moves. The
Woven-in Check-in prompt reloads from the seed on next start, so it leaves
out a Check-in, or weaves one in without another question, when the reply
already asks one.

Revision ID: 0058
Revises: 0057
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0058"
down_revision: str | None = "0057"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add each Move's "asks a question" and reload the Woven-in Check-in prompt."""
    op.add_column(
        "moves",
        sa.Column(
            "asks_a_question", sa.Boolean, nullable=False, server_default=sa.false()
        ),
    )
    op.get_bind().execute(
        sa.text("DELETE FROM platform_settings WHERE key = 'woven_check_in_prompt'")
    )


def downgrade() -> None:
    """Remove each Move's "asks a question"; the new prompt stays."""
    op.drop_column("moves", "asks_a_question")
