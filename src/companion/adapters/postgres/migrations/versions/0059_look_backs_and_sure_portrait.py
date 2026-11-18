"""Look-back Curiosities, and a Portrait of only what Zeph is fairly sure of.

The Curiosity keeping prompt now asks for a gentle look-back on a vent
where Zeph only listened. The Portrait prompt no longer asks for open
questions. Both reload from the seed on next start.

Revision ID: 0059
Revises: 0058
Create Date: 2026-11-18
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0059"
down_revision: str | None = "0058"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Reload the Curiosity keeping and Portrait prompts from the seed."""
    op.execute(
        "DELETE FROM platform_settings "
        "WHERE key IN ('curiosity_keeping_prompt', 'portrait_prompt')"
    )


def downgrade() -> None:
    """Nothing to undo; the new prompts stay."""
