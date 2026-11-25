"""The Whole-pipeline Eval Case `cannot-stand-waiting` reloads from the seed.

Its first real run stopped at "score" for reasons in its script (issue 32):
the strongest sign was told as an opinion, not a story, and the person in
its "it doesn't happen with…" story had no relationship named. The stored
case is removed where no Admin edited or archived it; the corrected one
loads from the seed on next start. Past Case Results keep the case as it
was. No User data is removed.

Revision ID: 0104
Revises: 0103
Create Date: 2026-11-25
"""

from collections.abc import Sequence

from alembic import op

from companion.adapters.postgres.eval_case_reload import reload_eval_case_unless_edited

revision: str = "0104"
down_revision: str | None = "0103"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RELOADED_EVAL_CASES = ("cannot-stand-waiting",)


def upgrade() -> None:
    """Reload the case where no Admin changed it."""
    for key in RELOADED_EVAL_CASES:
        reload_eval_case_unless_edited(op.get_bind(), key)


def downgrade() -> None:
    """Keep the case as stored: the earlier seed case is not brought back."""
