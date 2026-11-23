"""Read the backend's load-test logs and write the load test's report."""

import re
import statistics
from collections.abc import Sequence
from dataclasses import dataclass

from companion.adapters.load_test.chat_channel import SENT_TEXT_LOG_PREFIX
from companion.adapters.load_test.chat_model import ANSWERED_CALL_LOG_PREFIX
from companion.adapters.load_test.scheduler import TICK_TOOK_LOG_PREFIX

DASHBOARD_BAR_SECONDS = 1.0
TICK_TARGET_SECONDS = 60.0
FAILED_REPLY_LOGS = (
    "Could not answer a Message from a User",
    "Could not check a text from a User",
)
FALLBACK_LOG = "using the fallback"
SENT_TEXT = re.compile(re.escape(SENT_TEXT_LOG_PREFIX) + r"(-?\d+)")
TICK_TOOK = re.compile(re.escape(TICK_TOOK_LOG_PREFIX) + r"([\d.]+)s")
MODEL_CALL = re.compile(re.escape(ANSWERED_CALL_LOG_PREFIX) + r"(.+) call")
DATABASE_ERROR = re.compile(
    r"(sqlalchemy\.exc\.\w+|psycopg\.\w*Error|psycopg\.errors\.\w+):"
    r"|QueuePool limit|too many clients"
)
SHOWN_DATABASE_ERRORS = 5


@dataclass(frozen=True)
class MessageRound:
    """One Message a test User sent, and when its reply came.

    Attributes:
        chat_id: The User's chat.
        texts: How many texts the Message was.
        last_text_at: When its last text was posted, in seconds on the
            script's clock.
        answered_at: When the first reply text after it was sent; None if
            none came.
    """

    chat_id: int
    texts: int
    last_text_at: float
    answered_at: float | None


@dataclass(frozen=True)
class TimedCall:
    """One HTTP call the script made and how it went.

    Attributes:
        seconds: How long it took.
        status: Its HTTP status; 0 when it failed without one, e.g. a timeout.
    """

    seconds: float
    status: int


@dataclass(frozen=True)
class ChatResults:
    """What happened while the test Users chatted.

    Attributes:
        users: How many Users chatted.
        heavy_users: How many of them sent bursts of texts.
        rounds: Every Message they sent.
        webhook_posts: Every text posted to the webhook.
        failed_replies: Replies and text checks the backend logged as failed.
        database_errors: Database timeout and pool error lines it logged.
        fallback_warnings: Times it fell back from a model answer it
            couldn't read.
        model_calls: How many calls the load-test model answered, by shape.
        dashboard_calls: Every Dashboard API call made meanwhile.
    """

    users: int
    heavy_users: int
    rounds: tuple[MessageRound, ...]
    webhook_posts: tuple[TimedCall, ...]
    failed_replies: int
    database_errors: tuple[str, ...]
    fallback_warnings: int
    model_calls: dict[str, int]
    dashboard_calls: tuple[TimedCall, ...]


@dataclass(frozen=True)
class LoadTestResults:
    """Everything the load test measured.

    Attributes:
        chat: The chat part.
        tick_users: How many due Check-ins and ended Conversations the timed
            tick had, each.
        tick_seconds: How long that tick took; None if it didn't finish in
            time.
    """

    chat: ChatResults
    tick_users: int
    tick_seconds: float | None


def sent_text_chat_id(line: str) -> int | None:
    """Read which chat a sent text was for, from a load-test chat channel log.

    Args:
        line: A backend log line.

    Returns:
        The chat ID; None if the line isn't about a sent text.
    """
    match = SENT_TEXT.search(line)
    return int(match.group(1)) if match else None


def tick_seconds(line: str) -> float | None:
    """Read how long a tick took, from a load-test scheduler log.

    Args:
        line: A backend log line.

    Returns:
        The seconds; None if the line isn't about a finished tick.
    """
    match = TICK_TOOK.search(line)
    return float(match.group(1)) if match else None


def model_call_shape(line: str) -> str | None:
    """Read which kind of model call the load-test model answered.

    Args:
        line: A backend log line.

    Returns:
        The call's shape, e.g. "reply plan"; None if the line isn't one.
    """
    match = MODEL_CALL.search(line)
    return match.group(1) if match else None


def is_failed_reply(line: str) -> bool:
    """Tell whether a log line says a reply or a text check failed.

    Args:
        line: A backend log line.

    Returns:
        True if it does; the User then got the fallback reply.
    """
    return any(log in line for log in FAILED_REPLY_LOGS)


def is_fallback_warning(line: str) -> bool:
    """Tell whether a log line says a model answer couldn't be read or used.

    Args:
        line: A backend log line.

    Returns:
        True if the app fell back from a model answer.
    """
    return FALLBACK_LOG in line


def is_database_error(line: str) -> bool:
    """Tell whether a log line is a database timeout or connection pool error.

    Args:
        line: A backend log line.

    Returns:
        True if it is.
    """
    return DATABASE_ERROR.search(line) is not None


def seconds_summary(seconds: Sequence[float]) -> str:
    """Write the median and worst of some times.

    Args:
        seconds: The times.

    Returns:
        E.g. "median 0.12s, worst 0.80s"; "none" when there are none.
    """
    if not seconds:
        return "none"
    return f"median {statistics.median(seconds):.2f}s, worst {max(seconds):.2f}s"


def dashboard_passed(calls: Sequence[TimedCall]) -> bool:
    """Tell whether every Dashboard API call worked in under the bar.

    Args:
        calls: The calls.

    Returns:
        True if there were calls and all were 200s under 1s.
    """
    return bool(calls) and all(
        call.status == 200 and call.seconds < DASHBOARD_BAR_SECONDS for call in calls
    )


def bar_lines(results: LoadTestResults) -> list[tuple[str, str, bool]]:
    """Judge each line of the bar.

    Args:
        results: What the load test measured.

    Returns:
        (name, value, passed) for each line.
    """
    chat = results.chat
    texts = sum(round_.texts for round_ in chat.rounds)
    answered = sum(
        round_.texts for round_ in chat.rounds if round_.answered_at is not None
    )
    dashboard_errors = sum(1 for call in chat.dashboard_calls if call.status != 200)
    dashboard_slow = sum(
        1 for call in chat.dashboard_calls if call.seconds >= DASHBOARD_BAR_SECONDS
    )
    dashboard_value = (
        f"{seconds_summary([call.seconds for call in chat.dashboard_calls])}, "
        f"{dashboard_slow} of {len(chat.dashboard_calls)} calls over "
        f"{DASHBOARD_BAR_SECONDS:.0f}s, {dashboard_errors} not 200"
    )
    failed_posts = sum(1 for post in chat.webhook_posts if post.status != 200)
    webhook_value = (
        f"{seconds_summary([post.seconds for post in chat.webhook_posts])}, "
        f"{failed_posts} not 200"
    )
    return [
        ("Webhook posts", webhook_value, failed_posts == 0),
        ("Texts answered", f"{answered} / {texts}", answered == texts and texts > 0),
        ("Failed replies", str(chat.failed_replies), chat.failed_replies == 0),
        (
            "Database timeouts",
            str(len(chat.database_errors)),
            not chat.database_errors,
        ),
        ("Dashboard API", dashboard_value, dashboard_passed(chat.dashboard_calls)),
    ]


def bar_failed(results: LoadTestResults) -> bool:
    """Tell whether any line of the bar failed; the tick never fails it.

    Args:
        results: What the load test measured.

    Returns:
        True if a line failed.
    """
    return not all(passed for _, _, passed in bar_lines(results))


def write_report(results: LoadTestResults) -> str:
    """Write the report: each bar line passed or failed, then the other numbers.

    Args:
        results: What the load test measured.

    Returns:
        The report's text.
    """
    chat = results.chat
    texts = sum(round_.texts for round_ in chat.rounds)
    reply_seconds = [
        round_.answered_at - round_.last_text_at
        for round_ in chat.rounds
        if round_.answered_at is not None
    ]
    tick = (
        f"{results.tick_seconds:.1f}s"
        if results.tick_seconds is not None
        else "did not finish in time"
    )
    model_calls = ", ".join(
        f"{shape} {count}" for shape, count in sorted(chat.model_calls.items())
    )
    lines = [
        "Load test report",
        f"  {chat.users} Users chatting ({chat.heavy_users} sending bursts of "
        f"texts): {texts} texts in {len(chat.rounds)} Messages",
        "",
        *(
            f"  {'PASS' if passed else 'FAIL'}  {name:<20}{value}"
            for name, value, passed in bar_lines(results)
        ),
        "",
        f"  INFO  {'Reply time':<20}{seconds_summary(reply_seconds)} "
        "(a Message's last text to its first reply, with the Message wait)",
        f"  INFO  {'Fallback answers':<20}{chat.fallback_warnings}",
        f"  INFO  {'Load-test model':<20}{model_calls or 'no calls'}",
        f"  INFO  {'Tick':<20}{tick} for {results.tick_users} due Check-ins and "
        f"{results.tick_users} ended Conversations "
        f"(target {TICK_TARGET_SECONDS:.0f}s, not part of the bar)",
    ]
    if chat.database_errors:
        lines += ["", "  Database errors (first few):"]
        distinct_errors = list(dict.fromkeys(chat.database_errors))
        lines += [f"    {line}" for line in distinct_errors[:SHOWN_DATABASE_ERRORS]]
    return "\n".join(lines)
