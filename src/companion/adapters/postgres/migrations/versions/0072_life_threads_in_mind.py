"""Wide recall: Life Threads stay in mind for the whole Conversation.

Adds the table of Life Threads that came to mind in each Conversation, so
one found by an early message still reaches the Reply Plan later on. It
goes with its Conversation and with its Thread. The most Life Threads per
message is raised from 3 to a high cap; a stored value still at the old
seed reloads from the seed on next start, so an Admin's change stays.

Revision ID: 0072
Revises: 0071
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0072"
down_revision: str | None = "0071"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_LIFE_THREADS_PER_REPLY = 3


def upgrade() -> None:
    """Add the Threads in mind table and reload an old-seed Thread cap."""
    op.create_table(
        "life_threads_in_mind",
        sa.Column(
            "conversation_id",
            sa.Uuid(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "life_thread_id",
            sa.Uuid(),
            sa.ForeignKey("life_threads.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("came_to_mind_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_life_threads_in_mind_life_thread_id",
        "life_threads_in_mind",
        ["life_thread_id"],
    )
    op.get_bind().execute(
        sa.text(
            "DELETE FROM platform_settings WHERE key = 'life_threads_per_reply' "
            "AND value = to_jsonb(CAST(:old AS int))"
        ),
        {"old": OLD_LIFE_THREADS_PER_REPLY},
    )


def downgrade() -> None:
    """Drop the Threads in mind table; the Thread cap stays as it is."""
    op.drop_index(
        "ix_life_threads_in_mind_life_thread_id", table_name="life_threads_in_mind"
    )
    op.drop_table("life_threads_in_mind")
