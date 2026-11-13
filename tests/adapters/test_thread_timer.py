import threading

import pytest

from companion.adapters.timer import ThreadTimer


def test_the_work_runs_once_after_the_wait() -> None:
    ran = threading.Semaphore(0)

    ThreadTimer().start("album", 0.01, ran.release)

    assert ran.acquire(timeout=2)
    assert not ran.acquire(timeout=0.1)


def test_starting_the_same_key_again_restarts_the_wait_and_runs_only_the_last() -> None:
    timer = ThreadTimer()
    runs: list[str] = []
    done = threading.Event()

    def last() -> None:
        runs.append("last")
        done.set()

    timer.start("album", 0.2, lambda: runs.append("first"))
    timer.start("album", 0.01, last)

    assert done.wait(timeout=2)
    threading.Event().wait(0.3)
    assert runs == ["last"]


def test_different_keys_wait_separately() -> None:
    timer = ThreadTimer()
    both = threading.Semaphore(0)

    timer.start("album-1", 0.01, both.release)
    timer.start("album-2", 0.01, both.release)

    assert both.acquire(timeout=2)
    assert both.acquire(timeout=2)


def test_failing_work_is_logged_not_raised(caplog: pytest.LogCaptureFixture) -> None:
    timer = ThreadTimer()
    failed = threading.Event()
    after = threading.Event()

    def fail() -> None:
        failed.set()
        raise RuntimeError("boom")

    timer.start("bad", 0.01, fail)
    assert failed.wait(timeout=2)
    timer.start("good", 0.05, after.set)

    assert after.wait(timeout=2)
    assert "Work run after a wait failed" in caplog.text
