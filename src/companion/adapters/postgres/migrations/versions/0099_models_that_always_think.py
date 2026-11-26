"""Name the models that always think.

Claude Sonnet 5.5, Opus 5.5 and Fable 5.2 (OpenRouter names) are saved as
the Platform Setting `models_that_always_think`. Their thinking switch is
then on and locked, and their calls are never told thinking is off. A list
already saved is kept as it is. No other setting is touched.

Revision ID: 0099
Revises: 0098
Create Date: 2026-11-25
"""

import json
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0099"
down_revision: str | None = "0098"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MODELS_THAT_ALWAYS_THINK = [
    "anthropic/claude-sonnet-5.5",
    "anthropic/claude-opus-5.5",
    "anthropic/claude-fable-5.2",
]


def upgrade() -> None:
    """Save the list of models that always think, unless one is saved."""
    op.get_bind().execute(
        sa.text(
            "INSERT INTO platform_settings (key, value, updated_at) "
            "VALUES ('models_that_always_think', CAST(:value AS jsonb), now()) "
            "ON CONFLICT (key) DO NOTHING"
        ),
        {"value": json.dumps(MODELS_THAT_ALWAYS_THINK)},
    )


def downgrade() -> None:
    """Remove the list of models that always think."""
    op.execute("DELETE FROM platform_settings WHERE key = 'models_that_always_think'")
