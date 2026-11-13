"""Give a git worktree its own `.env`, ports and Docker project.

Run once in a new worktree through `make worktree-setup`. It copies `.env`
from the main folder, picks free ports, names the Compose project after the
folder (so it gets its own database) and leaves Telegram to the main stack.
It never writes to the main folder.
"""

import re
import socket
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

MAIN_WEB_PORT = 3000
MAIN_BACKEND_PORT = 8000
MAIN_POSTGRES_PORT = 5432
PORT_STEP = 10
MAX_SLOTS = 50


@dataclass(frozen=True)
class Ports:
    """The host ports one stack publishes."""

    web: int
    backend: int
    postgres: int


def choose_ports(
    port_is_free: Callable[[int], bool], taken_web_ports: set[int]
) -> Ports:
    """Pick the first set of ports after the main ones that nobody uses.

    Slot 1 is 3010/8010/5442, slot 2 is 3020/8020/5452, and so on.

    Args:
        port_is_free: Says whether a host port is free right now.
        taken_web_ports: Web ports other worktrees have claimed, even if their
            stacks are stopped.

    Returns:
        The chosen ports.

    Raises:
        RuntimeError: If no slot is free.
    """
    for slot in range(1, MAX_SLOTS + 1):
        offset = slot * PORT_STEP
        ports = Ports(
            web=MAIN_WEB_PORT + offset,
            backend=MAIN_BACKEND_PORT + offset,
            postgres=MAIN_POSTGRES_PORT + offset,
        )
        if ports.web in taken_web_ports:
            continue
        if all(
            port_is_free(port) for port in (ports.web, ports.backend, ports.postgres)
        ):
            return ports
    raise RuntimeError("No free set of ports found")


def compose_project_name(folder_name: str) -> str:
    """Turn a folder name into a valid Docker Compose project name.

    Args:
        folder_name: The worktree folder's name.

    Returns:
        The name in lower case, with anything but letters, digits, `-` and
        `_` replaced by `-`.
    """
    return re.sub(r"[^a-z0-9_-]", "-", folder_name.lower())


def env_line_key(line: str) -> str | None:
    """Find the variable a `.env` line sets.

    Args:
        line: One line of a `.env` file.

    Returns:
        The variable name, or None for comments, blanks and other lines.
    """
    name, separator, _ = line.partition("=")
    if not separator or name.strip().startswith("#"):
        return None
    return name.strip()


def read_env_value(env_text: str, key: str) -> str | None:
    """Find a key's value in `.env` text.

    Args:
        env_text: The contents of a `.env` file.
        key: The variable name.

    Returns:
        The value, or None if the key is not set.
    """
    for line in env_text.splitlines():
        if env_line_key(line) == key:
            return line.partition("=")[2].strip()
    return None


def claimed_web_ports(other_worktree_env_texts: list[str]) -> set[int]:
    """Collect the web ports other worktrees have claimed.

    Args:
        other_worktree_env_texts: Each other worktree's `.env` contents, or
            an empty string when it has none.

    Returns:
        Each worktree's `WEB_PORT`, or the main web port when it sets none.
    """
    return {
        int(read_env_value(env_text, "WEB_PORT") or MAIN_WEB_PORT)
        for env_text in other_worktree_env_texts
    }


def build_worktree_env(main_env_text: str, ports: Ports, project_name: str) -> str:
    """Build a worktree's `.env` from the main folder's.

    Keeps every secret, and replaces the keys that must differ per stack:
    ports, the addresses built from them, the Compose project, the ngrok
    profile and Telegram webhook registration.

    Args:
        main_env_text: The main folder's `.env` contents.
        ports: The worktree's host ports.
        project_name: The worktree's Compose project name.

    Returns:
        The worktree's `.env` contents.
    """
    worktree_values = {
        "COMPOSE_PROJECT_NAME": project_name,
        "COMPOSE_PROFILES": "",
        "WEB_PORT": str(ports.web),
        "BACKEND_PORT": str(ports.backend),
        "POSTGRES_PORT": str(ports.postgres),
        "NEXT_PUBLIC_API_URL": f"http://localhost:{ports.backend}",
        "DASHBOARD_URL": f"http://localhost:{ports.web}",
        "TELEGRAM_WEBHOOK_REGISTER": "false",
    }
    kept_lines = [
        line
        for line in main_env_text.splitlines()
        if env_line_key(line) not in worktree_values
    ]
    worktree_lines = [
        "",
        "# --- Worktree (written by make worktree-setup) ---------------------------",
        "# Own ports and database; ngrok and the Telegram webhook stay with the",
        "# main stack. Test Telegram by posting to /telegram/webhook on BACKEND_PORT.",
        *(f"{key}={value}" for key, value in worktree_values.items()),
    ]
    return "\n".join(kept_lines + worktree_lines) + "\n"


def is_port_free(port: int) -> bool:
    """Check whether a host port can be bound right now.

    Args:
        port: The port to check.

    Returns:
        True if nothing is listening on it.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("0.0.0.0", port))
        except OSError:
            return False
    return True


def git_output(*args: str) -> str:
    """Run a git command in the current folder.

    Args:
        *args: The git arguments.

    Returns:
        The command's output, stripped.
    """
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def other_worktree_env_texts(worktree_dir: Path) -> list[str]:
    """Read the `.env` of every other worktree of this repo.

    Args:
        worktree_dir: This worktree, which is left out.

    Returns:
        Each other worktree's `.env` contents, or an empty string when it has
        none.
    """
    env_texts = []
    for line in git_output("worktree", "list", "--porcelain").splitlines():
        if not line.startswith("worktree "):
            continue
        other_dir = Path(line.removeprefix("worktree "))
        if other_dir.resolve() == worktree_dir.resolve():
            continue
        env_file = other_dir / ".env"
        env_texts.append(env_file.read_text() if env_file.exists() else "")
    return env_texts


def main() -> int:
    """Write this worktree's `.env`, leaving the main folder untouched.

    Returns:
        The exit code.
    """
    worktree_dir = Path.cwd().resolve()
    main_dir = Path(
        git_output("rev-parse", "--path-format=absolute", "--git-common-dir")
    ).parent.resolve()
    if worktree_dir == main_dir:
        print("Run this in a worktree, not the main folder.", file=sys.stderr)
        return 1
    worktree_env = worktree_dir / ".env"
    if worktree_env.exists():
        print(f"{worktree_env} already exists; leaving it as it is.")
        return 0
    main_env = main_dir / ".env"
    if not main_env.exists():
        print(f"No .env in the main folder ({main_dir}).", file=sys.stderr)
        return 1
    ports = choose_ports(
        is_port_free, claimed_web_ports(other_worktree_env_texts(worktree_dir))
    )
    project_name = compose_project_name(worktree_dir.name)
    worktree_env.write_text(
        build_worktree_env(main_env.read_text(), ports, project_name)
    )
    print(
        f"Wrote {worktree_env}: Dashboard http://localhost:{ports.web}, "
        f"backend http://localhost:{ports.backend}, Postgres {ports.postgres}, "
        f"Compose project {project_name}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
