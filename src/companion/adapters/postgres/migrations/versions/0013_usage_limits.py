"""Usage limits: messages, chat model tokens and limits hit per User per day.

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add message and token counts, and limits hit, to daily usage."""
    op.add_column(
        "daily_usage",
        sa.Column("message_count", sa.Integer, nullable=False, server_default="0"),
    )
    op.add_column(
        "daily_usage",
        sa.Column("tokens_in", sa.BigInteger, nullable=False, server_default="0"),
    )
    op.add_column(
        "daily_usage",
        sa.Column("tokens_out", sa.BigInteger, nullable=False, server_default="0"),
    )
    for column in ("message_limit_reached", "web_search_limit_reached"):
        op.add_column(
            "daily_usage",
            sa.Column(column, sa.Boolean, nullable=False, server_default="false"),
        )


def downgrade() -> None:
    """Remove message and token counts, and limits hit, from daily usage."""
    op.drop_column("daily_usage", "web_search_limit_reached")
    op.drop_column("daily_usage", "message_limit_reached")
    op.drop_column("daily_usage", "tokens_out")
    op.drop_column("daily_usage", "tokens_in")
    op.drop_column("daily_usage", "message_count")
