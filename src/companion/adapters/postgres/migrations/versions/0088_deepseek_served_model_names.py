"""Saved DeepSeek model names become the names DeepSeek itself serves.

On OpenRouter, DeepSeek's own servers answer only to the dated names, so
only those can use our own DeepSeek key. Each older name in a `*_model`
Platform Setting, in `available_models`, in the `model_prices` keys and in
the Judge's model is renamed. An Admin's own choice is kept, only renamed.
The pro model is added to `available_models` when missing, so Admins can
pick it. Other names, past Eval Runs and User data are not touched.

Revision ID: 0088
Revises: 0087
Create Date: 2026-11-24
"""

import json
from collections.abc import Mapping, Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "0088"
down_revision: str | None = "0087"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PRO_MODEL = "deepseek/deepseek-v4-pro-0813"
SERVED_NAME_BY_OLD_NAME = {
    "deepseek/deepseek-v4.1-flash": "deepseek/deepseek-v4.1-flash-1017",
    "deepseek/deepseek-v4-pro": PRO_MODEL,
}
OLD_NAME_BY_SERVED_NAME = {new: old for old, new in SERVED_NAME_BY_OLD_NAME.items()}


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


def with_pro_model(key: str, value: Any) -> Any:
    """Add the pro model to the models Admins can pick, when missing.

    Args:
        key: The setting's key.
        value: The setting's stored value.

    Returns:
        `available_models` with the pro model in it; other values as they were.
    """
    if key == "available_models" and isinstance(value, list):
        return value if PRO_MODEL in value else [*value, PRO_MODEL]
    return value


def change_settings(table: str, names: Mapping[str, str], add_pro_model: bool) -> None:
    """Rename the model names in every stored setting of a table.

    Args:
        table: The settings table, "platform_settings" or "eval_judge_settings".
        names: Each old model name's new name.
        add_pro_model: Whether the pro model is added to `available_models`.
    """
    connection = op.get_bind()
    rows = connection.execute(sa.text(f"SELECT key, value FROM {table}")).all()
    for row in rows:
        new_value = renamed_value(row.key, row.value, names)
        if add_pro_model:
            new_value = with_pro_model(row.key, new_value)
        if new_value != row.value:
            connection.execute(
                sa.text(
                    f"UPDATE {table} SET value = CAST(:value AS jsonb) WHERE key = :key"
                ),
                {"key": row.key, "value": json.dumps(new_value)},
            )


def upgrade() -> None:
    """Rename the DeepSeek models to the names DeepSeek serves; add pro."""
    change_settings("platform_settings", SERVED_NAME_BY_OLD_NAME, add_pro_model=True)
    change_settings("eval_judge_settings", SERVED_NAME_BY_OLD_NAME, add_pro_model=False)


def downgrade() -> None:
    """Rename the DeepSeek models back; an added pro model stays pickable."""
    change_settings("platform_settings", OLD_NAME_BY_SERVED_NAME, add_pro_model=False)
    change_settings("eval_judge_settings", OLD_NAME_BY_SERVED_NAME, add_pro_model=False)
