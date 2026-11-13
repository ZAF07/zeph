import logging

import pytest
from sqlalchemy import create_engine

from companion.adapters.tavily.web_search import TavilyWebSearch
from companion.config import MissingSettingsError, load_settings
from companion.main import (
    UnknownAdapterError,
    build_embedder,
    build_text_extractor,
    build_vector_store,
    build_web_search,
    quiet_http_client_logs,
)

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
    "TAVILY_API_KEY": "tvly-x",
}


def test_missing_required_key_is_named_in_the_error() -> None:
    environment = dict(COMPLETE_ENVIRONMENT)
    del environment["TELEGRAM_BOT_TOKEN"]

    with pytest.raises(MissingSettingsError) as error:
        load_settings(environment)

    assert "TELEGRAM_BOT_TOKEN" in str(error.value)


def test_tavily_key_is_required() -> None:
    environment = dict(COMPLETE_ENVIRONMENT)
    del environment["TAVILY_API_KEY"]

    with pytest.raises(MissingSettingsError) as error:
        load_settings(environment)

    assert "TAVILY_API_KEY" in str(error.value)


def test_web_search_adapter_defaults_to_tavily() -> None:
    settings = load_settings(COMPLETE_ENVIRONMENT)

    assert settings.web_search_adapter == "tavily"
    assert isinstance(build_web_search(settings), TavilyWebSearch)


def test_unknown_web_search_adapter_is_refused() -> None:
    settings = load_settings({**COMPLETE_ENVIRONMENT, "WEB_SEARCH_ADAPTER": "bing"})

    with pytest.raises(UnknownAdapterError):
        build_web_search(settings)


def test_deepseek_key_is_required() -> None:
    environment = dict(COMPLETE_ENVIRONMENT)
    del environment["DEEPSEEK_API_KEY"]

    with pytest.raises(MissingSettingsError) as error:
        load_settings(environment)

    assert "DEEPSEEK_API_KEY" in str(error.value)


def test_initial_admin_emails_are_split_and_lower_cased() -> None:
    environment = {
        **COMPLETE_ENVIRONMENT,
        "INITIAL_ADMIN_EMAILS": " Owner@Example.com, ,ren@example.com ",
    }

    settings = load_settings(environment)

    assert settings.initial_admin_email_set == frozenset(
        {"owner@example.com", "ren@example.com"}
    )


def test_knowledge_adapters_default_to_fastembed_pgvector_and_pypdf() -> None:
    settings = load_settings(COMPLETE_ENVIRONMENT)

    assert settings.embedder_adapter == "fastembed"
    assert settings.vector_store_adapter == "pgvector"
    assert settings.text_extractor_adapter == "pypdf"


def test_an_unknown_knowledge_adapter_is_named_in_the_error() -> None:
    settings = load_settings(
        {
            **COMPLETE_ENVIRONMENT,
            "EMBEDDER_ADAPTER": "nope",
            "VECTOR_STORE_ADAPTER": "nada",
            "TEXT_EXTRACTOR_ADAPTER": "zilch",
        }
    )

    with pytest.raises(UnknownAdapterError, match="EMBEDDER_ADAPTER"):
        build_embedder(settings)
    with pytest.raises(UnknownAdapterError, match="VECTOR_STORE_ADAPTER"):
        build_vector_store(settings, create_engine(settings.database_url))
    with pytest.raises(UnknownAdapterError, match="TEXT_EXTRACTOR_ADAPTER"):
        build_text_extractor(settings)


def test_http_client_loggers_are_pinned_to_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for logger_name in ("httpx", "httpcore"):
        monkeypatch.setattr(logging.getLogger(logger_name), "level", logging.NOTSET)

    quiet_http_client_logs()

    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING
