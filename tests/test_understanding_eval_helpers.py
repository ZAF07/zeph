from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from companion.adapters.evals.terminal_report import eval_lines
from companion.core.evals.cases import (
    EvalMoveOutcome,
    InvalidEvalCaseError,
    UnderstandingCase,
    UnderstandingExpectations,
)
from companion.core.evals.made_up_memory import to_curiosity
from companion.core.evals.models import CaseOutcome, Check, EvalName
from companion.core.evals.understanding_checks import (
    CheckResult,
    ObservedUnderstanding,
    check_steps,
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
    reply_plan_input="Life Threads this reminds you of:\n[1] Falling-out with Mei",
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
    assert any(expect.asked_why is False for expect in expectations)
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
    for flag in (
        "struggling",
        "cause_known",
        "looks_up_past",
        "feelings_said",
        "wants_said",
        "read_formed",
        "read_said",
    ):
        assert any(getattr(expect, flag) is not None for expect in expectations)
    assert any(expect.read_said is True for expect in expectations)
    assert any(expect.read_said is False for expect in expectations)
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
      - text: what do you think is going on with me?
        expect:
          struggling: true
          cause_known: false
          looks_up_past: true
          feelings_said: false
          wants_said: true
          read_formed: true
          read_said: true
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
    assert case.messages[1].expect == UnderstandingExpectations(
        struggling=True,
        cause_known=False,
        looks_up_past=True,
        feelings_said=False,
        wants_said=True,
        read_formed=True,
        read_said=True,
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

    checks = check_steps(
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
        CheckResult("Recall · found", True, "was reminded of Falling-out with Mei"),
        CheckResult("Reply Plan · need", True, "picked Be heard"),
        CheckResult("Reply Plan · raised", True, "brought up Falling-out with Mei"),
        CheckResult("Reply Plan · curiosity", True, "brought up 1 Curiosity"),
        CheckResult("Reply Plan · asked why", True, "asked why"),
        CheckResult(
            "Reply Plan · knowledge",
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

    checks = check_steps(
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
        CheckResult("Recall · found", False, "wasn't reminded of Moving to Perth"),
        CheckResult("Reply Plan · need", False, "picked Advice, expected Be heard"),
        CheckResult(
            "Reply Plan · not raised", False, "brought up Falling-out with Mei"
        ),
        CheckResult(
            "Reply Plan · curiosity", False, "brought up 2 Curiosities, expected none"
        ),
        CheckResult("Reply Plan · asked why", False, "asked why, expected not to"),
        CheckResult(
            "Reply Plan · knowledge", False, "chose On the breath, expected none"
        ),
    ]


def test_each_expectation_is_checked_on_the_step_that_owns_it() -> None:
    expect = UnderstandingExpectations(
        struggling=True,
        cause_known=False,
        looks_up_past=True,
        feelings_said=False,
        wants_said=True,
        found=["Falling-out with Mei"],
        read_formed=True,
        read_said=False,
        need=["Be heard"],
    )
    observed = replace(
        NOTHING_RAISED,
        struggling=True,
        cause_known=False,
        looked_up_past=True,
        wants_said=True,
        read_formed=True,
    )

    assert check_steps(expect, observed) == [
        CheckResult("Understanding · struggling", True, "struggling"),
        CheckResult(
            "Understanding · cause known", True, "didn't know why they feel this way"
        ),
        CheckResult("Understanding · looks up the past", True, "looked up the past"),
        CheckResult("Understanding · feelings said", True, "kept no feelings as said"),
        CheckResult(
            "Understanding · wants said", True, "kept wants said in their words"
        ),
        CheckResult("Recall · found", True, "was reminded of Falling-out with Mei"),
        CheckResult("Reply Plan · read formed", True, "formed a Read"),
        CheckResult("Reply Plan · read said", True, "held the Read back"),
        CheckResult("Reply Plan · need", True, "picked Be heard"),
    ]


def test_a_missed_understanding_or_read_says_what_was_expected() -> None:
    expect = UnderstandingExpectations(
        struggling=False,
        cause_known=True,
        looks_up_past=False,
        feelings_said=True,
        read_formed=True,
        read_said=True,
    )
    observed = replace(
        NOTHING_RAISED, struggling=True, cause_known=False, looked_up_past=True
    )

    assert check_steps(expect, observed) == [
        CheckResult(
            "Understanding · struggling", False, "struggling, expected: not struggling"
        ),
        CheckResult(
            "Understanding · cause known",
            False,
            "didn't know why they feel this way, expected: knew why they feel this way",
        ),
        CheckResult(
            "Understanding · looks up the past",
            False,
            "looked up the past, expected: looked up nothing",
        ),
        CheckResult(
            "Understanding · feelings said",
            False,
            "kept no feelings as said, expected: kept feelings said in their words",
        ),
        CheckResult(
            "Reply Plan · read formed", False, "formed no Read, expected: formed a Read"
        ),
        CheckResult(
            "Reply Plan · read said",
            False,
            "held the Read back, expected: said the Read",
        ),
    ]


def test_expectations_left_out_are_not_checked() -> None:
    assert check_steps(UnderstandingExpectations(), NOTHING_RAISED) == []


def test_a_woven_in_check_in_is_checked_against_what_was_expected() -> None:
    woven = replace(NOTHING_RAISED, woven_in=True)

    assert check_steps(UnderstandingExpectations(woven_in=True), woven) == [
        CheckResult("Reply Plan · woven in", True, "wove in the due Check-in")
    ]
    assert check_steps(UnderstandingExpectations(woven_in=False), woven) == [
        CheckResult(
            "Reply Plan · woven in", False, "wove in the due Check-in, expected not now"
        )
    ]
    assert check_steps(UnderstandingExpectations(woven_in=True), NOTHING_RAISED) == [
        CheckResult(
            "Reply Plan · woven in", False, "said not now, expected it woven in"
        )
    ]


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

    checks = check_steps(expect, NOTHING_RAISED)

    assert checks == [
        CheckResult(
            "Reply Plan · raised", False, "didn't bring up Falling-out with Mei"
        ),
        CheckResult("Reply Plan · not raised", True, "left Falling-out with Mei alone"),
        CheckResult("Reply Plan · curiosity", False, "brought up no Curiosity"),
        CheckResult("Reply Plan · knowledge", False, "chose no document"),
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

    [check] = check_steps(
        expect, replace(NOTHING_RAISED, knowledge_documents=["On the breath"])
    )

    assert check == CheckResult(
        "Reply Plan · knowledge",
        False,
        "chose On the breath, but no passage reached the reply",
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

    assert check_steps(expect, moved) == [
        CheckResult("Reply Plan · lead move", True, "led with Research"),
        CheckResult("Reply Plan · supporting move", True, "supported with Suggest"),
        CheckResult("Reply Plan · no move", True, "led with Research"),
    ]


def test_the_wrong_moves_or_a_move_when_none_was_expected_fail() -> None:
    pushed = replace(NOTHING_RAISED, lead_move="Push")

    assert check_steps(
        UnderstandingExpectations(
            lead_move=["Research"], support_move=["Suggest"], no_move=True
        ),
        pushed,
    ) == [
        CheckResult(
            "Reply Plan · lead move", False, "led with Push, expected Research"
        ),
        CheckResult(
            "Reply Plan · supporting move",
            False,
            "had no supporting Move, expected Suggest",
        ),
        CheckResult("Reply Plan · no move", False, "led with Push, expected no Move"),
    ]
    assert check_steps(
        UnderstandingExpectations(lead_move=["Research", "Suggest"], no_move=False),
        NOTHING_RAISED,
    ) == [
        CheckResult(
            "Reply Plan · lead move",
            False,
            "made no Move, expected Research or Suggest",
        ),
        CheckResult("Reply Plan · no move", False, "made no Move, expected one"),
    ]
    assert check_steps(
        UnderstandingExpectations(no_move=True),
        replace(NOTHING_RAISED, support_move="Calm"),
    ) == [
        CheckResult(
            "Reply Plan · no move",
            False,
            "made no lead Move (supported with Calm), expected no Move",
        )
    ]
    assert check_steps(UnderstandingExpectations(no_move=True), NOTHING_RAISED) == [
        CheckResult("Reply Plan · no move", True, "made no Move")
    ]


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
    small_talk = cases["small-talk-stays-light"].messages[0].expect
    assert small_talk.rules == ["spilled_coffee_stays_light"]


def test_a_supporting_move_without_a_lead_is_not_a_lead() -> None:
    supported_only = replace(NOTHING_RAISED, support_move="Calm")

    assert check_steps(
        UnderstandingExpectations(lead_move=["Calm"], no_move=False),
        supported_only,
    ) == [
        CheckResult(
            "Reply Plan · lead move",
            False,
            "made no lead Move (supported with Calm), expected Calm",
        ),
        CheckResult(
            "Reply Plan · no move",
            False,
            "made no lead Move (supported with Calm), expected one",
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

    assert check_steps(expect, replace(NOTHING_RAISED, next_move="Research")) == [
        CheckResult("Reply Plan · next move", True, "has Research in mind next")
    ]
    assert check_steps(expect, replace(NOTHING_RAISED, next_move="Push")) == [
        CheckResult(
            "Reply Plan · next move", False, "has Push in mind next, expected research"
        )
    ]
    assert check_steps(expect, NOTHING_RAISED) == [
        CheckResult(
            "Reply Plan · next move",
            False,
            "has no next Move in mind, expected research",
        )
    ]


def test_the_understanding_cases_check_hosting_help_and_move_outcomes() -> None:
    seed_cases: list[UnderstandingCase] = seeded(EvalName.UNDERSTANDING)
    cases = {case.id: case for case in seed_cases}

    first, second = cases["hosting-help-over-two-messages"].messages
    assert first.expect.rules == ["starts_them_off_on_hosting"]
    assert second.expect.rules == ["fits_hosts_to_their_budget"]
    strong_mood = cases["strong-mood-unknown-cause"].messages[0].expect
    assert strong_mood.rules == ["gentle_probe"]
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


def test_a_made_up_guess_curiosity_is_read_and_saved_with_how_sure_zeph_is(
    tmp_path: Path,
) -> None:
    [case] = read_cases(
        tmp_path,
        CASE_FILE_START + "  - id: mum\n"
        "    memory:\n"
        "      curiosities:\n"
        "        - question: Is your mum back in Singapore?\n"
        "          why: She went home after a visit.\n"
        "          guess: their mum lives in Singapore\n"
        "          how_sure: medium\n"
        "        - question: How was the week?\n"
        "          why: Busy week.\n"
        "    messages:\n"
        "      - text: talked to mum\n",
    )
    now = datetime(2026, 11, 13, 18, 30, tzinfo=UTC)

    guess, plain = (
        to_curiosity(uuid4(), curiosity, now) for curiosity in case.memory.curiosities
    )

    assert (guess.guess, guess.how_sure) == ("their mum lives in Singapore", "medium")
    assert (plain.guess, plain.how_sure) == (None, None)


def test_the_understanding_cases_check_a_guess_by_raising_its_curiosity() -> None:
    seed_cases: list[UnderstandingCase] = seeded(EvalName.UNDERSTANDING)
    case = {case.id: case for case in seed_cases}["guess-checked-gently"]

    [curiosity] = case.memory.curiosities
    [message] = case.messages
    assert (curiosity.guess, curiosity.how_sure) == (
        "their mum lives in Singapore",
        "medium",
    )
    assert "mum" in message.text
    assert message.expect.curiosity_raised is True
    assert message.expect.lead_move == []
    assert message.expect.rules == ["checks_guess_gently"]


def test_the_understanding_cases_draw_the_line_between_an_update_and_a_vent() -> None:
    seed_cases: list[UnderstandingCase] = seeded(EvalName.UNDERSTANDING)
    cases = {case.id: case for case in seed_cases}
    update = cases["passing-update-gets-curious"]
    vent = cases["real-vent-is-heard"]

    check_in, long_day, _ = update.earlier
    [sleep] = update.messages
    assert not check_in.from_person and "morning" in check_in.text.lower()
    assert long_day.text == "It's going to be a long day"
    assert sleep.text == "5 hours sleep only"
    assert sleep.expect.need == ["Just chatting"]
    assert sleep.expect.lead_move == ["Get curious"]
    assert sleep.expect.rules == ["one_light_question"]
    [rant] = vent.messages
    assert rant.expect.need == ["Be heard"]
    assert rant.expect.asked_why is False
    assert rant.expect.rules == ["no_why_question"]
