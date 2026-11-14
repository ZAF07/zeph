from collections.abc import Callable, Sequence
from dataclasses import dataclass

from evals.cases import UnderstandingExpectations


@dataclass(frozen=True)
class ObservedUnderstanding:
    """What one Message's Understanding did, as the eval saw it.

    Attributes:
        need: The Need it picked.
        understanding_input: What the Understanding model was given, from
            the Model Call Log; the Life Threads the Companion was reminded
            of are in it.
        raised_threads: The titles of the Life Threads it brought up.
        raised_curiosities: How many Curiosities it brought up.
        asked_why: Whether the reply was asked to gently ask why.
        knowledge_documents: The Knowledge documents it chose to search, as
            it named them; empty when none.
        knowledge_in_reply: The Knowledge documents whose passages reached
            the reply's instructions.
    """

    need: str
    understanding_input: str
    raised_threads: list[str]
    raised_curiosities: int
    asked_why: bool
    knowledge_documents: list[str]
    knowledge_in_reply: list[str]


@dataclass(frozen=True)
class CheckResult:
    """The outcome of one check on a Message's Understanding.

    Attributes:
        name: What was checked, e.g. "need".
        passed: Whether it did what was expected.
        detail: What it did, and what was expected when it failed.
    """

    name: str
    passed: bool
    detail: str


def check_need(allowed: list[str], need: str) -> CheckResult:
    """Check the Need picked is one of those allowed.

    Args:
        allowed: The Needs that may be picked.
        need: The Need picked.

    Returns:
        The check's outcome.
    """
    if need in allowed:
        return CheckResult("need", True, f"picked {need}")
    expected = " or ".join(allowed)
    return CheckResult("need", False, f"picked {need}, expected {expected}")


def check_each_thread(
    name: str,
    titles: Sequence[str],
    is_met: Callable[[str], bool],
    passed_detail: str,
    failed_detail: str,
) -> list[CheckResult]:
    """Check each Life Thread a case names for one expectation.

    Args:
        name: What is checked, e.g. "raised".
        titles: The Threads' titles.
        is_met: Says whether the expectation is met for a title.
        passed_detail: What it did when met, with `{title}` for the title.
        failed_detail: What it did when not met, with `{title}`.

    Returns:
        One outcome per Thread.
    """
    return [
        CheckResult(name, True, passed_detail.format(title=title))
        if is_met(title)
        else CheckResult(name, False, failed_detail.format(title=title))
        for title in titles
    ]


def check_curiosity(expected: bool, raised: int) -> CheckResult:
    """Check a Curiosity was brought up, or wasn't, as expected.

    Args:
        expected: Whether one must be brought up.
        raised: How many were brought up.

    Returns:
        The check's outcome.
    """
    if raised == 0:
        return CheckResult("curiosity", not expected, "brought up no Curiosity")
    counted = "1 Curiosity" if raised == 1 else f"{raised} Curiosities"
    if expected:
        return CheckResult("curiosity", True, f"brought up {counted}")
    return CheckResult("curiosity", False, f"brought up {counted}, expected none")


def check_asked_why(expected: bool, asked_why: bool) -> CheckResult:
    """Check the reply was asked to gently ask why, or wasn't, as expected.

    Args:
        expected: Whether it must ask.
        asked_why: Whether it was asked to.

    Returns:
        The check's outcome.
    """
    if asked_why == expected:
        detail = "asked why" if asked_why else "didn't ask why"
        return CheckResult("asked why", True, detail)
    if asked_why:
        return CheckResult("asked why", False, "asked why, expected not to")
    return CheckResult("asked why", False, "didn't ask why")


def check_knowledge(
    expected: bool, chosen: list[str], in_reply: list[str]
) -> CheckResult:
    """Check Knowledge was chosen and reached the reply, or neither, as expected.

    Args:
        expected: Whether Knowledge must be chosen and reach the reply.
        chosen: The documents the Understanding chose, as it named them.
        in_reply: The documents whose passages reached the reply.

    Returns:
        The check's outcome.
    """
    if not chosen and not in_reply:
        return CheckResult("knowledge", not expected, "chose no document")
    chosen_names = ", ".join(chosen) or "no document"
    if not expected:
        return CheckResult("knowledge", False, f"chose {chosen_names}, expected none")
    if not in_reply:
        return CheckResult(
            "knowledge",
            False,
            f"chose {chosen_names}, but no passage reached the reply",
        )
    return CheckResult(
        "knowledge",
        True,
        f"chose {chosen_names}; passages from {', '.join(in_reply)} reached the reply",
    )


def check_understanding(
    expect: UnderstandingExpectations, observed: ObservedUnderstanding
) -> list[CheckResult]:
    """Check one Message's Understanding against what it should have done.

    A Life Thread counts as found when its title is in what the
    Understanding model was given; the cases file keeps titles out of the
    rest of the memory, so only being reminded puts it there.

    Args:
        expect: What it should have done; empty fields aren't checked.
        observed: What it did.

    Returns:
        One outcome per check, in a fixed order: the Need, each Thread to
        be found, brought up and left alone, then the Curiosity, asking why
        and Knowledge.
    """
    checks = []
    if expect.need:
        checks.append(check_need(expect.need, observed.need))
    checks += check_each_thread(
        "found",
        expect.found,
        lambda title: title in observed.understanding_input,
        "was reminded of {title}",
        "wasn't reminded of {title}",
    )
    checks += check_each_thread(
        "raised",
        expect.raised,
        lambda title: title in observed.raised_threads,
        "brought up {title}",
        "didn't bring up {title}",
    )
    checks += check_each_thread(
        "not raised",
        expect.not_raised,
        lambda title: title not in observed.raised_threads,
        "left {title} alone",
        "brought up {title}",
    )
    if expect.curiosity_raised is not None:
        checks.append(
            check_curiosity(expect.curiosity_raised, observed.raised_curiosities)
        )
    if expect.asked_why is not None:
        checks.append(check_asked_why(expect.asked_why, observed.asked_why))
    if expect.knowledge is not None:
        checks.append(
            check_knowledge(
                expect.knowledge,
                observed.knowledge_documents,
                observed.knowledge_in_reply,
            )
        )
    return checks
