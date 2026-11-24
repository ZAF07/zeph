"""Just chatting tests the water, and the Reply Plan says how a Curiosity was taken.

Just chatting moves from only if it fits to test the water: one light
opener, none more once the User lets one pass. It is found by name, ignoring
case; a Need an Admin changed to another choice keeps that choice. The Reply
Plan prompt reloads from the seed on next start, even where an Admin edited
it, because the old one knows nothing of test the water or of saying how
the User took the last Curiosity. No User data is removed.

Revision ID: 0081
Revises: 0080
Create Date: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0081"
down_revision: str | None = "0080"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RELOADED_PROMPTS = ("reply_plan_prompt",)


def upgrade() -> None:
    """Move Just chatting to test the water and drop the stored prompt."""
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "UPDATE needs SET curiosities = 'test_the_water' "
            "WHERE lower(name) = 'just chatting' "
            "AND curiosities = 'only_if_it_fits'"
        )
    )
    connection.execute(
        sa.text("DELETE FROM platform_settings WHERE key IN :keys").bindparams(
            sa.bindparam("keys", expanding=True)
        ),
        {"keys": list(RELOADED_PROMPTS)},
    )


def downgrade() -> None:
    """Move any Need that tests the water back to only if it fits."""
    op.get_bind().execute(
        sa.text(
            "UPDATE needs SET curiosities = 'only_if_it_fits' "
            "WHERE curiosities = 'test_the_water'"
        )
    )
