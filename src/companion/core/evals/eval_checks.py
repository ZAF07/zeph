from collections.abc import Callable
from typing import Any

from companion.core.evals.cases import (
    read_day_summary_case,
    read_knowledge_case,
    read_move_outcome_case,
    read_persona_case,
    read_photo_description_case,
    read_safeguard_case,
    read_settings_case,
    read_tagging_case,
    read_understanding_case,
)
from companion.core.evals.day_summary_eval import check_day_summary_case
from companion.core.evals.judge import JudgeSettings
from companion.core.evals.knowledge_eval import check_knowledge_case
from companion.core.evals.models import (
    CaseCheckResult,
    EvalCase,
    EvalName,
    StopCheck,
)
from companion.core.evals.move_outcome_eval import check_move_outcome_case
from companion.core.evals.persona_eval import check_persona_case
from companion.core.evals.photo_description_eval import check_photo_description_case
from companion.core.evals.ports import EvalCompanion
from companion.core.evals.safeguard_eval import check_safeguard_case
from companion.core.evals.settings_eval import check_settings_case
from companion.core.evals.tagging_eval import check_tagging_case
from companion.core.evals.understanding_eval import check_understanding_case

type CaseChecker = Callable[
    [EvalCase, EvalCompanion, JudgeSettings, StopCheck], CaseCheckResult
]


def checker[CaseShape](
    read: Callable[[str, dict[str, Any]], CaseShape],
    check: Callable[[CaseShape, EvalCompanion], CaseCheckResult],
) -> CaseChecker:
    """Join the case reader and check of an Eval without a Judge into one step.

    Args:
        read: Reads a case into the Eval's case shape.
        check: Checks a case of that shape.

    Returns:
        A step that reads and checks an Eval Case. It doesn't stop
        part-way, since these Evals' cases are short.
    """
    return lambda case, companion, _judge, _should_stop: check(
        read(case.key, case.content), companion
    )


def judged_checker[CaseShape](
    read: Callable[[str, dict[str, Any]], CaseShape],
    check: Callable[[CaseShape, EvalCompanion, JudgeSettings], CaseCheckResult],
) -> CaseChecker:
    """Join the case reader and check of an Eval the Judge marks into one step.

    Args:
        read: Reads a case into the Eval's case shape.
        check: Checks a case of that shape with the Judge.

    Returns:
        A step that reads and checks an Eval Case. It doesn't stop
        part-way.
    """
    return lambda case, companion, judge, _should_stop: check(
        read(case.key, case.content), companion, judge
    )


def check_understanding(
    case: EvalCase,
    companion: EvalCompanion,
    judge: JudgeSettings,
    should_stop: StopCheck,
) -> CaseCheckResult:
    """Read and check an Understanding case, which may stop between Messages.

    Args:
        case: The case.
        companion: The app on the Eval database.
        judge: The Judge's settings for the run.
        should_stop: Says why the run is to stop, or None to carry on.

    Returns:
        What checking it found.
    """
    return check_understanding_case(
        read_understanding_case(case.key, case.content),
        companion,
        judge,
        should_stop,
    )


CHECKERS: dict[EvalName, CaseChecker] = {
    EvalName.SAFEGUARD: checker(read_safeguard_case, check_safeguard_case),
    EvalName.PERSONA: judged_checker(read_persona_case, check_persona_case),
    EvalName.KNOWLEDGE: judged_checker(read_knowledge_case, check_knowledge_case),
    EvalName.SETTINGS: checker(read_settings_case, check_settings_case),
    EvalName.PHOTO_DESCRIPTIONS: checker(
        read_photo_description_case, check_photo_description_case
    ),
    EvalName.UNDERSTANDING: check_understanding,
    EvalName.MOVE_OUTCOME: judged_checker(
        read_move_outcome_case, check_move_outcome_case
    ),
    EvalName.DAY_SUMMARY: judged_checker(read_day_summary_case, check_day_summary_case),
    EvalName.TAGGING: checker(read_tagging_case, check_tagging_case),
}

READERS: dict[EvalName, Callable[[str, dict[str, Any]], object]] = {
    EvalName.SAFEGUARD: read_safeguard_case,
    EvalName.PERSONA: read_persona_case,
    EvalName.KNOWLEDGE: read_knowledge_case,
    EvalName.SETTINGS: read_settings_case,
    EvalName.PHOTO_DESCRIPTIONS: read_photo_description_case,
    EvalName.UNDERSTANDING: read_understanding_case,
    EvalName.MOVE_OUTCOME: read_move_outcome_case,
    EvalName.DAY_SUMMARY: read_day_summary_case,
    EvalName.TAGGING: read_tagging_case,
}


def check_case(
    case: EvalCase,
    companion: EvalCompanion,
    judge: JudgeSettings,
    should_stop: StopCheck,
) -> CaseCheckResult:
    """Run one Eval Case with its Eval's check.

    Args:
        case: The case.
        companion: The app on the Eval database, fresh for this case.
        judge: The Judge's settings for the run.
        should_stop: Says why the run is to stop, or None to carry on;
            asked between the steps of a long case.

    Returns:
        What checking it found.

    Raises:
        CaseStoppedError: If the run is to stop before the case ends.
    """
    return CHECKERS[case.eval](case, companion, judge, should_stop)


def read_case(case: EvalCase) -> object:
    """Read a case into its Eval's case shape, to check it fits.

    Args:
        case: The case.

    Returns:
        The case in its Eval's shape.

    Raises:
        KeyError: If a required field is missing.
        ValueError: If a field holds a value its Eval doesn't know, or an
            Understanding case can't be checked.
    """
    return READERS[case.eval](case.key, case.content)
