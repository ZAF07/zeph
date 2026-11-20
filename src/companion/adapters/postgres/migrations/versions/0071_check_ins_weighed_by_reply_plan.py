"""Woven-in Check-ins are weighed by the Reply Plan.

The separate Woven-in Check-in model call is retired, so its prompt is
removed. The Reply Plan prompt reloads from the seed on next start, even
where an Admin edited it, because the old one never weighs a Check-in. The
Check-in the Reply Plan chose is saved in its form, and the Model Call Log's
shapes are JSON, so no column changes.

Revision ID: 0071
Revises: 0070
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0071"
down_revision: str | None = "0070"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove the Woven-in Check-in prompt and drop the stored Reply Plan prompt."""
    op.get_bind().execute(
        sa.text(
            "DELETE FROM platform_settings "
            "WHERE key IN ('woven_check_in_prompt', 'reply_plan_prompt')"
        )
    )


def downgrade() -> None:
    """Leave the prompts as they are; nothing else changed."""
