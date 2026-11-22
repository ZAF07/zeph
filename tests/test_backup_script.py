import os
import subprocess
import time
from pathlib import Path

BACKUP_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "backup.sh"


def write_stub(bin_dir: Path, name: str, body: str) -> None:
    stub = bin_dir / name
    stub.write_text(f'#!/bin/sh\necho "$@" >> {bin_dir}/{name}.calls\n{body}\n')
    stub.chmod(0o755)


def run_backup(tmp_path: Path, docker_body: str) -> subprocess.CompletedProcess[str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    write_stub(bin_dir, "docker", docker_body)
    write_stub(bin_dir, "rclone", "")
    return subprocess.run(
        [str(BACKUP_SCRIPT)],
        env={
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "BACKUP_DIR": str(tmp_path / "backups"),
        },
        capture_output=True,
        text=True,
    )


def calls(tmp_path: Path, name: str) -> list[str]:
    calls_file = tmp_path / "bin" / f"{name}.calls"
    return calls_file.read_text().splitlines() if calls_file.exists() else []


def test_backup_dumps_postgres_and_copies_the_dump_to_r2(tmp_path: Path) -> None:
    result = run_backup(tmp_path, "echo dump-bytes")

    assert result.returncode == 0, result.stderr
    dumps = list((tmp_path / "backups").glob("zeph-*.dump"))
    assert len(dumps) == 1
    assert dumps[0].read_text() == "dump-bytes\n"
    assert "pg_dump" in calls(tmp_path, "docker")[0]
    assert calls(tmp_path, "rclone") == [f"copy {dumps[0]} r2:zeph-backups"]


def test_failed_dump_uploads_nothing_and_leaves_no_file(tmp_path: Path) -> None:
    result = run_backup(tmp_path, "echo half-a-dump; exit 1")

    assert result.returncode != 0
    assert calls(tmp_path, "rclone") == []
    assert list((tmp_path / "backups").iterdir()) == []


def test_local_dumps_older_than_seven_days_are_removed(tmp_path: Path) -> None:
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    old_dump = backup_dir / "zeph-old.dump"
    recent_dump = backup_dir / "zeph-recent.dump"
    old_dump.write_text("old")
    recent_dump.write_text("recent")
    eight_days_ago = time.time() - 8 * 24 * 60 * 60
    os.utime(old_dump, (eight_days_ago, eight_days_ago))

    result = run_backup(tmp_path, "echo dump-bytes")

    assert result.returncode == 0, result.stderr
    assert not old_dump.exists()
    assert recent_dump.exists()
