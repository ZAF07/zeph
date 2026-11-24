import json
from pathlib import Path

import yaml

from companion.core.models import PatternTypeFile
from companion.core.pattern_catalog import InvalidPatternCatalogError


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
            PatternTypeFile(
                name=path.name, content=json.loads(json.dumps(content, default=str))
            )
        )
    if problems:
        raise InvalidPatternCatalogError(problems)
    return files
