"""A story that settles a Prediction counts once.

Adds `predictions.outcome_conversation_id`: the Conversation the User said
how a Prediction went in. That Conversation's Observations of the same
Pattern Type then count nothing for the Pattern, so one event never moves
it twice. The two new numbers (`predictions_to_close`,
`predictions_unanswered_to_stop`) come from the seed on next start. No
User data is removed.

Revision ID: 0106
Revises: 0105
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0106"
down_revision: str | None = "0105"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add where a Prediction's outcome was said."""
    op.add_column(
        "predictions",
        sa.Column(
            "outcome_conversation_id",
            sa.Uuid,
            sa.ForeignKey("conversations.id", ondelete="SET NULL"),
        ),
    )


def downgrade() -> None:
    """Remove it; a story that settles a Prediction counts twice again."""
    op.drop_column("predictions", "outcome_conversation_id")
