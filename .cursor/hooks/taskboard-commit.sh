#!/usr/bin/env bash
# Cursor stop wrapper — mark linked Taskboard tickets done (fail-open).
set -u
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/scripts/hooks/taskboard-sync.sh" commit
