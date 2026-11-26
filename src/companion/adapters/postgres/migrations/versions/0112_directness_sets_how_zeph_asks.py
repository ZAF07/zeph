"""The directness setting also sets how Zeph asks.

The Account page's help text for "How direct Zeph is" and
`reply_settings_instructions` now say the setting also changes how Zeph
asks. Each reloads from the seed only where no Admin edited it: the Copy
slot is removed when it still holds the text being replaced, and the
prompt goes through `reload_prompt_unless_edited`, which logs a warning
when it keeps an edit. The six new numbers (wait, tries before resting and
replies between Curiosities, for gentle and for direct) load from the seed
by themselves. No User data is removed.

Revision ID: 0112
Revises: 0111
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from companion.adapters.postgres.prompt_reload import reload_prompt_unless_edited

revision: str = "0112"
down_revision: str | None = "0111"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PREVIOUS_SEED_HASHES = {
    "reply_settings_instructions": (
        "0d1a1572995b68388379f2d41a8744c53a83b4318f6c5e50ca5eb153c8e5d067"
    ),
}
PREVIOUS_DIRECTNESS_HELP = (
    "How soon and how plainly Zeph tells you what it thinks is really going on. "
    "Whatever you pick, Zeph gives its view when you ask, and takes extra care "
    "when things are hard."
)


def upgrade() -> None:
    """Reload the help text and the settings instructions where not edited."""
    for key, previous_seed_hash in PREVIOUS_SEED_HASHES.items():
        reload_prompt_unless_edited(op.get_bind(), key, previous_seed_hash)
    op.get_bind().execute(
        sa.text(
            "DELETE FROM copy_slots WHERE key = 'account.directness.help' "
            "AND text = :previous_help"
        ),
        {"previous_help": PREVIOUS_DIRECTNESS_HELP},
    )


def downgrade() -> None:
    """Keep the texts as stored: the earlier seed texts are not brought back."""
