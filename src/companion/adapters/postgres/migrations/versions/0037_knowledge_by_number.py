"""Reload the Understanding prompt, which now picks Knowledge by number.

The prompt asks for the numbers of the listed Knowledge documents instead
of their titles. Deleting the saved prompt reloads it from the seed on next
start.

Revision ID: 0037
Revises: 0036
Create Date: 2026-11-15
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0037"
down_revision: str | None = "0036"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Reload the Understanding prompt from the seed."""
    op.execute("DELETE FROM platform_settings WHERE key = 'understanding_prompt'")


def downgrade() -> None:
    """Reload the Understanding prompt from the seed."""
    op.execute("DELETE FROM platform_settings WHERE key = 'understanding_prompt'")
