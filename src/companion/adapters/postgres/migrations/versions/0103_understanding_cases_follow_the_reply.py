"""Three Understanding Eval Cases reload from the seed.

They failed for what the Reply Plan picked while the reply itself was fine
(issue 33). `strong-mood-unknown-cause` no longer expects "ask why" set: its
rule checks the reply asks what is behind the mood. `small-talk-makes-no-move`
becomes `small-talk-stays-light`: a light Move is fine and a rule checks the
reply stays light. `next-move-held-then-made` becomes
`hosting-help-over-two-messages`: Zeph may research at once or hold it. Each
stored case is removed where no Admin edited or archived it; the new ones load
from the seed on next start. Past Case Results keep the case as it was. No
User data is removed.

Revision ID: 0103
Revises: 0102
Create Date: 2026-11-25
"""

from collections.abc import Sequence

from alembic import op

from companion.adapters.postgres.eval_case_reload import reload_eval_case_unless_edited

revision: str = "0103"
down_revision: str | None = "0102"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RELOADED_EVAL_CASES = (
    "strong-mood-unknown-cause",
    "small-talk-makes-no-move",
    "next-move-held-then-made",
)


def upgrade() -> None:
    """Reload the cases where no Admin changed them."""
    for key in RELOADED_EVAL_CASES:
        reload_eval_case_unless_edited(op.get_bind(), key)


def downgrade() -> None:
    """Keep the cases as stored: the earlier seed cases are not brought back."""
