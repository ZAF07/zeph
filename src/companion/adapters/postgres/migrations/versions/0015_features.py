"""Features: each Feature's switch for everyone, starting with Web Search.

Moves the `web_search_enabled` platform setting into the Web Search switch.

Revision ID: 0015
Revises: 0014
Create Date: 2026-11-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the switches for everyone and carry Web Search's setting over.

    An install with no `web_search_enabled` setting yet gets Web Search on.
    Who last saved the setting, and when, becomes the switch's last change.
    """
    op.create_table(
        "feature_switches",
        sa.Column("feature", sa.Text, primary_key=True),
        sa.Column("is_on", sa.Boolean, nullable=False),
        sa.Column(
            "changed_by", sa.Uuid, sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("changed_at", sa.DateTime(timezone=True)),
    )
    op.execute(
        """
        INSERT INTO feature_switches (feature, is_on, changed_by, changed_at)
        SELECT 'web_search',
               COALESCE(
                   (SELECT (value #>> '{}')::boolean FROM platform_settings
                    WHERE key = 'web_search_enabled'),
                   true
               ),
               (SELECT updated_by FROM platform_settings
                WHERE key = 'web_search_enabled'),
               (SELECT updated_at FROM platform_settings
                WHERE key = 'web_search_enabled' AND updated_by IS NOT NULL)
        """
    )
    op.execute("DELETE FROM platform_settings WHERE key = 'web_search_enabled'")


def downgrade() -> None:
    """Put Web Search's switch back as a setting and remove the switches."""
    op.execute(
        """
        INSERT INTO platform_settings (key, value, updated_at, updated_by)
        SELECT 'web_search_enabled',
               to_jsonb(COALESCE(
                   (SELECT is_on FROM feature_switches
                    WHERE feature = 'web_search'),
                   true
               )),
               COALESCE(
                   (SELECT changed_at FROM feature_switches
                    WHERE feature = 'web_search'),
                   now()
               ),
               (SELECT changed_by FROM feature_switches
                WHERE feature = 'web_search')
        ON CONFLICT (key) DO NOTHING
        """
    )
    op.drop_table("feature_switches")
