"""The Reply Plan forms a Read from the Persona's Outlook.

The Read, whether to say it and where the Conversation is now are saved in
each Reply Plan's form, and the Model Call Log's Reply Plan shape records
whether a Read was formed and said; both are JSON, so no column changes.
The Reply Plan prompt reloads from the seed on next start, even where an
Admin edited it, because the old one never asks for a Read. The Outlook is a
new setting, so the seed adds it on next start.

Revision ID: 0068
Revises: 0067
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0068"
down_revision: str | None = "0067"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop the stored Reply Plan prompt so the seed's new one loads."""
    op.get_bind().execute(
        sa.text("DELETE FROM platform_settings WHERE key = 'reply_plan_prompt'")
    )


def downgrade() -> None:
    """Leave the prompt and the Outlook as they are; nothing else changed."""
