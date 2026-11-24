"""Most Curiosities per reply and holding one when a reply asks why are settings.

Both settings come from the seed on next start, at today's behaviour: one
Curiosity per reply, held back when the reply asks why. The Reply Plan
prompt reloads from the seed on next start, even where an Admin edited it,
because the old one says a reply asks at most one Curiosity whatever the
setting says. No User data is removed.

Revision ID: 0084
Revises: 0083
Create Date: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0084"
down_revision: str | None = "0083"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RELOADED_PROMPTS = ("reply_plan_prompt",)


def upgrade() -> None:
    """Drop the stored Reply Plan prompt so it reloads from the seed."""
    op.get_bind().execute(
        sa.text("DELETE FROM platform_settings WHERE key IN :keys").bindparams(
            sa.bindparam("keys", expanding=True)
        ),
        {"keys": list(RELOADED_PROMPTS)},
    )


def downgrade() -> None:
    """Nothing to undo: the prompt and the settings come from the seed."""
