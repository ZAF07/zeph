import threading

import pytest

from companion.adapters.user_work_queue import ThreadPoolUserWorkQueue

WAIT_SECONDS = 2


def test_one_users_work_runs_in_the_order_it_was_added() -> None:
    queue = ThreadPoolUserWorkQueue(max_running=4)
    runs: list[int] = []
    done = threading.Event()

    for number in range(20):
        queue.add("user-1", lambda number=number: runs.append(number))
    queue.add("user-1", done.set)

    assert done.wait(timeout=WAIT_SECONDS)
    assert runs == list(range(20))


def test_one_users_work_runs_one_piece_at_a_time() -> None:
    queue = ThreadPoolUserWorkQueue(max_running=4)
    first_started = threading.Event()
    let_first_finish = threading.Event()
    second_started = threading.Event()

    def first() -> None:
        first_started.set()
        let_first_finish.wait(timeout=WAIT_SECONDS)

    queue.add("user-1", first)
    queue.add("user-1", second_started.set)

    assert first_started.wait(timeout=WAIT_SECONDS)
    assert not second_started.wait(timeout=0.1)
    let_first_finish.set()
    assert second_started.wait(timeout=WAIT_SECONDS)


def test_different_users_work_runs_side_by_side() -> None:
    queue = ThreadPoolUserWorkQueue(max_running=4)
    both_running = threading.Barrier(2, timeout=WAIT_SECONDS)
    done = threading.Semaphore(0)

    def meet_the_other_user() -> None:
        both_running.wait()
        done.release()

    queue.add("user-1", meet_the_other_user)
    queue.add("user-2", meet_the_other_user)

    assert done.acquire(timeout=WAIT_SECONDS)
    assert done.acquire(timeout=WAIT_SECONDS)


def test_no_more_than_the_limit_run_at_once() -> None:
    queue = ThreadPoolUserWorkQueue(max_running=2)
    guard = threading.Lock()
    running = 0
    most_running = 0
    let_finish = threading.Event()
    finished = threading.Semaphore(0)

    def hold_a_place() -> None:
        nonlocal running, most_running
        with guard:
            running += 1
            most_running = max(most_running, running)
        let_finish.wait(timeout=WAIT_SECONDS)
        with guard:
            running -= 1
        finished.release()

    for number in range(5):
        queue.add(f"user-{number}", hold_a_place)
    threading.Event().wait(0.2)
    let_finish.set()

    for _ in range(5):
        assert finished.acquire(timeout=WAIT_SECONDS)
    assert most_running == 2


def test_failed_work_is_logged_and_the_users_later_work_still_runs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    queue = ThreadPoolUserWorkQueue(max_running=4)
    after = threading.Event()

    def fail() -> None:
        raise RuntimeError("boom")

    queue.add("user-1", fail)
    queue.add("user-1", after.set)

    assert after.wait(timeout=WAIT_SECONDS)
    assert "A User's queued work failed" in caplog.text
