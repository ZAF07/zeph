from dataclasses import dataclass

from evals.cases import UnderstandingExpectations


@dataclass(frozen=True)
class ObservedUnderstanding:
    """What one Message's Understanding did, as the eval saw it.

    Attributes:
        need: The Need it picked.
        shown: What the Understanding model was given, from the Model Call
            Log; the Life Threads the Companion was reminded of are in it.
        raised_threads: The titles of the Life Threads it brought up.
        raised_curiosities: How many Curiosities it brought up.
        asked_why: Whether the reply was asked to gently ask why.
        knowledge_documents: The Knowledge documents it chose to search;
            empty when none.
    """

    need: str
    shown: str
    raised_threads: list[str]
    raised_curiosities: int
    asked_why: bool
    knowledge_documents: list[str]


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


def check_knowledge(expected: bool, documents: list[str]) -> CheckResult:
    """Check Knowledge documents were chosen, or weren't, as expected.

    Args:
        expected: Whether some must be chosen.
        documents: The documents chosen.

    Returns:
        The check's outcome.
    """
    if not documents:
        return CheckResult("knowledge", not expected, "chose no document")
    chosen = ", ".join(documents)
    if expected:
        return CheckResult("knowledge", True, f"chose {chosen}")
    return CheckResult("knowledge", False, f"chose {chosen}, expected none")


def check_understanding(
    expect: UnderstandingExpectations, observed: ObservedUnderstanding
) -> list[CheckResult]:
    """Check one Message's Understanding against what it should have done.

    A Life Thread counts as found when its title is in what the
    Understanding model was given.

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
    for title in expect.found:
        if title in observed.shown:
            checks.append(CheckResult("found", True, f"was reminded of {title}"))
        else:
            checks.append(CheckResult("found", False, f"wasn't reminded of {title}"))
    for title in expect.raised:
        if title in observed.raised_threads:
            checks.append(CheckResult("raised", True, f"brought up {title}"))
        else:
            checks.append(CheckResult("raised", False, f"didn't bring up {title}"))
    for title in expect.not_raised:
        if title in observed.raised_threads:
            checks.append(CheckResult("not raised", False, f"brought up {title}"))
        else:
            checks.append(CheckResult("not raised", True, f"left {title} alone"))
    if expect.curiosity_raised is not None:
        checks.append(
            check_curiosity(expect.curiosity_raised, observed.raised_curiosities)
        )
    if expect.asked_why is not None:
        checks.append(check_asked_why(expect.asked_why, observed.asked_why))
    if expect.knowledge is not None:
        checks.append(check_knowledge(expect.knowledge, observed.knowledge_documents))
    return checks
