"""Pattern Types: every loaded version of each Pattern Catalog entry (ADR-0025).

Pattern Types are loaded from their YAML files on start, so this only makes
the table. A row is one version and never changes; `is_current` marks the
version in the catalog now.

Revision ID: 0079
Revises: 0078
Create Date: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0079"
down_revision: str | None = "0078"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the Pattern Types table."""
    op.create_table(
        "pattern_types",
        sa.Column("pattern_type_id", sa.Text, primary_key=True),
        sa.Column("version", sa.Text, primary_key=True),
        sa.Column("content", JSONB, nullable=False),
        sa.Column("is_current", sa.Boolean, nullable=False),
        sa.Column("loaded_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Remove the Pattern Types table."""
    op.drop_table("pattern_types")
