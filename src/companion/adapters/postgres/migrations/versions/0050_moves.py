"""Moves: what the Companion does to help, apart from the Need (ADR-0016).

Adds Moves, the Moves each Need rules out, and the lead and supporting Moves
each Understanding picked. An existing install gets the starter Moves and
rule-outs when it has Needs but no Moves; a fresh install has no Needs yet
and gets them when the seed loads. The starter Needs whose "how to reply"
now sets only the stance get the new wording, and the Persona, Understanding
prompt and web search wording reload from the seed on next start. The
starter rows are written out here, as they were when Moves came in, so later
seed changes don't change what this migration does.

Revision ID: 0050
Revises: 0049
Create Date: 2026-11-17
"""

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "0050"
down_revision: str | None = "0049"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STARTER_MOVES = (
    {
        "name": "Calm",
        "when_it_fits": (
            "They are anxious, panicky or overwhelmed, and need to settle "
            "before anything else can help."
        ),
        "how_to_do_it": (
            "Slow things down. Keep it short and steady, name that it's a lot, "
            "and offer one small thing to settle, like a slow breath or putting"
            " the phone down for a minute. No plans or fixes yet."
        ),
    },
    {
        "name": "Ground",
        "when_it_fits": (
            "They are spiralling into what-ifs or the worst case, and losing "
            "hold of what is real and in their control."
        ),
        "how_to_do_it": (
            "Bring them back to what is true right now and what is in their "
            "hands. Gently separate what has happened from what they fear "
            "might, and name one thing they can do or let go of today."
        ),
    },
    {
        "name": "Reframe",
        "when_it_fits": (
            'A belief or story is holding them back ("I always mess up", "it\'s '
            'too late for me"), and they are steady enough to look at it.'
        ),
        "how_to_do_it": (
            "Offer a different, honest angle on it, in a sentence or two, as "
            "your own view, not a correction. Use what you know about them as "
            "evidence. Don't argue if they push back; leave it with them."
        ),
    },
    {
        "name": "Mirror",
        "when_it_fits": (
            "You can see a pattern in what they say or have said before that "
            "they may not have noticed, and pointing it out would help them see"
            " themselves."
        ),
        "how_to_do_it": (
            'Name the pattern plainly and kindly, with what you noticed ("this '
            "is the third time you've said you're fine right after a call with "
            'your dad"), then let them make of it what they will.'
        ),
    },
    {
        "name": "Suggest",
        "when_it_fits": (
            "They are stuck on a choice or problem and a concrete idea, option "
            "or your real view would move them forward, even if they didn't ask"
            " for it outright."
        ),
        "how_to_do_it": (
            "Say what you'd do and why, or give two or three concrete options "
            "with a clear lean, plainly and briefly. Fit it to what you know of"
            " their situation, and don't hedge it into nothing."
        ),
    },
    {
        "name": "Plan steps",
        "when_it_fits": (
            "They have a goal or task that feels big or keeps growing, with no "
            "clear next step or finish line."
        ),
        "how_to_do_it": (
            "Break it into a few small next steps, the first one doable today, "
            'and agree on what "done" looks like so it stops growing. Keep it '
            "short enough to text."
        ),
    },
    {
        "name": "Push",
        "when_it_fits": (
            "They are avoiding, stalling or making excuses about something they"
            " said they want, and are steady enough to be challenged."
        ),
        "how_to_do_it": (
            "Hold them to what they said they wanted, kindly but directly. Name"
            " the excuse or the stall, ask for a specific commitment (what, by "
            "when), and don't let a vague answer slide."
        ),
    },
    {
        "name": "Research",
        "when_it_fits": (
            "They need practical options or facts found and compared for them, "
            "like products, services, places or prices, and doing the legwork "
            "would help more than another question."
        ),
        "how_to_do_it": (
            "Do the legwork: look up real options with your web tools, compare "
            "them against what they need (budget, must-haves, where they are), "
            "and name the best few with what sets each apart and where you "
            "found it. If you can't look things up, say so plainly and suggest "
            "from what you know."
        ),
    },
)
STARTER_RULE_OUTS = {
    "Be heard": ("Reframe", "Suggest", "Plan steps", "Push", "Research"),
    "Think it through": ("Suggest", "Research"),
    "Get it done": (
        "Calm",
        "Ground",
        "Reframe",
        "Mirror",
        "Suggest",
        "Plan steps",
        "Push",
        "Research",
    ),
    "Ask more": (
        "Calm",
        "Ground",
        "Reframe",
        "Mirror",
        "Suggest",
        "Plan steps",
        "Push",
        "Research",
    ),
    "Just chatting": ("Calm", "Ground", "Reframe", "Mirror", "Plan steps", "Push"),
}
NEW_HOW_TO_REPLY = {
    "Advice": (
        "Be the wise friend they asked: direct, honest and brief. Say what "
        "you really think, even if it isn't what they hope to hear, and "
        "check it fits their situation rather than piling on options."
    ),
    "Accountability": (
        "Be on their side and on the side of what they said they want, "
        "kindly but honestly. Name the progress or the slip without "
        "lecturing, and remind them why it matters to them. Help them move "
        "it forward, rather than only asking what's next."
    ),
}
RELOADED_SETTINGS = (
    "persona",
    "understanding_prompt",
    "web_search_tool_description",
    "reply_web_search_instructions",
)


def upgrade() -> None:
    """Add Moves and rule-outs, and bring in the new wording."""
    op.create_table(
        "moves",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("when_it_fits", sa.Text, nullable=False),
        sa.Column("how_to_do_it", sa.Text, nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False),
    )
    op.create_index(
        "moves_name_ignoring_case", "moves", [sa.text("lower(name)")], unique=True
    )
    op.create_table(
        "need_ruled_out_moves",
        sa.Column(
            "need_id",
            sa.Uuid,
            sa.ForeignKey("needs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "move_id",
            sa.Uuid,
            sa.ForeignKey("moves.id", ondelete="CASCADE"),
            primary_key=True,
            index=True,
        ),
    )
    op.add_column("understandings", sa.Column("lead_move", sa.Text))
    op.add_column("understandings", sa.Column("support_move", sa.Text))
    connection = op.get_bind()
    if connection.execute(sa.text("SELECT EXISTS (SELECT 1 FROM needs)")).scalar():
        add_starter_moves(connection)
    for name, how_to_reply in NEW_HOW_TO_REPLY.items():
        connection.execute(
            sa.text(
                "UPDATE needs SET how_to_reply = :how_to_reply "
                "WHERE lower(name) = lower(:name)"
            ),
            {"how_to_reply": how_to_reply, "name": name},
        )
    connection.execute(
        sa.text("DELETE FROM platform_settings WHERE key = ANY(:keys)"),
        {"keys": list(RELOADED_SETTINGS)},
    )


def add_starter_moves(connection: sa.Connection) -> None:
    """Add the starter Moves, and rule them out on the starter Needs.

    A starter Need is matched to a stored one by name, ignoring case; one
    with no stored match is skipped.

    Args:
        connection: The migration's connection.
    """
    move_ids = {move["name"]: uuid4() for move in STARTER_MOVES}
    for sort_order, move in enumerate(STARTER_MOVES):
        connection.execute(
            sa.text(
                "INSERT INTO moves (id, name, when_it_fits, how_to_do_it, "
                "sort_order) VALUES (:id, :name, :when_it_fits, :how_to_do_it, "
                ":sort_order)"
            ),
            {**move, "id": move_ids[move["name"]], "sort_order": sort_order},
        )
    for need_name, move_names in STARTER_RULE_OUTS.items():
        for move_name in move_names:
            connection.execute(
                sa.text(
                    "INSERT INTO need_ruled_out_moves (need_id, move_id) "
                    "SELECT id, :move_id FROM needs WHERE lower(name) = lower(:name)"
                ),
                {"move_id": move_ids[move_name], "name": need_name},
            )


def downgrade() -> None:
    """Remove Moves, rule-outs and the Understandings' Moves.

    The new wording stays.
    """
    op.drop_column("understandings", "support_move")
    op.drop_column("understandings", "lead_move")
    op.drop_table("need_ruled_out_moves")
    op.drop_table("moves")
