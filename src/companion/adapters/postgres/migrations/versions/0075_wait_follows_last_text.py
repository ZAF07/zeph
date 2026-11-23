"""The wait follows how the last text reads: the Message wait becomes 6 seconds.

The Message wait is now the wait for a text that reads neither finished
nor trailing. It reloads from the seed (6) on next start only where it
still holds the old seed value, so an Admin's own wait stays. The new wait
settings are added from the seed on next start too. The old value is
written out here, so later seed changes don't change what this migration
does.

Revision ID: 0075
Revises: 0074
Create Date: 2026-11-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0075"
down_revision: str | None = "0074"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_MESSAGE_WAIT_SECONDS = 15


def upgrade() -> None:
    """Remove the Message wait still at the old seed, so the new one loads."""
    op.get_bind().execute(
        sa.text(
            "DELETE FROM platform_settings WHERE key = 'message_wait_seconds' "
            "AND value = to_jsonb(CAST(:old_seconds AS int))"
        ),
        {"old_seconds": OLD_MESSAGE_WAIT_SECONDS},
    )


def downgrade() -> None:
    """Nothing to undo; the shorter wait stays."""
