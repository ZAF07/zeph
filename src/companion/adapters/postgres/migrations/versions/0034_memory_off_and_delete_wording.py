"""Clear wording for User Memory off and Delete My Data.

Reloads the consent explanation, the memory-off notes and the "data
deleted" reply from the seed on next start, so they mention private notes
and Delete My Data.

Revision ID: 0034
Revises: 0033
Create Date: 2026-11-14
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0034"
down_revision: str | None = "0033"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RELOADED_KEYS = (
    "'user_memory_explanation', 'memory_paused_note', "
    "'memory_not_available_note', 'data_deleted_reply'"
)


def upgrade() -> None:
    """Reload the reworded settings from the seed on next start."""
    op.execute(f"DELETE FROM platform_settings WHERE key IN ({RELOADED_KEYS})")


def downgrade() -> None:
    """Reload the reworded settings from the seed on next start."""
    op.execute(f"DELETE FROM platform_settings WHERE key IN ({RELOADED_KEYS})")
