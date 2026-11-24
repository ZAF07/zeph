import copy
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from companion.adapters.pattern_catalog_seed import read_pattern_catalog_seed
from companion.core.models import (
    ExcludedEvidence,
    PatternArea,
    PatternType,
    PatternTypeFile,
    PatternTypeStatus,
    Power,
    Relationship,
    SignPart,
    SignStrength,
    SituationMatch,
    SituationSetting,
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


CLINICAL_TERMS = re.compile(
    r"\b(disorder|diagnos\w*|trauma\w*|depress\w*|anxiety|anxious|avoidant|"
    r"attachment|codependen\w*|narcissis\w*|borderline|neurotic\w*|ocd|adhd|ptsd|"
    r"symptom\w*|patholog\w*|obsessi\w*|compulsi\w*|phobi\w*|paranoi\w*|"
    r"clinical\w*|schema\w*|dysfunction\w*|mental illness)\b",
    re.IGNORECASE,
)


def seed_pattern_types() -> list[PatternType]:
    """The Pattern Types in the repo's catalog folder."""
    return read_pattern_types(read_pattern_catalog_seed(PATTERN_CATALOG_DIR))


def test_the_fifteen_pattern_types_in_the_repo_are_valid_drafts_three_per_area() -> (
    None
):
    pattern_types = seed_pattern_types()

    assert len(pattern_types) == 15
    for area in PatternArea:
        in_area = [
            pattern_type for pattern_type in pattern_types if pattern_type.area == area
        ]
        assert len(in_area) == 3, area
    assert {pattern_type.status for pattern_type in pattern_types} == {
        PatternTypeStatus.DRAFT
    }


def test_every_look_alike_in_the_repo_is_named_back_by_the_other_pattern_type() -> None:
    pattern_types = seed_pattern_types()
    pairs = {
        (pattern_type.id, look_alike.pattern_type_id)
        for pattern_type in pattern_types
        for look_alike in pattern_type.look_alikes
        if look_alike.pattern_type_id
    }

    assert [pair for pair in sorted(pairs) if pair[::-1] not in pairs] == []


def test_no_pattern_type_in_the_repo_uses_clinical_terms_outside_its_frameworks() -> (
    None
):
    found = []
    for pattern_type in seed_pattern_types():
        texts = [
            pattern_type.name,
            pattern_type.definition,
            pattern_type.if_situation,
            pattern_type.then_behaviour,
            pattern_type.function,
            pattern_type.anyone_would,
            pattern_type.approved_wording,
            pattern_type.prediction_wording,
            *(sign.text for sign in pattern_type.signs + pattern_type.signs_against),
            *(look_alike.tells_apart for look_alike in pattern_type.look_alikes),
            *(look_alike.name or "" for look_alike in pattern_type.look_alikes),
            *(exclusion.text for exclusion in pattern_type.exclusions),
        ]
        found += [
            f"{pattern_type.id}: {match.group()}"
            for text in texts
            for match in CLINICAL_TERMS.finditer(text)
        ]

    assert found == []


def test_a_pattern_type_is_read_with_all_its_details() -> None:
    conflict = next(
        pattern_type
        for pattern_type in read_pattern_types(
            read_pattern_catalog_seed(PATTERN_CATALOG_DIR)
        )
        if pattern_type.id == "CONF.AVOID.BELONG"
    )

    assert conflict.version == "0.3.0"
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
        "APPR.GIVE.NEEDED",
        "REL.MOOD.FIX",
    ]
    assert conflict.anyone_would == (
        "Low-stakes avoidance with strangers or authority only"
    )
    assert conflict.anyone_would_when == (
        SituationMatch(relationships=(Relationship.STRANGER,)),
        SituationMatch(powers=(Power.ABOVE,)),
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


def test_anyone_would_when_is_read_as_tag_matches() -> None:
    [pattern_type] = read_pattern_types(
        [
            PatternTypeFile(
                name="a.yaml",
                content=changed(
                    anyone_would_when=[
                        {"relationship": ["stranger", "acquaintance"]},
                        {"power": ["above"], "setting": ["work"]},
                    ]
                ),
            )
        ]
    )

    assert pattern_type.anyone_would_when == (
        SituationMatch(
            relationships=(Relationship.STRANGER, Relationship.ACQUAINTANCE)
        ),
        SituationMatch(powers=(Power.ABOVE,), settings=(SituationSetting.WORK,)),
    )


def test_anyone_would_when_may_be_left_out() -> None:
    [pattern_type] = read_pattern_types([PatternTypeFile(name="a.yaml", content=VALID)])

    assert pattern_type.anyone_would_when == ()


@pytest.mark.parametrize(
    ("anyone_would_when", "problem"),
    [
        ("strangers", "a.yaml: anyone_would_when must be a list."),
        (
            [{}],
            "a.yaml: anyone_would_when[1] needs at least one of relationship, "
            "power, setting or stance.",
        ),
        (
            [{"relationship": ["boss"]}],
            "a.yaml: anyone_would_when[1].relationship has boss; each must be one "
            "of partner, family, friend, acquaintance, colleague, stranger.",
        ),
        (
            [{"power": "above"}],
            "a.yaml: anyone_would_when[1].power must be a list.",
        ),
        (
            [{"relationship": ["stranger"], "mood": ["calm"]}],
            "a.yaml: anyone_would_when[1].mood is not a field of a situation "
            "anyone would act the same in.",
        ),
    ],
)
def test_a_wrong_anyone_would_when_is_refused_with_a_reason(
    anyone_would_when: Any, problem: str
) -> None:
    assert problems_of(changed(anyone_would_when=anyone_would_when)) == [problem]
