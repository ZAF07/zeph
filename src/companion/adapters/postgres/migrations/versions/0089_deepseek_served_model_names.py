"""Saved DeepSeek model names become the names DeepSeek itself serves.

On OpenRouter, DeepSeek's own servers answer only to the dated names, so
only those can use our own DeepSeek key. Each older name in a `*_model`
Platform Setting, in `available_models`, in the `model_prices` keys and in
the Judge's model is renamed. An Admin's own choice is kept, only renamed.
The pro model is added to `available_models` when missing, so Admins can
pick it. Other names, past Eval Runs and User data are not touched.

Revision ID: 0089
Revises: 0088
Create Date: 2026-11-24
"""

import json
from collections.abc import Mapping, Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "0089"
down_revision: str | None = "0088"
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

    A model saved under both its old and its new name is kept once: the
    list holds it once, and the price already saved under the new name wins.

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
        return list(dict.fromkeys(names.get(name, name) for name in value))
    if key == "model_prices" and isinstance(value, dict):
        renamed = {names[name]: price for name, price in value.items() if name in names}
        kept = {name: price for name, price in value.items() if name not in names}
        return {**renamed, **kept}
    return value


def save_value(table: str, key: str, value: Any) -> None:
    """Store one setting's new value.

    Args:
        table: The settings table, "platform_settings" or "eval_judge_settings".
        key: The setting's key.
        value: The value to store.
    """
    op.get_bind().execute(
        sa.text(f"UPDATE {table} SET value = CAST(:value AS jsonb) WHERE key = :key"),
        {"key": key, "value": json.dumps(value)},
    )


def rename_models(table: str, names: Mapping[str, str]) -> None:
    """Rename the model names in every stored setting of a table.

    Args:
        table: The settings table, "platform_settings" or "eval_judge_settings".
        names: Each old model name's new name.
    """
    rows = op.get_bind().execute(sa.text(f"SELECT key, value FROM {table}")).all()
    for row in rows:
        new_value = renamed_value(row.key, row.value, names)
        if new_value != row.value:
            save_value(table, row.key, new_value)


def add_pro_model() -> None:
    """Add the pro model to the models Admins can pick, when missing."""
    models = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT value FROM platform_settings WHERE key = 'available_models'"
            )
        )
        .scalar()
    )
    if isinstance(models, list) and PRO_MODEL not in models:
        save_value("platform_settings", "available_models", [*models, PRO_MODEL])


def upgrade() -> None:
    """Rename the DeepSeek models to the names DeepSeek serves; add pro."""
    rename_models("platform_settings", SERVED_NAME_BY_OLD_NAME)
    rename_models("eval_judge_settings", SERVED_NAME_BY_OLD_NAME)
    add_pro_model()


def downgrade() -> None:
    """Rename the DeepSeek models back; an added pro model stays pickable."""
    rename_models("platform_settings", OLD_NAME_BY_SERVED_NAME)
    rename_models("eval_judge_settings", OLD_NAME_BY_SERVED_NAME)
