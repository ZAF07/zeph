"""When a User agreed with a Pattern, for the Memories page's Patterns tab.

Adds `patterns.confirmed_at`: when a Pattern became confirmed. The last
time a view was offered isn't enough, since a confirmed Pattern can be
offered again. Confirmed Patterns already kept take their last offered time,
which is when they were confirmed (or when they last changed, if none). The
User Portrait prompt now names the Patterns the User agreed with, and the
Memories hero line names the patterns Zeph has noticed: each reloads from the
seed on next start only where it still matches the old seed word for word, so
an Admin's edits stay. The old texts are written out here, so later seed
changes don't change what this migration does.

Revision ID: 0069
Revises: 0068
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0069"
down_revision: str | None = "0068"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_PORTRAIT_PROMPT = """\
You write the User Portrait of a person who talks with Zeph, an AI
companion: a short, living picture of them that Zeph reads before every
reply, so it talks to them like a friend who knows them well. You are
given today's date, what Zeph remembers about them (by Memory Category),
the Life Threads (ongoing stories in their life), what has helped and
what hasn't (Move Outcomes: how each kind of help Zeph gave went, in what
situation and mood) and their most recent Conversations, newest first.

Write about "they", in plain warm sentences, in a few short paragraphs:
- Who they are: their life, work, people who matter, what they care about.
- What's going on in their life now.
- Themes they keep coming back to, and patterns (e.g. "low on Sunday
  nights").
- What has helped them and what hasn't, and in what moods (e.g. "a firm
  push helps when they're frustrated, not when they're exhausted; walks
  help"). Draw on the Move Outcomes, and say a pattern only when they
  show one.
- Where they stand on their Goals.
Write only what Zeph is fairly sure of; leave out what it only suspects.
Use only what you are given. Don't guess, diagnose or judge. Leave out
anything they would not want said back to them. At most about 250 words.
Answer with the Portrait only, no heading."""

OLD_MEMORIES_HERO_LEAD = (
    "What Zeph remembers, what it knows about you, what's going on in your "
    "life, what helps you, short summaries of past Conversations and the "
    "photos it kept. Delete anything you'd rather it forgot."
)


def upgrade() -> None:
    """Add when each Pattern was confirmed and reload the unedited texts."""
    op.add_column("patterns", sa.Column("confirmed_at", sa.DateTime(timezone=True)))
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "UPDATE patterns SET confirmed_at = COALESCE(last_offered_at, updated_at) "
            "WHERE state = 'confirmed'"
        )
    )
    connection.execute(
        sa.text(
            "DELETE FROM platform_settings WHERE key = 'portrait_prompt' "
            "AND value = to_jsonb(CAST(:old_prompt AS text))"
        ),
        {"old_prompt": OLD_PORTRAIT_PROMPT},
    )
    connection.execute(
        sa.text(
            "DELETE FROM copy_slots WHERE key = 'memories.hero.lead' "
            "AND text = :old_lead"
        ),
        {"old_lead": OLD_MEMORIES_HERO_LEAD},
    )


def downgrade() -> None:
    """Drop when each Pattern was confirmed; reloaded texts stay as they are."""
    op.drop_column("patterns", "confirmed_at")
