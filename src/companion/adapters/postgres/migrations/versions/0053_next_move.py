"""The next Move each Understanding holds in mind, and why (ADR-0016).

Adds the Move an Understanding means to make later in the Conversation, and
why. The Understanding prompt reloads from the seed on next start, so it
asks for the next Move.

Revision ID: 0053
Revises: 0052
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0053"
down_revision: str | None = "0052"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add each Understanding's next Move and why, and reload its prompt."""
    op.add_column("understandings", sa.Column("next_move", sa.Text))
    op.add_column("understandings", sa.Column("next_move_why", sa.Text))
    op.get_bind().execute(
        sa.text("DELETE FROM platform_settings WHERE key = 'understanding_prompt'")
    )


def downgrade() -> None:
    """Remove each Understanding's next Move and why.

    The new prompt stays.
    """
    op.drop_column("understandings", "next_move_why")
    op.drop_column("understandings", "next_move")
