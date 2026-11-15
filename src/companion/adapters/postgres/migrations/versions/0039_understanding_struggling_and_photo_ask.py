"""Reload the Understanding prompt, which now asks if the User is struggling.

The prompt asks whether the User is struggling and whether they asked to
see one of their photos, so a struggling User isn't sent one back unasked.
Deleting the saved prompt reloads it from the seed on next start.

Revision ID: 0039
Revises: 0038
Create Date: 2026-11-15
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0039"
down_revision: str | None = "0038"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Reload the Understanding prompt from the seed."""
    op.execute("DELETE FROM platform_settings WHERE key = 'understanding_prompt'")


def downgrade() -> None:
    """Reload the Understanding prompt from the seed."""
    op.execute("DELETE FROM platform_settings WHERE key = 'understanding_prompt'")
