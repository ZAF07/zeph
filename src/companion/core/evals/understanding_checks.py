from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace

from companion.core.evals.cases import UnderstandingExpectations

UNDERSTANDING_STEP = "Understanding"
RECALL_STEP = "Recall"
REPLY_PLAN_STEP = "Reply Plan"


@dataclass(frozen=True)
class ObservedUnderstanding:
    """What one Message's Understanding and Reply Plan did, as the eval saw it.

    Attributes:
        need: The Need the Reply Plan picked.
        reply_plan_input: What the Reply Plan model was given, from the
            Model Call Log; the Life Threads the Companion was reminded of
            are in it.
        raised_threads: The titles of the Life Threads it brought up.
        raised_curiosities: How many Curiosities it brought up.
        asked_why: Whether the reply was asked to gently ask why.
        knowledge_documents: The titles of the Knowledge documents it chose
            to search; empty when none.
        knowledge_in_reply: The Knowledge documents whose passages reached
            the reply's instructions.
        woven_in: Whether the Reply Plan chose to weave the due Check-in
            into the reply.
        lead_move: The Move the reply led with; None for none.
        support_move: The Move that supported it; None for none.
        next_move: The Move it had in mind to make next; None for none.
        struggling: Whether the Understanding read the User as struggling.
        cause_known: Whether the Understanding knew why they feel that way.
        looked_up_past: Whether the Understanding asked to look up the past.
        feelings_said: Whether the Understanding kept feelings the User said
            in their own words.
        wants_said: Whether the Understanding kept wants the User said in
            their own words.
        read_formed: Whether the Reply Plan formed a Read.
        read_said: Whether the Reply Plan had the reply say its Read.
    """

    need: str
    reply_plan_input: str
    raised_threads: list[str]
    raised_curiosities: int
    asked_why: bool
    knowledge_documents: list[str]
    knowledge_in_reply: list[str]
    woven_in: bool
    lead_move: str | None = None
    support_move: str | None = None
    next_move: str | None = None
    struggling: bool = False
    cause_known: bool = False
    looked_up_past: bool = False
    feelings_said: bool = False
    wants_said: bool = False
    read_formed: bool = False
    read_said: bool = False


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


def check_yes_no(
    name: str, expected: bool, observed: bool, yes_detail: str, no_detail: str
) -> CheckResult:
    """Check something was so, or wasn't, as expected.

    Args:
        name: What is checked, e.g. "struggling".
        expected: Whether it must be so.
        observed: Whether it was.
        yes_detail: What happened when it was so.
        no_detail: What happened when it wasn't.

    Returns:
        The check's outcome, e.g. "not struggling, expected: struggling".
    """
    detail = yes_detail if observed else no_detail
    if observed == expected:
        return CheckResult(name, True, detail)
    wanted = yes_detail if expected else no_detail
    return CheckResult(name, False, f"{detail}, expected: {wanted}")


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


def is_one_of(name: str, allowed: Sequence[str]) -> bool:
    """Say whether a Move's name is among those allowed, ignoring case.

    Args:
        name: The Move's name.
        allowed: The names allowed.

    Returns:
        True if it is.
    """
    return name.lower() in {other.lower() for other in allowed}


def describe_moves_made(lead_move: str | None, support_move: str | None) -> str:
    """Say which Moves a reply made, for a check's detail.

    Args:
        lead_move: The Move it led with; None for none.
        support_move: The Move that supported it; None for none.

    Returns:
        E.g. "led with Research", "made no lead Move (supported with Calm)"
        or "made no Move".
    """
    if lead_move is not None:
        return f"led with {lead_move}"
    if support_move is not None:
        return f"made no lead Move (supported with {support_move})"
    return "made no Move"


def check_move_made(
    name: str, allowed: list[str], made: str | None, made_detail: str, none_detail: str
) -> CheckResult:
    """Check a reply's lead or supporting Move is one of those allowed.

    Args:
        name: The check's name, e.g. "lead move".
        allowed: The Moves allowed.
        made: The Move made; None for none.
        made_detail: What it did when a Move was made, with `{move}` for it.
        none_detail: What it did when none was made.

    Returns:
        The check's outcome.
    """
    expected = " or ".join(allowed)
    if made is None:
        return CheckResult(name, False, f"{none_detail}, expected {expected}")
    detail = made_detail.format(move=made)
    if is_one_of(made, allowed):
        return CheckResult(name, True, detail)
    return CheckResult(name, False, f"{detail}, expected {expected}")


def check_no_move(
    expected: bool, lead_move: str | None, support_move: str | None
) -> CheckResult:
    """Check the reply made no Move at all, or led with one, as expected.

    Args:
        expected: True if it must make no Move; False if it must lead with one.
        lead_move: The Move it led with; None for none.
        support_move: The Move that supported it; None for none.

    Returns:
        The check's outcome.
    """
    made = describe_moves_made(lead_move, support_move)
    if expected:
        made_none = lead_move is None and support_move is None
        return CheckResult(
            "no move", made_none, made if made_none else f"{made}, expected no Move"
        )
    if lead_move is None:
        return CheckResult("no move", False, f"{made}, expected one")
    return CheckResult("no move", True, made)


def check_next_move(allowed: list[str], next_move: str | None) -> CheckResult:
    """Check the Move the Understanding has in mind next is one of those allowed.

    Args:
        allowed: The Moves it may have in mind.
        next_move: The Move it has in mind; None for none.

    Returns:
        The check's outcome.
    """
    return check_move_made(
        "next move",
        allowed,
        next_move,
        "has {move} in mind next",
        "has no next Move in mind",
    )


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
        chosen: The titles of the documents the Understanding chose.
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


def check_woven_in(expected: bool, woven_in: bool) -> CheckResult:
    """Check the due Check-in was woven in, or left for later, as expected.

    Args:
        expected: Whether it must be woven in.
        woven_in: Whether the Reply Plan chose to weave it in.

    Returns:
        The check's outcome.
    """
    detail = "wove in the due Check-in" if woven_in else "said not now"
    if woven_in != expected:
        detail += ", expected not now" if woven_in else ", expected it woven in"
    return CheckResult("woven in", woven_in == expected, detail)


def mark_with_step(step: str, results: list[CheckResult]) -> list[CheckResult]:
    """Mark checks with the step that owns them.

    Args:
        step: The step, e.g. "Reply Plan".
        results: Its checks.

    Returns:
        The checks, each named e.g. "Reply Plan · need".
    """
    return [replace(result, name=f"{step} · {result.name}") for result in results]


def check_understanding_step(
    expect: UnderstandingExpectations, observed: ObservedUnderstanding
) -> list[CheckResult]:
    """Check what the Understanding read: struggling, cause, look-ups, said.

    Args:
        expect: What it should have read; None fields aren't checked.
        observed: What it read.

    Returns:
        One outcome per check: struggling, cause known, looked up the past,
        feelings said, then wants said.
    """
    flags = [
        (
            "struggling",
            expect.struggling,
            observed.struggling,
            "struggling",
            "not struggling",
        ),
        (
            "cause known",
            expect.cause_known,
            observed.cause_known,
            "knew why they feel this way",
            "didn't know why they feel this way",
        ),
        (
            "looks up the past",
            expect.looks_up_past,
            observed.looked_up_past,
            "looked up the past",
            "looked up nothing",
        ),
        (
            "feelings said",
            expect.feelings_said,
            observed.feelings_said,
            "kept feelings said in their words",
            "kept no feelings as said",
        ),
        (
            "wants said",
            expect.wants_said,
            observed.wants_said,
            "kept wants said in their words",
            "kept no wants as said",
        ),
    ]
    return [
        check_yes_no(name, expected, seen, yes_detail, no_detail)
        for name, expected, seen, yes_detail, no_detail in flags
        if expected is not None
    ]


def check_recall(
    expect: UnderstandingExpectations, observed: ObservedUnderstanding
) -> list[CheckResult]:
    """Check Recall reminded the Companion of each Life Thread expected.

    A Life Thread counts as found when its title is in what the Reply Plan
    model was given; the cases file keeps titles out of the rest of the
    memory, so only being reminded puts it there.

    Args:
        expect: The Threads to be found.
        observed: What the Reply Plan was given.

    Returns:
        One outcome per Thread.
    """
    return check_each_thread(
        "found",
        expect.found,
        lambda title: title in observed.reply_plan_input,
        "was reminded of {title}",
        "wasn't reminded of {title}",
    )


def check_reply_plan(
    expect: UnderstandingExpectations, observed: ObservedUnderstanding
) -> list[CheckResult]:
    """Check what the Reply Plan decided.

    Args:
        expect: What it should have decided; empty fields aren't checked.
        observed: What it decided.

    Returns:
        One outcome per check, in a fixed order: the Read formed and said,
        the Need, the lead, supporting, no and next Move, each Thread to be
        brought up and left alone, then the Curiosity, asking why, Knowledge
        and the woven-in Check-in.
    """
    checks = []
    if expect.read_formed is not None:
        checks.append(
            check_yes_no(
                "read formed",
                expect.read_formed,
                observed.read_formed,
                "formed a Read",
                "formed no Read",
            )
        )
    if expect.read_said is not None:
        checks.append(
            check_yes_no(
                "read said",
                expect.read_said,
                observed.read_said,
                "said the Read",
                "held the Read back",
            )
        )
    if expect.need:
        checks.append(check_need(expect.need, observed.need))
    if expect.lead_move:
        checks.append(
            check_move_made(
                "lead move",
                expect.lead_move,
                observed.lead_move,
                "led with {move}",
                describe_moves_made(None, observed.support_move),
            )
        )
    if expect.support_move:
        checks.append(
            check_move_made(
                "supporting move",
                expect.support_move,
                observed.support_move,
                "supported with {move}",
                "had no supporting Move",
            )
        )
    if expect.no_move is not None:
        checks.append(
            check_no_move(expect.no_move, observed.lead_move, observed.support_move)
        )
    if expect.next_move:
        checks.append(check_next_move(expect.next_move, observed.next_move))
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
    if expect.woven_in is not None:
        checks.append(check_woven_in(expect.woven_in, observed.woven_in))
    return checks


def check_steps(
    expect: UnderstandingExpectations, observed: ObservedUnderstanding
) -> list[CheckResult]:
    """Check one Message on each step that owns an expectation.

    The Understanding owns what it reads, Recall owns the Life Threads found
    and the Reply Plan owns what the reply does, so a failed check says
    which step went wrong.

    Args:
        expect: What the Message should do; empty fields aren't checked.
        observed: What its steps did.

    Returns:
        The Understanding's checks, then Recall's, then the Reply Plan's,
        each named after its step, e.g. "Reply Plan · need".
    """
    return [
        *mark_with_step(UNDERSTANDING_STEP, check_understanding_step(expect, observed)),
        *mark_with_step(RECALL_STEP, check_recall(expect, observed)),
        *mark_with_step(REPLY_PLAN_STEP, check_reply_plan(expect, observed)),
    ]
