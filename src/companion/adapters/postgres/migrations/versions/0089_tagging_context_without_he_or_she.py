"""Reload the Pattern tagging prompt, whose context lines never say he or she.

The tagging step guessed the User's gender in context lines, which Users
read as "Zeph's note" on their Memories page. The new prompt has it call the
person "they" and name others by name or role. Deleting the stored prompt
reloads it from the seed on next start, even where an Admin edited it;
Pattern noticing is off for everyone, so none is expected. No User data is
removed.

Revision ID: 0089
Revises: 0088
Create Date: 2026-11-24
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0089"
down_revision: str | None = "0088"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Reload the Pattern tagging prompt from the seed."""
    op.execute("DELETE FROM platform_settings WHERE key = 'pattern_tagging_prompt'")


def downgrade() -> None:
    """Reload the Pattern tagging prompt from the seed."""
    op.execute("DELETE FROM platform_settings WHERE key = 'pattern_tagging_prompt'")
