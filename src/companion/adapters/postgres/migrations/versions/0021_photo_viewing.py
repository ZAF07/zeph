"""Photo Viewing: the User's own switch for whether the Companion looks at photos.

Revision ID: 0021
Revises: 0020
Create Date: 2026-11-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the User's Photo Viewing switch, on for everyone.

    The stored reply settings instructions don't mention Photo Viewing, so
    the old row is removed and the new seed value loads on the next start.
    """
    op.add_column(
        "users",
        sa.Column(
            "photo_viewing_enabled",
            sa.Boolean,
            nullable=False,
            server_default="true",
        ),
    )
    op.execute(
        "DELETE FROM platform_settings WHERE key = 'reply_settings_instructions'"
    )


def downgrade() -> None:
    """Remove the Photo Viewing switch and reload the old settings instructions."""
    op.execute(
        "DELETE FROM platform_settings WHERE key = 'reply_settings_instructions'"
    )
    op.drop_column("users", "photo_viewing_enabled")
