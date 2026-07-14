#!/usr/bin/env bash
# Gemini CLI AfterAgent hook — advisory workflow reminder (stdout = JSON only).
# Install via scripts/hooks/scaffolds/gemini-settings-hooks.json
set -Eeuo pipefail

repo_root="${GEMINI_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
checklist="${repo_root}/scripts/hooks/workflow-checklist.txt"
msg="PJTemplate: update task memory and docs/code before next turn."
if [[ -f "$checklist" ]]; then
  msg="$(head -c 4000 "$checklist")"
fi

if command -v python3 >/dev/null 2>&1; then
  export MSG="$msg"
  python3 -c 'import json, os; print(json.dumps({"systemMessage": os.environ["MSG"]}))'
elif command -v jq >/dev/null 2>&1; then
  jq -n --arg m "$msg" '{systemMessage: $m}'
else
  printf '{"systemMessage":"%s"}\n' "${msg//\"/\\\"}"
fi
exit 0