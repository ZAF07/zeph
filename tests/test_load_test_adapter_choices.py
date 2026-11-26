from collections.abc import Callable

import pytest

from companion.adapters.clerk.auth_verifier import ClerkAuthVerifier
from companion.adapters.load_test.auth import LoadTestAccounts
from companion.adapters.load_test.chat_channel import LoggingChatChannel
from companion.adapters.load_test.chat_model import (
    LoadTestChatModel,
    LoadTestPhotoViewer,
)
from companion.adapters.load_test.scheduler import TimedScheduler
from companion.adapters.load_test.switch import LoadTestNotAllowedError
from companion.adapters.load_test.web_search import EmptyWebSearch
from companion.adapters.openrouter.chat_model import OpenRouterChatModel
from companion.adapters.scheduler import InProcessScheduler
from companion.adapters.tavily.web_search import TavilyWebSearch
from companion.adapters.telegram.chat_channel import TelegramChatChannel
from companion.config import Settings, load_settings
from companion.main import (
    build_auth_accounts,
    build_auth_verifier,
    build_chat_channel,
    build_chat_model,
    build_photo_viewer,
    build_scheduler,
    build_web_search,
)
from tests.test_config import COMPLETE_ENVIRONMENT

LOAD_TEST_CHOICES = {
    "CHAT_MODEL_ADAPTER": "load_test",
    "WEB_SEARCH_ADAPTER": "load_test",
    "CHAT_CHANNEL_ADAPTER": "load_test",
    "AUTH_VERIFIER_ADAPTER": "load_test",
    "SCHEDULER_ADAPTER": "load_test",
}
BUILDERS: list[Callable[[Settings], object]] = [
    build_chat_model,
    build_photo_viewer,
    build_web_search,
    build_chat_channel,
    build_auth_verifier,
    build_auth_accounts,
    build_scheduler,
]


def test_the_load_test_choices_build_the_load_test_adapters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LOAD_TEST_RUN", "true")
    settings = load_settings({**COMPLETE_ENVIRONMENT, **LOAD_TEST_CHOICES})

    assert isinstance(build_chat_model(settings), LoadTestChatModel)
    assert isinstance(build_photo_viewer(settings), LoadTestPhotoViewer)
    assert isinstance(build_web_search(settings), EmptyWebSearch)
    assert isinstance(build_chat_channel(settings), LoggingChatChannel)
    assert isinstance(build_auth_verifier(settings), LoadTestAccounts)
    assert isinstance(build_auth_accounts(settings), LoadTestAccounts)
    assert isinstance(build_scheduler(settings), TimedScheduler)


def test_the_load_test_choices_are_refused_outside_a_load_test(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LOAD_TEST_RUN", raising=False)
    settings = load_settings({**COMPLETE_ENVIRONMENT, **LOAD_TEST_CHOICES})

    for build in BUILDERS:
        with pytest.raises(LoadTestNotAllowedError):
            build(settings)


def test_the_load_test_switch_alone_changes_no_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LOAD_TEST_RUN", "true")
    settings = load_settings(COMPLETE_ENVIRONMENT)

    assert isinstance(build_chat_model(settings), OpenRouterChatModel)
    assert isinstance(build_web_search(settings), TavilyWebSearch)
    assert isinstance(build_chat_channel(settings), TelegramChatChannel)
    assert isinstance(build_auth_verifier(settings), ClerkAuthVerifier)
    assert isinstance(build_scheduler(settings), InProcessScheduler)
