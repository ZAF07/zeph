"""The "something I've been wondering" Check-in Kind.

Revision ID: 0034
Revises: 0033
Create Date: 2026-11-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0034"
down_revision: str | None = "0033"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

WONDERING_NAME = "Something I've been wondering"
WONDERING_DESCRIPTION = (
    "A question about something you mentioned, asked when the time is right."
)


def upgrade() -> None:
    """Let a Check-in Kind ask a Curiosity, and add the "wondering" Kind.

    Each Check-in records the Curiosity it asked. An existing install gets
    the new Kind last in its list, unless a Kind already has its name; a
    fresh install has no Kinds yet and gets it from the seed file.
    """
    op.add_column(
        "check_in_kinds",
        sa.Column(
            "raises_curiosity",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("check_in_kinds", "raises_curiosity", server_default=None)
    op.add_column(
        "check_ins",
        sa.Column(
            "curiosity_id",
            sa.Uuid,
            sa.ForeignKey("curiosities.id", ondelete="SET NULL"),
        ),
    )
    op.execute(
        sa.text(
            "INSERT INTO check_in_kinds (id, name, description, sort_order, "
            "sends_shared_photo, raises_curiosity) "
            "SELECT gen_random_uuid(), :name, :description, "
            "max(sort_order) + 1, false, true FROM check_in_kinds "
            "HAVING count(*) > 0 AND NOT bool_or(lower(name) = lower(:name))"
        ).bindparams(name=WONDERING_NAME, description=WONDERING_DESCRIPTION)
    )


def downgrade() -> None:
    """Remove Kinds that ask a Curiosity and the columns behind them.

    Past Check-ins of those Kinds keep no Kind, as when an Admin removes one.
    """
    op.drop_column("check_ins", "curiosity_id")
    op.execute("DELETE FROM check_in_kinds WHERE raises_curiosity")
    op.drop_column("check_in_kinds", "raises_curiosity")
