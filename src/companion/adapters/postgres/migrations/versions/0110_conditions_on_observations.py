"""An Observation holds three more Conditions: audience, stakes, state going in.

Adds `audience`, `stakes` and `state_going_in` to `observations`, each
empty unless the User's story said it. Observations kept before have them
empty; nothing is tagged again. They go when their Observation goes.

`pattern_tagging_prompt` reloads from the seed where no Admin edited it:
the tagging step is now told the three lists and to leave a Condition
empty when the story doesn't say it. An edited prompt is kept and a
warning is logged; until the new text is merged in by hand, the three
Conditions stay empty. No User data is removed.

Revision ID: 0110
Revises: 0109
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from companion.adapters.postgres.prompt_reload import reload_prompt_unless_edited

revision: str = "0110"
down_revision: str | None = "0109"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONDITION_COLUMNS = ("audience", "stakes", "state_going_in")
PREVIOUS_SEED_HASHES = {
    "pattern_tagging_prompt": (
        "1b761f35fdb5411932320a5e8f64bd6a98b8f57063f9cd705d3a0ad4b53f44f6"
    ),
}


def upgrade() -> None:
    """Add the three Conditions and reload the tagging prompt unless edited."""
    for column in CONDITION_COLUMNS:
        op.add_column("observations", sa.Column(column, sa.Text))
    for key, previous_seed_hash in PREVIOUS_SEED_HASHES.items():
        reload_prompt_unless_edited(op.get_bind(), key, previous_seed_hash)


def downgrade() -> None:
    """Drop the three Conditions; the earlier seed prompt is not brought back."""
    for column in CONDITION_COLUMNS:
        op.drop_column("observations", column)
