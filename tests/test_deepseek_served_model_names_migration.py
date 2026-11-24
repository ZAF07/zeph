from sqlalchemy import Engine

from companion.adapters.postgres.database import migrate
from tests.test_moves_migration import downgrade_to
from tests.test_openrouter_model_names_migration import save_values, stored_values

OLD_SETTINGS = {
    "response_model": "deepseek/deepseek-v4-pro",
    "photo_model": "deepseek/deepseek-v4.1-flash",
    "check_in_model": "anthropic/claude-haiku-5.5",
    "available_models": ["deepseek/deepseek-v4.1-flash"],
    "model_prices": {
        "deepseek/deepseek-v4.1-flash": {"in": 0.38, "out": 1.54},
        "deepseek/deepseek-v4-pro": {"in": 1.69, "out": 5.07},
        "anthropic/claude-haiku-5.5": {"in": 1, "out": 2},
    },
}


def test_the_migration_renames_saved_models_to_the_names_deepseek_serves(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0088")
    try:
        save_values(engine, "platform_settings", OLD_SETTINGS)
        save_values(
            engine, "eval_judge_settings", {"model": "deepseek/deepseek-v4.1-flash"}
        )
    finally:
        migrate(database_url)

    assert stored_values(engine, "platform_settings", list(OLD_SETTINGS)) == {
        "response_model": "deepseek/deepseek-v4-pro-0813",
        "photo_model": "deepseek/deepseek-v4.1-flash-1017",
        "check_in_model": "anthropic/claude-haiku-5.5",
        "available_models": [
            "deepseek/deepseek-v4.1-flash-1017",
            "deepseek/deepseek-v4-pro-0813",
        ],
        "model_prices": {
            "deepseek/deepseek-v4.1-flash-1017": {"in": 0.38, "out": 1.54},
            "deepseek/deepseek-v4-pro-0813": {"in": 1.69, "out": 5.07},
            "anthropic/claude-haiku-5.5": {"in": 1, "out": 2},
        },
    }
    assert stored_values(engine, "eval_judge_settings", ["model"]) == {
        "model": "deepseek/deepseek-v4.1-flash-1017"
    }


def test_a_pro_model_already_pickable_is_renamed_not_added_twice(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0088")
    try:
        save_values(
            engine,
            "platform_settings",
            {
                "available_models": [
                    "deepseek/deepseek-v4-pro",
                    "deepseek/deepseek-v4.1-flash",
                ]
            },
        )
    finally:
        migrate(database_url)

    assert stored_values(engine, "platform_settings", ["available_models"]) == {
        "available_models": [
            "deepseek/deepseek-v4-pro-0813",
            "deepseek/deepseek-v4.1-flash-1017",
        ]
    }


def test_a_model_saved_under_both_names_is_kept_once_with_its_newer_price(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0088")
    try:
        save_values(
            engine,
            "platform_settings",
            {
                "available_models": [
                    "deepseek/deepseek-v4.1-flash",
                    "deepseek/deepseek-v4.1-flash-1017",
                    "deepseek/deepseek-v4-pro-0813",
                ],
                "model_prices": {
                    "deepseek/deepseek-v4.1-flash": {"in": 0.38, "out": 1.54},
                    "deepseek/deepseek-v4.1-flash-1017": {"in": 0.5, "out": 2},
                },
            },
        )
    finally:
        migrate(database_url)

    assert stored_values(
        engine, "platform_settings", ["available_models", "model_prices"]
    ) == {
        "available_models": [
            "deepseek/deepseek-v4.1-flash-1017",
            "deepseek/deepseek-v4-pro-0813",
        ],
        "model_prices": {"deepseek/deepseek-v4.1-flash-1017": {"in": 0.5, "out": 2}},
    }


def test_going_back_restores_the_older_names(engine: Engine, database_url: str) -> None:
    downgrade_to(database_url, "0088")
    try:
        save_values(engine, "platform_settings", OLD_SETTINGS)
        migrate(database_url)
        downgrade_to(database_url, "0088")

        assert stored_values(engine, "platform_settings", list(OLD_SETTINGS)) == {
            **OLD_SETTINGS,
            "available_models": [
                "deepseek/deepseek-v4.1-flash",
                "deepseek/deepseek-v4-pro",
            ],
        }
    finally:
        migrate(database_url)
