import logging
import threading

from companion.adapters.evals.logged_failures import logged_failures

logger = logging.getLogger("companion.core.post_conversation")


def test_a_failure_the_app_logs_is_kept_with_what_went_wrong() -> None:
    with logged_failures() as failures:
        try:
            raise ValueError("no bar")
        except ValueError:
            logger.exception("Could not score Patterns")
        logger.error("Could not send %s", "a Check-in")
        logger.warning("Slow answer")

    assert failures == [
        "Could not score Patterns: ValueError('no bar')",
        "Could not send a Check-in",
    ]


def test_another_thread_s_failure_is_left_out() -> None:
    with logged_failures() as failures:
        other = threading.Thread(target=lambda: logger.error("Could not reply"))
        other.start()
        other.join()

    assert failures == []


def test_nothing_is_kept_once_the_block_is_over() -> None:
    with logged_failures() as failures:
        pass
    logger.error("Could not score Patterns")

    assert failures == []
