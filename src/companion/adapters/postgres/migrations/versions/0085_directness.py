"""Directness: how direct each User wants Zeph to be with its Read.

Every User starts on balanced. The Reply Plan prompt and the reply settings
instructions reload from the seed on next start, even where an Admin edited
them, because the old ones know nothing of the setting. No User data is
removed.

Revision ID: 0085
Revises: 0084
Create Date: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0085"
down_revision: str | None = "0084"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RELOADED_PROMPTS = ("reply_plan_prompt", "reply_settings_instructions")


def upgrade() -> None:
    """Add the directness setting to Users and drop the stored prompts."""
    op.add_column(
        "users",
        sa.Column("directness", sa.Text, nullable=False, server_default="balanced"),
    )
    op.get_bind().execute(
        sa.text("DELETE FROM platform_settings WHERE key IN :keys").bindparams(
            sa.bindparam("keys", expanding=True)
        ),
        {"keys": list(RELOADED_PROMPTS)},
    )


def downgrade() -> None:
    """Remove the directness setting."""
    op.drop_column("users", "directness")
