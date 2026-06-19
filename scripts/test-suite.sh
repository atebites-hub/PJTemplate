#!/usr/bin/env bash
# scripts/test-suite.sh — the single local quality gate.
#
# Runs, in order: ruff lint, ruff format check, basedpyright type check, and pytest
# with coverage. This is the one command AGENTS.md and README point to before
# commits/PRs. CI runs the same gates as separate steps.
#
# Coverage thresholds live in pyproject.toml ([tool.pytest.ini_options] addopts).
# The template ships --cov-fail-under=0 (measure, don't gate) so the skeleton stays
# green; per project raise it to the 80% line-coverage floor documented in
# docs/agents/testing_guidelines.md.

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Use the project venv's tools when present and not already active.
if [[ -z "${VIRTUAL_ENV:-}" && -f "$REPO_ROOT/.venv/bin/activate" ]]; then
  # shellcheck source=/dev/null
  source "$REPO_ROOT/.venv/bin/activate"
fi

printf '==> ruff check\n'
ruff check .

printf '==> ruff format --check\n'
ruff format --check .

printf '==> basedpyright\n'
basedpyright

printf '==> pytest (with coverage)\n'
pytest

printf 'test-suite: OK\n'
