import json
from pathlib import Path
from typing import Any

import yaml

from companion.core.models import PatternTypeFile
from companion.core.pattern_catalog import InvalidPatternCatalogError


def as_plain_json_values(content: Any) -> Any:
    """Turn what YAML read into plain JSON values, so it can be stored as it is.

    Args:
        content: What a YAML file holds; a day such as `2026-11-24` is read
            as a date.

    Returns:
        The same content with every date written as text.
    """
    return json.loads(json.dumps(content, default=str))


def read_pattern_catalog_seed(seed_dir: Path) -> list[PatternTypeFile]:
    """Read the Pattern Catalog's files, one Pattern Type per YAML file.

    Args:
        seed_dir: The folder holding the `.yaml` files (ADR-0025).

    Returns:
        Each file's content as plain JSON values, by file name. The content
        is not checked here.

    Raises:
        InvalidPatternCatalogError: If a file is not valid YAML.
    """
    files = []
    problems = []
    for path in sorted(seed_dir.glob("*.yaml")):
        try:
            content = yaml.safe_load(path.read_text())
        except yaml.YAMLError:
            problems.append(f"{path.name}: the file is not valid YAML.")
            continue
        files.append(
            PatternTypeFile(name=path.name, content=as_plain_json_values(content))
        )
    if problems:
        raise InvalidPatternCatalogError(problems)
    return files
