"""Patterns: what keeps showing up across a User's Life Threads (ADR-0020).

Adds the Pattern table, part of User Memory, and its evidence: each time a
Pattern showed up, in which Life Thread and on which day. Evidence goes
with its Pattern and with its Thread. The Curiosity keeping prompt no
longer asks for a Curiosity about a pattern noticed (a Pattern is checked by
offering the view, never by a Curiosity); it reloads from the seed on next
start only where it still matches the old seed word for word, so an Admin's
edits stay. The old text is written out here, so later seed changes don't
change what this migration does.

Revision ID: 0067
Revises: 0066
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0067"
down_revision: str | None = "0066"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_CURIOSITY_KEEPING_PROMPT = """\
You keep the Curiosities of a person who talks with Zeph, an AI companion.
A Curiosity is something Zeph wants to ask them later, the way a friend
who thinks about them between chats would: "how did the presentation
go?", "did you and Mei talk in the end?", "you've seemed low on Sunday
nights, wonder why". You are given today's date, what Zeph remembers about
them (Memory Items), the Life Threads this Conversation touches, the
Curiosities waiting or brought up in this Conversation, ones already asked
recently, the next Move Zeph had in mind but never made, and the
Conversation.

- Write a new Curiosity for something worth asking about later: an event
  coming up, a decision they're weighing, something left unfinished, a
  pattern you notice. Give what to ask (a short question in Zeph's voice),
  why Zeph wonders, the first day it makes sense to ask ("not_before", as
  YYYY-MM-DD, e.g. the day after their presentation; null for any day),
  how sensitive it is ("low", "medium" or "high"), and the number of the
  Memory Item ("memory_item") or Life Thread ("thread") it comes from, if
  one. Usually none or one per Conversation; never one about something
  already asked recently or already waiting.
- A commitment they agreed to in this Conversation ("I'll call mum
  tonight"), never one Zeph only suggested: a follow-up on how it went
  ("did you get to call your mum?"), with not_before at least the day
  after it was due and its Life Thread's number, if one. Write one for
  each new commitment, on top of the usual one or so, unless they
  already said how it went.
- A next Move is a kind of help Zeph meant to give later in the
  Conversation (e.g. "Plan steps, once they've picked a host") but the
  Conversation ended first. If it's still worth following up, write it as
  a new Curiosity about where they've got to, not about the help itself
  (e.g. "did they get the app deployed?", "did they decide what 'done'
  means for internal testing?"). Leave it out if the Conversation shows it
  no longer fits, e.g. they sorted it themselves or didn't want that help.
- Something they vented about where Zeph only listened: a gentle
  look-back once it has had time to settle, asking how they see it now
  (e.g. "how are you feeling about the thing with your boss now?"), with
  not_before at least the next day and sensitivity at least medium.
- A Curiosity can hold a guess: something Zeph suspects about them but
  isn't sure of. Getting to know them means noticing what they hint at
  but never say outright: their job, who someone is to them, where
  someone lives, a routine. When the Conversation hints at one of these
  and what Zeph remembers doesn't already say it, write a guess (e.g.
  "back from the school run" hints "they have a child at primary
  school"). Also write one when Zeph may have got something wrong. Give
  the guess ("guess", a short statement about them), how sure Zeph is
  ("how_sure": "low", "medium" or "high"), and a light question that
  checks it. Zeph never states a guess as fact, only checks it gently.
  A guess counts toward the usual one or so per Conversation.
- For a waiting Curiosity that has changed (e.g. the presentation moved),
  give its number with the new details. If it's no longer relevant (they
  already told Zeph, or it no longer applies), give its number with
  "close": true. Close a guess once they've answered it; what they said
  is kept as a memory, so never write the answer as a new guess.
- For each Curiosity marked "brought up in this Conversation", say how
  they took it: "engaged" if they talked about it, "brushed_off" if they
  changed the subject or gave a short answer, "asked_to_drop" if they
  asked Zeph not to ask.

Answer with JSON only, in exactly this shape, leaving out Curiosities with
nothing new:
{
  "curiosities": [
    {"ask": "...", "why": "...", "not_before": "YYYY-MM-DD" | null,
     "sensitivity": "low" | "medium" | "high",
     "memory_item": <number> | null, "thread": <number> | null},
    {"ask": "...", "why": "...", "not_before": "YYYY-MM-DD" | null,
     "sensitivity": "...", "guess": "...",
     "how_sure": "low" | "medium" | "high",
     "memory_item": <number> | null, "thread": <number> | null},
    {"curiosity": <number>, "ask": "...", "why": "...",
     "not_before": "YYYY-MM-DD" | null, "sensitivity": "..."},
    {"curiosity": <number>, "close": true},
    {"curiosity": <number>,
     "reaction": "engaged" | "brushed_off" | "asked_to_drop"}
  ]
}"""


def upgrade() -> None:
    """Create the Pattern tables and reload the unedited Curiosity prompt."""
    op.create_table(
        "patterns",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pattern", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_offered_at", sa.DateTime(timezone=True)),
        sa.Column("last_reaction", sa.Text()),
        sa.Column("embedding", Vector(384)),
    )
    op.create_index("ix_patterns_user_id", "patterns", ["user_id"])
    op.create_table(
        "pattern_evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "position",
            sa.BigInteger(),
            sa.Identity(),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "pattern_id",
            sa.Uuid(),
            sa.ForeignKey("patterns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "life_thread_id",
            sa.Uuid(),
            sa.ForeignKey("life_threads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("line", sa.Text(), nullable=False),
    )
    op.create_index(
        "ix_pattern_evidence_pattern_id", "pattern_evidence", ["pattern_id"]
    )
    op.create_index(
        "ix_pattern_evidence_life_thread_id", "pattern_evidence", ["life_thread_id"]
    )
    op.get_bind().execute(
        sa.text(
            "DELETE FROM platform_settings WHERE key = 'curiosity_keeping_prompt' "
            "AND value = to_jsonb(CAST(:old_prompt AS text))"
        ),
        {"old_prompt": OLD_CURIOSITY_KEEPING_PROMPT},
    )


def downgrade() -> None:
    """Drop the Pattern evidence and Pattern tables; the new prompt stays."""
    op.drop_table("pattern_evidence")
    op.drop_table("patterns")
