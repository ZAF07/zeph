from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from companion.adapters.evals.terminal_report import eval_lines
from companion.core.evals.cases import (
    EvalMoveOutcome,
    InvalidEvalCaseError,
    UnderstandingCase,
    UnderstandingExpectations,
)
from companion.core.evals.models import CaseOutcome, Check, EvalName
from companion.core.evals.understanding_checks import (
    CheckResult,
    ObservedUnderstanding,
    check_understanding,
)
from companion.core.models import MoveResult, MoveRole
from tests.test_eval_helpers import case_result, from_file, seeded

CASE_FILE_START = """\
now: 2026-11-13T18:30:00
rules:
  no_fixing: Zeph's last reply gives no advice.
cases:
"""


def read_cases(tmp_path: Path, text: str) -> list[UnderstandingCase]:
    """Read Understanding cases from a case file's text."""
    return from_file(tmp_path, EvalName.UNDERSTANDING, text)


NOTHING_RAISED = ObservedUnderstanding(
    need="Be heard",
    understanding_input="Life Threads this reminds you of:\n[1] Falling-out with Mei",
    raised_threads=[],
    raised_curiosities=0,
    asked_why=False,
    knowledge_documents=[],
    knowledge_in_reply=[],
    woven_in=False,
)


def test_the_understanding_cases_cover_every_check_the_issue_asks_for() -> None:
    cases: list[UnderstandingCase] = seeded(EvalName.UNDERSTANDING)

    expectations = [message.expect for case in cases for message in case.messages]
    needs = {need for expect in expectations for need in expect.need}
    assert {"Be heard", "Advice", "Just chatting", "Accountability"} <= needs
    assert any(expect.raised for expect in expectations)
    assert any(expect.found and expect.not_raised for expect in expectations)
    assert any(expect.curiosity_raised is True for expect in expectations)
    assert any(expect.curiosity_raised is False for expect in expectations)
    assert any(expect.asked_why is True for expect in expectations)
    assert any(expect.knowledge is True for expect in expectations)
    assert any(expect.knowledge is False for expect in expectations)
    assert any(expect.rules for expect in expectations)
    assert any(expect.woven_in is True for expect in expectations)
    assert any(expect.woven_in is False for expect in expectations)
    assert all(
        case.check_in_due
        for case in cases
        for message in case.messages
        if message.expect.woven_in is not None
    )
    threads = [thread for case in cases for thread in case.memory.threads]
    assert any(thread.raised_in_this_conversation for thread in threads)
    assert any(thread.reaction == "brushed_off" for thread in threads)


def test_a_case_is_read_with_its_memory_earlier_lines_and_messages(
    tmp_path: Path,
) -> None:
    [case] = read_cases(
        tmp_path,
        CASE_FILE_START
        + """\
  - id: wedding
    now: 2026-11-12T09:00:00
    check_in_due: true
    memory:
      portrait: Maya, 34, a nurse.
      items: {Goals: [Run three times a week]}
      summaries: [{days_ago: 3, summary: Talked about work., mood: tired}]
      threads:
        - title: Falling-out with Mei
          story: They argued about their mum.
          people: [Mei, sister]
          updated_days_ago: 270
          raised_days_ago: 5
          reaction: brushed_off
      curiosities:
        - question: How did it go?
          why: Big day.
          not_before_days_ago: 1
      knowledge_documents:
        - title: On the breath
          source: Owner's notes
          tradition: Mindfulness
          when_it_helps: When their mind races.
          text: Breathe in for four.
    earlier:
      - person: hey
      - zeph: hi Maya
    messages:
      - text: my sister's wedding is next week
        expect:
          need: [Be heard]
          found: [Falling-out with Mei]
          raised: [Falling-out with Mei]
          curiosity_raised: false
          knowledge: false
          woven_in: false
          rules: [no_fixing]
""",
    )

    assert case.now == datetime(2026, 11, 12, 9, tzinfo=UTC)
    assert case.check_in_due is True
    assert case.memory.portrait == "Maya, 34, a nurse."
    assert case.memory.items == {"Goals": ["Run three times a week"]}
    assert case.memory.summaries[0].days_ago == 3
    thread = case.memory.threads[0]
    assert thread.people == ["Mei", "sister"]
    assert thread.is_open
    assert (thread.raised_days_ago, thread.reaction) == (5, "brushed_off")
    assert case.memory.curiosities[0].not_before_days_ago == 1
    assert case.memory.knowledge_documents[0].when_it_helps == (
        "When their mind races."
    )
    assert [(line.from_person, line.text) for line in case.earlier] == [
        (True, "hey"),
        (False, "hi Maya"),
    ]
    assert case.messages[0].expect == UnderstandingExpectations(
        need=["Be heard"],
        found=["Falling-out with Mei"],
        raised=["Falling-out with Mei"],
        not_raised=[],
        curiosity_raised=False,
        asked_why=None,
        knowledge=False,
        woven_in=False,
        rules=["no_fixing"],
    )


def test_a_case_without_its_own_time_uses_the_files(tmp_path: Path) -> None:
    [case] = read_cases(
        tmp_path, CASE_FILE_START + "  - id: hi\n    messages: [{text: hi}]\n"
    )

    assert case.now == datetime(2026, 11, 13, 18, 30, tzinfo=UTC)
    assert case.messages[0].expect == UnderstandingExpectations()


@pytest.mark.parametrize(
    ("message", "refused"),
    [
        ("{text: hi, expect: {rules: [be_funny]}}", "be_funny"),
        ("{text: hi, expect: {raised: [No such thread]}}", "No such thread"),
    ],
)
def test_a_case_naming_an_unknown_rule_or_thread_is_refused(
    tmp_path: Path, message: str, refused: str
) -> None:
    with pytest.raises(InvalidEvalCaseError, match=refused):
        read_cases(
            tmp_path, CASE_FILE_START + f"  - id: hi\n    messages: [{message}]\n"
        )


def test_a_thread_raised_in_this_conversation_needs_earlier_lines(
    tmp_path: Path,
) -> None:
    with pytest.raises(InvalidEvalCaseError, match="earlier"):
        read_cases(
            tmp_path,
            CASE_FILE_START + "  - id: hi\n"
            "    memory:\n"
            "      threads: [{title: T, story: S, raised_in_this_conversation: true}]\n"
            "    messages: [{text: hi}]\n",
        )


def test_understanding_cases_with_the_same_id_are_refused(tmp_path: Path) -> None:
    message = "    messages: [{text: hi}]\n"

    with pytest.raises(InvalidEvalCaseError, match="a"):
        read_cases(
            tmp_path, CASE_FILE_START + f"  - id: a\n{message}  - id: a\n{message}"
        )


def test_every_expectation_met_passes_each_check() -> None:
    expect = UnderstandingExpectations(
        need=["Be heard", "Think it through"],
        found=["Falling-out with Mei"],
        raised=["Falling-out with Mei"],
        curiosity_raised=True,
        asked_why=True,
        knowledge=True,
    )

    checks = check_understanding(
        expect,
        replace(
            NOTHING_RAISED,
            raised_threads=["Falling-out with Mei"],
            raised_curiosities=1,
            asked_why=True,
            knowledge_documents=["On the breath"],
            knowledge_in_reply=["On the breath"],
        ),
    )

    assert checks == [
        CheckResult("need", True, "picked Be heard"),
        CheckResult("found", True, "was reminded of Falling-out with Mei"),
        CheckResult("raised", True, "brought up Falling-out with Mei"),
        CheckResult("curiosity", True, "brought up 1 Curiosity"),
        CheckResult("asked why", True, "asked why"),
        CheckResult(
            "knowledge",
            True,
            "chose On the breath; passages from On the breath reached the reply",
        ),
    ]


def test_each_missed_expectation_fails_its_check_and_says_what_happened() -> None:
    expect = UnderstandingExpectations(
        need=["Be heard"],
        found=["Moving to Perth"],
        not_raised=["Falling-out with Mei"],
        curiosity_raised=False,
        asked_why=False,
        knowledge=False,
    )

    checks = check_understanding(
        expect,
        replace(
            NOTHING_RAISED,
            need="Advice",
            raised_threads=["Falling-out with Mei"],
            raised_curiosities=2,
            asked_why=True,
            knowledge_documents=["On the breath"],
        ),
    )

    assert checks == [
        CheckResult("need", False, "picked Advice, expected Be heard"),
        CheckResult("found", False, "wasn't reminded of Moving to Perth"),
        CheckResult("not raised", False, "brought up Falling-out with Mei"),
        CheckResult("curiosity", False, "brought up 2 Curiosities, expected none"),
        CheckResult("asked why", False, "asked why, expected not to"),
        CheckResult("knowledge", False, "chose On the breath, expected none"),
    ]


def test_expectations_left_out_are_not_checked() -> None:
    assert check_understanding(UnderstandingExpectations(), NOTHING_RAISED) == []


def test_a_woven_in_check_in_is_checked_against_what_was_expected() -> None:
    woven = replace(NOTHING_RAISED, woven_in=True)

    assert check_understanding(UnderstandingExpectations(woven_in=True), woven) == [
        CheckResult("woven in", True, "wove in the due Check-in")
    ]
    assert check_understanding(UnderstandingExpectations(woven_in=False), woven) == [
        CheckResult("woven in", False, "wove in the due Check-in, expected not now")
    ]
    assert check_understanding(
        UnderstandingExpectations(woven_in=True), NOTHING_RAISED
    ) == [CheckResult("woven in", False, "said not now, expected it woven in")]


def test_a_case_expecting_a_woven_in_check_in_needs_one_due(tmp_path: Path) -> None:
    with pytest.raises(InvalidEvalCaseError, match="check_in_due"):
        read_cases(
            tmp_path,
            CASE_FILE_START
            + "  - id: hi\n    messages: [{text: hi, expect: {woven_in: true}}]\n",
        )


def test_a_thread_left_alone_passes_and_a_missing_curiosity_fails() -> None:
    expect = UnderstandingExpectations(
        raised=["Falling-out with Mei"],
        not_raised=["Falling-out with Mei"],
        curiosity_raised=True,
        knowledge=True,
    )

    checks = check_understanding(expect, NOTHING_RAISED)

    assert checks == [
        CheckResult("raised", False, "didn't bring up Falling-out with Mei"),
        CheckResult("not raised", True, "left Falling-out with Mei alone"),
        CheckResult("curiosity", False, "brought up no Curiosity"),
        CheckResult("knowledge", False, "chose no document"),
    ]


def understanding_result(
    key: str, messages: list[dict[str, Any]], checks: list[Check]
) -> Any:
    passed = all(message["passed"] for message in messages)
    return case_result(
        EvalName.UNDERSTANDING,
        key,
        CaseOutcome.PASS if passed else CaseOutcome.FAIL,
        checks,
        {"messages": messages},
    )


def test_the_report_shows_each_message_with_its_checks_reasons_time_and_tokens() -> (
    None
):
    result = understanding_result(
        "rant",
        [
            {
                "text": "ugh my landlord",
                "passed": False,
                "call": {"duration_ms": 1200, "tokens_in": 2000, "tokens_out": 150},
            },
            {
                "text": "anyway",
                "passed": False,
                "call": {"duration_ms": 1800, "tokens_in": 2400, "tokens_out": 250},
            },
        ],
        [
            Check("need", True, "picked Be heard", group="ugh my landlord"),
            Check("no_fixing", False, "Suggests a lawyer.", group="ugh my landlord"),
            Check("need", False, "picked Advice, expected Be heard", group="anyway"),
        ],
    )

    text = "\n".join(eval_lines(EvalName.UNDERSTANDING, [result]))

    assert "Understanding: 1 of 3 checks and rules passed" in text
    assert (
        "  Understanding calls: 2, 1500 ms on average (slowest 1800 ms), "
        "2200 tokens in and 200 out on average"
    ) in text
    assert (
        "  rant\n"
        "    ugh my landlord (1200 ms, 2000 in, 150 out)\n"
        "      PASS need: picked Be heard\n"
        "      FAIL no_fixing: Suggests a lawyer.\n"
        "    anyway (1800 ms, 2400 in, 250 out)\n"
        "      FAIL need: picked Advice, expected Be heard"
    ) in text


def test_a_message_with_no_understanding_call_shows_no_calls() -> None:
    result = understanding_result(
        "hi", [{"text": "hi", "passed": False, "call": None}], []
    )

    text = "\n".join(eval_lines(EvalName.UNDERSTANDING, [result]))

    assert result.result.outcome == CaseOutcome.FAIL
    assert "Understanding calls: 0" in text


def test_knowledge_chosen_but_not_reaching_the_reply_fails() -> None:
    expect = UnderstandingExpectations(knowledge=True)

    [check] = check_understanding(
        expect, replace(NOTHING_RAISED, knowledge_documents=["On the breath"])
    )

    assert check == CheckResult(
        "knowledge", False, "chose On the breath, but no passage reached the reply"
    )


@pytest.mark.parametrize(
    "memory",
    [
        "      portrait: Maya has a Falling-out with Mei.\n",
        "      summaries: [{days_ago: 2, summary: Falling-out with Mei again.}]\n",
    ],
)
def test_a_thread_title_written_elsewhere_in_the_case_is_refused(
    tmp_path: Path, memory: str
) -> None:
    with pytest.raises(InvalidEvalCaseError, match="Falling-out with Mei"):
        read_cases(
            tmp_path,
            CASE_FILE_START + "  - id: hi\n"
            "    memory:\n"
            + memory
            + "      threads: [{title: Falling-out with Mei, story: S}]\n"
            "    messages: [{text: hi, expect: {found: [Falling-out with Mei]}}]\n",
        )


def test_moves_are_read_and_a_move_expected_alongside_no_move_is_refused(
    tmp_path: Path,
) -> None:
    [case] = read_cases(
        tmp_path,
        CASE_FILE_START + "  - id: hosting\n"
        "    web_search: false\n"
        "    web_results:\n"
        "      - {title: Hosts, url: 'https://hosts.example', text: Cheap hosts.}\n"
        "    messages:\n"
        "      - text: which host?\n"
        "        expect: {lead_move: [Research], support_move: [Suggest]}\n"
        "      - text: ugh\n"
        "        expect: {no_move: true}\n",
    )

    assert case.web_search is False
    assert [(result.title, result.url, result.text) for result in case.web_results] == [
        ("Hosts", "https://hosts.example", "Cheap hosts.")
    ]
    first, second = case.messages
    assert (first.expect.lead_move, first.expect.support_move) == (
        ["Research"],
        ["Suggest"],
    )
    assert second.expect.no_move is True
    with pytest.raises(InvalidEvalCaseError, match="no_move"):
        read_cases(
            tmp_path,
            CASE_FILE_START + "  - id: hi\n    messages:\n"
            "      - {text: hi, expect: {no_move: true, lead_move: [Push]}}\n",
        )


def test_a_case_without_web_settings_has_web_search_on_and_finds_nothing(
    tmp_path: Path,
) -> None:
    [case] = read_cases(
        tmp_path, CASE_FILE_START + "  - id: hi\n    messages: [{text: hi}]\n"
    )

    assert (case.web_search, case.web_results) == (True, [])


def test_the_moves_made_are_checked_ignoring_case() -> None:
    moved = replace(NOTHING_RAISED, lead_move="Research", support_move="Suggest")
    expect = UnderstandingExpectations(
        lead_move=["research", "Push"], support_move=["Suggest"], no_move=False
    )

    assert check_understanding(expect, moved) == [
        CheckResult("lead move", True, "led with Research"),
        CheckResult("supporting move", True, "supported with Suggest"),
        CheckResult("no move", True, "led with Research"),
    ]


def test_the_wrong_moves_or_a_move_when_none_was_expected_fail() -> None:
    pushed = replace(NOTHING_RAISED, lead_move="Push")

    assert check_understanding(
        UnderstandingExpectations(
            lead_move=["Research"], support_move=["Suggest"], no_move=True
        ),
        pushed,
    ) == [
        CheckResult("lead move", False, "led with Push, expected Research"),
        CheckResult(
            "supporting move", False, "had no supporting Move, expected Suggest"
        ),
        CheckResult("no move", False, "led with Push, expected no Move"),
    ]
    assert check_understanding(
        UnderstandingExpectations(lead_move=["Research", "Suggest"], no_move=False),
        NOTHING_RAISED,
    ) == [
        CheckResult("lead move", False, "made no Move, expected Research or Suggest"),
        CheckResult("no move", False, "made no Move, expected one"),
    ]
    assert check_understanding(
        UnderstandingExpectations(no_move=True),
        replace(NOTHING_RAISED, support_move="Calm"),
    ) == [
        CheckResult(
            "no move",
            False,
            "made no lead Move (supported with Calm), expected no Move",
        )
    ]
    assert check_understanding(
        UnderstandingExpectations(no_move=True), NOTHING_RAISED
    ) == [CheckResult("no move", True, "made no Move")]


def test_the_understanding_cases_check_moves_and_web_search() -> None:
    seed_cases: list[UnderstandingCase] = seeded(EvalName.UNDERSTANDING)
    cases = {case.id: case for case in seed_cases}

    hosting = cases["hosting-research"]
    assert hosting.web_search and hosting.web_results
    assert len(hosting.earlier) == 4
    assert hosting.messages[0].expect.lead_move == ["Research"]
    assert hosting.messages[0].expect.rules == ["names_hosts_under_budget"]
    assert set(cases["internal-testing-finish-line"].messages[0].expect.lead_move) == {
        "Push",
        "Plan steps",
    }
    venting = cases["venting-is-not-pushed"].messages[0].expect
    assert (venting.need, venting.rules) == (["Be heard"], ["no_fixing", "no_push"])
    no_search = cases["research-with-web-search-off"]
    assert no_search.web_search is False
    assert no_search.messages[0].expect.rules == ["honest_no_lookup"]
    assert cases["small-talk-makes-no-move"].messages[0].expect.no_move is True


def test_a_supporting_move_without_a_lead_is_not_a_lead() -> None:
    supported_only = replace(NOTHING_RAISED, support_move="Calm")

    assert check_understanding(
        UnderstandingExpectations(lead_move=["Calm"], no_move=False),
        supported_only,
    ) == [
        CheckResult(
            "lead move", False, "made no lead Move (supported with Calm), expected Calm"
        ),
        CheckResult(
            "no move", False, "made no lead Move (supported with Calm), expected one"
        ),
    ]


def test_a_next_move_and_made_up_move_outcomes_are_read(tmp_path: Path) -> None:
    [case] = read_cases(
        tmp_path,
        CASE_FILE_START + "  - id: exhausted\n"
        "    memory:\n"
        "      move_outcomes:\n"
        "        - move: Push\n"
        "          role: lead\n"
        "          situation: Their launch slipped again.\n"
        "          feeling: exhausted\n"
        "          result: didnt_help\n"
        "          why: They had nothing left to give.\n"
        "          days_ago: 5\n"
        "    messages:\n"
        "      - text: which host?\n"
        "        expect: {next_move: [Research, suggest]}\n",
    )

    [outcome] = case.memory.move_outcomes
    assert outcome == EvalMoveOutcome(
        move="Push",
        role=MoveRole.LEAD,
        situation="Their launch slipped again.",
        feeling="exhausted",
        result=MoveResult.DIDNT_HELP,
        why="They had nothing left to give.",
        days_ago=5,
    )
    assert case.messages[0].expect.next_move == ["Research", "suggest"]


def test_the_next_move_in_mind_is_checked_ignoring_case() -> None:
    expect = UnderstandingExpectations(next_move=["research"])

    assert check_understanding(
        expect, replace(NOTHING_RAISED, next_move="Research")
    ) == [CheckResult("next move", True, "has Research in mind next")]
    assert check_understanding(expect, replace(NOTHING_RAISED, next_move="Push")) == [
        CheckResult("next move", False, "has Push in mind next, expected research")
    ]
    assert check_understanding(expect, NOTHING_RAISED) == [
        CheckResult("next move", False, "has no next Move in mind, expected research")
    ]


def test_the_understanding_cases_check_the_next_move_and_move_outcomes() -> None:
    seed_cases: list[UnderstandingCase] = seeded(EvalName.UNDERSTANDING)
    cases = {case.id: case for case in seed_cases}

    first, second = cases["next-move-held-then-made"].messages
    assert first.expect.next_move and first.expect.next_move == second.expect.lead_move
    exhausted = cases["no-push-when-exhausted"]
    frustrated = cases["push-when-frustrated"]
    assert exhausted.memory == frustrated.memory
    assert {
        (outcome.move, outcome.feeling, outcome.result)
        for outcome in exhausted.memory.move_outcomes
    } == {
        ("Push", "exhausted, drained", MoveResult.DIDNT_HELP),
        ("Push", "frustrated, fed up", MoveResult.HELPED),
    }
    assert exhausted.messages[0].expect.rules == ["no_push_while_exhausted"]
    assert "Push" in frustrated.messages[0].expect.lead_move
