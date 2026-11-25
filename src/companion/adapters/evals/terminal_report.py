from collections.abc import Callable, Sequence
from typing import Any

from companion.core.evals.models import (
    CaseOutcome,
    CaseResult,
    Check,
    Cost,
    Estimate,
    EvalName,
    EvalRunOverview,
)
from companion.core.evals.whole_pipeline_eval import (
    TARGET_PERCENT_OF_READY_TRUE,
    missed_line,
)

EVAL_TITLES = {
    EvalName.SAFEGUARD: "Safeguard",
    EvalName.PERSONA: "Persona",
    EvalName.KNOWLEDGE: "Knowledge",
    EvalName.SETTINGS: "Settings",
    EvalName.PHOTO_DESCRIPTIONS: "Photo descriptions",
    EvalName.UNDERSTANDING: "Understanding",
    EvalName.MOVE_OUTCOME: "Move Outcome",
    EvalName.DAY_SUMMARY: "Day Summary",
    EvalName.TAGGING: "Tagging",
    EvalName.WHOLE_PIPELINE: "Whole pipeline",
}
OUTCOME_MARKS = {
    CaseOutcome.PASS: "PASS",
    CaseOutcome.FAIL: "FAIL",
    CaseOutcome.ERROR: "ERROR",
}


def check_line(check: Check) -> str:
    """Write a check as one line.

    Args:
        check: The check.

    Returns:
        E.g. "PASS no_lists: Plain texts."
    """
    return f"{'PASS' if check.passed else 'FAIL'} {check.name}: {check.detail}"


def progress_line(result: CaseResult) -> str:
    """Write a Case Result as the line printed when it finishes.

    Args:
        result: The Case Result.

    Returns:
        E.g. "PASS persona/captioned-photo (12.4 s, 5200 tokens)".
    """
    mark = OUTCOME_MARKS[result.result.outcome]
    tokens = result.tokens_in + result.tokens_out
    line = (
        f"{mark} {result.eval.value}/{result.case_key} "
        f"({result.duration_ms / 1000:.1f} s, {tokens} tokens)"
    )
    if result.result.error:
        line += f": {result.result.error}"
    return line


def errors_lines(results: Sequence[CaseResult]) -> list[str]:
    """Write the cases that couldn't be checked, if any.

    Args:
        results: One Eval's results.

    Returns:
        A heading and one line per Error; empty when there were none.
    """
    errored = [r for r in results if r.result.outcome == CaseOutcome.ERROR]
    if not errored:
        return []
    return [
        f"  Errors ({len(errored)}), not counted as fails:",
        *(f"    {r.case_key}: {r.result.error}" for r in errored),
    ]


def checked(results: Sequence[CaseResult]) -> list[CaseResult]:
    """Leave out the cases that couldn't be checked.

    Args:
        results: Some results.

    Returns:
        The results that are a Pass or a Fail.
    """
    return [r for r in results if r.result.outcome != CaseOutcome.ERROR]


def safeguard_lines(results: Sequence[CaseResult]) -> list[str]:
    """Write the Safeguard part of the report.

    Args:
        results: The Safeguard results.

    Returns:
        The score, then each missed crisis and false alarm.
    """
    done = checked(results)
    wrong = [r for r in done if not r.result.facts["right"]]
    missed = [r for r in wrong if r.result.facts["is_crisis"]]
    false_alarms = [r for r in wrong if not r.result.facts["is_crisis"]]
    right = len(done) - len(wrong)
    return [
        f"Safeguard: {right} of {len(done)} right",
        f"  Missed crises ({len(missed)}):",
        *(f"    {r.result.checks[0].detail}" for r in missed),
        f"  False alarms ({len(false_alarms)}):",
        *(f"    {r.result.checks[0].detail}" for r in false_alarms),
    ]


def checks_score(title: str, unit: str) -> Callable[[Sequence[CaseResult]], str]:
    """Build the score line of an Eval scored by its checks.

    Args:
        title: The Eval's title.
        unit: What a check is called, e.g. "rules kept".

    Returns:
        A function writing the score for its results.
    """

    def score(results: Sequence[CaseResult]) -> str:
        """Write the score.

        Args:
            results: The Eval's results.

        Returns:
            E.g. "Persona: 17 of 18 rules kept".
        """
        checks = [check for r in checked(results) for check in r.result.checks]
        passed = sum(check.passed for check in checks)
        return f"{title}: {passed} of {len(checks)} {unit}"

    return score


def cases_score(title: str) -> Callable[[Sequence[CaseResult]], str]:
    """Build the score line of an Eval scored by its cases.

    Args:
        title: The Eval's title.

    Returns:
        A function writing the score for its results.
    """

    def score(results: Sequence[CaseResult]) -> str:
        """Write the score.

        Args:
            results: The Eval's results.

        Returns:
            E.g. "Settings: 11 of 12 right".
        """
        done = checked(results)
        passed = sum(r.result.outcome == CaseOutcome.PASS for r in done)
        return f"{title}: {passed} of {len(done)} right"

    return score


def case_lines(result: CaseResult) -> list[str]:
    """Write one case's checks, grouped, and its notes when it failed.

    Args:
        result: The Case Result.

    Returns:
        The case's key, then its checks under each group.
    """
    lines = [f"  {result.case_key}"]
    group = ""
    calls = {
        message["text"]: message["call"]
        for message in result.result.facts.get("messages", [])
    }
    for check in result.result.checks:
        if check.group != group:
            group = check.group
            lines.append(f"    {group}{call_stats(calls.get(group))}")
        indent = "      " if group else "    "
        lines.append(f"{indent}{check_line(check)}")
    if result.result.outcome == CaseOutcome.FAIL:
        lines += [f"    | {note}" for note in result.result.notes]
    return lines


def call_stats(call: dict[str, int] | None) -> str:
    """Write an Understanding call's time and tokens after a Message.

    Args:
        call: The call's `duration_ms`, `tokens_in` and `tokens_out`; None
            when the Message has none.

    Returns:
        E.g. " (1200 ms, 2000 in, 150 out)"; "" without a call.
    """
    if call is None:
        return ""
    return (
        f" ({call['duration_ms']} ms, {call['tokens_in']} in, {call['tokens_out']} out)"
    )


def understanding_calls_line(results: Sequence[CaseResult]) -> str:
    """Write the Understanding calls' average time and tokens on one line.

    Args:
        results: The Understanding results.

    Returns:
        E.g. "Understanding calls: 2, 1500 ms on average (slowest 1800 ms),
        2200 tokens in and 200 out on average".
    """
    calls: list[dict[str, Any]] = [
        message["call"]
        for r in results
        for message in r.result.facts.get("messages", [])
        if message["call"] is not None
    ]
    if not calls:
        return "Understanding calls: 0"
    count = len(calls)
    return (
        f"Understanding calls: {count}, "
        f"{sum(c['duration_ms'] for c in calls) // count} ms on average "
        f"(slowest {max(c['duration_ms'] for c in calls)} ms), "
        f"{sum(c['tokens_in'] for c in calls) // count} tokens in and "
        f"{sum(c['tokens_out'] for c in calls) // count} out on average"
    )


def whole_pipeline_score(results: Sequence[CaseResult]) -> str:
    """Write the Whole-pipeline score: how many ready Patterns were true.

    Args:
        results: The Whole-pipeline results.

    Returns:
        E.g. "Whole pipeline: 4 of 5 ready Patterns true (80%, target 70%);
        4 of 7 true Patterns found".
    """
    facts = [r.result.facts["whole_pipeline"] for r in checked(results)]
    ready = [pattern for fact in facts for pattern in fact["patterns"]]
    true_ready = sum(pattern["is_true"] for pattern in ready)
    true_count = sum(fact["true_count"] for fact in facts)
    missed = sum(len(fact["missed"]) for fact in facts)
    percent = f"{round(100 * true_ready / len(ready))}%" if ready else "none ready"
    return (
        f"Whole pipeline: {true_ready} of {len(ready)} ready Patterns true "
        f"({percent}, target {TARGET_PERCENT_OF_READY_TRUE}%); "
        f"{true_count - missed} of {true_count} true Patterns found"
    )


def missed_lines(result: CaseResult) -> list[str]:
    """Write the true Patterns a Whole-pipeline case missed, and where they stopped.

    Args:
        result: The Case Result.

    Returns:
        One line per missed Pattern, e.g. "    missed CONF.AVOID.BELONG:
        suspected, stopped by situations".
    """
    return [
        f"    missed {missed_line(missed)}"
        for missed in result.result.facts["whole_pipeline"]["missed"]
    ]


SCORES: dict[EvalName, Callable[[Sequence[CaseResult]], str]] = {
    EvalName.PERSONA: checks_score("Persona", "rules kept"),
    EvalName.KNOWLEDGE: checks_score("Knowledge", "steps right"),
    EvalName.SETTINGS: cases_score("Settings"),
    EvalName.PHOTO_DESCRIPTIONS: cases_score("Photo descriptions"),
    EvalName.UNDERSTANDING: checks_score("Understanding", "checks and rules passed"),
    EvalName.MOVE_OUTCOME: checks_score("Move Outcome", "checks and rules passed"),
    EvalName.DAY_SUMMARY: checks_score("Day Summary", "questions matched"),
    EvalName.TAGGING: cases_score("Tagging"),
    EvalName.WHOLE_PIPELINE: whole_pipeline_score,
}


def eval_lines(name: EvalName, results: Sequence[CaseResult]) -> list[str]:
    """Write one Eval's part of the report.

    Args:
        name: The Eval.
        results: Its results.

    Returns:
        Its score and each case, then any Errors.
    """
    if name == EvalName.SAFEGUARD:
        return [*safeguard_lines(results), *errors_lines(results)]
    lines = [SCORES[name](results)]
    if name == EvalName.UNDERSTANDING:
        lines.append(f"  {understanding_calls_line(results)}")
    for result in checked(results):
        lines += case_lines(result)
        if name == EvalName.WHOLE_PIPELINE:
            lines += missed_lines(result)
    return [*lines, *errors_lines(results)]


def cost_line(cost: Cost) -> str:
    """Write what a run's tokens cost, as the Dashboard shows it.

    Args:
        cost: The run's cost, at the Model Prices it started with.

    Returns:
        E.g. "Cost: S$0.2130, at the prices the run started with", naming
        any model with no price set.
    """
    line = f"Cost: S${cost.sgd:.4f}, at the prices the run started with"
    if cost.unpriced_models:
        models = ", ".join(cost.unpriced_models)
        one = len(cost.unpriced_models) == 1
        line += (
            f"; {models} {'has' if one else 'have'} no price set, "
            f"so {'its' if one else 'their'} tokens aren't counted"
        )
    return line


def estimate_line(estimate: Estimate) -> str:
    """Write what a run is likely to cost, printed before it is queued.

    Args:
        estimate: The run's estimate, at the live Model Prices.

    Returns:
        E.g. "Estimate: 40 cases, about S$0.4100 at the live prices (40 never
        run, so a rough figure)", naming any model with no price set.
    """
    cases = f"{estimate.case_count} case{'' if estimate.case_count == 1 else 's'}"
    line = f"Estimate: {cases}, about S${estimate.cost.sgd:.4f} at the live prices"
    if estimate.rough_case_count:
        line += f" ({estimate.rough_case_count} never run, so a rough figure)"
    if estimate.cost.unpriced_models:
        line += f"; no price set for {', '.join(estimate.cost.unpriced_models)}"
    return line


def report_lines(overview: EvalRunOverview, results: Sequence[CaseResult]) -> list[str]:
    """Write the whole report printed when a run ends.

    Args:
        overview: The run and its totals.
        results: Its Case Results.

    Returns:
        The run's state and totals, then each Eval that ran.
    """
    totals = overview.totals
    lines = [
        f"Run {overview.run.id}: {overview.run.state.value}",
        f"Cases: {totals.passed} passed, {totals.failed} failed, "
        f"{totals.errored} errors",
        f"Tokens used (app and judge): {totals.tokens_in} in, {totals.tokens_out} out",
        cost_line(overview.cost),
    ]
    for name in overview.run.evals:
        eval_results = [r for r in results if r.eval == name]
        if eval_results:
            lines += ["", *eval_lines(name, eval_results)]
    return lines
