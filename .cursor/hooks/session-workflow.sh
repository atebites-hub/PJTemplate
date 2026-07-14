#!/usr/bin/env bash
# Cursor project hook wrapper — forces JSON envelope for sessionStart.
set -Eeuo pipefail
export PJ_HOOK_FORMAT=cursor
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/scripts/hooks/session-workflow-checklist.sh"