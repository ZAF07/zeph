"""Each Need says how Curiosities are treated, and every Curiosity has an aim.

Needs get a `curiosities` column: ask by default, only if it fits, or never.
The starting Needs get the values agreed for them, by name; any other Need
asks only if it fits. Curiosities get an `aim` column. Every Curiosity
already saved keeps its row: one that holds a guess aims at checking it,
and any other is a look-back. The Reply Plan and Curiosity keeping prompts
reload from the seed on next start, even where an Admin edited them,
because the old ones know nothing of aims or of how a Need treats
Curiosities. No User data is removed.

Revision ID: 0080
Revises: 0079
Create Date: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0080"
down_revision: str | None = "0079"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STARTING_TREATMENTS = {
    "be heard": "never",
    "get it done": "never",
    "think it through": "ask_by_default",
    "accountability": "ask_by_default",
}
RELOADED_PROMPTS = ("reply_plan_prompt", "curiosity_keeping_prompt")


def upgrade() -> None:
    """Add both columns, fill them in and drop the stored prompts."""
    op.add_column(
        "needs",
        sa.Column(
            "curiosities",
            sa.Text(),
            nullable=False,
            server_default="only_if_it_fits",
        ),
    )
    connection = op.get_bind()
    for name, treatment in STARTING_TREATMENTS.items():
        connection.execute(
            sa.text(
                "UPDATE needs SET curiosities = :treatment WHERE lower(name) = :name"
            ),
            {"treatment": treatment, "name": name},
        )
    op.add_column("curiosities", sa.Column("aim", sa.Text()))
    connection.execute(
        sa.text(
            "UPDATE curiosities SET aim = "
            "CASE WHEN guess IS NOT NULL THEN 'guess' ELSE 'look_back' END"
        )
    )
    op.alter_column("curiosities", "aim", nullable=False)
    connection.execute(
        sa.text("DELETE FROM platform_settings WHERE key IN :keys").bindparams(
            sa.bindparam("keys", expanding=True)
        ),
        {"keys": list(RELOADED_PROMPTS)},
    )


def downgrade() -> None:
    """Drop both columns; the prompts stay as they are."""
    op.drop_column("curiosities", "aim")
    op.drop_column("needs", "curiosities")
