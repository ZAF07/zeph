"""The "look back at a photo" Check-in Kind.

Revision ID: 0020
Revises: 0019
Create Date: 2026-11-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LOOK_BACK_NAME = "A look back at a photo"
LOOK_BACK_DESCRIPTION = "One of the photos you shared, sent back with a word about it."


def upgrade() -> None:
    """Let a Check-in Kind send a Shared Photo, and add the "look back" Kind.

    Each Check-in records the Shared Photo sent with it. An existing install
    gets the new Kind last in its list, unless a Kind already has its name;
    a fresh install has no Kinds yet and gets it from the seed file.
    """
    op.add_column(
        "check_in_kinds",
        sa.Column(
            "sends_shared_photo",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("check_in_kinds", "sends_shared_photo", server_default=None)
    op.add_column(
        "check_ins",
        sa.Column(
            "shared_photo_id",
            sa.Uuid,
            sa.ForeignKey("shared_photos.id", ondelete="SET NULL"),
        ),
    )
    op.execute(
        sa.text(
            "INSERT INTO check_in_kinds (id, name, description, "
            "allowed_without_user_memory, sort_order, sends_shared_photo) "
            "SELECT gen_random_uuid(), :name, :description, false, "
            "max(sort_order) + 1, true FROM check_in_kinds "
            "HAVING count(*) > 0 AND NOT bool_or(lower(name) = lower(:name))"
        ).bindparams(name=LOOK_BACK_NAME, description=LOOK_BACK_DESCRIPTION)
    )


def downgrade() -> None:
    """Remove Kinds that send a Shared Photo and the columns behind them.

    Past Check-ins of those Kinds keep no Kind, as when an Admin removes one.
    """
    op.drop_column("check_ins", "shared_photo_id")
    op.execute("DELETE FROM check_in_kinds WHERE sends_shared_photo")
    op.drop_column("check_in_kinds", "sends_shared_photo")
