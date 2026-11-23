"""Load test a worktree's running stack for free: `make load-test`.

The backend runs on the load-test adapters (`docker-compose.load-test.yml`),
so no model, search or Telegram call is made. The script makes test Users in
the worktree's database, posts Telegram updates to the backend's webhook as
many Users chatting at once while timing a Dashboard API page, then times one
tick with many due Check-ins and ended Conversations. It reads the backend's
logs to see which Messages were answered, and prints a report against the bar
(`.scratch/scaling/PRD.md`). Its test Users are deleted when it ends.
"""

import argparse
import itertools
import os
import random
import subprocess
import sys
import threading
import time
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import create_engine

from companion.adapters.load_test.scheduler import TICK_STARTED_LOG
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.config import load_settings
from companion.core.platform_settings import CONVERSATION_QUIET_GAP
from companion.core.ports import Repositories
from scripts.load_test.report import (
    ChatResults,
    LoadTestResults,
    MessageRound,
    TimedCall,
    bar_failed,
    is_database_error,
    is_failed_reply,
    is_fallback_warning,
    model_call_shape,
    sent_text_chat_id,
    tick_seconds,
    write_report,
)
from scripts.load_test.test_data import (
    create_admin,
    create_chat_users,
    create_due_check_in_users,
    create_ended_conversations,
    delete_test_users,
)

MAIN_BACKEND_PORT = "8000"
MAIN_POSTGRES_PORT = "5432"
WEBHOOK_SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"
DASHBOARD_PAGE = "/api/admin/users"
DASHBOARD_EVERY_SECONDS = 3.0
BURST_TEXTS = 8
HEAVY_TEXTER_ROUNDS = 2
NORMAL_ROUNDS = 4
REPLY_TIMEOUT_SECONDS = 240.0
REPLY_SETTLED_SECONDS = 4.0
HTTP_TIMEOUT_SECONDS = 120.0
MOST_OPEN_POSTS = 500
TEXTS = (
    "work has been a lot this week",
    "my manager moved the deadline again",
    "i didn't sleep much",
    "honestly i just want a quiet weekend",
    "do you think i should say something?",
    "anyway how are you",
    "haha yeah",
    "it's been a weird day",
)


class NotAWorktreeStackError(Exception):
    """Raised when the load test is pointed at the main stack."""


def check_worktree_stack(environment: Mapping[str, str]) -> None:
    """Refuse to run against anything but a worktree's own stack.

    Args:
        environment: The worktree's `.env` values.

    Raises:
        NotAWorktreeStackError: If the ports are the main stack's or no
            worktree Compose project is set.
    """
    if not environment.get("COMPOSE_PROJECT_NAME"):
        raise NotAWorktreeStackError(
            "No COMPOSE_PROJECT_NAME; run make worktree-setup in a worktree first."
        )
    if environment.get("BACKEND_PORT", MAIN_BACKEND_PORT) == MAIN_BACKEND_PORT:
        raise NotAWorktreeStackError("BACKEND_PORT is the main stack's.")
    if environment.get("POSTGRES_PORT", MAIN_POSTGRES_PORT) == MAIN_POSTGRES_PORT:
        raise NotAWorktreeStackError("POSTGRES_PORT is the main stack's.")


class LogWatcher:
    """Follows the backend's logs and notes what the load test needs from them.

    Times are when each line was read, on the script's own clock, so they
    compare with the times texts were posted.
    """

    def __init__(self, command: Sequence[str]) -> None:
        """Set up the watcher; nothing is read until it starts.

        Args:
            command: The command that prints the backend's logs as they come.
        """
        self._command = list(command)
        self._process: subprocess.Popen[str] | None = None
        self._changed = threading.Condition()
        self._sent_at: dict[int, list[float]] = {}
        self._ticks_started_at: list[float] = []
        self._ticks_took: list[tuple[float, float]] = []
        self.failed_replies = 0
        self.database_errors: list[str] = []
        self.fallback_warnings = 0
        self.model_calls: Counter[str] = Counter()

    def start(self) -> None:
        """Start following the logs on a background thread."""
        self._process = subprocess.Popen(
            self._command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        threading.Thread(target=self._follow, daemon=True).start()

    def stop(self) -> None:
        """Stop following the logs."""
        if self._process is not None:
            self._process.terminate()

    def _follow(self) -> None:
        """Read each log line as it comes and note it."""
        assert self._process is not None and self._process.stdout is not None
        for line in self._process.stdout:
            self.take(line.rstrip(), time.monotonic())

    def take(self, line: str, read_at: float) -> None:
        """Note what one log line says.

        Args:
            line: The log line.
            read_at: When it was read.
        """
        with self._changed:
            chat_id = sent_text_chat_id(line)
            if chat_id is not None:
                self._sent_at.setdefault(chat_id, []).append(read_at)
            seconds = tick_seconds(line)
            if seconds is not None:
                self._ticks_took.append((read_at, seconds))
            if TICK_STARTED_LOG in line:
                self._ticks_started_at.append(read_at)
            shape = model_call_shape(line)
            if shape is not None:
                self.model_calls[shape] += 1
            if is_failed_reply(line):
                self.failed_replies += 1
            if is_fallback_warning(line):
                self.fallback_warnings += 1
            if is_database_error(line):
                self.database_errors.append(line)
            self._changed.notify_all()

    def wait_for_reply(
        self, chat_id: int, after: float, timeout: float
    ) -> float | None:
        """Wait for the first text sent to a chat after a time.

        Args:
            chat_id: The chat.
            after: The time the reply must come after.
            timeout: How long to wait, in seconds.

        Returns:
            When it was sent; None if none came in time.
        """
        return self._wait_for(
            lambda: next(
                (at for at in self._sent_at.get(chat_id, []) if at > after), None
            ),
            timeout,
        )

    def wait_until_quiet(self, chat_id: int, quiet_seconds: float) -> None:
        """Wait until nothing more has been sent to a chat for a while.

        A reply can come in several texts; this lets all of them arrive.

        Args:
            chat_id: The chat.
            quiet_seconds: How long nothing must be sent.
        """
        while True:
            with self._changed:
                last_sent_at = max(self._sent_at.get(chat_id, [0.0]))
            quiet_for = time.monotonic() - last_sent_at
            if quiet_for >= quiet_seconds:
                return
            time.sleep(quiet_seconds - quiet_for)

    def wait_for_tick(self, started_after: float, timeout: float) -> float | None:
        """Wait for a tick that started after a time to finish.

        Ticks run one at a time, so the first one to finish after that start
        is it.

        Args:
            started_after: The time the tick must start after.
            timeout: How long to wait, in seconds.

        Returns:
            How long the tick took, in seconds; None if it didn't finish in time.
        """

        def took() -> float | None:
            """Find how long the first tick started after the time took."""
            started = next(
                (at for at in self._ticks_started_at if at > started_after), None
            )
            if started is None:
                return None
            return next(
                (seconds for at, seconds in self._ticks_took if at > started), None
            )

        return self._wait_for(took, timeout)

    def _wait_for(
        self, found: Callable[[], float | None], timeout: float
    ) -> float | None:
        """Wait until the logs show something.

        Args:
            found: Looks for it in what was noted so far; None if not there.
            timeout: How long to wait, in seconds.

        Returns:
            What was found; None if nothing was in time.
        """
        deadline = time.monotonic() + timeout
        with self._changed:
            while (value := found()) is None:
                left = deadline - time.monotonic()
                if left <= 0:
                    return None
                self._changed.wait(left)
            return value


class TelegramPoster:
    """Posts Telegram text updates to the backend's webhook, as Telegram would."""

    def __init__(self, client: httpx.Client, webhook_secret: str) -> None:
        """Set up the poster.

        Args:
            client: The HTTP client for the backend.
            webhook_secret: The webhook's secret token.
        """
        self._client = client
        self._webhook_secret = webhook_secret
        self._next_id = itertools.count(1)
        self._next_id_lock = threading.Lock()

    def post(self, chat_id: int, text: str) -> TimedCall:
        """Post one text from a User's private chat.

        Args:
            chat_id: The User's Telegram chat and account ID.
            text: The text.

        Returns:
            How long the post took and its status.
        """
        with self._next_id_lock:
            update_id = next(self._next_id)
        update: dict[str, Any] = {
            "update_id": update_id,
            "message": {
                "message_id": update_id,
                "date": int(time.time()),
                "from": {"id": chat_id, "is_bot": False},
                "chat": {"id": chat_id, "type": "private"},
                "text": text,
            },
        }
        return timed_call(
            lambda: self._client.post(
                "/telegram/webhook",
                json=update,
                headers={WEBHOOK_SECRET_HEADER: self._webhook_secret},
            )
        )


def timed_call(call: Callable[[], httpx.Response]) -> TimedCall:
    """Make an HTTP call and time it.

    Args:
        call: Makes the call.

    Returns:
        How long it took and its status; status 0 if it failed without one.
    """
    started = time.monotonic()
    try:
        status = call().status_code
    except httpx.HTTPError:
        status = 0
    return TimedCall(seconds=time.monotonic() - started, status=status)


def chat_as_user(
    chat_id: int,
    heavy_texter: bool,
    poster: TelegramPoster,
    posts: ThreadPoolExecutor,
    watcher: LogWatcher,
    rounds: list[MessageRound],
    post_results: list[Future[TimedCall]],
) -> None:
    """Chat back and forth as one User, waiting for each reply.

    A heavy texter sends each Message as a burst of 8 quick texts; anyone
    else sends one text and a short pause to read the reply. Texts are
    posted without waiting for the webhook to answer, as they are typed.

    Args:
        chat_id: The User's chat.
        heavy_texter: Whether they send bursts of texts.
        poster: Posts their texts.
        posts: Runs the posts.
        watcher: Tells when replies were sent.
        rounds: Where each Message they send is added.
        post_results: Where each post is added.
    """
    texts_per_message = BURST_TEXTS if heavy_texter else 1
    for _ in range(HEAVY_TEXTER_ROUNDS if heavy_texter else NORMAL_ROUNDS):
        for number in range(texts_per_message):
            if number:
                time.sleep(random.uniform(0.5, 1.5))
            last_text_at = time.monotonic()
            post_results.append(
                posts.submit(poster.post, chat_id, random.choice(TEXTS))
            )
        answered_at = watcher.wait_for_reply(
            chat_id, after=last_text_at, timeout=REPLY_TIMEOUT_SECONDS
        )
        rounds.append(
            MessageRound(
                chat_id=chat_id,
                texts=texts_per_message,
                last_text_at=last_text_at,
                answered_at=answered_at,
            )
        )
        if answered_at is not None:
            watcher.wait_until_quiet(chat_id, REPLY_SETTLED_SECONDS)
        time.sleep(random.uniform(2.0, 8.0))


def poll_dashboard(
    client: httpx.Client, token: str, stop: threading.Event, calls: list[TimedCall]
) -> None:
    """Call a Dashboard API page every few seconds until told to stop.

    Args:
        client: The HTTP client for the backend.
        token: The Admin's bearer token.
        stop: Set to stop.
        calls: Where each call is added.
    """
    headers = {"Authorization": f"Bearer {token}"}
    while not stop.is_set():
        calls.append(timed_call(lambda: client.get(DASHBOARD_PAGE, headers=headers)))
        stop.wait(DASHBOARD_EVERY_SECONDS)


def run_chat(
    repositories: Repositories,
    backend_url: str,
    webhook_secret: str,
    watcher: LogWatcher,
    users: int,
    heavy_users: int,
) -> tuple[list[MessageRound], list[TimedCall], list[TimedCall]]:
    """Have the test Users chat at once while a Dashboard page is timed.

    Args:
        repositories: The stack's database.
        backend_url: The backend's address.
        webhook_secret: The webhook's secret token.
        watcher: Follows the backend's logs.
        users: How many Users chat.
        heavy_users: How many of them send bursts of texts.

    Returns:
        Every Message sent, every webhook post and every Dashboard call.
    """
    now = datetime.now(UTC)
    chat_ids = create_chat_users(repositories, users, now)
    admin_token = create_admin(repositories, now)
    rounds: list[MessageRound] = []
    post_results: list[Future[TimedCall]] = []
    dashboard_calls: list[TimedCall] = []
    stop_dashboard = threading.Event()
    limits = httpx.Limits(max_connections=MOST_OPEN_POSTS)
    with (
        httpx.Client(
            base_url=backend_url, timeout=HTTP_TIMEOUT_SECONDS, limits=limits
        ) as webhook_client,
        httpx.Client(
            base_url=backend_url, timeout=HTTP_TIMEOUT_SECONDS
        ) as dashboard_client,
        ThreadPoolExecutor(max_workers=MOST_OPEN_POSTS) as posts,
    ):
        poster = TelegramPoster(webhook_client, webhook_secret)
        dashboard = threading.Thread(
            target=poll_dashboard,
            args=(dashboard_client, admin_token, stop_dashboard, dashboard_calls),
        )
        dashboard.start()
        chatters = [
            threading.Thread(
                target=chat_as_user,
                args=(
                    chat_id,
                    number < heavy_users,
                    poster,
                    posts,
                    watcher,
                    rounds,
                    post_results,
                ),
            )
            for number, chat_id in enumerate(chat_ids)
        ]
        for chatter in chatters:
            chatter.start()
        for chatter in chatters:
            chatter.join()
        stop_dashboard.set()
        dashboard.join()
        webhook_posts = [result.result() for result in post_results]
    return rounds, webhook_posts, dashboard_calls


def time_a_tick(
    repositories: Repositories, watcher: LogWatcher, users: int, timeout: float
) -> float | None:
    """Make Check-ins due and Conversations ended, then time the next tick.

    Args:
        repositories: The stack's database.
        watcher: Follows the backend's logs.
        users: How many due Check-ins and ended Conversations, each.
        timeout: How long to wait for the tick to finish, in seconds.

    Returns:
        How long the tick took; None if it didn't finish in time.
    """
    now = datetime.now(UTC)
    quiet_gap = repositories.platform_settings.load().get(CONVERSATION_QUIET_GAP)
    create_due_check_in_users(repositories, users, now)
    create_ended_conversations(repositories, users, now, quiet_gap)
    return watcher.wait_for_tick(started_after=time.monotonic(), timeout=timeout)


def parse_arguments() -> argparse.Namespace:
    """Read the command-line options; the defaults are the PRD's bar.

    Returns:
        The options.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--users", type=int, default=50)
    parser.add_argument("--heavy-users", type=int, default=10)
    parser.add_argument("--tick-users", type=int, default=100)
    parser.add_argument("--tick-timeout-minutes", type=float, default=120)
    return parser.parse_args()


def main() -> None:
    """Run the load test against this worktree's stack and print the report.

    Exits with 1 when a line of the bar fails.
    """
    arguments = parse_arguments()
    check_worktree_stack(os.environ)
    settings = load_settings({**os.environ, "POSTGRES_HOST": "localhost"})
    engine = create_engine(settings.database_url)
    repositories = build_postgres_repositories(engine)
    watcher = LogWatcher(
        [
            "docker",
            "compose",
            "-p",
            os.environ["COMPOSE_PROJECT_NAME"],
            "logs",
            "--follow",
            "--since",
            "1s",
            "--no-log-prefix",
            "backend",
        ]
    )
    delete_test_users(engine)
    watcher.start()
    try:
        print(
            f"Chat: {arguments.users} Users at once, {arguments.heavy_users} "
            f"sending bursts of {BURST_TEXTS} texts...",
            flush=True,
        )
        rounds, webhook_posts, dashboard_calls = run_chat(
            repositories,
            f"http://localhost:{os.environ['BACKEND_PORT']}",
            settings.telegram_webhook_secret,
            watcher,
            arguments.users,
            arguments.heavy_users,
        )
        print(
            f"Tick: {arguments.tick_users} due Check-ins and "
            f"{arguments.tick_users} ended Conversations, waiting for the next "
            "tick to finish...",
            flush=True,
        )
        tick = time_a_tick(
            repositories,
            watcher,
            arguments.tick_users,
            arguments.tick_timeout_minutes * 60,
        )
    finally:
        watcher.stop()
        delete_test_users(engine)
        engine.dispose()
    results = LoadTestResults(
        chat=ChatResults(
            users=arguments.users,
            heavy_users=arguments.heavy_users,
            rounds=tuple(rounds),
            webhook_posts=tuple(webhook_posts),
            failed_replies=watcher.failed_replies,
            database_errors=tuple(watcher.database_errors),
            fallback_warnings=watcher.fallback_warnings,
            model_calls=dict(watcher.model_calls),
            dashboard_calls=tuple(dashboard_calls),
        ),
        tick_users=arguments.tick_users,
        tick_seconds=tick,
    )
    print(write_report(results))
    sys.exit(1 if bar_failed(results) else 0)


if __name__ == "__main__":
    main()
