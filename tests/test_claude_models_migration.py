from sqlalchemy import Engine

from companion.adapters.postgres.database import migrate
from tests.test_moves_migration import downgrade_to
from tests.test_openrouter_model_names_migration import save_values, stored_values

OLD_SETTINGS = {
    "response_model": "deepseek/deepseek-v4-pro-0813",
    "photo_model": "deepseek/deepseek-v4.1-flash-1017",
    "response_thinking": True,
    "available_models": [
        "deepseek/deepseek-v4.1-flash-1017",
        "deepseek/deepseek-v4-pro-0813",
    ],
    "model_prices": {
        "deepseek/deepseek-v4.1-flash-1017": {"in": 0.5, "out": 2},
        "deepseek/deepseek-v4-pro-0813": {"in": 1.69, "out": 5.07},
    },
}

CLAUDE_PRICES = {
    "anthropic/claude-haiku-5.5": {"in": 0.13, "out": 0.64},
    "anthropic/claude-sonnet-5.5": {"in": 2.56, "out": 12.8},
}


def test_the_migration_adds_the_claude_models_and_keeps_everything_else(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0090")
    try:
        save_values(engine, "platform_settings", OLD_SETTINGS)
    finally:
        migrate(database_url)

    assert stored_values(engine, "platform_settings", list(OLD_SETTINGS)) == {
        **OLD_SETTINGS,
        "available_models": [
            "deepseek/deepseek-v4.1-flash-1017",
            "deepseek/deepseek-v4-pro-0813",
            "anthropic/claude-haiku-5.5",
            "anthropic/claude-sonnet-5.5",
        ],
        "model_prices": {**OLD_SETTINGS["model_prices"], **CLAUDE_PRICES},
    }


def test_a_claude_model_already_saved_without_a_price_stays_without_one(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0090")
    try:
        save_values(
            engine,
            "platform_settings",
            {
                "available_models": [
                    "anthropic/claude-haiku-5.5",
                    "anthropic/claude-sonnet-5.5",
                ],
                "model_prices": {"anthropic/claude-sonnet-5.5": {"in": 3, "out": 9}},
            },
        )
    finally:
        migrate(database_url)

    assert stored_values(
        engine, "platform_settings", ["available_models", "model_prices"]
    ) == {
        "available_models": [
            "anthropic/claude-haiku-5.5",
            "anthropic/claude-sonnet-5.5",
        ],
        "model_prices": {"anthropic/claude-sonnet-5.5": {"in": 3, "out": 9}},
    }


def test_a_claude_model_already_saved_keeps_its_place_and_its_price(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0090")
    try:
        save_values(
            engine,
            "platform_settings",
            {
                "available_models": [
                    "anthropic/claude-haiku-5.5",
                    "deepseek/deepseek-v4.1-flash-1017",
                ],
                "model_prices": {"anthropic/claude-haiku-5.5": {"in": 1, "out": 2}},
            },
        )
    finally:
        migrate(database_url)

    assert stored_values(
        engine, "platform_settings", ["available_models", "model_prices"]
    ) == {
        "available_models": [
            "anthropic/claude-haiku-5.5",
            "deepseek/deepseek-v4.1-flash-1017",
            "anthropic/claude-sonnet-5.5",
        ],
        "model_prices": {
            "anthropic/claude-haiku-5.5": {"in": 1, "out": 2},
            "anthropic/claude-sonnet-5.5": {"in": 2.56, "out": 12.8},
        },
    }


def test_going_back_keeps_the_claude_models(engine: Engine, database_url: str) -> None:
    downgrade_to(database_url, "0090")
    try:
        save_values(engine, "platform_settings", OLD_SETTINGS)
        migrate(database_url)
        after_upgrade = stored_values(engine, "platform_settings", list(OLD_SETTINGS))
        downgrade_to(database_url, "0090")

        assert (
            stored_values(engine, "platform_settings", list(OLD_SETTINGS))
            == after_upgrade
        )
    finally:
        migrate(database_url)
