#!/usr/bin/env bash
# scripts/notebook.sh — launch JupyterLab for dev exploration notebooks.
#
# Requires: ./scripts/setup.sh --with-notebooks  (or manual install of
# requirements-notebooks.txt + ipykernel registration).
set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ -z "${VIRTUAL_ENV:-}" && -f "$REPO_ROOT/.venv/bin/activate" ]]; then
  # shellcheck source=/dev/null
  source "$REPO_ROOT/.venv/bin/activate"
fi

if ! command -v jupyter >/dev/null 2>&1; then
  echo "jupyter not found. Run: ./scripts/setup.sh --with-notebooks" >&2
  exit 1
fi

NOTEBOOK_PORT="${NOTEBOOK_PORT:-8888}"

exec jupyter lab \
  --notebook-dir="$REPO_ROOT/notebooks" \
  --port="$NOTEBOOK_PORT" \
  --no-browser \
  --ServerApp.token='' \
  --ServerApp.password=''