"""A cap on the wait from the Message's first text: add the Message wait cap.

No Message waits more than the cap from its first text. The cap is added at
20 seconds, or at the longest wait already stored if an Admin set one
longer, so the cap is never shorter than a wait and no Admin's wait is cut
short. A cap already stored is kept. No User data is touched.

Revision ID: 0076
Revises: 0075
Create Date: 2026-11-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0076"
down_revision: str | None = "0075"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_WAIT_CAP_SECONDS = 20


def upgrade() -> None:
    """Add the wait cap, at least as long as the longest stored wait."""
    op.get_bind().execute(
        sa.text(
            """
            INSERT INTO platform_settings (key, value, updated_at)
            SELECT 'message_wait_cap_seconds',
                   to_jsonb(GREATEST(
                       CAST(:default_cap AS int),
                       COALESCE(MAX((value #>> '{}')::int), 0)
                   )),
                   now()
            FROM platform_settings
            WHERE key IN (
                'message_wait_finished_seconds',
                'message_wait_trailing_seconds',
                'message_wait_seconds'
            )
            ON CONFLICT (key) DO NOTHING
            """
        ),
        {"default_cap": DEFAULT_WAIT_CAP_SECONDS},
    )


def downgrade() -> None:
    """Remove the wait cap."""
    op.execute("DELETE FROM platform_settings WHERE key = 'message_wait_cap_seconds'")
