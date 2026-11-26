import yaml
from sqlalchemy import Engine

from companion.adapters.postgres.database import migrate
from tests.conftest import SEED_FILE
from tests.test_moves_migration import downgrade_to, upgrade_to
from tests.test_openrouter_model_names_migration import save_values, stored_values

MODELS_THAT_ALWAYS_THINK = [
    "anthropic/claude-sonnet-5.5",
    "anthropic/claude-opus-5.5",
    "anthropic/claude-fable-5.2",
]
OTHER_SETTINGS = {
    "response_model": "anthropic/claude-sonnet-5.5",
    "response_thinking": False,
    "models_that_cannot_think": [],
}


def test_the_migration_lists_sonnet_opus_and_fable_and_keeps_everything_else(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0098")
    try:
        save_values(engine, "platform_settings", OTHER_SETTINGS)
        upgrade_to(database_url, "0099")

        assert stored_values(
            engine,
            "platform_settings",
            ["models_that_always_think", *OTHER_SETTINGS],
        ) == {**OTHER_SETTINGS, "models_that_always_think": MODELS_THAT_ALWAYS_THINK}
    finally:
        migrate(database_url)


def test_a_list_already_saved_is_kept(engine: Engine, database_url: str) -> None:
    downgrade_to(database_url, "0098")
    try:
        save_values(engine, "platform_settings", {"models_that_always_think": []})
        upgrade_to(database_url, "0099")

        assert stored_values(
            engine, "platform_settings", ["models_that_always_think"]
        ) == {"models_that_always_think": []}
    finally:
        migrate(database_url)


def test_the_seed_lists_sonnet_opus_and_fable() -> None:
    seed = yaml.safe_load(SEED_FILE.read_text())

    assert seed["models_that_always_think"] == MODELS_THAT_ALWAYS_THINK
