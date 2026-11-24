"""Explorations and the Agenda: what Zeph is trying to learn about a Pattern.

Adds `explorations` (one per Pattern, going with it) and `exploration_tries`
(one per aimed Curiosity, going with it). A Curiosity can now aim at an
Exploration's need: it gets the Exploration it is a try for and the
Observation it aims at, and goes with either. `pattern_tagging_prompt` and
`reply_plan_prompt` reload from the seed on next start, even where an Admin
edited them, since tagging now settles unclear
Observations and the Reply Plan now sees the Agenda. The Agenda's numbers
come from the seed on next start. No User data is removed.

Revision ID: 0087
Revises: 0086
Create Date: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0087"
down_revision: str | None = "0086"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RELOADED_PROMPTS = ("pattern_tagging_prompt", "reply_plan_prompt")


def upgrade() -> None:
    """Add Explorations and their tries, and let a Curiosity aim at one."""
    op.create_table(
        "explorations",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "pattern_id",
            sa.Uuid,
            sa.ForeignKey("patterns.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("pattern_type_id", sa.Text, nullable=False),
        sa.Column("state", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rested_at", sa.DateTime(timezone=True)),
        sa.Column("woke_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_explorations_user_id", "explorations", ["user_id"])
    op.add_column(
        "curiosities",
        sa.Column(
            "exploration_id",
            sa.Uuid,
            sa.ForeignKey("explorations.id", ondelete="CASCADE"),
        ),
    )
    op.add_column(
        "curiosities",
        sa.Column(
            "source_observation_id",
            sa.Uuid,
            sa.ForeignKey("observations.id", ondelete="CASCADE"),
        ),
    )
    op.create_index("ix_curiosities_exploration_id", "curiosities", ["exploration_id"])
    op.create_index(
        "ix_curiosities_source_observation_id",
        "curiosities",
        ["source_observation_id"],
    )
    op.create_table(
        "exploration_tries",
        sa.Column(
            "curiosity_id",
            sa.Uuid,
            sa.ForeignKey("curiosities.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "exploration_id",
            sa.Uuid,
            sa.ForeignKey("explorations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("need", sa.Text, nullable=False),
        sa.Column("way", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "observation_id",
            sa.Uuid,
            sa.ForeignKey("observations.id", ondelete="SET NULL"),
        ),
        sa.Column("part_of_life", sa.Text),
        sa.Column("outcome", sa.Text),
    )
    op.get_bind().execute(
        sa.text("DELETE FROM platform_settings WHERE key IN :keys").bindparams(
            sa.bindparam("keys", expanding=True)
        ),
        {"keys": list(RELOADED_PROMPTS)},
    )


def downgrade() -> None:
    """Remove Explorations, their tries and every aimed Curiosity."""
    op.drop_table("exploration_tries")
    op.execute("DELETE FROM curiosities WHERE aim = 'exploration'")
    op.drop_index("ix_curiosities_source_observation_id", "curiosities")
    op.drop_index("ix_curiosities_exploration_id", "curiosities")
    op.drop_column("curiosities", "source_observation_id")
    op.drop_column("curiosities", "exploration_id")
    op.drop_table("explorations")
