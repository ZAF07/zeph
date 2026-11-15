from collections.abc import Mapping, Sequence
from typing import Any

from companion.core.evals.case_shapes import CASE_SHAPES, find_problems
from companion.core.evals.cases import InvalidEvalCaseError, require_unique_keys
from companion.core.evals.eval_checks import read_case
from companion.core.evals.models import EvalCase, EvalImage
from companion.core.evals.ports import (
    EvalCaseRepository,
    EvalImageRepository,
    JudgeSettingsRepository,
)
from companion.core.ports import Clock


def add_seed_cases(
    cases: EvalCaseRepository,
    images: EvalImageRepository,
    seed_cases: Sequence[EvalCase],
    seed_images: Sequence[EvalImage],
    clock: Clock,
) -> list[str]:
    """Add the seed's Eval Cases whose key isn't stored yet, and their images.

    A case already stored, edited or archived, is never touched, so Admin
    changes stay and archived cases don't come back. An image already
    stored by its name is never changed.

    Args:
        cases: Where Eval Cases are stored.
        images: Where the cases' test images are stored.
        seed_cases: The cases in the seed files.
        seed_images: The test images the seed cases send.
        clock: Tells the time.

    Returns:
        The keys added.

    Raises:
        InvalidEvalCaseError: If two seed cases share a key or a case doesn't
            fit its Eval's case shape.
    """
    require_unique_keys([case.key for case in seed_cases])
    for case in seed_cases:
        problems = find_problems(CASE_SHAPES[case.eval], case.content)
        if problems:
            raise InvalidEvalCaseError(
                f"The seed case {case.key} doesn't fit the {case.eval} case shape: "
                + "; ".join(f"{path}: {message}" for path, message in problems.items()),
                problems,
            )
        try:
            read_case(case)
        except (KeyError, ValueError, TypeError) as error:
            raise InvalidEvalCaseError(
                f"The seed case {case.key} doesn't fit the {case.eval} case shape: "
                f"{error}"
            ) from error
    images.add_missing(seed_images, clock.now())
    return cases.add_missing(seed_cases, clock.now())


def add_seed_judge_settings(
    judge_settings: JudgeSettingsRepository,
    seed_values: Mapping[str, Any],
    clock: Clock,
) -> None:
    """Add the Judge settings from the seed file that aren't stored yet.

    A setting an Admin changed is never overwritten.

    Args:
        judge_settings: Where the Judge's settings are stored.
        seed_values: Each setting's starting value by name.
        clock: Tells the time.
    """
    judge_settings.add_missing(seed_values, clock.now())
