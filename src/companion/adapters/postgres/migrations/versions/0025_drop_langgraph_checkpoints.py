"""Replies run in plain core code: drop LangGraph's checkpoint tables (ADR-0009).

Revision ID: 0025
Revises: 0024
Create Date: 2026-11-14
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CHECKPOINT_TABLES = (
    "checkpoint_writes",
    "checkpoint_blobs",
    "checkpoints",
    "checkpoint_migrations",
)


def upgrade() -> None:
    """Drop the tables LangGraph's Postgres checkpointer made for itself.

    The checkpointer made them outside Alembic, so a database may not have
    them; nothing in them is needed, as each held one message's steps only.
    """
    for table in CHECKPOINT_TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table}")


def downgrade() -> None:
    """Nothing to recreate: the checkpointer made its own tables when it ran."""
