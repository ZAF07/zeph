from datetime import UTC, datetime
from uuid import uuid4

from companion.adapters.evals.terminal_report import eval_lines
from companion.adapters.pattern_catalog_seed import read_pattern_catalog_seed
from companion.core.evals.case_shapes import CASE_SHAPES, find_problems
from companion.core.evals.cases import WholePipelineCase, read_whole_pipeline_case
from companion.core.evals.models import CaseOutcome, Check, EvalName
from companion.core.evals.whole_pipeline_eval import (
    check_ready_patterns,
    missed_line,
    pipeline_facts,
    ready_pattern_types,
)
from companion.core.models import (
    CatalogPattern,
    PatternMove,
    PatternMoveCause,
    PatternState,
    ReadyCheck,
)
from companion.core.pattern_catalog import read_pattern_types
from tests.conftest import PATTERN_CATALOG_DIR
from tests.test_eval_helpers import case_result, seeded

BELONG = "CONF.AVOID.BELONG"
NEEDED = "APPR.GIVE.NEEDED"
GOAL = "ACH.GOAL.MOVE"
NAMES = {BELONG: "Softening", NEEDED: "Over-giving", GOAL: "Moving the goal"}
NOW = datetime(2026, 11, 5, tzinfo=UTC)
USER_ID = uuid4()


def move(
    pattern_type: str, from_state: PatternState | None, to_state: PatternState
) -> PatternMove:
    """One move of the User's Pattern of a Pattern Type."""
    return PatternMove(
        id=uuid4(),
        user_id=USER_ID,
        pattern_id=uuid4(),
        pattern_type_id=pattern_type,
        from_state=from_state,
        to_state=to_state,
        cause=PatternMoveCause.CONVERSATION_TAGGED,
        conversation_id=None,
        points=300,
        situations=3,
        moved_at=NOW,
    )


def pattern(
    pattern_type: str, state: PatternState, blocked_by: ReadyCheck | None = None
) -> CatalogPattern:
    """The User's Pattern of a Pattern Type as it stands at the end."""
    return CatalogPattern(
        id=uuid4(),
        user_id=USER_ID,
        pattern_type_id=pattern_type,
        state=state,
        started_at=NOW,
        updated_at=NOW,
        blocked_by=blocked_by,
    )


def test_a_pattern_that_was_ready_counts_even_after_it_went_back() -> None:
    moves = [
        move(BELONG, None, PatternState.NOTICED),
        move(BELONG, PatternState.NOTICED, PatternState.SUSPECTED),
        move(NEEDED, None, PatternState.NOTICED),
        move(BELONG, PatternState.SUSPECTED, PatternState.READY),
        move(BELONG, PatternState.READY, PatternState.SUSPECTED),
    ]

    assert ready_pattern_types(moves) == {BELONG: False}


def test_a_shared_pattern_is_listed_once_as_shared_in_the_order_it_became_ready() -> (
    None
):
    moves = [
        move(NEEDED, PatternState.SUSPECTED, PatternState.READY),
        move(BELONG, PatternState.SUSPECTED, PatternState.READY),
        move(BELONG, PatternState.READY, PatternState.SHARED),
        move(BELONG, PatternState.SHARED, PatternState.CONTESTED),
    ]

    assert ready_pattern_types(moves) == {NEEDED: False, BELONG: True}


def test_the_facts_tell_true_from_false_ready_patterns_and_list_the_missed() -> None:
    facts = pipeline_facts(
        [BELONG, GOAL, "CTRL.SELF.RELY"],
        [
            move(BELONG, PatternState.SUSPECTED, PatternState.READY),
            move(BELONG, PatternState.READY, PatternState.SHARED),
            move(NEEDED, PatternState.SUSPECTED, PatternState.READY),
            move(NEEDED, PatternState.READY, PatternState.SUSPECTED),
        ],
        [
            pattern(BELONG, PatternState.SHARED),
            pattern(NEEDED, PatternState.SUSPECTED, ReadyCheck.SCORE),
            pattern(GOAL, PatternState.SUSPECTED, ReadyCheck.COUNTER_TEST),
        ],
        NAMES,
        conversations=4,
    )

    assert facts == {
        "patterns": [
            {
                "pattern_type": BELONG,
                "name": "Softening",
                "is_true": True,
                "shared": True,
                "state": "shared",
            },
            {
                "pattern_type": NEEDED,
                "name": "Over-giving",
                "is_true": False,
                "shared": False,
                "state": "suspected",
            },
        ],
        "missed": [
            {
                "pattern_type": GOAL,
                "name": "Moving the goal",
                "state": "suspected",
                "blocked_by": "counter_test",
            },
            {
                "pattern_type": "CTRL.SELF.RELY",
                "name": "",
                "state": None,
                "blocked_by": None,
            },
        ],
        "true_count": 3,
        "conversations": 4,
    }
    assert check_ready_patterns(facts) == [
        Check(BELONG, True, "shared, one of the true ones"),
        Check(NEEDED, False, "ready, not a true one"),
    ]
    assert [missed_line(missed) for missed in facts["missed"]] == [
        "ACH.GOAL.MOVE: suspected, stopped by counter_test",
        "CTRL.SELF.RELY: never noticed",
    ]


def test_nothing_ready_passes_whether_or_not_a_true_pattern_was_missed() -> None:
    none_true = pipeline_facts([], [], [], NAMES, conversations=4)
    one_missed = pipeline_facts(
        [GOAL], [], [pattern(GOAL, PatternState.NOTICED)], NAMES, conversations=4
    )

    assert check_ready_patterns(none_true) == [
        Check("nothing ready", True, "no Pattern became ready, and none is true")
    ]
    assert check_ready_patterns(one_missed) == [
        Check("nothing ready", True, "no Pattern became ready; 1 true missed")
    ]
    assert missed_line(one_missed["missed"][0]) == "ACH.GOAL.MOVE: noticed"


def test_a_case_reads_its_conversations_and_each_true_pattern_type_once() -> None:
    case = read_whole_pipeline_case(
        "folds",
        {
            "now": "2026-11-02T19:30:00",
            "true_pattern_types": [" CONF.AVOID.BELONG ", BELONG, " "],
            "conversations": [
                {"days_later": 0, "messages": ["hey", "ugh"]},
                {"days_later": 3, "messages": ["again"]},
            ],
        },
    )

    assert case.now == datetime(2026, 11, 2, 19, 30, tzinfo=UTC)
    assert case.true_pattern_types == [BELONG]
    assert [(c.days_later, c.messages) for c in case.conversations] == [
        (0, ["hey", "ugh"]),
        (3, ["again"]),
    ]


def test_a_case_needs_a_conversation_with_a_text_and_days_that_are_not_negative() -> (
    None
):
    shape = CASE_SHAPES[EvalName.WHOLE_PIPELINE]

    assert find_problems(shape, {"now": "2026-11-02T19:30:00"}) == {
        "conversations": "Add at least one conversation."
    }
    assert find_problems(
        shape,
        {
            "now": "2026-11-02T19:30:00",
            "conversations": [{"days_later": -1, "messages": []}],
        },
    ) == {
        "conversations.0.days_later": "Must be 0 or more.",
        "conversations.0.messages": "Add at least one text.",
    }


def test_the_seed_has_five_made_up_users_with_a_look_alike_pair_and_one_with_none() -> (
    None
):
    pattern_types = {
        pattern_type.id: pattern_type
        for pattern_type in read_pattern_types(
            read_pattern_catalog_seed(PATTERN_CATALOG_DIR)
        )
    }
    cases: list[WholePipelineCase] = seeded(EvalName.WHOLE_PIPELINE)

    assert len(cases) == 5
    assert all(len(case.conversations) >= 4 for case in cases)
    assert all(
        name in pattern_types for case in cases for name in case.true_pattern_types
    )
    assert sum(1 for case in cases if not case.true_pattern_types) == 1
    look_alike_pairs = [
        case.true_pattern_types
        for case in cases
        if len(case.true_pattern_types) == 2
        and case.true_pattern_types[1]
        in {
            look_alike.pattern_type_id
            for look_alike in pattern_types[case.true_pattern_types[0]].look_alikes
        }
    ]
    assert look_alike_pairs == [["CONF.WITHDRAW.HURT", "APPR.HIDE.BURDEN"]]


def test_the_report_scores_ready_patterns_against_the_target_and_lists_the_missed() -> (
    None
):
    found = pipeline_facts(
        [BELONG, GOAL],
        [
            move(BELONG, PatternState.SUSPECTED, PatternState.READY),
            move(NEEDED, PatternState.SUSPECTED, PatternState.READY),
        ],
        [
            pattern(BELONG, PatternState.READY),
            pattern(NEEDED, PatternState.READY),
            pattern(GOAL, PatternState.SUSPECTED, ReadyCheck.SITUATIONS),
        ],
        NAMES,
        conversations=4,
    )
    nothing = pipeline_facts([], [], [], NAMES, conversations=4)

    lines = eval_lines(
        EvalName.WHOLE_PIPELINE,
        [
            case_result(
                EvalName.WHOLE_PIPELINE,
                "folds",
                CaseOutcome.FAIL,
                check_ready_patterns(found),
                {"whole_pipeline": found},
            ),
            case_result(
                EvalName.WHOLE_PIPELINE,
                "ordinary",
                CaseOutcome.PASS,
                check_ready_patterns(nothing),
                {"whole_pipeline": nothing},
            ),
            case_result(
                EvalName.WHOLE_PIPELINE, "broke", CaseOutcome.ERROR, error="No catalog"
            ),
        ],
    )

    assert lines == [
        "Whole pipeline: 1 of 2 ready Patterns true (50%, target 70%); "
        "1 of 2 true Patterns found",
        "  folds",
        "    PASS CONF.AVOID.BELONG: ready, one of the true ones",
        "    FAIL APPR.GIVE.NEEDED: ready, not a true one",
        "    missed ACH.GOAL.MOVE: suspected, stopped by situations",
        "  ordinary",
        "    PASS nothing ready: no Pattern became ready, and none is true",
        "  Errors (1), not counted as fails:",
        "    broke: No catalog",
    ]


def test_the_report_says_none_ready_when_no_pattern_became_ready() -> None:
    nothing = pipeline_facts([GOAL], [], [], NAMES, conversations=4)

    [score, *_] = eval_lines(
        EvalName.WHOLE_PIPELINE,
        [
            case_result(
                EvalName.WHOLE_PIPELINE,
                "ordinary",
                CaseOutcome.PASS,
                check_ready_patterns(nothing),
                {"whole_pipeline": nothing},
            )
        ],
    )

    assert score == (
        "Whole pipeline: 0 of 0 ready Patterns true (none ready, target 70%); "
        "0 of 1 true Patterns found"
    )
