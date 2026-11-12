from pathlib import Path

import pytest

from evals.cases import (
    CASES_DIR,
    InvalidEvalCasesError,
    KnowledgeDetails,
    SafeguardCase,
    SafeguardCaseKind,
    load_knowledge_cases,
    load_persona_cases,
    load_safeguard_cases,
)
from evals.judge import (
    RuleVerdict,
    VersionVerdict,
    read_json_answer,
    read_rule_verdicts,
    read_version_verdict,
)
from evals.report import (
    EvalReport,
    KnowledgeStepResult,
    PersonaResult,
    SafeguardResult,
)


def test_the_safeguard_cases_cover_clear_and_subtle_crises_and_false_alarms() -> None:
    cases = load_safeguard_cases(CASES_DIR / "safeguard.yaml")

    kinds = {case.kind for case in cases}
    assert len(cases) >= 30
    assert kinds == set(SafeguardCaseKind)
    assert len({case.id for case in cases}) == len(cases)


def test_the_persona_cases_use_only_known_rules_and_include_a_photo() -> None:
    cases = load_persona_cases(CASES_DIR / "persona.yaml")

    for conversation in cases.conversations:
        assert conversation.rules
        assert all(rule in cases.rules for rule in conversation.rules)
    photo_conversations = [
        conversation
        for conversation in cases.conversations
        if any(message.photo for message in conversation.messages)
    ]
    assert photo_conversations
    assert all("photo_honesty" in c.rules for c in photo_conversations)


def test_the_knowledge_cases_have_three_different_versions_and_new_details() -> None:
    cases = load_knowledge_cases(CASES_DIR / "knowledge.yaml")

    assert cases
    for case in cases:
        texts = {case.original_text, case.edited_text, case.replacement_text}
        assert len(texts) == 3
        assert case.original_details != case.edited_details


def test_a_persona_conversation_naming_an_unknown_rule_is_refused(
    tmp_path: Path,
) -> None:
    cases_file = tmp_path / "persona.yaml"
    cases_file.write_text(
        "rules:\n  no_lists: No lists.\n"
        "conversations:\n"
        "  - id: chat\n    messages: [hi]\n    rules: [no_lists, be_funny]\n"
    )

    with pytest.raises(InvalidEvalCasesError, match="be_funny"):
        load_persona_cases(cases_file)


def test_cases_with_the_same_id_are_refused(tmp_path: Path) -> None:
    cases_file = tmp_path / "safeguard.yaml"
    cases_file.write_text(
        "- {id: a, kind: false_alarm, message: one}\n"
        "- {id: a, kind: clear_crisis, message: two}\n"
    )

    with pytest.raises(InvalidEvalCasesError, match="a"):
        load_safeguard_cases(cases_file)


def test_a_photo_message_is_read_from_its_caption(tmp_path: Path) -> None:
    cases_file = tmp_path / "persona.yaml"
    cases_file.write_text(
        "rules:\n  photo_honesty: Can't see photos.\n"
        "conversations:\n"
        "  - id: plant\n"
        "    messages: [hi, {photo_caption: my new plant}]\n"
        "    rules: [photo_honesty]\n"
    )

    [conversation] = load_persona_cases(cases_file).conversations

    assert [(m.text, m.photo) for m in conversation.messages] == [
        ("hi", False),
        ("my new plant", True),
    ]


def test_a_json_answer_is_read_with_or_without_a_code_fence() -> None:
    assert read_json_answer('{"version": "edited"}') == {"version": "edited"}
    assert read_json_answer('```json\n{"version": "edited"}\n```') == {
        "version": "edited"
    }


def test_an_answer_that_is_not_a_json_object_is_refused() -> None:
    with pytest.raises(ValueError):
        read_json_answer("The reply uses the edited text.")
    with pytest.raises(ValueError):
        read_json_answer('["edited"]')


def test_rule_verdicts_are_read_for_every_asked_rule() -> None:
    answer = (
        '{"verdicts": ['
        '{"rule": "no_lists", "passed": true, "reason": "Plain texts."},'
        '{"rule": "not_preachy", "passed": false, "reason": "Lectures."}'
        "]}"
    )

    verdicts = read_rule_verdicts(answer, ["no_lists", "not_preachy"])

    assert verdicts == [
        RuleVerdict(rule="no_lists", passed=True, reason="Plain texts."),
        RuleVerdict(rule="not_preachy", passed=False, reason="Lectures."),
    ]


def test_a_rule_the_judge_skipped_or_an_unreadable_answer_fails() -> None:
    skipped = read_rule_verdicts(
        '{"verdicts": [{"rule": "no_lists", "passed": true, "reason": "ok"}]}',
        ["no_lists", "not_preachy"],
    )
    unreadable = read_rule_verdicts("all good", ["no_lists"])

    assert skipped[1] == RuleVerdict(
        rule="not_preachy", passed=False, reason="The judge gave no verdict."
    )
    assert unreadable[0].passed is False
    assert "could not be read" in unreadable[0].reason


def test_a_version_verdict_is_read_and_an_unknown_version_counts_as_none() -> None:
    labels = ["original", "edited"]

    known = read_version_verdict('{"version": "Edited", "reason": "4 counts"}', labels)
    unknown = read_version_verdict('{"version": "both", "reason": "?"}', labels)
    unreadable = read_version_verdict("edited", labels)

    assert known == VersionVerdict(version="edited", reason="4 counts")
    assert unknown.version == "none"
    assert unreadable.version == "none"
    assert "could not be read" in unreadable.reason


def safeguard_case(case_id: str, kind: SafeguardCaseKind) -> SafeguardCase:
    return SafeguardCase(id=case_id, kind=kind, message=f"{case_id} message")


def test_the_report_lists_missed_crises_and_false_alarms() -> None:
    report = EvalReport(settings_source="the seed file")
    report.safeguard = [
        SafeguardResult(safeguard_case("plan", SafeguardCaseKind.CLEAR_CRISIS), None),
        SafeguardResult(
            safeguard_case("traffic", SafeguardCaseKind.FALSE_ALARM), "abuse"
        ),
        SafeguardResult(
            safeguard_case("letters", SafeguardCaseKind.SUBTLE_CRISIS),
            "suicide_or_self_harm",
        ),
    ]

    text = "\n".join(report.lines())

    assert "Settings: the seed file" in text
    assert "Safeguard: 1 of 3 right" in text
    assert "Missed crises (1):\n    plan (clear_crisis): plan message" in text
    assert "False alarms (1):\n    traffic: traffic message → abuse" in text


def test_the_report_shows_each_rule_and_knowledge_step_with_the_reason() -> None:
    report = EvalReport(settings_source="the app database")
    report.persona = [
        PersonaResult(
            conversation_id="photo",
            verdicts=[RuleVerdict("photo_honesty", False, "Talks about the leaves.")],
        )
    ]
    report.knowledge = [
        KnowledgeStepResult(
            case_id="lantern",
            step="text edited",
            expected="edited",
            older=["original"],
            verdict=VersionVerdict("original", "Says 7 counts."),
        )
    ]

    text = "\n".join(report.lines())

    assert "  photo\n    FAIL photo_honesty: Talks about the leaves." in text
    assert (
        "  lantern\n    FAIL text edited: uses an old version (original), "
        "expected edited. Says 7 counts."
    ) in text


def test_knowledge_details_read_as_one_line_for_the_judge() -> None:
    details = KnowledgeDetails(title="Night", source="Brother Elk", tradition="Coast")

    assert details.describe() == "title “Night”, source Brother Elk, tradition Coast"
