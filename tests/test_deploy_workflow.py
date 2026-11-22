import re
from pathlib import Path
from typing import Any

import yaml

WORKFLOW_FILE = (
    Path(__file__).resolve().parent.parent / ".github" / "workflows" / "deploy.yml"
)
WORKFLOW_TEXT = WORKFLOW_FILE.read_text()
WORKFLOW: dict[str, Any] = yaml.safe_load(WORKFLOW_TEXT)
JOBS: dict[str, Any] = WORKFLOW["jobs"]


def step_scripts(job_name: str) -> str:
    """Return every shell command a job runs, joined into one string."""
    return "\n".join(step.get("run", "") for step in JOBS[job_name]["steps"])


def workflow_triggers() -> dict[str, Any]:
    """Return the workflow's `on:` triggers, which YAML reads as the key True."""
    triggers: dict[str, Any] = WORKFLOW[True]
    return triggers


def test_runs_only_on_push_to_production() -> None:
    triggers = workflow_triggers()

    assert list(triggers) == ["push"]
    assert triggers["push"]["branches"] == ["production"]


def test_checks_run_before_deploy() -> None:
    assert "make check" in step_scripts("check")
    assert JOBS["deploy"]["needs"] == "check"


def test_deploy_moves_the_server_to_the_checked_commit_and_rebuilds() -> None:
    deploy_commands = step_scripts("deploy")

    assert "git fetch origin production" in deploy_commands
    assert "git merge --ff-only $GITHUB_SHA" in deploy_commands
    assert "docker compose up -d --build" in deploy_commands
    assert "sudo" not in deploy_commands


def test_deploy_checks_the_live_health_endpoint() -> None:
    deploy_commands = step_scripts("deploy")

    assert '"$PRODUCTION_URL/health"' in deploy_commands
    assert WORKFLOW["env"]["PRODUCTION_URL"].startswith("https://")


def test_only_the_four_ssh_secrets_are_used() -> None:
    secrets_used = set(re.findall(r"secrets\.(\w+)", WORKFLOW_TEXT))

    assert secrets_used == {"SSH_KEY", "SSH_HOST", "SSH_USER", "SSH_KNOWN_HOSTS"}


def test_host_key_checking_stays_on() -> None:
    deploy_commands = step_scripts("deploy")

    assert "StrictHostKeyChecking=yes" in deploy_commands
    assert "StrictHostKeyChecking=no" not in WORKFLOW_TEXT
    assert "ssh-keyscan" not in WORKFLOW_TEXT


def test_only_one_deploy_runs_at_a_time_and_none_is_cancelled_halfway() -> None:
    assert WORKFLOW["concurrency"] == {
        "group": "deploy-production",
        "cancel-in-progress": False,
    }
