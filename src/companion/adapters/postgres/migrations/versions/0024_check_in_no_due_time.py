"""No Check-in due time means not due: give Users with Check-ins on a due time.

Revision ID: 0024
Revises: 0023
Create Date: 2026-11-14
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Make Users with Check-ins on but no next due time due now.

    No due time used to mean "due now"; it now means "not due until they
    resume or connect Telegram", so these Users keep being due.
    """
    op.execute(
        "UPDATE users SET check_in_next_due_at = now() "
        "WHERE check_ins_enabled AND check_in_next_due_at IS NULL"
    )


def downgrade() -> None:
    """Nothing to undo: a due time of now is due under both meanings."""
