from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from companion.core.evals.case_shapes import CASE_SHAPES, image_names
from companion.core.evals.cases import InvalidEvalCaseError, require_unique_keys
from companion.core.evals.models import EvalCase, EvalImage, EvalName

CASE_FILES = {
    EvalName.SAFEGUARD: "safeguard.yaml",
    EvalName.PERSONA: "persona.yaml",
    EvalName.KNOWLEDGE: "knowledge.yaml",
    EvalName.SETTINGS: "settings.yaml",
    EvalName.PHOTO_DESCRIPTIONS: "photo_descriptions.yaml",
    EvalName.UNDERSTANDING: "understanding.yaml",
    EvalName.MOVE_OUTCOME: "move_outcome.yaml",
    EvalName.DAY_SUMMARY: "day_summary.yaml",
}


def without_id(entry: dict[str, Any]) -> dict[str, Any]:
    """Copy a case entry without its `id`, which becomes the case's key.

    Args:
        entry: The case as written in its file.

    Returns:
        Everything else in it.
    """
    return {name: value for name, value in entry.items() if name != "id"}


def rules_named(
    rules: dict[str, str], names: list[str], key: str
) -> list[dict[str, str]]:
    """Pick the rules a case names from its file's rules.

    Args:
        rules: Every rule in the file, by ID.
        names: The IDs the case names.
        key: The case's key, for the error message.

    Returns:
        The rules it names, each `{id, check}`.

    Raises:
        InvalidEvalCaseError: If it names a rule the file doesn't define.
    """
    unknown = [name for name in names if name not in rules]
    if unknown:
        raise InvalidEvalCaseError(f"{key} names unknown rules: {', '.join(unknown)}")
    return [{"id": name, "check": rules[name]} for name in names]


def memory_item_list(items: dict[str, list[str]] | None) -> list[dict[str, Any]]:
    """Write Memory Items given by category as a list of `{category, contents}`.

    Args:
        items: Memory Items' contents by Memory Category name; None for none.

    Returns:
        One entry per category, in the order written.
    """
    return [
        {"category": category, "contents": contents}
        for category, contents in (items or {}).items()
    ]


def persona_message(entry: str | dict[str, str]) -> dict[str, Any]:
    """Write a scripted message as `{text, photo, shows}`.

    Args:
        entry: Plain text, or `{photo, shows, caption}` as the file has it.

    Returns:
        The message.
    """
    if isinstance(entry, str):
        return {"text": entry, "photo": None, "shows": ""}
    return {
        "text": entry.get("caption", ""),
        "photo": entry["photo"],
        "shows": entry["shows"],
    }


def earlier_line(entry: dict[str, str]) -> dict[str, str]:
    """Write a message already in the Conversation as `{who, text}`.

    Args:
        entry: `{person: <text>}` or `{zeph: <text>}` as the file has it.

    Returns:
        The message.
    """
    if "person" in entry:
        return {"who": "person", "text": entry["person"]}
    return {"who": "zeph", "text": entry["zeph"]}


def persona_cases(content: dict[str, Any]) -> list[EvalCase]:
    """Read the Persona file into cases, each carrying the rules it names.

    Args:
        content: `rules` and `conversations`.

    Returns:
        One case per conversation, each message written as
        `{text, photo, shows}`.
    """
    return [
        EvalCase(
            key=entry["id"],
            eval=EvalName.PERSONA,
            content={
                **without_id(entry),
                "messages": [persona_message(message) for message in entry["messages"]],
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
        One case per entry, its `now` written as ISO text, its Memory Items
        and earlier lines as lists.
    """
    cases = []
    for entry in content["cases"]:
        named = [
            rule
            for message in entry["messages"]
            for rule in message.get("expect", {}).get("rules", [])
        ]
        now = entry.get("now", content["now"])
        memory = entry.get("memory", {})
        cases.append(
            EvalCase(
                key=entry["id"],
                eval=EvalName.UNDERSTANDING,
                content={
                    **without_id(entry),
                    "memory": {
                        **memory,
                        "items": memory_item_list(memory.get("items")),
                    },
                    "earlier": [
                        earlier_line(line) for line in entry.get("earlier", [])
                    ],
                    "now": now.isoformat() if isinstance(now, datetime) else now,
                    "rules": rules_named(
                        content["rules"], list(dict.fromkeys(named)), entry["id"]
                    ),
                },
            )
        )
    return cases


def move_outcome_cases(content: dict[str, Any]) -> list[EvalCase]:
    """Read the Move Outcome file into cases, each with its time and rules.

    Args:
        content: `now`, `rules` and `cases`.

    Returns:
        One case per entry, its `now` written as ISO text and the rules its
        outcomes name as a list.
    """
    cases = []
    for entry in content["cases"]:
        named = [
            rule
            for outcome in entry.get("outcomes", [])
            for rule in outcome.get("rules", [])
        ]
        now = entry.get("now", content["now"])
        cases.append(
            EvalCase(
                key=entry["id"],
                eval=EvalName.MOVE_OUTCOME,
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
    elif name == EvalName.MOVE_OUTCOME:
        cases = move_outcome_cases(content)
    elif name == EvalName.SETTINGS:
        cases = [
            EvalCase(
                key=entry["id"],
                eval=name,
                content={
                    **without_id(entry),
                    "memories": memory_item_list(entry.get("memories")),
                },
            )
            for entry in content
        ]
    else:
        cases = [
            EvalCase(key=entry["id"], eval=name, content=without_id(entry))
            for entry in content
        ]
    require_unique_keys([case.key for case in cases])
    for case in cases:
        missing = [
            image
            for image in image_names(CASE_SHAPES[case.eval], case.content)
            if not (images_dir / image).is_file()
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


MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


def read_eval_image_seed(cases: list[EvalCase], images_dir: Path) -> list[EvalImage]:
    """Read the test images the seed cases send, to keep with the cases.

    Args:
        cases: The seed cases.
        images_dir: The folder of test images.

    Returns:
        Each image the cases name, once.
    """
    names = dict.fromkeys(
        name
        for case in cases
        for name in image_names(CASE_SHAPES[case.eval], case.content)
    )
    return [
        EvalImage(
            name=name,
            content=(images_dir / name).read_bytes(),
            media_type=MEDIA_TYPES[(images_dir / name).suffix.lower()],
        )
        for name in names
    ]
