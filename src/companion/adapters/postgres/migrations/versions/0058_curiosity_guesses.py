"""Curiosities can hold a guess, with how sure the Companion is (ADR-0017).

Both are empty for a plain Curiosity. The Curiosity keeping prompt reloads
from the seed on next start, so it explains guesses.

Revision ID: 0058
Revises: 0057
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0058"
down_revision: str | None = "0057"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the guess columns and reload the Curiosity keeping prompt."""
    op.add_column("curiosities", sa.Column("guess", sa.Text()))
    op.add_column("curiosities", sa.Column("how_sure", sa.Text()))
    op.execute("DELETE FROM platform_settings WHERE key = 'curiosity_keeping_prompt'")


def downgrade() -> None:
    """Drop the guess columns; the new prompt stays."""
    op.drop_column("curiosities", "how_sure")
    op.drop_column("curiosities", "guess")
