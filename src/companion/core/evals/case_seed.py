from collections.abc import Sequence

from companion.core.evals.cases import InvalidEvalCaseError, require_unique_keys
from companion.core.evals.eval_checks import read_case
from companion.core.evals.models import EvalCase
from companion.core.evals.ports import EvalCaseRepository
from companion.core.ports import Clock


def add_seed_cases(
    cases: EvalCaseRepository, seed_cases: Sequence[EvalCase], clock: Clock
) -> list[str]:
    """Add the seed's Eval Cases whose key isn't stored yet.

    A case already stored, edited or archived, is never touched, so Admin
    changes stay and archived cases don't come back.

    Args:
        cases: Where Eval Cases are stored.
        seed_cases: The cases in the seed files.
        clock: Tells the time.

    Returns:
        The keys added.

    Raises:
        InvalidEvalCaseError: If two seed cases share a key or a case doesn't
            fit its Eval's case shape.
    """
    require_unique_keys([case.key for case in seed_cases])
    for case in seed_cases:
        try:
            read_case(case)
        except (KeyError, ValueError, TypeError) as error:
            raise InvalidEvalCaseError(
                f"The seed case {case.key} doesn't fit the {case.eval} case shape: "
                f"{error}"
            ) from error
    return cases.add_missing(seed_cases, clock.now())
