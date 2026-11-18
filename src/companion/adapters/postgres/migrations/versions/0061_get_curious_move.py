"""The Get curious Move, and the line between venting and a passing update.

Adds Get curious, asking a question, last in the order, when the platform
has Moves but none called Get curious, ignoring case; a fresh install gets
it when the seed loads. Ask more and Get it done rule it out, if they still
exist. Be heard and Just chatting get their new "when it fits" only where it
still matches the old seed word for word, so an Admin's edits stay. The rows
are written out here, so later seed changes don't change what this migration
does.

Revision ID: 0061
Revises: 0060
Create Date: 2026-11-18
"""

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "0061"
down_revision: str | None = "0060"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

GET_CURIOUS = {
    "name": "Get curious",
    "when_it_fits": (
        "They mention something about their life, like plans, people, sleep, "
        "routines or work, that you know little about, only half know, or "
        "aren't sure you have right."
    ),
    "how_to_do_it": (
        "Ask one short, light question about something they just said, the "
        "way a curious friend would. Prefer what you don't know about them "
        "yet, or a guess you hold. Checking something you think you know is "
        "fine when you aren't sure. It can be practical and kind (\"you a "
        'coffee person?"), but never a quiz. If they give a short answer, let '
        "it go."
    ),
}
RULED_OUT_BY = ("Ask more", "Get it done")
NEW_WHEN_IT_FITS = {
    "Be heard": {
        "old": (
            "They are venting or sharing something painful or frustrating, and "
            "want it to land with someone, not to be fixed, and it isn't mainly "
            "about one of their Goals. A slip on a Goal mentioned beside real "
            "pain (say, their mum in hospital) is still Be heard."
        ),
        "new": (
            "They're letting out something painful or frustrating, staying on "
            "it or coming back to it, often with strong words, and want it to "
            "land with someone, not to be fixed, and it isn't mainly about one "
            "of their Goals. A hard thing mentioned in passing (tired, busy "
            "day, a small annoyance) is not this: that's an update. A slip on a"
            " Goal mentioned beside real pain (say, their mum in hospital) is "
            "still Be heard."
        ),
    },
    "Just chatting": {
        "old": (
            "Small talk, banter, a greeting, a passing update or something fun,"
            " with nothing heavy underneath."
        ),
        "new": (
            "Small talk, banter, a greeting, a passing update or something fun,"
            " with nothing heavy underneath, including passing mentions of "
            "everyday hard things, like poor sleep or a long day."
        ),
    },
}


def upgrade() -> None:
    """Add Get curious with its rule-outs, and draw the venting line."""
    connection = op.get_bind()
    has_moves = connection.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM moves)")
    ).scalar()
    has_get_curious = connection.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM moves WHERE lower(name) = :name)"),
        {"name": GET_CURIOUS["name"].lower()},
    ).scalar()
    if has_moves and not has_get_curious:
        add_get_curious(connection)
    for name, wording in NEW_WHEN_IT_FITS.items():
        connection.execute(
            sa.text(
                "UPDATE needs SET when_it_fits = :new "
                "WHERE lower(name) = lower(:name) AND when_it_fits = :old"
            ),
            {**wording, "name": name},
        )


def add_get_curious(connection: sa.Connection) -> None:
    """Add Get curious last in the order, and rule it out where it never fits.

    A Need is matched by name, ignoring case; one that no longer exists is
    skipped.

    Args:
        connection: The migration's connection.
    """
    move_id = uuid4()
    connection.execute(
        sa.text(
            "INSERT INTO moves (id, name, when_it_fits, how_to_do_it, sort_order, "
            "asks_a_question) SELECT :id, :name, :when_it_fits, :how_to_do_it, "
            "max(sort_order) + 1, true FROM moves"
        ),
        {**GET_CURIOUS, "id": move_id},
    )
    for need_name in RULED_OUT_BY:
        connection.execute(
            sa.text(
                "INSERT INTO need_ruled_out_moves (need_id, move_id) "
                "SELECT id, :move_id FROM needs WHERE lower(name) = lower(:name)"
            ),
            {"move_id": move_id, "name": need_name},
        )


def downgrade() -> None:
    """Leave Get curious and the new wording in place."""
