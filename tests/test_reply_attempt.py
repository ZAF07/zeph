import pytest

from companion.core.reply_attempt import ReplyAttempt, ReplyDroppedError
from companion.core.reply_gate import ReplyNeeded, Stopped, StopReason


class SendingNotes:
    """Counts how often a try's `on_sending` ran."""

    def __init__(self) -> None:
        """Start with no runs."""
        self.runs = 0

    def note(self) -> None:
        """Note one run."""
        self.runs += 1


def test_a_try_dropped_before_sending_sends_nothing() -> None:
    notes = SendingNotes()
    attempt = ReplyAttempt(on_sending=notes.note)

    attempt.drop()

    with pytest.raises(ReplyDroppedError):
        attempt.start_sending()
    assert notes.runs == 0
    assert attempt.finish() is True


def test_a_try_that_started_sending_cannot_be_dropped() -> None:
    notes = SendingNotes()
    attempt = ReplyAttempt(on_sending=notes.note)

    attempt.start_sending()
    attempt.drop()
    attempt.start_sending()

    assert notes.runs == 1
    assert attempt.finish() is False


def test_a_try_that_ended_cannot_be_dropped() -> None:
    attempt = ReplyAttempt(on_sending=SendingNotes().note)

    assert attempt.finish() is False
    attempt.drop()

    assert attempt.finish() is False


def test_house_rules_that_stop_the_message_settle_the_try() -> None:
    notes = SendingNotes()
    attempt = ReplyAttempt(on_sending=notes.note)

    result = attempt.apply_house_rules(lambda: Stopped(StopReason.OVER_LIMIT))
    attempt.drop()

    assert result == Stopped(StopReason.OVER_LIMIT)
    assert notes.runs == 1
    assert attempt.finish() is False


def test_house_rules_passed_by_an_earlier_try_are_not_applied_again() -> None:
    passed = ReplyNeeded(data_deletion_note="")
    attempt = ReplyAttempt(on_sending=SendingNotes().note, house_rules=passed)

    def apply_again() -> ReplyNeeded:
        raise AssertionError("house rules applied twice")

    assert attempt.apply_house_rules(apply_again) is passed


def test_house_rules_are_not_applied_to_a_dropped_try() -> None:
    attempt = ReplyAttempt(on_sending=SendingNotes().note)
    attempt.drop()

    with pytest.raises(ReplyDroppedError):
        attempt.apply_house_rules(lambda: ReplyNeeded(data_deletion_note=""))
    assert attempt.house_rules is None
