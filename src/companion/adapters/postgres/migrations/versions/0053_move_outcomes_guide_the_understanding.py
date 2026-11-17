"""Move Outcomes guide the Understanding (ADR-0016).

Reloads the Understanding prompt from the seed on next start, so it uses
how Moves went for the User before. The two new Move Outcome settings load
from the seed on their own.

Revision ID: 0053
Revises: 0052
Create Date: 2026-11-17
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0053"
down_revision: str | None = "0052"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Reload the Understanding prompt."""
    op.execute("DELETE FROM platform_settings WHERE key = 'understanding_prompt'")


def downgrade() -> None:
    """Reload the Understanding prompt."""
    op.execute("DELETE FROM platform_settings WHERE key = 'understanding_prompt'")
