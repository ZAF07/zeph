"""An unmade next Move may become a Curiosity (ADR-0016).

The Curiosity keeping prompt reloads from the seed on next start, so it
explains the next Move the Companion had in mind but never made.

Revision ID: 0055
Revises: 0054
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0055"
down_revision: str | None = "0054"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Reload the Curiosity keeping prompt from the seed."""
    op.get_bind().execute(
        sa.text("DELETE FROM platform_settings WHERE key = 'curiosity_keeping_prompt'")
    )


def downgrade() -> None:
    """Nothing to undo; the new prompt stays."""
