"""Thought Experiments: made-up situations that tell two Pattern Types apart.

Adds `thought_experiments`, managed by Admins and never deleted; the first
set comes from the seed on next start. A try can now put one to a User:
`exploration_tries.thought_experiment_id`. `pattern_tagging_prompt` reloads
from the seed on next start, even where an Admin edited it, since tagging
now marks answers to Thought Experiments. The weekly number comes from the
seed on next start. No User data is removed.

Revision ID: 0089
Revises: 0088
Create Date: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0089"
down_revision: str | None = "0088"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RELOADED_PROMPTS = ("pattern_tagging_prompt",)


def upgrade() -> None:
    """Add Thought Experiments and let a try put one to a User."""
    op.create_table(
        "thought_experiments",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("wording", sa.Text, nullable=False),
        sa.Column("pattern_type_id", sa.Text, nullable=False),
        sa.Column("other_pattern_type_id", sa.Text, nullable=False),
        sa.Column("sensitivity", sa.Text, nullable=False),
        sa.Column("starter", sa.Boolean, nullable=False),
        sa.Column("is_on", sa.Boolean, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("seed_key", sa.Text, unique=True),
    )
    op.add_column(
        "exploration_tries",
        sa.Column(
            "thought_experiment_id",
            sa.Uuid,
            sa.ForeignKey("thought_experiments.id"),
        ),
    )
    op.create_index(
        "ix_exploration_tries_thought_experiment_id",
        "exploration_tries",
        ["thought_experiment_id"],
    )
    op.get_bind().execute(
        sa.text("DELETE FROM platform_settings WHERE key IN :keys").bindparams(
            sa.bindparam("keys", expanding=True)
        ),
        {"keys": list(RELOADED_PROMPTS)},
    )


def downgrade() -> None:
    """Remove Thought Experiments and the aimed Curiosities that put one."""
    op.execute(
        "DELETE FROM curiosities WHERE id IN (SELECT curiosity_id FROM "
        "exploration_tries WHERE thought_experiment_id IS NOT NULL)"
    )
    op.drop_index("ix_exploration_tries_thought_experiment_id", "exploration_tries")
    op.drop_column("exploration_tries", "thought_experiment_id")
    op.drop_table("thought_experiments")
