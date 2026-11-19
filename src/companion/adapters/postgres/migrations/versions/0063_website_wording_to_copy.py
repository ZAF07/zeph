"""Drop the website wording that moved from Platform Settings to Copy.

The AI notices, the User Memory and Photo Viewing explanations, the memory-off
notes and the Delete My Data description are Copy slots now (ADR-0019), seeded
from the Copy seed. The platform isn't live, so nothing is carried over.

Revision ID: 0063
Revises: 0062
Create Date: 2026-11-19
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0063"
down_revision: str | None = "0062"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MOVED_SETTINGS = (
    "('ai_notice', 'ai_notice_short', 'user_memory_explanation', "
    "'photo_viewing_explanation', 'memory_paused_note', "
    "'memory_not_available_note', 'delete_my_data_description')"
)


def upgrade() -> None:
    """Drop the settings that are Copy now."""
    op.execute(f"DELETE FROM platform_settings WHERE key IN {MOVED_SETTINGS}")


def downgrade() -> None:
    """Nothing to restore: an older release seeds the settings again on start."""
