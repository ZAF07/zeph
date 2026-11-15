"""Reload the Knowledge intro, which now has replies answer from the passages.

When the person asks about a practice or teaching in the passages, or where
it comes from, the reply answers from them instead of holding back. Deleting
the saved intro reloads it from the seed on next start.

Revision ID: 0038
Revises: 0037
Create Date: 2026-11-15
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0038"
down_revision: str | None = "0037"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Reload the Knowledge intro from the seed."""
    op.execute("DELETE FROM platform_settings WHERE key = 'reply_knowledge_intro'")


def downgrade() -> None:
    """Reload the Knowledge intro from the seed."""
    op.execute("DELETE FROM platform_settings WHERE key = 'reply_knowledge_intro'")
