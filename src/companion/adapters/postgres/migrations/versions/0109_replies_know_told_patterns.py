"""Replies know the Patterns Zeph told the User, and the gate holds when they ask.

`reply_plan_prompt` reloads from the seed where no Admin edited it: the
Reply Plan now says when the User asks what patterns Zeph sees in them
(`asked_for_patterns`) and may link today's story to a Pattern it told
them (`named_pattern`). An edited prompt is kept and a warning is logged;
until the new text is merged in by hand, those two fields are never
filled, so replies behave as before. No User data is removed.

Revision ID: 0109
Revises: 0108
Create Date: 2026-11-25
"""

from collections.abc import Sequence

from alembic import op

from companion.adapters.postgres.prompt_reload import reload_prompt_unless_edited

revision: str = "0109"
down_revision: str | None = "0108"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PREVIOUS_SEED_HASHES = {
    "reply_plan_prompt": (
        "34f914a00989e6bccf4aa8dfccbe40984bc8ff7b93c8c2c17fe6797a68d10fef"
    ),
}


def upgrade() -> None:
    """Reload the Reply Plan prompt where no Admin edited it."""
    for key, previous_seed_hash in PREVIOUS_SEED_HASHES.items():
        reload_prompt_unless_edited(op.get_bind(), key, previous_seed_hash)


def downgrade() -> None:
    """Keep the prompt as stored: the earlier seed text is not brought back."""
