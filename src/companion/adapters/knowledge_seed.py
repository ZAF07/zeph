from pathlib import Path

import yaml

from companion.core.knowledge import knowledge_file_type
from companion.core.models import KnowledgeUpload


def read_knowledge_seed(seed_file: Path) -> list[KnowledgeUpload]:
    """Read the starter Knowledge documents listed in a seed file.

    Args:
        seed_file: YAML file listing documents with `file` (next to the seed
            file), `title`, `source` and `tradition`.

    Returns:
        The documents with their files, in the order listed.
    """
    seed = yaml.safe_load(seed_file.read_text())
    return [
        KnowledgeUpload(
            title=document["title"],
            source=document["source"],
            tradition=document["tradition"],
            file_name=document["file"],
            file_type=knowledge_file_type(document["file"]),
            content=(seed_file.parent / document["file"]).read_bytes(),
        )
        for document in seed
    ]
