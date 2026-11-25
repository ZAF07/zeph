"""The ready gate: code decides when a Pattern may be shared.

Adds what the gate keeps on a Pattern (`patterns.blocked_by`, the ready
check that last stopped it; `narrowings`, where a counter-test showed it
doesn't happen; `other_side_asked_at` and `other_side_found_better`), the
check on each logged move to or from ready (`pattern_moves.blocked_by`),
what the tagging step now notes on an Observation (`excluded`,
`ruled_out_topic`, `raised_by_user`) and the exclusions that apply to a
User now (`pattern_exclusion_flags`).
`pattern_tagging_prompt` reloads from the seed on next start, even where an
Admin edited it, since the tagging step now flags exclusions and ruled-out
topics. The bars, the ruled-out topics and the other-side prompt come from
the seed on next start. No User data is removed.

Revision ID: 0096
Revises: 0095
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0096"
down_revision: str | None = "0095"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RELOADED_PROMPTS = ("pattern_tagging_prompt",)


def upgrade() -> None:
    """Add what the ready gate and the tagging step's safety flags keep."""
    op.add_column("patterns", sa.Column("blocked_by", sa.Text))
    op.add_column(
        "patterns",
        sa.Column("narrowings", JSONB, nullable=False, server_default="[]"),
    )
    op.add_column(
        "patterns", sa.Column("other_side_asked_at", sa.DateTime(timezone=True))
    )
    op.add_column("patterns", sa.Column("other_side_found_better", sa.Boolean))
    op.add_column("pattern_moves", sa.Column("blocked_by", sa.Text))
    op.add_column(
        "observations",
        sa.Column("excluded", sa.Boolean, nullable=False, server_default="false"),
    )
    op.add_column("observations", sa.Column("ruled_out_topic", sa.Text))
    op.add_column(
        "observations",
        sa.Column("raised_by_user", sa.Boolean, nullable=False, server_default="false"),
    )
    op.create_table(
        "pattern_exclusion_flags",
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("pattern_type_id", sa.Text, primary_key=True),
        sa.Column("exclusion", sa.Text, primary_key=True),
        sa.Column("evidence", sa.Text, nullable=False),
        sa.Column("flagged_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.get_bind().execute(
        sa.text("DELETE FROM platform_settings WHERE key IN :keys").bindparams(
            sa.bindparam("keys", expanding=True)
        ),
        {"keys": list(RELOADED_PROMPTS)},
    )


def downgrade() -> None:
    """Remove what the ready gate keeps; a ready Pattern is suspected again."""
    op.execute("UPDATE patterns SET state = 'suspected' WHERE state = 'ready'")
    op.drop_table("pattern_exclusion_flags")
    op.drop_column("observations", "raised_by_user")
    op.drop_column("observations", "ruled_out_topic")
    op.drop_column("observations", "excluded")
    op.drop_column("pattern_moves", "blocked_by")
    op.drop_column("patterns", "other_side_found_better")
    op.drop_column("patterns", "other_side_asked_at")
    op.drop_column("patterns", "narrowings")
    op.drop_column("patterns", "blocked_by")
