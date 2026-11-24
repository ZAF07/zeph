"""Patterns kept before the Pattern Catalog move across (ADR-0024).

Every Pattern kept under the old rules stays, with all its evidence. A
suspected one becomes unmatched: it was hidden already and stays hidden. A
confirmed one stays confirmed and shown, and a closed one stays closed. A
Pattern with no Pattern Type can now keep the Pattern Type the matching pass
finds it fits. The Pattern keeping prompt is reloaded from the seed on next
start, even where an Admin edited it, since the step now only notes
unmatched Patterns. No User data is removed.

Revision ID: 0091
Revises: 0090
Create Date: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0091"
down_revision: str | None = "0090"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Make old suspected Patterns unmatched and let a Pattern keep its match."""
    op.add_column("patterns", sa.Column("matched_pattern_type_id", sa.Text))
    op.execute(
        "UPDATE patterns SET state = 'unmatched' "
        "WHERE pattern_type_id IS NULL AND state = 'suspected'"
    )
    op.execute("DELETE FROM platform_settings WHERE key = 'pattern_keeping_prompt'")


def downgrade() -> None:
    """Make unmatched Patterns suspected again and forget every match.

    The Pattern keeping prompt is reloaded from the seed again.
    """
    op.execute("UPDATE patterns SET state = 'suspected' WHERE state = 'unmatched'")
    op.drop_column("patterns", "matched_pattern_type_id")
    op.execute("DELETE FROM platform_settings WHERE key = 'pattern_keeping_prompt'")
