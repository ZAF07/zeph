from collections.abc import Mapping, Sequence
from datetime import timedelta
from typing import Any
from uuid import UUID

from companion.core.evals.cases import WholePipelineCase
from companion.core.evals.models import (
    CaseCheckResult,
    CaseOutcome,
    CaseStoppedError,
    Check,
    StopCheck,
)
from companion.core.evals.ports import EvalCompanion, EvalSetupError
from companion.core.evals.understanding_eval import (
    calls_in_new_traces,
    transcript_line,
)
from companion.core.models import (
    CatalogPattern,
    ModelStep,
    PatternMove,
    PatternState,
)
from companion.core.pattern_catalog import PatternCatalogService

MESSAGE_GAP = timedelta(minutes=1)
STATES_THAT_COUNT = frozenset({PatternState.READY, PatternState.SHARED})
NOTHING_READY = "nothing ready"
TRUE_PATTERNS_FOUND = "true Patterns found"
CONVERSATION_END_STEP = "Conversation-end step failed"
TARGET_PERCENT_OF_READY_TRUE = 70


def ready_pattern_types(moves: Sequence[PatternMove]) -> dict[str, bool]:
    """Find the Pattern Types whose Pattern ever became ready or was shared.

    The move log is read, not where Patterns stand now, since a ready
    Pattern can go back.

    Args:
        moves: Every move of the User's Patterns, oldest first.

    Returns:
        Whether it was shared, by Pattern Type ID, in the order each first
        became ready.
    """
    found: dict[str, bool] = {}
    for move in moves:
        if move.to_state in STATES_THAT_COUNT:
            found[move.pattern_type_id] = (
                found.get(move.pattern_type_id, False)
                or move.to_state == PatternState.SHARED
            )
    return found


def pipeline_facts(
    true_pattern_types: Sequence[str],
    moves: Sequence[PatternMove],
    patterns: Sequence[CatalogPattern],
    names: Mapping[str, str],
    conversations: int,
) -> dict[str, Any]:
    """Write which Patterns became ready or shared, against the true ones.

    Args:
        true_pattern_types: The IDs of the Pattern Types true of the User.
        moves: Every move of the User's Patterns, oldest first.
        patterns: The User's Patterns as they stand at the end.
        names: Each Pattern Type's name, by ID.
        conversations: How many Conversations the User had.

    Returns:
        `patterns` (each ready or shared one: its Pattern Type, name,
        whether it is true, whether it was shared and where it stands now),
        `missed` (each true one never ready: where it stands now and the
        ready check that last stopped it, both None when never noticed),
        `true_count` and `conversations`.
    """
    standing = {pattern.pattern_type_id: pattern for pattern in patterns}
    ready = ready_pattern_types(moves)

    def state_of(pattern_type: str) -> str | None:
        """Read where the User's Pattern of a Pattern Type stands now.

        Args:
            pattern_type: The Pattern Type's ID.

        Returns:
            Its state; None when they have no such Pattern.
        """
        pattern = standing.get(pattern_type)
        return pattern.state.value if pattern else None

    def blocked_by(pattern_type: str) -> str | None:
        """Read the ready check that last stopped a Pattern.

        Args:
            pattern_type: The Pattern Type's ID.

        Returns:
            The check; None when there is no Pattern or nothing stopped it.
        """
        pattern = standing.get(pattern_type)
        return pattern.blocked_by.value if pattern and pattern.blocked_by else None

    return {
        "patterns": [
            {
                "pattern_type": pattern_type,
                "name": names.get(pattern_type, ""),
                "is_true": pattern_type in true_pattern_types,
                "shared": shared,
                "state": state_of(pattern_type),
            }
            for pattern_type, shared in ready.items()
        ],
        "missed": [
            {
                "pattern_type": pattern_type,
                "name": names.get(pattern_type, ""),
                "state": state_of(pattern_type),
                "blocked_by": blocked_by(pattern_type),
            }
            for pattern_type in true_pattern_types
            if pattern_type not in ready
        ],
        "true_count": len(true_pattern_types),
        "conversations": conversations,
    }


def check_ready_patterns(
    facts: Mapping[str, Any], failed_steps: Sequence[str] = ()
) -> list[Check]:
    """Check the ready Patterns are true ones, a true one was found and no step failed.

    Args:
        facts: What `pipeline_facts` wrote.
        failed_steps: Each Conversation-end step that failed and was
            skipped, one line each.

    Returns:
        One check per ready or shared Pattern, passed when it is true of
        the User. When the User has true Patterns, one "true Patterns
        found" check, failed when none of them became ready. With neither,
        one passed "nothing ready" check. Then one failed check per failed
        step.
    """
    checks = [
        Check(
            pattern["pattern_type"],
            pattern["is_true"],
            f"{'shared' if pattern['shared'] else 'ready'}, "
            f"{'one of the true ones' if pattern['is_true'] else 'not a true one'}",
        )
        for pattern in facts["patterns"]
    ]
    true_count = facts["true_count"]
    if true_count:
        found = true_count - len(facts["missed"])
        checks.append(
            Check(
                TRUE_PATTERNS_FOUND,
                found > 0,
                f"{found} of {true_count} became ready",
            )
        )
    if not checks:
        checks.append(
            Check(NOTHING_READY, True, "no Pattern became ready, and none is true")
        )
    return [
        *checks,
        *(Check(CONVERSATION_END_STEP, False, failure) for failure in failed_steps),
    ]


def missed_line(missed: Mapping[str, Any]) -> str:
    """Write one missed true Pattern as a line.

    Args:
        missed: Its Pattern Type, where it stands and what stopped it.

    Returns:
        E.g. "CONF.AVOID.BELONG: suspected, stopped by situations".
    """
    if missed["state"] is None:
        return f"{missed['pattern_type']}: never noticed"
    stopped = f", stopped by {missed['blocked_by']}" if missed["blocked_by"] else ""
    return f"{missed['pattern_type']}: {missed['state']}{stopped}"


def check_whole_pipeline_case(
    case: WholePipelineCase, companion: EvalCompanion, should_stop: StopCheck
) -> CaseCheckResult:
    """Have a made-up User's Conversations and check which Patterns became ready.

    The made-up User has Pattern noticing, exploring and sharing on. Each
    text goes through the real reply path, a minute apart; when a
    Conversation is over the clock moves past the quiet gap and every
    Conversation-end step runs, then the clock moves on to the next one.

    Args:
        case: The hidden true Pattern Types and the scripted Conversations.
        companion: The app on the Eval database.
        should_stop: Says why the run is to stop, or None to carry on;
            asked before each Conversation after the first.

    Returns:
        A check per Pattern that became ready or was shared, passed when it
        is one of the true ones; a failed check when the User has true
        Patterns and none became ready; and a failed check per
        Conversation-end step that failed and was skipped. Its facts hold
        the ready Patterns and the true ones missed. A failed case notes
        why it failed, the missed ones and every Conversation.

    Raises:
        CaseStoppedError: If the run is to stop before the last Conversation.
        EvalSetupError: If a true Pattern Type isn't in the Pattern Catalog,
            or the tagging step didn't run after a Conversation, so the case
            is an Error, not a Fail.
    """
    repositories = companion.repositories
    names = {
        entry.pattern_type.id: entry.pattern_type.name
        for entry in PatternCatalogService(repositories.pattern_catalog).catalog()
    }
    unknown = [name for name in case.true_pattern_types if name not in names]
    if unknown:
        raise EvalSetupError(f"Not in the Pattern Catalog: {', '.join(unknown)}")
    companion.move_clock(case.now - companion.now())
    user_id = companion.connect_user()
    companion.turn_pattern_sharing_on()
    seen_trace_ids: set[UUID] = set()
    calls_in_new_traces(repositories, user_id, seen_trace_ids)

    transcript: list[str] = []
    failed_steps: list[str] = []
    for number, conversation in enumerate(case.conversations, start=1):
        stop_reason = should_stop() if number > 1 else None
        if stop_reason is not None:
            raise CaseStoppedError(
                f"Stopped after {number - 1} of {len(case.conversations)} "
                f"Conversations: {stop_reason}."
            )
        companion.move_clock(timedelta(days=conversation.days_later))
        transcript += ["", f"Conversation {number}, {companion.now():%d %b %Y}:"]
        for text in conversation.messages:
            replies = companion.send_text(text)
            transcript.append(transcript_line(True, text))
            transcript += [transcript_line(False, reply) for reply in replies.texts]
            companion.move_clock(MESSAGE_GAP)
        failed_steps += [
            f"after Conversation {number}: {failure}"
            for failure in companion.end_conversation()
        ]
        if not any(
            call.step == ModelStep.PATTERN_TAGGING
            for call in calls_in_new_traces(repositories, user_id, seen_trace_ids)
        ):
            raise EvalSetupError(
                f"The tagging step didn't run after Conversation {number}"
            )

    facts = pipeline_facts(
        case.true_pattern_types,
        repositories.patterns.list_moves(user_id),
        repositories.patterns.list_of_pattern_types(user_id),
        names,
        len(case.conversations),
    )
    checks = check_ready_patterns(facts, failed_steps)
    passed = all(check.passed for check in checks)
    return CaseCheckResult(
        outcome=CaseOutcome.PASS if passed else CaseOutcome.FAIL,
        checks=checks,
        facts={"whole_pipeline": facts},
        notes=[] if passed else [*failure_notes(checks, facts["missed"]), *transcript],
    )


def failure_notes(
    checks: Sequence[Check], missed: Sequence[Mapping[str, Any]]
) -> list[str]:
    """Write why a case failed and which true Patterns it missed.

    Args:
        checks: The case's checks.
        missed: The true Patterns never ready.

    Returns:
        "Why it failed:" and each failed check, then "True Patterns
        missed:" and each one, left out when none was missed.
    """
    notes = [
        "Why it failed:",
        *(f"{check.name}: {check.detail}" for check in checks if not check.passed),
    ]
    if missed:
        notes += ["True Patterns missed:", *(missed_line(one) for one in missed)]
    return notes
