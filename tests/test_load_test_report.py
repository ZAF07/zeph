import pytest

from scripts.load_test.report import (
    ChatResults,
    LoadTestResults,
    MessageRound,
    TimedCall,
    bar_failed,
    is_database_error,
    is_failed_reply,
    model_call_shape,
    sent_text_chat_id,
    tick_seconds,
    write_report,
)


def results(
    rounds: tuple[MessageRound, ...] = (
        MessageRound(chat_id=1, texts=3, last_text_at=10.0, answered_at=30.0),
        MessageRound(chat_id=2, texts=1, last_text_at=10.0, answered_at=50.0),
    ),
    failed_replies: int = 0,
    database_errors: tuple[str, ...] = (),
    dashboard_calls: tuple[TimedCall, ...] = (
        TimedCall(seconds=0.2, status=200),
        TimedCall(seconds=0.4, status=200),
    ),
    tick: float | None = 75.0,
) -> LoadTestResults:
    return LoadTestResults(
        chat=ChatResults(
            users=2,
            heavy_users=1,
            rounds=rounds,
            webhook_posts=(TimedCall(seconds=0.1, status=200),),
            failed_replies=failed_replies,
            database_errors=database_errors,
            fallback_warnings=0,
            model_calls={"reply": 2, "safeguard": 4},
            dashboard_calls=dashboard_calls,
        ),
        tick_users=100,
        tick_seconds=tick,
    )


def test_a_sent_text_names_its_chat() -> None:
    line = "Load test: sent a text to chat 9100000004"

    assert sent_text_chat_id(line) == 9100000004
    assert sent_text_chat_id("Load test: sent a sticker to chat 9100000004") is None


def test_failed_replies_and_database_errors_are_spotted() -> None:
    assert is_failed_reply("Could not answer a Message from a User")
    assert is_failed_reply("Could not check a text from a User")
    assert not is_failed_reply("A new text started a User's reply over")
    assert is_database_error(
        "sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached"
    )
    assert is_database_error("psycopg.OperationalError: connection failed")
    assert not is_database_error("Load test: answered a reply call")


def test_tick_times_and_model_calls_are_read() -> None:
    assert tick_seconds("Load test: tick took 61.5s") == pytest.approx(61.5)
    assert tick_seconds("Load test: tick started") is None
    assert model_call_shape("Load test: answered a reply plan call") == "reply plan"
    assert model_call_shape("Load test: tick started") is None


def test_a_run_that_meets_the_bar_passes_every_line() -> None:
    report = write_report(results())

    assert not bar_failed(results())
    assert "PASS  Texts answered" in report
    assert "4 / 4" in report
    assert "PASS  Failed replies" in report
    assert "PASS  Database timeouts" in report
    assert "PASS  Dashboard API" in report
    assert "75.0s" in report
    assert "FAIL" not in report


def test_an_unanswered_message_fails_the_run() -> None:
    unanswered = (
        MessageRound(chat_id=1, texts=8, last_text_at=10.0, answered_at=None),
        MessageRound(chat_id=2, texts=1, last_text_at=10.0, answered_at=40.0),
    )

    assert bar_failed(results(rounds=unanswered))
    assert "FAIL  Texts answered" in write_report(results(rounds=unanswered))
    assert "1 / 9" in write_report(results(rounds=unanswered))


def test_failures_database_errors_and_a_slow_dashboard_each_fail_the_run() -> None:
    slow = (TimedCall(seconds=0.2, status=200), TimedCall(seconds=1.4, status=200))
    broken = (TimedCall(seconds=0.2, status=500),)

    assert bar_failed(results(failed_replies=1))
    assert bar_failed(results(database_errors=("sqlalchemy.exc.TimeoutError: x",)))
    assert bar_failed(results(dashboard_calls=slow))
    assert bar_failed(results(dashboard_calls=broken))
    assert "FAIL  Dashboard API" in write_report(results(dashboard_calls=slow))
    assert "1 of 2 calls over 1s" in write_report(results(dashboard_calls=slow))


def test_a_slow_or_unfinished_tick_is_reported_but_never_fails_the_run() -> None:
    assert not bar_failed(results(tick=3000.0))
    assert not bar_failed(results(tick=None))
    assert "did not finish" in write_report(results(tick=None))
