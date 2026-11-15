"""The "Get it done" Need, for when the User asks Zeph to do something.

Without it, "please delete all my data" or "forget what I told you" fit no
Need, so the fallback "Ask more" made the reply ask first instead of
calling the tool.

Revision ID: 0040
Revises: 0039
Create Date: 2026-11-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0040"
down_revision: str | None = "0039"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

GET_IT_DONE_NAME = "Get it done"
GET_IT_DONE_WHEN_IT_FITS = (
    "They ask Zeph to do something it can do for them: change a setting, turn "
    "something on or off, forget something, or delete their data."
)
GET_IT_DONE_HOW_TO_REPLY = (
    "Do it now with the right tool, then say plainly what you did. Don't ask "
    "them to confirm or explain first: a tool that needs confirming asks for it "
    "itself. Ask only if you truly can't tell what they want changed. Do only "
    "what they asked: if Zeph can't do it, say where they can, and never do "
    "something else in its place."
)
NO_NEED_HAS_THE_NAME = (
    "NOT EXISTS (SELECT 1 FROM needs WHERE lower(name) = lower(:name))"
)


def upgrade() -> None:
    """Add "Get it done" just before the fallback Need.

    An existing install gets it unless a Need already has its name; a fresh
    install has no Needs yet and gets it from the seed file.
    """
    op.execute(
        sa.text(
            "UPDATE needs SET sort_order = sort_order + 1 WHERE sort_order >= "
            "(SELECT sort_order FROM needs WHERE is_fallback) "
            f"AND {NO_NEED_HAS_THE_NAME}"
        ).bindparams(name=GET_IT_DONE_NAME)
    )
    op.execute(
        sa.text(
            "INSERT INTO needs (id, name, when_it_fits, how_to_reply, sort_order, "
            "is_fallback) SELECT gen_random_uuid(), :name, :when_it_fits, "
            ":how_to_reply, sort_order - 1, false FROM needs "
            f"WHERE is_fallback AND {NO_NEED_HAS_THE_NAME}"
        ).bindparams(
            name=GET_IT_DONE_NAME,
            when_it_fits=GET_IT_DONE_WHEN_IT_FITS,
            how_to_reply=GET_IT_DONE_HOW_TO_REPLY,
        )
    )


def downgrade() -> None:
    """Remove "Get it done"."""
    op.execute(
        sa.text("DELETE FROM needs WHERE name = :name").bindparams(
            name=GET_IT_DONE_NAME
        )
    )
