import logging
from collections.abc import Callable

import pytest

from companion.adapters.load_test.auth import LoadTestAccounts
from companion.adapters.load_test.chat_channel import (
    SENT_TEXT_LOG_PREFIX,
    LoggingChatChannel,
)
from companion.adapters.load_test.scheduler import (
    TICK_STARTED_LOG,
    TICK_TOOK_LOG_PREFIX,
    TimedScheduler,
)
from companion.adapters.load_test.switch import (
    LoadTestNotAllowedError,
    allow_load_test_adapter,
)
from companion.adapters.load_test.web_search import EmptyWebSearch
from companion.core.models import AccountIdentity


def test_the_chat_channel_logs_each_text_it_would_send(
    caplog: pytest.LogCaptureFixture,
) -> None:
    channel = LoggingChatChannel()

    with caplog.at_level(logging.INFO):
        channel.show_typing(7001)
        channel.send_text(7001, "hey there")
        channel.send_sticker(7001, "sticker-1")
        channel.react(7001, 10, "❤")

    assert [record.getMessage() for record in caplog.records] == [
        f"{SENT_TEXT_LOG_PREFIX}7001",
        "Load test: sent a sticker to chat 7001",
        "Load test: reacted in chat 7001",
    ]
    assert channel.get_sticker_set("CalmCreatures") is None
    assert channel.get_sticker_image("file-1") is None
    assert channel.download_photo("file-1").content


def test_web_search_finds_nothing_and_says_so(
    caplog: pytest.LogCaptureFixture,
) -> None:
    search = EmptyWebSearch()

    with caplog.at_level(logging.INFO):
        assert search.search("calm breathing") == []
        assert search.fetch_page("https://example.com") == ""

    assert len(caplog.records) == 2


def test_sign_in_accepts_only_load_test_tokens() -> None:
    accounts = LoadTestAccounts()

    assert accounts.verify("load-test-admin") == AccountIdentity(
        auth_id="load-test-admin", email="load-test-admin@load-test.invalid"
    )
    assert accounts.verify("user_maya") is None
    accounts.delete_account("load-test-admin")


def test_the_scheduler_logs_how_long_each_tick_took(
    caplog: pytest.LogCaptureFixture,
) -> None:
    ticks: list[Callable[[], None]] = []

    class KeepingScheduler:
        def start(self, tick: Callable[[], None]) -> None:
            ticks.append(tick)

        def stop(self) -> None:
            pass

    ran: list[str] = []
    scheduler = TimedScheduler(KeepingScheduler())
    scheduler.start(lambda: ran.append("tick"))
    [timed_tick] = ticks

    with caplog.at_level(logging.INFO):
        timed_tick()

    assert ran == ["tick"]
    started, took = [record.getMessage() for record in caplog.records]
    assert started == TICK_STARTED_LOG
    assert took.startswith(TICK_TOOK_LOG_PREFIX)


def test_the_scheduler_logs_a_failing_tick_too(
    caplog: pytest.LogCaptureFixture,
) -> None:
    ticks: list[Callable[[], None]] = []

    class KeepingScheduler:
        def start(self, tick: Callable[[], None]) -> None:
            ticks.append(tick)

        def stop(self) -> None:
            pass

    def failing_tick() -> None:
        raise RuntimeError("database down")

    TimedScheduler(KeepingScheduler()).start(failing_tick)

    with caplog.at_level(logging.INFO), pytest.raises(RuntimeError):
        ticks[0]()

    assert caplog.records[-1].getMessage().startswith(TICK_TOOK_LOG_PREFIX)


def test_load_test_adapters_need_the_load_test_switch() -> None:
    with pytest.raises(LoadTestNotAllowedError, match="CHAT_MODEL_ADAPTER"):
        allow_load_test_adapter("CHAT_MODEL_ADAPTER", environment={})
    with pytest.raises(LoadTestNotAllowedError):
        allow_load_test_adapter(
            "CHAT_MODEL_ADAPTER", environment={"LOAD_TEST_RUN": "false"}
        )

    allow_load_test_adapter("CHAT_MODEL_ADAPTER", environment={"LOAD_TEST_RUN": "true"})
