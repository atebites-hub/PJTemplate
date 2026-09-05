"""Guard: Actions uploads expire quickly and a cleanup workflow is present."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
UPLOAD_USES = re.compile(r"uses:\s+actions/upload-artifact@")
RETENTION = re.compile(r"retention-days:\s+(\d+)")
NEXT_STEP = re.compile(r"^      - ")
JOB_KEY = re.compile(r"^  [A-Za-z]")
SHA_USES = re.compile(r"uses:\s+\S+@[0-9a-f]{40}")


def _with_block_after(lines: list[str], start: int) -> str:
    """Return YAML lines after an upload-artifact uses: until the next step."""
    collected: list[str] = []
    for line in lines[start + 1 :]:
        if NEXT_STEP.match(line) or JOB_KEY.match(line):
            break
        collected.append(line)
    return "\n".join(collected)


@pytest.mark.unit
def test_every_upload_artifact_sets_short_retention() -> None:
    """Fail if any upload-artifact step omits retention-days or exceeds 7 days."""
    found = 0
    for path in sorted(WORKFLOWS.glob("*.yml")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            if not UPLOAD_USES.search(line):
                continue
            found += 1
            block = _with_block_after(lines, index)
            match = RETENTION.search(block)
            assert match, f"{path} upload-artifact step is missing retention-days"
            days = int(match.group(1))
            assert 1 <= days <= 7, f"{path} retention-days={days} exceeds 7"

    assert found >= 1, "expected at least one actions/upload-artifact step"


@pytest.mark.unit
def test_cleanup_artifacts_workflow_is_scheduled_and_pinned() -> None:
    """Fail if the cleanup workflow is missing, unscheduled, or not SHA-pinned."""
    path = WORKFLOWS / "cleanup-artifacts.yml"
    assert path.is_file(), "expected .github/workflows/cleanup-artifacts.yml"
    text = path.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "schedule:" in text
    assert "actions: write" in text
    assert SHA_USES.search(text), "cleanup workflow must SHA-pin its uses:"
    assert "deleteArtifact" in text or "delete artifact" in text.lower()
