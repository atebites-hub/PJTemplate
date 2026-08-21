#!/usr/bin/env bash
# Taskboard session snapshot / commit sync. Always exit 0 (Tier-2, fail-open).
#
# Usage:
#   taskboard-sync.sh [session|commit]
#   PJ_HOOK_FORMAT=<claude|codex|copilot|cursor> taskboard-sync.sh session
#
# Canonical copy lives in this template. The atebites-hub/taskboard plugin ships
# the same file as scripts/session-sync.sh and scripts/commit-sync.sh (basename
# selects the mode). Keep those copies in sync when you change this script.
#
# Missing binary, missing DB, or CLI errors must not block a session or commit.

set -u

mode="${1:-}"
if [[ -z "$mode" ]]; then
  case "$(basename "${BASH_SOURCE[0]}")" in
    session-sync.sh | taskboard-session-sync.sh) mode=session ;;
    commit-sync.sh | taskboard-commit-sync.sh) mode=commit ;;
    *) mode=session ;;
  esac
fi

repo_root="${CLAUDE_PROJECT_DIR:-}"
if [[ -z "$repo_root" ]] && command -v git >/dev/null 2>&1; then
  repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
fi
if [[ -z "$repo_root" ]]; then
  repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fi

db="${repo_root}/.taskboard/taskboard.db"

format="${PJ_HOOK_FORMAT:-}"
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

have_bin() { command -v taskboard >/dev/null 2>&1; }

json_out() {
  local content="$1"
  if command -v jq >/dev/null 2>&1; then
    jq -n --arg ctx "$content" "$2"
  elif command -v python3 >/dev/null 2>&1; then
    CTX="$content" JQ_FILTER="$2" python3 <<'PY'
import json, os
ctx = os.environ["CTX"]
f = os.environ["JQ_FILTER"]
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

emit_session() {
  local content="$1"
  case "$format" in
    codex)
      json_out "$content" '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $ctx}}'
      ;;
    copilot)
      json_out "$content" '{additionalContext: $ctx}'
      ;;
    cursor)
      json_out "$content" '{additional_context: $ctx}'
      ;;
    claude | plain | *)
      printf '%s' "$content"
      ;;
  esac
}

extract_taskboard_id() {
  local file="$1" line
  line="$(grep -E 'Taskboard:[[:space:]]+' "$file" 2>/dev/null | head -1 || true)"
  [[ -n "$line" ]] || return 0
  printf '%s' "$line" | sed -E 's/.*Taskboard:[[:space:]]*//; s/[`*]+//g; s/[[:space:]].*//; s/[^[:alnum:]-]//g'
}

linked_memories() {
  local f id state
  shopt -s nullglob
  for f in "${repo_root}"/docs/memories/*.md; do
    id="$(extract_taskboard_id "$f")"
    [[ -n "$id" ]] || continue
    state="$(grep -E '^state:[[:space:]]*' "$f" 2>/dev/null | head -1 | sed -E 's/^state:[[:space:]]*//' || true)"
    printf -- '- %s → %s (%s)\n' "${f#"${repo_root}/"}" "$id" "${state:-unknown}"
  done
}

session_main() {
  local msg=""
  if ! have_bin; then
    msg="Taskboard CLI is not on PATH. Board snapshot skipped. Install: brew tap tcarac/taskboard && brew install taskboard (or make build in atebites-hub/taskboard)."
  elif [[ ! -f "$db" ]]; then
    msg="No per-repo Taskboard DB at .taskboard/taskboard.db yet. After the plan is approved, create one project for this clone and one ticket per sprint item. Always pass --db .taskboard/taskboard.db (never the default Application Support DB)."
  else
    msg="$(taskboard --db "$db" ticket list 2>/dev/null || true)"
    if [[ -z "$msg" ]]; then
      msg="(empty or unreadable board)"
    fi
    msg="Taskboard snapshot (.taskboard/taskboard.db):"$'\n'"${msg}"
  fi
  local linked
  linked="$(linked_memories || true)"
  if [[ -n "$linked" ]]; then
    msg+=$'\n\n'"Linked memories:"$'\n'"${linked}"
  fi
  emit_session "$msg"
}

commit_main() {
  have_bin || return 0
  [[ -f "$db" ]] || return 0
  local f id
  shopt -s nullglob
  for f in "${repo_root}"/docs/memories/*.md; do
    grep -qE '^state:[[:space:]]*completed' "$f" 2>/dev/null || continue
    id="$(extract_taskboard_id "$f")"
    [[ -n "$id" ]] || continue
    taskboard --db "$db" ticket move "$id" --status done >/dev/null 2>&1 || true
  done
}

case "$mode" in
  session) session_main ;;
  commit) commit_main ;;
  *) ;;
esac

exit 0
