"""Fail-open Taskboard hook scripts (session snapshot / commit sync)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "hooks" / "taskboard-sync.sh"
BASH = "/bin/bash"
# Enough for bash/grep/sed inside the script; excludes Homebrew so a real
# `taskboard` on PATH cannot leak into the "missing binary" cases.
_SAFE_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"


def _run(mode: str, *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [BASH, str(SCRIPT), mode],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
        env=env,
    )


@pytest.mark.unit
def test_session_exits_zero_without_binary(tmp_path: Path) -> None:
    env = {
        **os.environ,
        "PATH": _SAFE_PATH,
        "CLAUDE_PROJECT_DIR": str(tmp_path),
        "PJ_HOOK_FORMAT": "claude",
    }
    result = _run("session", env=env)
    assert result.returncode == 0
    assert "not on PATH" in result.stdout


@pytest.mark.unit
def test_commit_exits_zero_without_binary(tmp_path: Path) -> None:
    env = {
        **os.environ,
        "PATH": _SAFE_PATH,
        "CLAUDE_PROJECT_DIR": str(tmp_path),
    }
    result = _run("commit", env=env)
    assert result.returncode == 0


@pytest.mark.unit
def test_commit_moves_completed_linked_ticket(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "log.txt"
    fake = bin_dir / "taskboard"
    fake.write_text(
        '#!/bin/sh\nprintf \'%s\\n\' "$*" >> "$TASKBOARD_HOOK_LOG"\n',
        encoding="utf-8",
    )
    fake.chmod(0o755)

    repo = tmp_path / "repo"
    memories = repo / "docs" / "memories"
    memories.mkdir(parents=True)
    (memories / "done.md").write_text(
        "state: completed\nTaskboard: `abc-uuid-1`\n",
        encoding="utf-8",
    )
    (memories / "wip.md").write_text(
        "state: in_progress\nTaskboard: should-not-move\n",
        encoding="utf-8",
    )
    db_dir = repo / ".taskboard"
    db_dir.mkdir()
    (db_dir / "taskboard.db").write_text("placeholder", encoding="utf-8")

    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{_SAFE_PATH}",
        "CLAUDE_PROJECT_DIR": str(repo),
        "TASKBOARD_HOOK_LOG": str(log),
    }
    result = _run("commit", env=env)
    assert result.returncode == 0, result.stderr
    logged = log.read_text(encoding="utf-8")
    assert "ticket move abc-uuid-1 --status done" in logged
    assert "should-not-move" not in logged


@pytest.mark.unit
def test_commit_skips_when_db_missing(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "log.txt"
    fake = bin_dir / "taskboard"
    fake.write_text(
        '#!/bin/sh\nprintf \'%s\\n\' "$*" >> "$TASKBOARD_HOOK_LOG"\n',
        encoding="utf-8",
    )
    fake.chmod(0o755)

    repo = tmp_path / "repo"
    memories = repo / "docs" / "memories"
    memories.mkdir(parents=True)
    (memories / "done.md").write_text("state: completed\nTaskboard: abc-uuid-1\n", encoding="utf-8")

    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{_SAFE_PATH}",
        "CLAUDE_PROJECT_DIR": str(repo),
        "TASKBOARD_HOOK_LOG": str(log),
    }
    result = _run("commit", env=env)
    assert result.returncode == 0
    assert not log.exists()
