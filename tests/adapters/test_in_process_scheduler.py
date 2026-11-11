import threading

from companion.adapters.scheduler import InProcessScheduler


def test_the_tick_runs_every_interval_until_stopped() -> None:
    three_ticks = threading.Semaphore(0)
    tick_count = 0

    def tick() -> None:
        nonlocal tick_count
        tick_count += 1
        three_ticks.release()

    scheduler = InProcessScheduler(interval_seconds=0.01)
    scheduler.start(tick)
    for _ in range(3):
        assert three_ticks.acquire(timeout=2)
    scheduler.stop()
    ticks_when_stopped = tick_count
    threading.Event().wait(0.1)

    assert tick_count == ticks_when_stopped


def test_a_failing_tick_does_not_stop_the_loop() -> None:
    second_tick = threading.Event()
    calls = 0

    def tick() -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("database down")
        second_tick.set()

    scheduler = InProcessScheduler(interval_seconds=0.01)
    scheduler.start(tick)

    assert second_tick.wait(timeout=2)
    scheduler.stop()
