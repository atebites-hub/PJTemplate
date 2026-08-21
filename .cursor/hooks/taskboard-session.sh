#!/usr/bin/env bash
# Cursor sessionStart wrapper — JSON envelope for Taskboard snapshot.
set -u
export PJ_HOOK_FORMAT=cursor
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/scripts/hooks/taskboard-sync.sh" session
