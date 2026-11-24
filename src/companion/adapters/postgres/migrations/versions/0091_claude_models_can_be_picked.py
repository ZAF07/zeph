"""Admins can pick a Claude model for a core service.

Two Claude models (OpenRouter names) are added to `available_models`, and
the Model Price of each one added to `model_prices`. Prices are SGD per
1,000,000 tokens: Anthropic's prices on 24 Nov 2026 at 1 USD ≈ 1.28 SGD.
A Claude model an Admin already added is kept as it is, with or without a
price. Every service stays on the model it uses, and no other setting is
touched.

Revision ID: 0091
Revises: 0090
Create Date: 2026-11-24
"""

import json
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "0091"
down_revision: str | None = "0090"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CLAUDE_MODEL_PRICES = {
    "anthropic/claude-haiku-5.5": {"in": 0.13, "out": 0.64},
    "anthropic/claude-sonnet-5.5": {"in": 2.56, "out": 12.8},
}
CLAUDE_MODELS = list(CLAUDE_MODEL_PRICES)


def stored_value(key: str) -> Any:
    """Read one Platform Setting's stored value.

    Args:
        key: The setting's key.

    Returns:
        The stored value, or None when the setting isn't saved.
    """
    return (
        op.get_bind()
        .execute(
            sa.text("SELECT value FROM platform_settings WHERE key = :key"),
            {"key": key},
        )
        .scalar()
    )


def save_value(key: str, value: Any) -> None:
    """Store one Platform Setting's new value.

    Args:
        key: The setting's key.
        value: The value to store.
    """
    op.get_bind().execute(
        sa.text(
            "UPDATE platform_settings SET value = CAST(:value AS jsonb) "
            "WHERE key = :key"
        ),
        {"key": key, "value": json.dumps(value)},
    )


def upgrade() -> None:
    """Add the Claude models Admins can't pick yet, each with its price.

    A Claude model an Admin already added is left as it is, with the price
    they saved or with none.
    """
    models = stored_value("available_models")
    if not isinstance(models, list):
        return
    added_models = [name for name in CLAUDE_MODELS if name not in models]
    if not added_models:
        return
    save_value("available_models", [*models, *added_models])
    prices = stored_value("model_prices")
    if isinstance(prices, dict):
        added_prices = {name: CLAUDE_MODEL_PRICES[name] for name in added_models}
        save_value("model_prices", {**added_prices, **prices})


def downgrade() -> None:
    """Keep the Claude models: a service may already use one."""
