"""What a User deleted or was told stays that way.

Adds `patterns_never_again`: a mark per User and Pattern Type, with none
of their words, kept when they delete a Pattern they disagreed with or
that didn't hold up, so it is never noted or shared for them again. Adds
`patterns.shared_wording`: the approved wording a Pattern was told in, so
the User keeps seeing those words and can still see and delete a Pattern
whose Pattern Type left the catalog. The ruled-out topics list reloads
from the seed where it still equals the first seed list; an Admin's list
is kept. No User data is removed.

Revision ID: 0107
Revises: 0106
Create Date: 2026-11-25
"""

import json
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0107"
down_revision: str | None = "0106"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FIRST_RULED_OUT_TOPICS = (
    "abuse",
    "sexual trauma",
    "self-harm or suicide",
    "eating and body image",
)


def upgrade() -> None:
    """Add the mark and the wording, and reload an unedited topics list."""
    op.create_table(
        "patterns_never_again",
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("pattern_type_id", sa.Text, primary_key=True),
        sa.Column("marked_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.add_column("patterns", sa.Column("shared_wording", sa.Text))
    op.get_bind().execute(
        sa.text(
            "DELETE FROM platform_settings WHERE key = 'pattern_ruled_out_topics' "
            "AND value = CAST(:first_list AS jsonb)"
        ),
        {"first_list": json.dumps(list(FIRST_RULED_OUT_TOPICS))},
    )


def downgrade() -> None:
    """Remove the mark and the wording; the topics list stays as stored."""
    op.drop_column("patterns", "shared_wording")
    op.drop_table("patterns_never_again")
