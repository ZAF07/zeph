import json
from typing import Any

from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
from tests.test_moves_migration import downgrade_to

OLD_SETTINGS = {
    "response_model": "deepseek-v4-pro",
    "photo_model": "deepseek-flash",
    "check_in_model": "some-other-model",
    "available_models": ["deepseek-flash", "deepseek-v4-pro"],
    "model_prices": {
        "deepseek-flash": {"in": 0.38, "out": 1.54},
        "deepseek-v4-pro": {"in": 1.69, "out": 5.07},
        "some-other-model": {"in": 1, "out": 2},
    },
}


def save_values(engine: Engine, table: str, values: dict[str, Any]) -> None:
    """Store each value under its key, replacing what was there."""
    with engine.begin() as connection:
        for key, value in values.items():
            connection.execute(
                text(
                    f"INSERT INTO {table} (key, value, updated_at) "
                    "VALUES (:key, CAST(:value AS jsonb), now()) "
                    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
                ),
                {"key": key, "value": json.dumps(value)},
            )


def stored_values(engine: Engine, table: str, keys: list[str]) -> dict[str, Any]:
    """The stored values of the keys asked for, by key."""
    with engine.connect() as connection:
        rows = connection.execute(
            text(f"SELECT key, value FROM {table} WHERE key = ANY(:keys)"),
            {"keys": keys},
        )
        return {row.key: row.value for row in rows}


def test_the_migration_renames_saved_models_to_openrouter_names(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0085")
    try:
        save_values(engine, "platform_settings", OLD_SETTINGS)
        save_values(engine, "eval_judge_settings", {"model": "deepseek-flash"})
    finally:
        migrate(database_url)

    assert stored_values(engine, "platform_settings", list(OLD_SETTINGS)) == {
        "response_model": "deepseek/deepseek-v4-pro",
        "photo_model": "deepseek/deepseek-v4.1-flash",
        "check_in_model": "some-other-model",
        "available_models": [
            "deepseek/deepseek-v4.1-flash",
            "deepseek/deepseek-v4-pro",
        ],
        "model_prices": {
            "deepseek/deepseek-v4.1-flash": {"in": 0.38, "out": 1.54},
            "deepseek/deepseek-v4-pro": {"in": 1.69, "out": 5.07},
            "some-other-model": {"in": 1, "out": 2},
        },
    }
    assert stored_values(engine, "eval_judge_settings", ["model"]) == {
        "model": "deepseek/deepseek-v4.1-flash"
    }


def test_going_back_restores_the_direct_deepseek_names(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0085")
    try:
        save_values(engine, "platform_settings", OLD_SETTINGS)
        migrate(database_url)
        downgrade_to(database_url, "0085")

        assert (
            stored_values(engine, "platform_settings", list(OLD_SETTINGS))
            == OLD_SETTINGS
        )
    finally:
        migrate(database_url)
