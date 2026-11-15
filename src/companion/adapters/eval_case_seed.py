from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from companion.core.evals.cases import InvalidEvalCaseError, require_unique_keys
from companion.core.evals.models import EvalCase, EvalName

CASE_FILES = {
    EvalName.SAFEGUARD: "safeguard.yaml",
    EvalName.PERSONA: "persona.yaml",
    EvalName.KNOWLEDGE: "knowledge.yaml",
    EvalName.SETTINGS: "settings.yaml",
    EvalName.PHOTO_DESCRIPTIONS: "photo_descriptions.yaml",
    EvalName.UNDERSTANDING: "understanding.yaml",
}


def without_id(entry: dict[str, Any]) -> dict[str, Any]:
    """Copy a case entry without its `id`, which becomes the case's key.

    Args:
        entry: The case as written in its file.

    Returns:
        Everything else in it.
    """
    return {name: value for name, value in entry.items() if name != "id"}


def rules_named(rules: dict[str, str], names: list[str], key: str) -> dict[str, str]:
    """Pick the rules a case names from its file's rules.

    Args:
        rules: Every rule in the file, by ID.
        names: The IDs the case names.
        key: The case's key, for the error message.

    Returns:
        The rules it names, by ID.

    Raises:
        InvalidEvalCaseError: If it names a rule the file doesn't define.
    """
    unknown = [name for name in names if name not in rules]
    if unknown:
        raise InvalidEvalCaseError(f"{key} names unknown rules: {', '.join(unknown)}")
    return {name: rules[name] for name in names}


def persona_cases(content: dict[str, Any]) -> list[EvalCase]:
    """Read the Persona file into cases, each carrying the rules it names.

    Args:
        content: `rules` and `conversations`.

    Returns:
        One case per conversation.
    """
    return [
        EvalCase(
            key=entry["id"],
            eval=EvalName.PERSONA,
            content={
                **without_id(entry),
                "rules": rules_named(content["rules"], entry["rules"], entry["id"]),
            },
        )
        for entry in content["conversations"]
    ]


def understanding_cases(content: dict[str, Any]) -> list[EvalCase]:
    """Read the Understanding file into cases, each with its time and rules.

    Args:
        content: `now`, `rules` and `cases`.

    Returns:
        One case per entry, its `now` written as ISO text.
    """
    cases = []
    for entry in content["cases"]:
        named = [
            rule
            for message in entry["messages"]
            for rule in message.get("expect", {}).get("rules", [])
        ]
        now = entry.get("now", content["now"])
        cases.append(
            EvalCase(
                key=entry["id"],
                eval=EvalName.UNDERSTANDING,
                content={
                    **without_id(entry),
                    "now": now.isoformat() if isinstance(now, datetime) else now,
                    "rules": rules_named(
                        content["rules"], list(dict.fromkeys(named)), entry["id"]
                    ),
                },
            )
        )
    return cases


def images_named(case: EvalCase) -> list[str]:
    """List the test images a case sends.

    Args:
        case: The case.

    Returns:
        The images' file names.
    """
    content = case.content
    if case.eval in (EvalName.SAFEGUARD, EvalName.PHOTO_DESCRIPTIONS):
        return [content["photo"]] if "photo" in content else []
    if case.eval == EvalName.PERSONA:
        return [
            message["photo"]
            for message in content["messages"]
            if isinstance(message, dict)
        ]
    return []


def read_eval_case_file(
    name: EvalName, cases_file: Path, images_dir: Path
) -> list[EvalCase]:
    """Read one Eval's seed file into Eval Cases.

    Args:
        name: The Eval.
        cases_file: Its case file.
        images_dir: The folder of test images the cases send.

    Returns:
        Its cases, in the order written.

    Raises:
        InvalidEvalCaseError: If two cases share a key, or a case names a
            rule its file doesn't define or an image that isn't there.
    """
    content = yaml.safe_load(cases_file.read_text())
    if name == EvalName.PERSONA:
        cases = persona_cases(content)
    elif name == EvalName.UNDERSTANDING:
        cases = understanding_cases(content)
    else:
        cases = [
            EvalCase(key=entry["id"], eval=name, content=without_id(entry))
            for entry in content
        ]
    require_unique_keys([case.key for case in cases])
    for case in cases:
        missing = [
            image for image in images_named(case) if not (images_dir / image).is_file()
        ]
        if missing:
            raise InvalidEvalCaseError(
                f"{case.key} sends images that aren't there: {', '.join(missing)}"
            )
    return cases


def read_eval_case_seed(cases_dir: Path, images_dir: Path) -> list[EvalCase]:
    """Read the Eval Cases from the seed files, one file per Eval.

    Args:
        cases_dir: The folder of case files.
        images_dir: The folder of test images the cases send.

    Returns:
        Every case, by Eval, in the order written.
    """
    return [
        case
        for name, file_name in CASE_FILES.items()
        for case in read_eval_case_file(name, cases_dir / file_name, images_dir)
    ]
