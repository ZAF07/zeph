import copy
from pathlib import Path
from typing import Any

import pytest
import yaml

from companion.adapters.pattern_catalog_seed import read_pattern_catalog_seed
from companion.core.models import (
    ExcludedEvidence,
    PatternArea,
    PatternTypeFile,
    PatternTypeStatus,
    SignPart,
    SignStrength,
)
from companion.core.pattern_catalog import (
    InvalidPatternCatalogError,
    read_pattern_types,
)
from tests.conftest import PATTERN_CATALOG_DIR

VALID: dict[str, Any] = {
    "id": "TEST.ONE",
    "version": "1.0.0",
    "area": "conflict",
    "name": "Test one",
    "status": "draft",
    "definition": "What it is.",
    "if": "Something happens",
    "then": "They do this",
    "function": "To get that",
    "frameworks": ["A published idea"],
    "signs": [
        {"id": "I1", "text": "Says a thing", "strength": "strong", "part": "inside"}
    ],
    "signs_against": [
        {"id": "D1", "text": "Says the other", "strength": "weak", "part": "situation"}
    ],
    "look_alikes": [{"name": "Something else", "tells_apart": "How they differ"}],
    "anyone_would": "What anyone would do",
    "exclusions": [{"text": "Grief", "evidence": "ignored"}],
    "approved_wording": "You seem to do this.",
    "prediction_wording": "Next time {person} asks, notice what you do.",
    "numbers": {"situations_needed": 3, "base_rate": 0.2},
}


def changed(**changes: Any) -> dict[str, Any]:
    """A valid Pattern Type's content with some fields changed."""
    return {**copy.deepcopy(VALID), **changes}


def without(field: str) -> dict[str, Any]:
    """A valid Pattern Type's content with one field taken out."""
    content = copy.deepcopy(VALID)
    del content[field]
    return content


def problems_of(*contents: dict[str, Any]) -> list[str]:
    """What the reader says is wrong with some files, named a.yaml, b.yaml, …"""
    files = [
        PatternTypeFile(name=f"{letter}.yaml", content=content)
        for letter, content in zip("abc", contents, strict=False)
    ]
    with pytest.raises(InvalidPatternCatalogError) as raised:
        read_pattern_types(files)
    return raised.value.problems


def test_the_three_drafted_pattern_types_in_the_repo_are_valid_drafts() -> None:
    pattern_types = read_pattern_types(read_pattern_catalog_seed(PATTERN_CATALOG_DIR))

    assert {pattern_type.id: pattern_type.area for pattern_type in pattern_types} == {
        "ACH.WORTH.PERF": PatternArea.ACHIEVEMENT,
        "CONF.AVOID.BELONG": PatternArea.CONFLICT,
        "CTRL.UNCERT.PLAN": PatternArea.CONTROL,
    }
    assert {pattern_type.status for pattern_type in pattern_types} == {
        PatternTypeStatus.DRAFT
    }


def test_a_pattern_type_is_read_with_all_its_details() -> None:
    conflict = next(
        pattern_type
        for pattern_type in read_pattern_types(
            read_pattern_catalog_seed(PATTERN_CATALOG_DIR)
        )
        if pattern_type.id == "CONF.AVOID.BELONG"
    )

    assert conflict.version == "0.1.0"
    assert conflict.if_situation == "Disagreement with a valued other"
    assert conflict.then_behaviour == "Withholds or softens own view"
    assert conflict.function == "To protect belonging"
    assert conflict.definition.startswith("When disagreement arises")
    assert len(conflict.signs) == 5
    assert (conflict.signs[1].strength, conflict.signs[1].part) == (
        SignStrength.STRONG,
        SignPart.INSIDE,
    )
    assert [sign.id for sign in conflict.signs_against] == ["D1", "D2"]
    assert [look_alike.pattern_type_id for look_alike in conflict.look_alikes] == [
        "ACH.WORTH.PERF",
        "CTRL.UNCERT.PLAN",
    ]
    assert conflict.anyone_would == (
        "Low-stakes avoidance with strangers or authority only"
    )
    assert [exclusion.evidence for exclusion in conflict.exclusions] == [
        ExcludedEvidence.IGNORED,
        ExcludedEvidence.IGNORED,
    ]
    assert conflict.approved_wording.startswith("You seem to protect closeness")
    assert "{person}" in conflict.prediction_wording
    assert (conflict.numbers.situations_needed, conflict.numbers.base_rate) == (3, 0.2)
    assert (conflict.approved_by, conflict.approved_on) == (None, None)


def test_a_missing_required_field_is_refused_by_name() -> None:
    assert problems_of(without("definition")) == ["a.yaml: definition is missing."]


def test_a_missing_field_inside_a_sign_says_which_sign() -> None:
    signs = [{"id": "I1", "text": "Says a thing", "part": "inside"}]

    assert problems_of(changed(signs=signs)) == [
        "a.yaml: signs[1].strength is missing."
    ]


def test_an_unknown_look_alike_is_refused() -> None:
    look_alikes = [{"pattern_type": "TEST.NOWHERE", "tells_apart": "How"}]

    assert problems_of(changed(look_alikes=look_alikes)) == [
        "a.yaml: look_alikes[1].pattern_type is TEST.NOWHERE, "
        "which is not a Pattern Type in the catalog."
    ]


def test_a_look_alike_may_name_another_pattern_type_in_the_catalog() -> None:
    look_alikes = [{"pattern_type": "TEST.TWO", "tells_apart": "How"}]
    files = [
        PatternTypeFile(name="a.yaml", content=changed(look_alikes=look_alikes)),
        PatternTypeFile(name="b.yaml", content=changed(id="TEST.TWO")),
    ]

    first, _ = read_pattern_types(files)

    assert first.look_alikes[0].pattern_type_id == "TEST.TWO"


@pytest.mark.parametrize(
    ("content", "problem"),
    [
        (
            changed(area="money"),
            "a.yaml: area is money; it must be one of conflict, approval, "
            "control, achievement, relationships.",
        ),
        (
            changed(status="live"),
            "a.yaml: status is live; it must be one of draft, approved, archived.",
        ),
        (
            changed(
                signs=[
                    {"id": "I1", "text": "Says", "strength": "huge", "part": "inside"}
                ]
            ),
            "a.yaml: signs[1].strength is huge; it must be one of weak, "
            "moderate, strong.",
        ),
        (
            changed(
                signs=[{"id": "I1", "text": "Says", "strength": "weak", "part": "mood"}]
            ),
            "a.yaml: signs[1].part is mood; it must be one of situation, "
            "inside, behaviour.",
        ),
        (
            changed(exclusions=[{"text": "Grief", "evidence": "hidden"}]),
            "a.yaml: exclusions[1].evidence is hidden; it must be one of "
            "ignored, counted_not_shared.",
        ),
    ],
)
def test_a_value_outside_a_fixed_list_is_refused(
    content: dict[str, Any], problem: str
) -> None:
    assert problems_of(content) == [problem]


def test_every_problem_is_listed_together_in_one_clear_message() -> None:
    files = [
        PatternTypeFile(name="a.yaml", content=without("name")),
        PatternTypeFile(name="b.yaml", content=changed(id="TEST.TWO", area="money")),
    ]

    with pytest.raises(InvalidPatternCatalogError) as raised:
        read_pattern_types(files)

    assert str(raised.value) == (
        "The Pattern Catalog can't be loaded. Nothing was changed.\n"
        "- a.yaml: name is missing.\n"
        "- b.yaml: area is money; it must be one of conflict, approval, "
        "control, achievement, relationships."
    )


@pytest.mark.parametrize(
    ("content", "problem"),
    [
        (changed(colour="blue"), "a.yaml: colour is not a field of a Pattern Type."),
        (changed(id="lower.case"), "a.yaml: id must look like CONF.AVOID.BELONG."),
        (changed(version="2"), "a.yaml: version must look like 1.0.0."),
        (changed(version=1.5), "a.yaml: version must be text."),
        (changed(definition="  "), "a.yaml: definition must not be empty."),
        (changed(signs=[]), "a.yaml: signs needs at least one entry."),
        (changed(signs="many"), "a.yaml: signs must be a list."),
        (
            changed(
                signs_against=[
                    {
                        "id": "I1",
                        "text": "Says",
                        "strength": "weak",
                        "part": "situation",
                    }
                ]
            ),
            "a.yaml: I1 is the ID of more than one sign.",
        ),
        (
            changed(look_alikes=[{"tells_apart": "How"}]),
            "a.yaml: look_alikes[1] needs either pattern_type or name.",
        ),
        (
            changed(look_alikes=[{"pattern_type": "TEST.ONE", "tells_apart": "How"}]),
            "a.yaml: look_alikes[1].pattern_type is TEST.ONE, "
            "which is this Pattern Type itself.",
        ),
        (
            changed(numbers={"situations_needed": 0, "base_rate": 0.2}),
            "a.yaml: numbers.situations_needed must be a whole number, 1 or more.",
        ),
        (
            changed(numbers={"situations_needed": 3, "base_rate": 20}),
            "a.yaml: numbers.base_rate must be a number between 0 and 1.",
        ),
        (
            changed(status="approved"),
            "a.yaml: an approved Pattern Type needs approved_by and approved_on.",
        ),
        (
            changed(approved_by="Zaf", approved_on="2026-11-24"),
            "a.yaml: only an approved or archived Pattern Type may have "
            "approved_by and approved_on.",
        ),
        (
            changed(status="approved", approved_by="Zaf", approved_on="soon"),
            "a.yaml: approved_on must be a day like 2026-11-24.",
        ),
        (
            changed(status="archived", approved_by="Zaf"),
            "a.yaml: approved_by and approved_on go together; one is missing.",
        ),
        (
            changed(look_alikes=[{"name": "TEST.TWOO", "tells_apart": "How"}]),
            "a.yaml: look_alikes[1].name is TEST.TWOO, which looks like a "
            "Pattern Type's ID; give an ID as pattern_type.",
        ),
        (without("anyone_would"), "a.yaml: anyone_would is missing."),
        ("just text", "a.yaml: the file must hold a Pattern Type's fields."),
    ],
)
def test_other_mistakes_are_refused_with_a_reason(content: Any, problem: str) -> None:
    assert problems_of(content) == [problem]


def test_a_look_alike_named_both_ways_is_refused() -> None:
    look_alikes = [{"pattern_type": "TEST.TWO", "name": "Two", "tells_apart": "How"}]

    assert problems_of(changed(look_alikes=look_alikes), changed(id="TEST.TWO")) == [
        "a.yaml: look_alikes[1] needs either pattern_type or name, not both."
    ]


def test_two_files_with_the_same_id_are_refused() -> None:
    assert problems_of(changed(), changed()) == [
        "b.yaml: TEST.ONE is already the ID of the Pattern Type in a.yaml."
    ]


def test_an_approved_pattern_type_says_who_approved_it_and_when() -> None:
    content = changed(status="approved", approved_by="Zaf", approved_on="2026-11-24")

    (pattern_type,) = read_pattern_types([PatternTypeFile("a.yaml", content)])

    assert pattern_type.status == PatternTypeStatus.APPROVED
    assert pattern_type.approved_by == "Zaf"
    assert pattern_type.approved_on is not None
    assert pattern_type.approved_on.isoformat() == "2026-11-24"


def test_the_seed_reader_reads_each_yaml_file_as_plain_values(tmp_path: Path) -> None:
    content = changed(status="approved", approved_by="Zaf")
    (tmp_path / "b-second.yaml").write_text(yaml.safe_dump(changed(id="TEST.TWO")))
    (tmp_path / "a-first.yaml").write_text(
        yaml.safe_dump(content) + "approved_on: 2026-11-24\n"
    )
    (tmp_path / "notes.txt").write_text("not a Pattern Type")

    files = read_pattern_catalog_seed(tmp_path)

    assert [file.name for file in files] == ["a-first.yaml", "b-second.yaml"]
    assert files[0].content == {**content, "approved_on": "2026-11-24"}


def test_a_file_that_is_not_yaml_is_refused_with_its_name(tmp_path: Path) -> None:
    (tmp_path / "broken.yaml").write_text("id: [unclosed")

    with pytest.raises(InvalidPatternCatalogError) as raised:
        read_pattern_catalog_seed(tmp_path)

    assert raised.value.problems == ["broken.yaml: the file is not valid YAML."]
