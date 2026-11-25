"""Patterns kept before the Pattern Catalog are removed (ADR-0024).

The confirmed and closed Patterns with no Pattern Type, kept under the old
rules, are deleted with their evidence, so a Pattern with no Pattern Type is
always unmatched. Unmatched Patterns and Patterns of Pattern Types are left
alone. How the User took an offered Pattern, when it was last offered and the
wait after a push-back were only used for the old ones, so they go too. The
User Portrait of a User who had a confirmed one is asked to be rewritten, so
it stops saying it.

Revision ID: 0097
Revises: 0096
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0097"
down_revision: str | None = "0096"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Delete the old confirmed and closed Patterns and what only they used."""
    op.execute(
        "UPDATE user_portraits SET rewrite_requested_at = now() "
        "WHERE user_id IN (SELECT user_id FROM patterns "
        "WHERE pattern_type_id IS NULL AND state = 'confirmed')"
    )
    op.execute(
        "DELETE FROM patterns "
        "WHERE pattern_type_id IS NULL AND state IN ('confirmed', 'closed')"
    )
    op.drop_column("patterns", "last_offered_at")
    op.drop_column("patterns", "last_reaction")
    op.execute(
        "DELETE FROM platform_settings WHERE key = 'pattern_pushed_back_wait_days'"
    )


def downgrade() -> None:
    """Bring the two columns back, empty.

    The deleted Patterns can't be brought back.
    """
    op.add_column("patterns", sa.Column("last_reaction", sa.Text))
    op.add_column("patterns", sa.Column("last_offered_at", sa.DateTime(timezone=True)))
