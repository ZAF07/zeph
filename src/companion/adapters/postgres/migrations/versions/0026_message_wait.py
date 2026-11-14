"""Message wait: one wait for every Message, Albums included.

Revision ID: 0026
Revises: 0025
Create Date: 2026-11-14
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove the Album wait; the Message wait loads from the seed on next start."""
    op.execute("DELETE FROM platform_settings WHERE key = 'photo_album_wait_seconds'")


def downgrade() -> None:
    """Remove the Message wait; the Album wait loads from the seed on next start."""
    op.execute("DELETE FROM platform_settings WHERE key = 'message_wait_seconds'")
