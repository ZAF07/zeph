import json

import httpx
import pytest

from scripts.load_test.__main__ import (
    LogWatcher,
    NotAWorktreeStackError,
    TelegramPoster,
    check_worktree_stack,
)

WORKTREE_ENVIRONMENT = {
    "COMPOSE_PROJECT_NAME": "ai-chat-companion-scaling-03",
    "BACKEND_PORT": "8010",
    "POSTGRES_PORT": "5442",
}


def test_a_worktree_stack_may_be_load_tested() -> None:
    check_worktree_stack(WORKTREE_ENVIRONMENT)


@pytest.mark.parametrize(
    "change",
    [
        {"COMPOSE_PROJECT_NAME": ""},
        {"BACKEND_PORT": "8000"},
        {"POSTGRES_PORT": "5432"},
    ],
)
def test_the_main_stack_is_never_load_tested(change: dict[str, str]) -> None:
    with pytest.raises(NotAWorktreeStackError):
        check_worktree_stack({**WORKTREE_ENVIRONMENT, **change})


def test_a_reply_is_the_first_text_sent_to_the_chat_after_the_message() -> None:
    watcher = LogWatcher([])
    watcher.take("Load test: sent a text to chat 7", read_at=5.0)
    watcher.take("Load test: sent a text to chat 8", read_at=12.0)
    watcher.take("Load test: sent a text to chat 7", read_at=14.0)

    assert watcher.wait_for_reply(7, after=10.0, timeout=0.01) == 14.0
    assert watcher.wait_for_reply(7, after=20.0, timeout=0.01) is None


def test_the_timed_tick_is_the_first_to_start_after_setup() -> None:
    watcher = LogWatcher([])
    watcher.take("Load test: tick started", read_at=1.0)
    watcher.take("Load test: tick took 3.0s", read_at=4.0)
    watcher.take("Load test: tick started", read_at=70.0)

    assert watcher.wait_for_tick(started_after=10.0, timeout=0.01) is None

    watcher.take("Load test: tick took 95.5s", read_at=165.5)
    assert watcher.wait_for_tick(started_after=10.0, timeout=0.01) == 95.5


def test_setup_waits_for_a_running_tick_to_finish() -> None:
    watcher = LogWatcher([])
    watcher.take("Load test: tick started", read_at=1.0)

    assert not watcher.wait_until_no_tick_runs(timeout=0.01)

    watcher.take("Load test: tick took 3.0s", read_at=4.0)
    assert watcher.wait_until_no_tick_runs(timeout=0.01)


def test_failures_and_model_calls_are_counted() -> None:
    watcher = LogWatcher([])
    for line in [
        "Load test: answered a safeguard call",
        "Load test: answered a reply call",
        "Load test: answered a reply call",
        "Could not answer a Message from a User",
        "sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached",
        "The Understanding form couldn't be read; using the fallback Understanding",
    ]:
        watcher.take(line, read_at=1.0)

    assert watcher.model_calls == {"safeguard": 1, "reply": 2}
    assert watcher.failed_replies == 1
    assert len(watcher.database_errors) == 1
    assert watcher.fallback_warnings == 1


def test_texts_are_posted_as_telegram_updates_with_the_secret() -> None:
    requests: list[httpx.Request] = []

    def answer(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200)

    client = httpx.Client(
        base_url="http://backend.test", transport=httpx.MockTransport(answer)
    )
    poster = TelegramPoster(client, "hook-secret")

    first = poster.post(9100000001, "hi")
    poster.post(9100000001, "you there?")

    assert first.status == 200
    assert [request.url.path for request in requests] == ["/telegram/webhook"] * 2
    assert requests[0].headers["X-Telegram-Bot-Api-Secret-Token"] == "hook-secret"
    updates = [json.loads(request.content) for request in requests]
    assert updates[0]["message"]["chat"] == {"id": 9100000001, "type": "private"}
    assert updates[0]["message"]["text"] == "hi"
    assert updates[0]["update_id"] != updates[1]["update_id"]
