"""Zeph doesn't make up details of a replied-to photo it can't see.

When a User replies to an old photo, Zeph gets only its caption. The
response prompt reloads from the seed on next start, even where an Admin
edited it, because the old one never says not to describe a photo it can't
see. No User data is touched.

Revision ID: 0078
Revises: 0077
Create Date: 2026-11-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0078"
down_revision: str | None = "0077"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop the stored response prompt so it reloads from the seed."""
    op.get_bind().execute(
        sa.text("DELETE FROM platform_settings WHERE key = 'response_prompt'")
    )


def downgrade() -> None:
    """Nothing to undo; the response prompt stays as it is."""
