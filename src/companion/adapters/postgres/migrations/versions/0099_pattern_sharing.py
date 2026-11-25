"""Sharing a ready Pattern with the User's quotes and a Prediction.

Adds when a Pattern was first told to its User (`patterns.shared_at`), the
Prediction given with it (`predictions`), how the User took it, read at each
Conversation end (`pattern_reactions`), the User's own switch for noting
evidence on a Pattern they disagreed with (`users.contested_gathering_enabled`,
on to start) and a Check-in Kind that shares a ready Pattern
(`check_in_kinds.shares_pattern`). An existing install gets the new Kind last
in its list, unless a Kind already has its name; a fresh one gets it from the
seed file.
`pattern_tagging_prompt`, `reply_plan_prompt` and `reply_settings_instructions`
reload from the seed on next start, even where an Admin edited them, since
the tagging step now reads reactions, the Reply Plan may share a Pattern and
the reply has a new settings tool. The two sharing numbers come from the
seed on next start. No User data is removed.

Revision ID: 0099
Revises: 0098
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0099"
down_revision: str | None = "0098"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RELOADED_PROMPTS = (
    "pattern_tagging_prompt",
    "reply_plan_prompt",
    "reply_settings_instructions",
)
PATTERN_KIND_NAME = "Something I've noticed"
PATTERN_KIND_DESCRIPTION = (
    "Something Zeph has noticed about you across different parts of your "
    "life, with your own words and one thing to watch for."
)
STATES_FROM_SHARING = ("shared", "contested")


def upgrade() -> None:
    """Add what sharing a Pattern keeps, and the Kind that shares one."""
    op.add_column("patterns", sa.Column("shared_at", sa.DateTime(timezone=True)))
    op.add_column(
        "users",
        sa.Column(
            "contested_gathering_enabled",
            sa.Boolean,
            nullable=False,
            server_default="true",
        ),
    )
    op.create_table(
        "predictions",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "pattern_id",
            sa.Uuid,
            sa.ForeignKey("patterns.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("wording", sa.Text, nullable=False),
        sa.Column("made_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "pattern_reactions",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "pattern_id",
            sa.Uuid,
            sa.ForeignKey("patterns.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("reaction", sa.Text, nullable=False),
        sa.Column(
            "conversation_id",
            sa.Uuid,
            sa.ForeignKey("conversations.id", ondelete="SET NULL"),
        ),
        sa.Column("reacted_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "pattern_id",
            "conversation_id",
            name="uq_pattern_reactions_pattern_id_conversation_id",
        ),
    )
    op.add_column(
        "check_in_kinds",
        sa.Column(
            "shares_pattern",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("check_in_kinds", "shares_pattern", server_default=None)
    op.execute(
        sa.text(
            "INSERT INTO check_in_kinds (id, name, description, sort_order, "
            "sends_shared_photo, raises_curiosity, shares_pattern) "
            "SELECT gen_random_uuid(), :name, :description, "
            "max(sort_order) + 1, false, false, true FROM check_in_kinds "
            "HAVING count(*) > 0 AND NOT bool_or(lower(name) = lower(:name))"
        ).bindparams(name=PATTERN_KIND_NAME, description=PATTERN_KIND_DESCRIPTION)
    )
    op.get_bind().execute(
        sa.text("DELETE FROM platform_settings WHERE key IN :keys").bindparams(
            sa.bindparam("keys", expanding=True)
        ),
        {"keys": list(RELOADED_PROMPTS)},
    )


def downgrade() -> None:
    """Remove what sharing keeps; a shared or contested Pattern is suspected again.

    Past Check-ins of the Kind that shares a Pattern keep no Kind, as when
    an Admin removes one.
    """
    op.get_bind().execute(
        sa.text(
            "UPDATE patterns SET state = 'suspected' WHERE state IN :states"
        ).bindparams(sa.bindparam("states", expanding=True)),
        {"states": list(STATES_FROM_SHARING)},
    )
    op.execute("DELETE FROM check_in_kinds WHERE shares_pattern")
    op.drop_column("check_in_kinds", "shares_pattern")
    op.drop_table("pattern_reactions")
    op.drop_table("predictions")
    op.drop_column("users", "contested_gathering_enabled")
    op.drop_column("patterns", "shared_at")
