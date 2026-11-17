"""A Move may need a Feature; Research needs Web Search (ADR-0016).

Adds the Feature each Move can't be made without. The Research Move, found
by name ignoring case, needs Web Search.

Revision ID: 0052
Revises: 0051
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0052"
down_revision: str | None = "0051"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add each Move's needed Feature and set Research's to Web Search."""
    op.add_column("moves", sa.Column("needed_feature", sa.Text))
    op.get_bind().execute(
        sa.text(
            "UPDATE moves SET needed_feature = 'web_search' "
            "WHERE lower(name) = 'research'"
        )
    )


def downgrade() -> None:
    """Remove each Move's needed Feature."""
    op.drop_column("moves", "needed_feature")
