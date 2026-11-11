import pytest

from companion.config import MissingSettingsError, load_settings

COMPLETE_ENVIRONMENT = {
    "POSTGRES_USER": "companion",
    "POSTGRES_PASSWORD": "secret",
    "POSTGRES_DB": "companion",
    "CLERK_SECRET_KEY": "sk_test_x",
    "TELEGRAM_BOT_TOKEN": "123:abc",
    "TELEGRAM_BOT_USERNAME": "zeph_bot",
    "TELEGRAM_WEBHOOK_SECRET": "hook-secret",
    "WEBHOOK_BASE_URL": "https://zeph.ngrok.app",
    "DASHBOARD_URL": "http://localhost:3000",
    "DEEPSEEK_API_KEY": "sk-deepseek-x",
}


def test_missing_required_key_is_named_in_the_error() -> None:
    environment = dict(COMPLETE_ENVIRONMENT)
    del environment["TELEGRAM_BOT_TOKEN"]

    with pytest.raises(MissingSettingsError) as error:
        load_settings(environment)

    assert "TELEGRAM_BOT_TOKEN" in str(error.value)


def test_keys_for_later_issues_are_optional() -> None:
    settings = load_settings(COMPLETE_ENVIRONMENT)

    assert settings.tavily_api_key is None


def test_deepseek_key_is_required() -> None:
    environment = dict(COMPLETE_ENVIRONMENT)
    del environment["DEEPSEEK_API_KEY"]

    with pytest.raises(MissingSettingsError) as error:
        load_settings(environment)

    assert "DEEPSEEK_API_KEY" in str(error.value)
