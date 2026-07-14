#!/usr/bin/env bash
# SessionStart / sessionStart hook: inject PJTemplate workflow checklist.
#
# Usage:
#   session-workflow-checklist.sh [claude|codex|copilot|cursor]
#   PJ_HOOK_FORMAT=<same> session-workflow-checklist.sh
#
# Auto-detect (when format omitted): PLUGIN_DATA→codex, Copilot tokens→copilot,
# CURSOR_VERSION→cursor; else claude (plain stdout).
#
# Fail-silent: missing checklist must not block the session.

set -Eeuo pipefail

format="${1:-${PJ_HOOK_FORMAT:-}}"

repo_root="${CLAUDE_PROJECT_DIR:-}"
if [[ -z "$repo_root" ]] && command -v git >/dev/null 2>&1; then
  repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
fi
repo_root="${repo_root:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

if [[ -z "$format" ]]; then
  if [[ -n "${PLUGIN_DATA:-}" ]] && [[ -z "${COPILOT_PLUGIN_DATA:-}" ]]; then
    format=codex
  elif [[ -n "${COPILOT_PLUGIN_DATA:-}" ]] || [[ -n "${GITHUB_COPILOT_TOKEN:-}" ]] || [[ -n "${GITHUB_COPILOT_API_TOKEN:-}" ]]; then
    format=copilot
  elif [[ -n "${CURSOR_VERSION:-}" ]]; then
    format=cursor
  else
    format=claude
  fi
fi

checklist="${repo_root}/scripts/hooks/workflow-checklist.txt"
if [[ ! -f "$checklist" ]]; then
  exit 0
fi

content="$(cat "$checklist")"

if [[ -d "${repo_root}/docs/memories" ]]; then
  active=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && active+=("$f")
  done < <(grep -l 'state: in_progress' "${repo_root}"/docs/memories/*.md 2>/dev/null || true)
  if [[ ${#active[@]} -gt 0 ]]; then
    content+=$'\n\nActive task memories (in_progress):\n'
    for f in "${active[@]}"; do
      content+="- ${f#"${repo_root}/"}"$'\n'
    done
  fi
fi

json_out() {
  if command -v jq >/dev/null 2>&1; then
    jq -n --arg ctx "$content" "$1"
  elif command -v python3 >/dev/null 2>&1; then
    export CTX="$content"
    export JQ_FILTER="$1"
    python3 <<'PY'
import json, os
ctx = os.environ["CTX"]
f = os.environ["JQ_FILTER"]
# minimal filters used by this script only
if "additional_context" in f:
    print(json.dumps({"additional_context": ctx}))
elif "additionalContext" in f and "hookSpecificOutput" not in f:
    print(json.dumps({"additionalContext": ctx}))
else:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
PY
  else
    printf '%s' "$content"
  fi
}

case "$format" in
  codex)
    json_out '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $ctx}}'
    ;;
  copilot)
    json_out '{additionalContext: $ctx}'
    ;;
  cursor)
    json_out '{additional_context: $ctx}'
    ;;
  claude | plain | *)
    printf '%s' "$content"
    ;;
esac

exit 0