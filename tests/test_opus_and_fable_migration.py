from sqlalchemy import Engine

from companion.adapters.postgres.database import migrate
from tests.test_moves_migration import downgrade_to, upgrade_to
from tests.test_openrouter_model_names_migration import save_values, stored_values

OLD_SETTINGS = {
    "response_model": "deepseek/deepseek-v4-pro-0813",
    "photo_model": "deepseek/deepseek-v4.1-flash-1017",
    "response_thinking": True,
    "available_models": [
        "deepseek/deepseek-v4.1-flash-1017",
        "deepseek/deepseek-v4-pro-0813",
        "anthropic/claude-haiku-5.5",
    ],
    "model_prices": {
        "deepseek/deepseek-v4.1-flash-1017": {"in": 0.5, "out": 2},
        "deepseek/deepseek-v4-pro-0813": {"in": 1.69, "out": 5.07},
    },
}

CLAUDE_PRICES = {
    "anthropic/claude-opus-5.5": {"in": 5.12, "out": 25.6},
    "anthropic/claude-fable-5.2": {"in": 10.24, "out": 51.2},
}


def test_the_migration_adds_opus_and_fable_and_keeps_everything_else(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0091")
    try:
        save_values(engine, "platform_settings", OLD_SETTINGS)
        upgrade_to(database_url, "0092")

        assert stored_values(engine, "platform_settings", list(OLD_SETTINGS)) == {
            **OLD_SETTINGS,
            "available_models": [
                "deepseek/deepseek-v4.1-flash-1017",
                "deepseek/deepseek-v4-pro-0813",
                "anthropic/claude-haiku-5.5",
                "anthropic/claude-opus-5.5",
                "anthropic/claude-fable-5.2",
            ],
            "model_prices": {**OLD_SETTINGS["model_prices"], **CLAUDE_PRICES},
        }
    finally:
        migrate(database_url)


def test_a_model_already_saved_without_a_price_stays_without_one(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0091")
    try:
        save_values(
            engine,
            "platform_settings",
            {
                "available_models": [
                    "anthropic/claude-opus-5.5",
                    "anthropic/claude-fable-5.2",
                ],
                "model_prices": {"anthropic/claude-fable-5.2": {"in": 3, "out": 9}},
            },
        )
        upgrade_to(database_url, "0092")

        assert stored_values(
            engine, "platform_settings", ["available_models", "model_prices"]
        ) == {
            "available_models": [
                "anthropic/claude-opus-5.5",
                "anthropic/claude-fable-5.2",
            ],
            "model_prices": {"anthropic/claude-fable-5.2": {"in": 3, "out": 9}},
        }
    finally:
        migrate(database_url)


def test_a_model_already_saved_keeps_its_place_and_its_price(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0091")
    try:
        save_values(
            engine,
            "platform_settings",
            {
                "available_models": [
                    "anthropic/claude-opus-5.5",
                    "deepseek/deepseek-v4.1-flash-1017",
                ],
                "model_prices": {"anthropic/claude-opus-5.5": {"in": 1, "out": 2}},
            },
        )
        upgrade_to(database_url, "0092")

        assert stored_values(
            engine, "platform_settings", ["available_models", "model_prices"]
        ) == {
            "available_models": [
                "anthropic/claude-opus-5.5",
                "deepseek/deepseek-v4.1-flash-1017",
                "anthropic/claude-fable-5.2",
            ],
            "model_prices": {
                "anthropic/claude-opus-5.5": {"in": 1, "out": 2},
                "anthropic/claude-fable-5.2": {"in": 10.24, "out": 51.2},
            },
        }
    finally:
        migrate(database_url)


def test_going_back_keeps_opus_and_fable(engine: Engine, database_url: str) -> None:
    downgrade_to(database_url, "0091")
    try:
        save_values(engine, "platform_settings", OLD_SETTINGS)
        upgrade_to(database_url, "0092")
        after_upgrade = stored_values(engine, "platform_settings", list(OLD_SETTINGS))
        downgrade_to(database_url, "0091")

        assert (
            stored_values(engine, "platform_settings", list(OLD_SETTINGS))
            == after_upgrade
        )
    finally:
        migrate(database_url)
