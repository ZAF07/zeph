"""An Exploration asks by an Approach, and about a missing Condition.

"Way" is renamed Approach: `exploration_tries.way` becomes `approach`, and
its value `other_person` becomes `would_it_differ`. The "missing part of
life" need is now "a missing Condition": `part_of_life` becomes
`condition_value`, a new `condition` column names the Condition, and a
stored `missing_part` try becomes a `missing_condition` try on `setting`.
Every existing try keeps what it asked and how it went.

Stored Understanding Eval Cases follow the same renames (`way` and
`aimed_way` become `approach` and `aimed_approach`), an Admin's edits
included, so none stops loading. The seed case
`agenda-missing-part-of-life-asked` tested the rule that is gone and is
removed unless an Admin edited it. Case Results already kept are left as
they were.

`reply_plan_prompt` reloads from the seed where no Admin edited it: it now
says "Approach" and never to offer a mood or state when told to ask
openly. An edited prompt is kept and a warning is logged; until the new
text is merged in by hand the Reply Plan lacks that line, while the
instruction code writes still says to name no state. No User data is
removed.

Revision ID: 0111
Revises: 0110
Create Date: 2026-11-26
"""

import json
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

from companion.adapters.postgres.eval_case_reload import reload_eval_case_unless_edited
from companion.adapters.postgres.prompt_reload import reload_prompt_unless_edited

revision: str = "0111"
down_revision: str | None = "0110"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PREVIOUS_SEED_HASHES = {
    "reply_plan_prompt": (
        "31d5473095db434b49b31af926c1a69587059e6c79c9c0b204e3dcd690822a6d"
    ),
}
REMOVED_SEED_CASE = "agenda-missing-part-of-life-asked"
RENAMED_KEYS = {"way": "approach", "aimed_way": "aimed_approach"}
RENAMED_VALUES = {
    "approach": {"other_person": "would_it_differ"},
    "aimed_approach": {"other_person": "would_it_differ"},
    "need": {"missing_part": "missing_condition"},
    "aimed_need": {"missing_part": "missing_condition"},
}


def renamed(content: Any) -> Any:
    """Bring a stored Eval Case's field names and values up to date.

    "way" and "aimed_way" become "approach" and "aimed_approach", the
    Approach "other_person" becomes "would_it_differ" and the need
    "missing_part" becomes "missing_condition".

    Args:
        content: The case's content, or any part of it.

    Returns:
        The same content with the old field names and values replaced.
    """
    if isinstance(content, list):
        return [renamed(entry) for entry in content]
    if not isinstance(content, dict):
        return content
    result: dict[str, Any] = {}
    for key, value in content.items():
        new_key = RENAMED_KEYS.get(str(key), str(key))
        new_value = renamed(value)
        if isinstance(new_value, str):
            new_value = RENAMED_VALUES.get(new_key, {}).get(new_value, new_value)
        result[new_key] = new_value
    return result


def upgrade() -> None:
    """Rename the columns and values, the stored cases and reload the prompt."""
    op.alter_column("exploration_tries", "way", new_column_name="approach")
    op.alter_column(
        "exploration_tries", "part_of_life", new_column_name="condition_value"
    )
    op.add_column("exploration_tries", sa.Column("condition", sa.Text))
    op.execute(
        "UPDATE exploration_tries SET approach = 'would_it_differ' "
        "WHERE approach = 'other_person'"
    )
    op.execute(
        "UPDATE exploration_tries SET need = 'missing_condition', "
        "condition = 'setting' WHERE need = 'missing_part'"
    )
    connection = op.get_bind()
    reload_eval_case_unless_edited(connection, REMOVED_SEED_CASE)
    stored = connection.execute(
        sa.text("SELECT key, content FROM eval_cases WHERE eval = 'understanding'")
    ).all()
    for key, content in stored:
        new_content = renamed(content)
        if new_content != content:
            connection.execute(
                sa.text(
                    "UPDATE eval_cases SET content = CAST(:content AS JSONB) "
                    "WHERE key = :key"
                ),
                {"key": key, "content": json.dumps(new_content)},
            )
    for key, previous_seed_hash in PREVIOUS_SEED_HASHES.items():
        reload_prompt_unless_edited(connection, key, previous_seed_hash)


def downgrade() -> None:
    """Bring the old column names and values back.

    A try at a Condition other than the setting can't be stored the old
    way, so it is deleted with its Curiosity. Stored Eval Cases and the
    prompt stay as they are.
    """
    op.execute(
        "UPDATE exploration_tries SET need = 'missing_part' "
        "WHERE need = 'missing_condition' AND condition = 'setting'"
    )
    op.execute(
        "DELETE FROM curiosities WHERE id IN (SELECT curiosity_id FROM "
        "exploration_tries WHERE need = 'missing_condition')"
    )
    op.execute(
        "UPDATE exploration_tries SET approach = 'other_person' "
        "WHERE approach = 'would_it_differ'"
    )
    op.drop_column("exploration_tries", "condition")
    op.alter_column(
        "exploration_tries", "condition_value", new_column_name="part_of_life"
    )
    op.alter_column("exploration_tries", "approach", new_column_name="way")
