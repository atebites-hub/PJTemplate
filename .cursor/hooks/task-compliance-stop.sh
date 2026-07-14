#!/usr/bin/env bash
# Cursor stop hook — Tier-2 in-loop compliance (same script as Claude Stop).
set -Eeuo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec bash "${root}/scripts/check-task-compliance.sh" --task