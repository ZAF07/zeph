"""Longer Message wait: 15 seconds, long enough to type the next thought.

The Message wait reloads from the seed on next start only where it still
holds the old seed value, so an Admin's own wait stays. The old value is
written out here, so later seed changes don't change what this migration
does.

Revision ID: 0066
Revises: 0065
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0066"
down_revision: str | None = "0065"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_MESSAGE_WAIT_SECONDS = 4


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
    """Nothing to undo; the longer wait stays."""
