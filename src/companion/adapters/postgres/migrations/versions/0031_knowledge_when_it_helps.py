"""Knowledge "when it helps": each Knowledge document gets a description.

Documents made ready before this have none until an Admin writes one or the
document is indexed again. Also reloads the Understanding prompt from the seed
on next start, so it explains knowledge.

Revision ID: 0031
Revises: 0030
Create Date: 2026-11-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0031"
down_revision: str | None = "0030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add "when it helps" and reload the Understanding prompt."""
    op.add_column(
        "knowledge_documents",
        sa.Column("when_it_helps", sa.Text(), nullable=False, server_default=""),
    )
    op.execute("DELETE FROM platform_settings WHERE key = 'understanding_prompt'")


def downgrade() -> None:
    """Drop "when it helps" and reload the Understanding prompt."""
    op.drop_column("knowledge_documents", "when_it_helps")
    op.execute("DELETE FROM platform_settings WHERE key = 'understanding_prompt'")
