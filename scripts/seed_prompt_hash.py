"""Print the hash of a seed prompt as it was at a git ref.

A migration that changes a seed prompt passes this hash to
`reload_prompt_unless_edited`, so only a stored prompt nobody edited is
reloaded. Run it for the text being replaced:

    uv run python -m scripts.seed_prompt_hash pattern_tagging_prompt

reads the seed on `main`; a second argument names another git ref.
"""

import subprocess
import sys

import yaml

from companion.adapters.postgres.prompt_reload import prompt_hash

SEED_FILE_IN_REPO = "src/companion/seed/platform_settings.yaml"
DEFAULT_GIT_REF = "main"


def seed_prompt_hash(seed_yaml: str, key: str) -> str:
    """Hash one prompt of a Platform Settings seed file.

    Args:
        seed_yaml: The seed file's text.
        key: The Platform Setting key of the prompt.

    Returns:
        The hash `reload_prompt_unless_edited` compares a stored prompt with.

    Raises:
        KeyError: If the seed holds no such setting.
    """
    prompt: str = yaml.safe_load(seed_yaml)[key]
    return prompt_hash(prompt)


def main() -> int:
    """Print the hash of the prompt named on the command line.

    Returns:
        The process exit code.
    """
    if len(sys.argv) not in (2, 3):
        print(
            "Usage: python -m scripts.seed_prompt_hash <setting key> [git ref]",
            file=sys.stderr,
        )
        return 1
    key = sys.argv[1]
    git_ref = sys.argv[2] if len(sys.argv) == 3 else DEFAULT_GIT_REF
    seed_yaml = subprocess.run(
        ["git", "show", f"{git_ref}:{SEED_FILE_IN_REPO}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    print(seed_prompt_hash(seed_yaml, key))
    return 0


if __name__ == "__main__":
    sys.exit(main())
