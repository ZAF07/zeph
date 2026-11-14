from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from evals.cases import (
    CASES_DIR,
    InvalidEvalCasesError,
    UnderstandingExpectations,
    load_understanding_cases,
)
from evals.judge import RuleVerdict
from evals.report import (
    EvalReport,
    UnderstandingCallStats,
    UnderstandingMessageResult,
)
from evals.understanding_checks import (
    CheckResult,
    ObservedUnderstanding,
    check_understanding,
)

CASE_FILE_START = """\
now: 2026-11-13T18:30:00
rules:
  no_fixing: Zeph's last reply gives no advice.
cases:
"""


NOTHING_RAISED = ObservedUnderstanding(
    need="Be heard",
    understanding_input="Life Threads this reminds you of:\n[1] Falling-out with Mei",
    raised_threads=[],
    raised_curiosities=0,
    asked_why=False,
    knowledge_documents=[],
    knowledge_in_reply=[],
)


def test_the_understanding_cases_cover_every_check_the_issue_asks_for() -> None:
    cases = load_understanding_cases(CASES_DIR / "understanding.yaml")

    expectations = [message.expect for case in cases.cases for message in case.messages]
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
    threads = [thread for case in cases.cases for thread in case.memory.threads]
    assert any(thread.raised_in_this_conversation for thread in threads)
    assert any(thread.reaction == "brushed_off" for thread in threads)


def test_a_case_is_read_with_its_memory_earlier_lines_and_messages(
    tmp_path: Path,
) -> None:
    cases_file = tmp_path / "understanding.yaml"
    cases_file.write_text(
        CASE_FILE_START
        + """\
  - id: wedding
    now: 2026-11-12T09:00:00
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
          rules: [no_fixing]
"""
    )

    [case] = load_understanding_cases(cases_file).cases

    assert case.now == datetime(2026, 11, 12, 9, tzinfo=UTC)
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
        rules=["no_fixing"],
    )


def test_a_case_without_its_own_time_uses_the_files(tmp_path: Path) -> None:
    cases_file = tmp_path / "understanding.yaml"
    cases_file.write_text(CASE_FILE_START + "  - id: hi\n    messages: [{text: hi}]\n")

    [case] = load_understanding_cases(cases_file).cases

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
    cases_file = tmp_path / "understanding.yaml"
    cases_file.write_text(CASE_FILE_START + f"  - id: hi\n    messages: [{message}]\n")

    with pytest.raises(InvalidEvalCasesError, match=refused):
        load_understanding_cases(cases_file)


def test_a_thread_raised_in_this_conversation_needs_earlier_lines(
    tmp_path: Path,
) -> None:
    cases_file = tmp_path / "understanding.yaml"
    cases_file.write_text(
        CASE_FILE_START + "  - id: hi\n"
        "    memory:\n"
        "      threads: [{title: T, story: S, raised_in_this_conversation: true}]\n"
        "    messages: [{text: hi}]\n"
    )

    with pytest.raises(InvalidEvalCasesError, match="earlier"):
        load_understanding_cases(cases_file)


def test_understanding_cases_with_the_same_id_are_refused(tmp_path: Path) -> None:
    cases_file = tmp_path / "understanding.yaml"
    message = "    messages: [{text: hi}]\n"
    cases_file.write_text(CASE_FILE_START + f"  - id: a\n{message}  - id: a\n{message}")

    with pytest.raises(InvalidEvalCasesError, match="a"):
        load_understanding_cases(cases_file)


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


def test_the_report_shows_each_message_with_its_checks_reasons_time_and_tokens() -> (
    None
):
    report = EvalReport(
        understanding=[
            UnderstandingMessageResult(
                case_id="rant",
                message="ugh my landlord",
                checks=[CheckResult("need", True, "picked Be heard")],
                verdicts=[RuleVerdict("no_fixing", False, "Suggests a lawyer.")],
                call=UnderstandingCallStats(1200, 2000, 150),
            ),
            UnderstandingMessageResult(
                case_id="rant",
                message="anyway",
                checks=[CheckResult("need", False, "picked Advice, expected Be heard")],
                verdicts=[],
                call=UnderstandingCallStats(1800, 2400, 250),
            ),
        ]
    )

    text = "\n".join(report.lines())

    assert "Understanding: 0 of 2 messages passed (1 of 2 checks, 0 of 1 rules)" in (
        text
    )
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


def test_a_message_with_no_understanding_call_fails_and_says_so() -> None:
    result = UnderstandingMessageResult(
        case_id="hi", message="hi", checks=[], verdicts=[], call=None
    )
    report = EvalReport(understanding=[result])

    text = "\n".join(report.lines())

    assert not result.passed
    assert "    hi (no Understanding call was logged)" in text
    assert "Understanding calls: 0" in text


def test_knowledge_chosen_but_not_reaching_the_reply_fails() -> None:
    expect = UnderstandingExpectations(knowledge=True)
    named_by_its_line = "“On the breath” (Owner's notes, Mindfulness)"

    [check] = check_understanding(
        expect, replace(NOTHING_RAISED, knowledge_documents=[named_by_its_line])
    )

    assert check == CheckResult(
        "knowledge",
        False,
        f"chose {named_by_its_line}, but no passage reached the reply",
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
    cases_file = tmp_path / "understanding.yaml"
    cases_file.write_text(
        CASE_FILE_START + "  - id: hi\n"
        "    memory:\n"
        + memory
        + "      threads: [{title: Falling-out with Mei, story: S}]\n"
        "    messages: [{text: hi, expect: {found: [Falling-out with Mei]}}]\n"
    )

    with pytest.raises(InvalidEvalCasesError, match="Falling-out with Mei"):
        load_understanding_cases(cases_file)
