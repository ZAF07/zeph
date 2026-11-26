"""The Eval Case `guess-checked-gently` reloads from the seed.

It expected the reply to lead with Get curious, but code drops a Move that
asks a question when the reply raises a Curiosity, so it could never pass.
The seed case now expects the Curiosity raised. The stored case is removed
where no Admin edited or archived it, and loads from the seed on next
start. Past Case Results keep the case as it was. No User data is removed.

Revision ID: 0102
Revises: 0101
Create Date: 2026-11-25
"""

from collections.abc import Sequence

from alembic import op

from companion.adapters.postgres.eval_case_reload import reload_eval_case_unless_edited

revision: str = "0102"
down_revision: str | None = "0101"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RELOADED_EVAL_CASES = ("guess-checked-gently",)


def upgrade() -> None:
    """Reload the case where no Admin changed it."""
    for key in RELOADED_EVAL_CASES:
        reload_eval_case_unless_edited(op.get_bind(), key)


def downgrade() -> None:
    """Keep the case as stored: the earlier seed case is not brought back."""
