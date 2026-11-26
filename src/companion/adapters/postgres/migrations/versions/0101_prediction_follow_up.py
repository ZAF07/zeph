"""Following up a Prediction, and confirming or closing a shared Pattern.

Adds how a Prediction went (`predictions.outcome`, `outcome_at`), the
Curiosity code writes to ask about one or to give a new one
(`curiosities.pattern_id`, `prediction_id`, and `not_after`, the last day a
Curiosity may be asked) and why a shared Pattern was confirmed or closed
(`pattern_moves.reason`). `pattern_tagging_prompt` reloads from the seed on
next start, even where an Admin edited it, since the tagging step now reads
how a Prediction went. The four new numbers come from the seed on next
start. No User data is removed.

Revision ID: 0101
Revises: 0100
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0101"
down_revision: str | None = "0100"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RELOADED_PROMPTS = ("pattern_tagging_prompt",)


def upgrade() -> None:
    """Add what following up a Prediction keeps."""
    op.add_column("predictions", sa.Column("outcome", sa.Text))
    op.add_column("predictions", sa.Column("outcome_at", sa.DateTime(timezone=True)))
    op.add_column("curiosities", sa.Column("not_after", sa.Date))
    op.add_column(
        "curiosities",
        sa.Column(
            "pattern_id",
            sa.Uuid,
            sa.ForeignKey("patterns.id", ondelete="CASCADE"),
            index=True,
        ),
    )
    op.add_column(
        "curiosities",
        sa.Column(
            "prediction_id",
            sa.Uuid,
            sa.ForeignKey("predictions.id", ondelete="CASCADE"),
            index=True,
        ),
    )
    op.add_column("pattern_moves", sa.Column("reason", sa.Text))
    op.get_bind().execute(
        sa.text("DELETE FROM platform_settings WHERE key IN :keys").bindparams(
            sa.bindparam("keys", expanding=True)
        ),
        {"keys": list(RELOADED_PROMPTS)},
    )


def downgrade() -> None:
    """Remove what following up keeps; a confirmed Pattern is shared again.

    A Pattern closed after it was shared stays closed. The Curiosities
    about Predictions are deleted.
    """
    op.execute(
        "UPDATE patterns SET state = 'shared' "
        "WHERE state = 'confirmed' AND pattern_type_id IS NOT NULL"
    )
    op.execute("DELETE FROM curiosities WHERE aim = 'prediction'")
    op.drop_column("pattern_moves", "reason")
    op.drop_column("curiosities", "prediction_id")
    op.drop_column("curiosities", "pattern_id")
    op.drop_column("curiosities", "not_after")
    op.drop_column("predictions", "outcome_at")
    op.drop_column("predictions", "outcome")
