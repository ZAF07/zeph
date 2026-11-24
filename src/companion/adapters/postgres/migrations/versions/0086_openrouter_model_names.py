"""Saved model names become OpenRouter names.

Each DeepSeek model name in a `*_model` Platform Setting, in
`available_models`, in the `model_prices` keys and in the Judge's model is
renamed to its OpenRouter name. An Admin's own choice is kept, only renamed.
Other names, past Eval Runs and User data are not touched.

Revision ID: 0086
Revises: 0085
Create Date: 2026-11-24
"""

import json
from collections.abc import Mapping, Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "0086"
down_revision: str | None = "0085"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OPENROUTER_NAMES = {
    "deepseek-flash": "deepseek/deepseek-v4.1-flash",
    "deepseek-v4-pro": "deepseek/deepseek-v4-pro",
}
DIRECT_NAMES = {new: old for old, new in OPENROUTER_NAMES.items()}


def renamed_value(key: str, value: Any, names: Mapping[str, str]) -> Any:
    """Rename the model names in one stored setting.

    Args:
        key: The setting's key.
        value: The setting's stored value.
        names: Each old model name's new name.

    Returns:
        The value with its model names renamed; other values as they were.
    """
    if key.endswith("_model") or key == "model":
        return names.get(value, value) if isinstance(value, str) else value
    if key == "available_models" and isinstance(value, list):
        return [names.get(name, name) for name in value]
    if key == "model_prices" and isinstance(value, dict):
        return {names.get(name, name): price for name, price in value.items()}
    return value


def rename_models(table: str, names: Mapping[str, str]) -> None:
    """Rename the model names in every stored setting of a table.

    Args:
        table: The settings table, "platform_settings" or "eval_judge_settings".
        names: Each old model name's new name.
    """
    connection = op.get_bind()
    rows = connection.execute(sa.text(f"SELECT key, value FROM {table}")).all()
    for row in rows:
        new_value = renamed_value(row.key, row.value, names)
        if new_value != row.value:
            connection.execute(
                sa.text(
                    f"UPDATE {table} SET value = CAST(:value AS jsonb) WHERE key = :key"
                ),
                {"key": row.key, "value": json.dumps(new_value)},
            )


def upgrade() -> None:
    """Rename the DeepSeek model names to their OpenRouter names."""
    rename_models("platform_settings", OPENROUTER_NAMES)
    rename_models("eval_judge_settings", OPENROUTER_NAMES)


def downgrade() -> None:
    """Rename the OpenRouter DeepSeek names back to the direct names."""
    rename_models("platform_settings", DIRECT_NAMES)
    rename_models("eval_judge_settings", DIRECT_NAMES)
