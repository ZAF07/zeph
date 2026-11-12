"""Knowledge: each document keeps the text read from its file.

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add a document's text and whether an Admin edited it."""
    op.add_column("knowledge_documents", sa.Column("text", sa.Text))
    op.add_column(
        "knowledge_documents",
        sa.Column("text_edited", sa.Boolean, nullable=False, server_default="false"),
    )


def downgrade() -> None:
    """Drop a document's text and edited flag."""
    op.drop_column("knowledge_documents", "text_edited")
    op.drop_column("knowledge_documents", "text")
