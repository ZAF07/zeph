"""Familiarity, and starter Thought Experiments for new Users.

Adds `users.familiarity` (how well Zeph knows a User; everyone starts as
new and it is worked out again when their next Conversation ends) and
`curiosities.thought_experiment_id` (the starter Thought Experiment a
Curiosity puts to a new User). `reply_plan_prompt` reloads from the seed on
next start, even where an Admin edited it, since the Reply Plan is now told
the User's Familiarity. The bars and limits come from the seed on next
start. No User data is removed.

Revision ID: 0095
Revises: 0094
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0095"
down_revision: str | None = "0094"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RELOADED_PROMPTS = ("reply_plan_prompt",)


def upgrade() -> None:
    """Add a User's Familiarity and let a Curiosity put a starter to them."""
    op.add_column(
        "users",
        sa.Column("familiarity", sa.Text, nullable=False, server_default="new"),
    )
    op.add_column(
        "curiosities",
        sa.Column(
            "thought_experiment_id",
            sa.Uuid,
            sa.ForeignKey("thought_experiments.id"),
        ),
    )
    op.create_index(
        "ix_curiosities_thought_experiment_id",
        "curiosities",
        ["thought_experiment_id"],
    )
    op.get_bind().execute(
        sa.text("DELETE FROM platform_settings WHERE key IN :keys").bindparams(
            sa.bindparam("keys", expanding=True)
        ),
        {"keys": list(RELOADED_PROMPTS)},
    )


def downgrade() -> None:
    """Remove Familiarity and every starter Thought Experiment Curiosity."""
    op.execute("DELETE FROM curiosities WHERE aim = 'starter'")
    op.drop_index("ix_curiosities_thought_experiment_id", "curiosities")
    op.drop_column("curiosities", "thought_experiment_id")
    op.drop_column("users", "familiarity")
