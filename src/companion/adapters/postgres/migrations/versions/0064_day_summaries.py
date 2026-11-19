"""Day Summaries: one Summary per User per day, in their time zone.

Conversation Summaries become Day Summaries, kept by User and day instead of
by Conversation. Existing Summaries from the same day (the day their
Conversation started, in the User's time zone, or the day they were written
when the Conversation is gone) are joined into one without a model rewrite:
their texts in the order written, their moods as an arc, what was offered,
and the average of their embeddings. The memory processing prompt reloads
from the seed on next start, so it writes the day's Summary from all of the
day's messages.

Revision ID: 0064
Revises: 0063
Create Date: 2026-11-19
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0064"
down_revision: str | None = "0063"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JOIN_SAME_DAY_SUMMARIES = """
WITH dated AS (
    SELECT
        summaries.*,
        (COALESCE(conversations.started_at, summaries.created_at)
            AT TIME ZONE COALESCE(users.time_zone, 'UTC'))::date AS day
    FROM conversation_summaries AS summaries
    JOIN users ON users.id = summaries.user_id
    LEFT JOIN conversations ON conversations.id = summaries.conversation_id
)
INSERT INTO day_summaries (id, user_id, day, summary, mood, written_at,
                           embedding, offered)
SELECT
    (array_agg(id ORDER BY created_at))[1],
    user_id,
    day,
    string_agg(summary, ' ' ORDER BY created_at),
    string_agg(mood, ', then ' ORDER BY created_at),
    max(created_at),
    avg(embedding),
    COALESCE(string_agg(NULLIF(offered, ''), ' ' ORDER BY created_at), '')
FROM dated
GROUP BY user_id, day
"""


def upgrade() -> None:
    """Make Day Summaries, join same-day Summaries into them, reload the prompt."""
    op.execute(
        """
        CREATE TABLE day_summaries (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
            day DATE NOT NULL,
            summary TEXT NOT NULL,
            mood TEXT NOT NULL,
            written_at TIMESTAMPTZ NOT NULL,
            embedding vector(384),
            offered TEXT NOT NULL DEFAULT '',
            UNIQUE (user_id, day)
        )
        """
    )
    op.create_index("ix_day_summaries_user_id", "day_summaries", ["user_id"])
    op.execute(JOIN_SAME_DAY_SUMMARIES)
    op.drop_table("conversation_summaries")
    op.execute("DELETE FROM platform_settings WHERE key = 'memory_processing_prompt'")


def downgrade() -> None:
    """Bring back per-Conversation Summaries, one per Day Summary, unlinked."""
    op.execute(
        """
        CREATE TABLE conversation_summaries (
            id UUID PRIMARY KEY,
            conversation_id UUID UNIQUE
                REFERENCES conversations (id) ON DELETE SET NULL,
            user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
            summary TEXT NOT NULL,
            mood TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            embedding vector(384),
            offered TEXT NOT NULL DEFAULT ''
        )
        """
    )
    op.create_index(
        "ix_conversation_summaries_user_id", "conversation_summaries", ["user_id"]
    )
    op.execute(
        "INSERT INTO conversation_summaries "
        "(id, user_id, summary, mood, created_at, embedding, offered) "
        "SELECT id, user_id, summary, mood, written_at, embedding, offered "
        "FROM day_summaries"
    )
    op.drop_table("day_summaries")
    op.execute("DELETE FROM platform_settings WHERE key = 'memory_processing_prompt'")
