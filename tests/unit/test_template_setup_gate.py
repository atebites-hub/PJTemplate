"""Behavioral tests for scripts/check-template-setup.sh (template-setup gate).

Cases:
  (1) marker present + no --force  -> exit 0 (dormant)       [real pristine repo]
  (2) --force on the real template -> exit 1 (incomplete)    [real pristine repo]
  (3) a synthesized clean repo     -> exit 0 (all checks OK) [tmp git fixture]
  (4) clean repo + a homoglyph     -> exit 1, names S9       [pins S9's existence]
  (5) clean repo + cov floor < 80  -> exit 1, names S8       [pins the 80 floor]
  (6) repo-wide grep of old ODW scorer catalog tokens -> empty

Honest scope: these cover dormancy, the incomplete-template invariant, the clean
happy path, and pin S8 (value 80) + S9 (homoglyph detection) against silent
removal. They do NOT pin every S-code individually. S10 (J-Space submodule)
and S11 (Taskboard marketplace) are keep-only and are not required on the strip
happy path used by the fixture. One extra test pins S11's existence on keep.
Another pins that the removed ODW transcript-scoring catalog stays gone.

The gate is bash, so it adds nothing to the src coverage numerator. This file
lives under tests/, which is OUTSIDE [tool.coverage.run] source = ["src"], so it
is not measured at all -- it adds nothing to the denominator either. The 80%
floor is unaffected; no pragma / omit / mark is required (see module bottom).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE = REPO_ROOT / "scripts" / "check-template-setup.sh"
MARKER = REPO_ROOT / ".template-scaffold"
GATE_TIMEOUT = 60  # gate is read-only and fast; bound it so CI never hangs.

# Fully filled, in-range config/setup.toml: no <TODO>, every decision key valid.
_CLEAN_SETUP_TOML = (
    'project_name = "Demo"\n'
    'project_slug = "demo"\n'
    'license_spdx = "MIT"\n'
    'gitnexus_license = "remove-mcp"\n'
    'observability_stack = "strip"\n'
    'odw_runtime = "strip"\n'
    'cd_docker = "strip"\n'
    'notebooks = "strip"\n'
    'jspace_skill = "strip"\n'
    'taskboard_plugin = "strip"\n'
    'ide_scaffolds = "claude"\n'
    'coverage_floor_pct = "80"\n'
    'defaults_toml_customized = "done"\n'
    'core_docs_filled = "done"\n'
    'secrets_reviewed = "done"\n'
    'plugin_refs_reviewed = "done"\n'
    'python_version_confirmed = "done"\n'
)

# S4: executable, non-empty, invokes both compliance gates. No placeholders.
_PRECOMMIT = (
    "#!/usr/bin/env bash\nscripts/check-task-compliance.sh\nscripts/check-template-setup.sh\n"
)


# S8: cov-fail-under>=80 on a non-comment line. pyproject is NOT in the S3
# exclude list, so it must contain NO template placeholder literals.
def _pyproject(floor: int) -> str:
    """Return a minimal pyproject.toml that pins the coverage floor."""
    return f'[tool.pytest.ini_options]\naddopts = "--cov-fail-under={floor}"\n'


# A placeholder disguised with a Cyrillic small a (U+0430) standing in for ASCII
# 'a'. Built from chr(0x0430) so THIS source file is pure ASCII (S3/S9-clean --
# the disguised token never appears here, literally or folded); the glyph is
# materialized when the fixture file is written, and S9's NFKC + fold reassembles
# the placeholder token and flags it as a near-miss.
_HOMOGLYPH_LINE = 'brand = "your' + chr(0x0430) + 'pp"\n'


def _run_gate(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the gate via bash (it self-cd's to its own REPO_ROOT); never raise."""
    return subprocess.run(
        ["bash", str(script), *args],
        capture_output=True,
        text=True,
        timeout=GATE_TIMEOUT,
        check=False,
    )


def _build_repo(dest: Path, *, cov_floor: int = 80, homoglyph: bool = False) -> Path:
    """A real git repo satisfying every gate check (S1-S11 on the strip path)
    -> exit 0, unless a dirty knob is set: ``cov_floor`` below 80 trips S8;
    ``homoglyph`` plants a disguised placeholder that trips S9.

    S10 is keep-only (``jspace_skill=keep``); S11 is keep-only
    (``taskboard_plugin=keep``). The fixture uses ``strip`` for both so the
    clean happy path does not clone J-Space or require the Taskboard marketplace.

    The gate derives REPO_ROOT from BASH_SOURCE[0], so the script is COPIED into
    the repo and invoked there. git grep / git config / git ls-files need a real
    repo, so we init, set local config, stage explicit files, and commit.
    Symlinks (S5, filesystem-only) are left UNTRACKED so S3's git grep skips
    them and host core.symlinks settings cannot affect the result.
    """
    fx = dest

    # Script copy -- its path determines the gate's REPO_ROOT.
    (fx / "scripts").mkdir()
    shutil.copyfile(GATE, fx / "scripts" / "check-template-setup.sh")

    # S2 decisions.
    (fx / "config").mkdir()
    (fx / "config" / "setup.toml").write_text(_CLEAN_SETUP_TOML, encoding="utf-8")

    # S8 floor + a tracked test file (S8 requires git ls-files to find one).
    (fx / "pyproject.toml").write_text(_pyproject(cov_floor), encoding="utf-8")
    (fx / "tests").mkdir()
    (fx / "tests" / "test_gate_scaffold_test.py").write_text("", encoding="utf-8")

    # S4: hooksPath target -- executable, non-empty, names both gates.
    (fx / ".githooks").mkdir()
    precommit = fx / ".githooks" / "pre-commit"
    precommit.write_text(_PRECOMMIT, encoding="utf-8")
    precommit.chmod(0o755)

    # S5: non-dangling symlinks (targets created just above / just below).
    (fx / "AGENTS.md").write_text("# demo\n", encoding="utf-8")
    (fx / ".agents").mkdir()
    (fx / "CLAUDE.md").symlink_to("AGENTS.md")
    (fx / ".claude").symlink_to(".agents")

    add_args = [
        "git",
        "add",
        "scripts/check-template-setup.sh",
        "config/setup.toml",
        "pyproject.toml",
        "tests",
        ".githooks",
        "AGENTS.md",
    ]
    if homoglyph:
        (fx / "brand.txt").write_text(_HOMOGLYPH_LINE, encoding="utf-8")
        add_args.append("brand.txt")

    # Real git repo; isolate from the host's global/system git config. Commit
    # with --no-verify: the fixture's own pre-commit references scripts that are
    # intentionally not copied. S4 is a STATIC check (hook exists / executable /
    # names both gates), so skipping its execution does not undermine it.
    home = dest / "home"
    home.mkdir()
    env = {**os.environ, "HOME": str(home), "GIT_CONFIG_NOSYSTEM": "1"}
    for argv in (
        ["git", "init"],
        ["git", "config", "user.email", "t@t"],
        ["git", "config", "user.name", "t"],
        ["git", "config", "core.hooksPath", ".githooks"],
        add_args,
        ["git", "commit", "--no-verify", "-m", "fixture"],
    ):
        subprocess.run(argv, cwd=fx, check=True, capture_output=True, env=env, text=True)
    return fx


@pytest.fixture()
def clean_fixture(tmp_path: Path) -> Path:
    """A fully clean repo -> gate exits 0 across S1-S9."""
    return _build_repo(tmp_path)


@pytest.mark.unit
def test_dormant_when_marker_present() -> None:
    """(1) Pristine template (marker present), no --force => exit 0 (dormant)."""
    if not MARKER.is_file():
        pytest.skip(".template-scaffold absent -- repo is being derived; dormancy N/A")
    result = _run_gate(GATE)
    assert result.returncode == 0
    assert "dormant" in result.stdout.lower()


@pytest.mark.unit
def test_force_fails_on_real_template() -> None:
    """(2) --force bypasses dormancy on the real template => exit 1 (incomplete)."""
    if "<TODO>" not in (REPO_ROOT / "config" / "setup.toml").read_text(encoding="utf-8"):
        pytest.skip("setup.toml already filled -- real-template invariant N/A")
    result = _run_gate(GATE, "--force")
    assert result.returncode == 1
    assert "template-setup: fail" in (result.stdout + result.stderr).lower()


@pytest.mark.unit
def test_clean_fixture_passes(clean_fixture: Path) -> None:
    """(3) A fully transformed repo (clean fixture) => exit 0 (S10/S11 not required on strip)."""
    result = _run_gate(clean_fixture / "scripts" / "check-template-setup.sh")
    combined = (result.stdout + result.stderr).lower()
    assert result.returncode == 0, combined
    assert "template-setup: ok" in combined


@pytest.mark.unit
def test_detects_homoglyph_placeholder(tmp_path: Path) -> None:
    """(4) A disguised placeholder (Cyrillic a) must trip S9, not pass silently.
    Pins S9's existence: delete the S9 block and this test fails."""
    repo = _build_repo(tmp_path, homoglyph=True)
    result = _run_gate(repo / "scripts" / "check-template-setup.sh")
    combined = (result.stdout + result.stderr).lower()
    assert result.returncode == 1, combined
    assert "s9" in combined


@pytest.mark.unit
def test_rejects_coverage_floor_below_80(tmp_path: Path) -> None:
    """(5) A cov-fail-under below 80 must trip S8. Pins the 80 floor: lower the
    gate's threshold and this test fails."""
    repo = _build_repo(tmp_path, cov_floor=70)
    result = _run_gate(repo / "scripts" / "check-template-setup.sh")
    combined = (result.stdout + result.stderr).lower()
    assert result.returncode == 1, combined
    assert "s8" in combined


@pytest.mark.unit
def test_keep_taskboard_without_marketplace_fails(tmp_path: Path) -> None:
    """Keep-path S11: marketplace + skill required. Pins S11's existence."""
    repo = _build_repo(tmp_path)
    toml_path = repo / "config" / "setup.toml"
    toml_path.write_text(
        toml_path.read_text(encoding="utf-8").replace(
            'taskboard_plugin = "strip"', 'taskboard_plugin = "keep"'
        ),
        encoding="utf-8",
    )
    result = _run_gate(repo / "scripts" / "check-template-setup.sh")
    combined = (result.stdout + result.stderr).lower()
    assert result.returncode == 1, combined
    assert "s11" in combined


@pytest.mark.unit
def test_repo_does_not_catalog_odw_transcript_scorer() -> None:
    """The optional ODW transcript-scoring catalog and its setup field are gone.

    Needles are built from concatenations so this file itself does not contain
    the contiguous tokens a repo-wide grep is expected to find empty.
    """
    needles = (
        "odw_" + "verifier",
        "llm-as-a-" + "verifier",
        "llm-" + "verifier",
        "Turbo" + "Agent",
        "llm-as-a-" + "verifier.com",
    )
    for needle in needles:
        result = subprocess.run(
            ["git", "grep", "-n", "-F", "-I", needle, "--", "."],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1, f"catalog token {needle!r} still present:\n{result.stdout}"


# Coverage-floor resolution (the bash gate + this python test):
#   * --cov=src  AND  [tool.coverage.run] source = ["src"]  => only src/** is
#     measured. tests/** is outside `source`, so this file is neither numerator
#     nor denominator. The bash script is not python. Net: the 80% floor is
#     unchanged. No pragma/omit/mark is needed.
#   * If a future config adds tests/ to `source`, every line here still executes
#     during the run (all helpers are called by the tests), so coverage of
#     this file is effectively 100% -- still no drag.
