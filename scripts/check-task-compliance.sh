#!/usr/bin/env bash
# scripts/check-task-compliance.sh — process-artifact compliance gate.
#
# Deterministic check that a change set keeps the template's distinctive context
# artifacts in sync. It is the single source of truth invoked by three tiers:
#   * Tier 1 (authoritative): the native git hook .githooks/pre-commit   --staged
#   * Tier 2 (optional, per harness): e.g. the Claude Code Stop hook      --task
#   * Tier 3 (backstop): CI over the PR range (survives --no-verify)      --range
#
# Checks (each fires only when relevant, and on failure says what is missing):
#   C1 memory-present    source changed  -> a task memory under docs/memories/ changed
#   C2 doc-mirror        each changed source file -> its docs/code/<path>.md changed
#   C3 reasoning-recorded each changed memory has filled Context/Evaluation/Key
#                        Challenges sections (delegated to scripts/helpers/check_memory_reasoning.py)
#
# Coverage is NOT checked here (slow) — it lives in scripts/test-suite.sh.
#
# Exit codes: 0 clean, 1 compliance failure, 2 usage error, 3 environment error.

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

HELPER="$REPO_ROOT/scripts/helpers/check_memory_reasoning.py"

# Scaffolding exempt from C2 (the doc/code mirror gate). Ships EMPTY because the
# template provides real docs/code mirrors for its skeleton. Add a path here only
# for a genuinely behaviour-free scaffold file, and REMOVE it the moment that file
# gains real logic — C2 will then require docs/code/<path>.md for it. Matching is
# exact-path (glob allowed), so anything not listed is enforced (fails safe).
C2_EXEMPT_GLOBS=(
)

usage() {
  cat >&2 <<'EOF'
usage: check-task-compliance.sh [--staged | --range BASE..HEAD | --task]

  --staged           check git index vs HEAD (pre-commit hook). Default.
  --range BASE..HEAD  check a commit range (CI backstop).
  --task             check the working tree vs HEAD (in-loop harness hooks).

Exit: 0 clean, 1 compliance failure, 2 usage error, 3 environment error.
EOF
}

die_usage() {
  printf 'ERROR: %s\n' "$1" >&2
  usage
  exit 2
}

# --- argument parsing -------------------------------------------------------

MODE=""
RANGE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --staged | --task)
      [[ -n "$MODE" ]] && die_usage "choose exactly one of --staged | --range | --task"
      MODE="${1#--}"
      ;;
    --range)
      [[ -n "$MODE" ]] && die_usage "choose exactly one of --staged | --range | --task"
      MODE="range"
      shift || true
      [[ $# -gt 0 ]] || die_usage "--range requires a BASE..HEAD operand"
      RANGE="$1"
      [[ "$RANGE" == *..* ]] || die_usage "--range operand must contain '..' (got '$RANGE')"
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      die_usage "unknown argument: $1"
      ;;
  esac
  shift || true
done
[[ -n "$MODE" ]] || MODE="staged"

command -v git >/dev/null 2>&1 || { printf 'ERROR: git not found\n' >&2; exit 3; }

# --- changed-file resolution ------------------------------------------------

# GIT_REV_ARGS holds the revisions passed to `git diff` for the selected mode.
GIT_REV_ARGS=()
case "$MODE" in
  staged) GIT_REV_ARGS=(--cached HEAD) ;;
  task) GIT_REV_ARGS=(HEAD) ;;
  range)
    base="${RANGE%%..*}"
    if [[ -z "$base" ]] || ! git rev-parse --verify --quiet "${base}^{commit}" >/dev/null 2>&1; then
      printf "WARN [task-compliance]: base '%s' not found (shallow clone / first push); skipping range checks.\n" "$base" >&2
      exit 0
    fi
    GIT_REV_ARGS=("$RANGE")
    ;;
esac

# CHANGED_PRESENT = files that exist after the change (added/copied/modified/renamed
# to). Deletes (D) are intentionally excluded so removing code needs no mirror edit;
# renames (-M) resolve to the new path.
CHANGED_PRESENT=()
while IFS= read -r path; do
  [[ -n "$path" ]] && CHANGED_PRESENT+=("$path")
done < <(git diff --name-only --diff-filter=ACMR -M "${GIT_REV_ARGS[@]}")

# --- predicates -------------------------------------------------------------

# is_source: a code file under src/ that should carry process artifacts. Excludes
# package __init__.py and idiomatic test file names.
is_source() {
  local f=$1
  [[ "$f" =~ ^src/.*\.(py|js|ts|jsx|tsx)$ ]] || return 1
  [[ "$f" =~ (^|/)__init__\.py$ ]] && return 1
  [[ "$f" =~ (^|/)(test_[^/]*|[^/]*_test|[^/]*\.test|[^/]*\.spec)\.(py|js|ts|jsx|tsx)$ ]] && return 1
  return 0
}

is_exempt() {
  local f=$1 glob
  if [[ ${#C2_EXEMPT_GLOBS[@]} -gt 0 ]]; then
    for glob in "${C2_EXEMPT_GLOBS[@]}"; do
      # shellcheck disable=SC2053  # intentional glob match, not literal compare
      [[ "$f" == $glob ]] && return 0
    done
  fi
  return 1
}

# mirror_for: docs/code mirror path for a src file (src/a/b.py -> docs/code/a/b.md).
mirror_for() {
  local f=$1
  f="docs/code/${f#src/}"
  printf '%s.md\n' "${f%.*}"
}

in_changed() {
  local target=$1 f
  for f in "${CHANGED_PRESENT[@]}"; do
    [[ "$f" == "$target" ]] && return 0
  done
  return 1
}

# --- checks -----------------------------------------------------------------

FAILED=0

check_c1() {
  [[ ${#CHANGED_PRESENT[@]} -gt 0 ]] || return 0
  local triggers=() f
  for f in "${CHANGED_PRESENT[@]}"; do
    is_source "$f" && triggers+=("$f")
  done
  [[ ${#triggers[@]} -gt 0 ]] || return 0
  for f in "${CHANGED_PRESENT[@]}"; do
    [[ "$f" =~ ^docs/memories/.*\.md$ ]] && return 0
  done
  {
    printf 'ERROR [C1 memory-present]: source files changed but no task memory was updated.\n'
    printf '  Changed source requiring a memory:\n'
    for f in "${triggers[@]}"; do printf '    - %s\n' "$f"; done
    printf '  Fix: add or update a memory under docs/memories/<YYYY-MM-DD>-<slug>.md\n'
    printf '  (see .agents/skills/memory-system/SKILL.md).\n'
  } >&2
  return 1
}

check_c2() {
  [[ ${#CHANGED_PRESENT[@]} -gt 0 ]] || return 0
  local missing=() f mirror
  for f in "${CHANGED_PRESENT[@]}"; do
    is_source "$f" || continue
    is_exempt "$f" && continue
    mirror="$(mirror_for "$f")"
    in_changed "$mirror" || missing+=("$f -> $mirror")
  done
  [[ ${#missing[@]} -eq 0 ]] && return 0
  {
    printf 'ERROR [C2 doc-mirror]: changed source files are missing their docs/code mirror.\n'
    printf '  Missing (source -> required, unchanged or absent mirror):\n'
    for f in "${missing[@]}"; do printf '    - %s\n' "$f"; done
    printf '  Fix: create/update each mirror in the same change. If a file is template\n'
    printf '  scaffolding with no behaviour, add its path to C2_EXEMPT_GLOBS in this script.\n'
  } >&2
  return 1
}

check_c3() {
  [[ ${#CHANGED_PRESENT[@]} -gt 0 ]] || return 0
  local mems=() f
  for f in "${CHANGED_PRESENT[@]}"; do
    [[ "$f" =~ ^docs/memories/.*\.md$ ]] && mems+=("$f")
  done
  [[ ${#mems[@]} -gt 0 ]] || return 0
  if ! command -v python3 >/dev/null 2>&1; then
    printf 'WARN [C3 reasoning-recorded]: python3 not found; deferring reasoning check to CI.\n' >&2
    return 0
  fi
  local out rc
  out="$(python3 "$HELPER" "${mems[@]}")" && rc=0 || rc=$?
  [[ $rc -eq 0 ]] && return 0
  {
    printf 'ERROR [C3 reasoning-recorded]: task memories have empty required reasoning sections.\n'
    if [[ -n "$out" ]]; then
      while IFS= read -r line; do printf '    - %s\n' "$line"; done <<<"$out"
    fi
    printf "  Fix: fill the '## Task (TCREI)' Context and Evaluation bullets and the\n"
    printf "  '### Key Challenges & Analysis' section. Evaluation must name a verifiability\n"
    printf "  class (verifiable/non-verifiable) and one acceptance gate (Gate: <command|rubric>).\n"
  } >&2
  return 1
}

check_c1 || FAILED=1
check_c2 || FAILED=1
check_c3 || FAILED=1

if [[ $FAILED -eq 0 ]]; then
  printf 'task-compliance: OK (no compliance violations)\n'
  exit 0
fi
exit 1
