#!/usr/bin/env bash
# scripts/check-template-setup.sh — template-setup completeness gate.
#
# Sibling to check-task-compliance.sh. That gate enforces *process artifacts*
# (memory, docs/code mirrors, reasoning) per change. This gate enforces
# *template-to-project transformation*: it fails until every placeholder is
# filled, every required tool is activated, every subsystem has an explicit
# keep/strip decision, and every review attestation is signed off.
#
# Activation model (the gate ships dormant):
#   * While the marker file .template-scaffold exists, the repo is still the
#     pristine template, so this gate prints one line and exits 0. The template
#     maintainer commits freely.
#   * Step 1 of deriving a project is `rm .template-scaffold`. The gate then
#     activates and blocks commits until setup is complete.
#   * Escape hatch (incremental setup, template maintenance):
#       SKIP_SETUP_GATE=1 git commit ...
#     or run any single check with --force even while dormant.
#
# It is wired into Tier 1 (.githooks/pre-commit) alongside check-task-compliance.sh.
# Promoting to CI (Tier 3) is NOT a copy of the task-compliance gate: this gate's
# checks are whole-tree (no --staged/--range/--task), and S4 (core.hooksPath) and
# S7 (built dist/cli.js) assert local-only artifacts a fresh checkout lacks — so a
# CI step needs a --ci mode (skip S4/S7) or must run setup.sh first. See
# docs/agents/enforcement_matrix.md §5.
#
# Checks (each says what is missing on failure):
#   S1 marker-off     .template-scaffold must be gone
#   S2 decisions      config/setup.toml present, non-empty, no <TODO>, and every
#                     decision key holds a value in its documented literal set
#   S3 placeholders   no template placeholders left in tracked text files
#   S4 hooks          git config core.hooksPath == .githooks AND the pre-commit
#                     hook is executable, non-empty, and invokes both gates
#   S5 symlinks       CLAUDE.md -> AGENTS.md and .claude -> .agents, non-dangling
#                     (or a Windows @AGENTS.md import fallback for CLAUDE.md)
#   S6 submodule      (only if odw_runtime=keep) ODW submodule initialized
#   S7 odw-build      (only if odw_runtime=keep) vendor/.../dist/cli.js built
#   S8 coverage       --cov-fail-under in pyproject.toml (non-comment) >= 80 AND
#                     at least one test file exists for the floor to measure
#
# Exit codes: 0 complete (or dormant/skipped), 1 setup incomplete, 2 usage/env error.

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MARKER="$REPO_ROOT/.template-scaffold"
SETUP_TOML="$REPO_ROOT/config/setup.toml"

usage() {
  cat >&2 <<'EOF'
usage: check-template-setup.sh [--force] [-h|--help]

  --force    run all checks even while the .template-scaffold marker is present
  -h|--help  show this help

The gate is dormant while .template-scaffold exists (pristine template). Delete
that file to activate it when deriving a project. Override once with
SKIP_SETUP_GATE=1.

Exit: 0 complete/dormant/skipped, 1 setup incomplete, 2 usage/env error.
EOF
}

FORCE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1 ;;
    -h | --help) usage; exit 0 ;;
    *) printf 'ERROR: unknown argument: %s\n' "$1" >&2; usage; exit 2 ;;
  esac
  shift
done

# --- dormancy / skip --------------------------------------------------------

if [[ "${SKIP_SETUP_GATE:-0}" == "1" ]]; then
  printf 'template-setup: SKIPPED (SKIP_SETUP_GATE=1)\n'
  exit 0
fi

if [[ -f "$MARKER" && $FORCE -eq 0 ]]; then
  printf 'template-setup: dormant (.template-scaffold present; pristine template).\n'
  exit 0
fi

command -v git >/dev/null 2>&1 || { printf 'ERROR: git not found\n' >&2; exit 2; }

# --- shared state -----------------------------------------------------------

FAILED=0
REPORT=()

fail() {
  FAILED=$((FAILED + 1))
  REPORT+=("$1")
}

note() { REPORT+=("$1"); }  # non-finding detail line, appended under a fail heading

# --- setup.toml helpers -----------------------------------------------------
#
# setup_val reads one decision value, stripping the key, inline TOML comments,
# and surrounding quotes/whitespace. Stripping the comment is load-bearing: every
# shipped decision line ends with a trailing `# keep | strip` comment, and without
# this `odw_runtime = "keep"  # keep | strip` would parse to "keep  # keep | strip".
setup_val() {
  local key="$1" val
  val="$(grep -E "^${key}[[:space:]]*=" "$SETUP_TOML" 2>/dev/null | head -1 || true)"
  val="${val#*=}"        # drop 'key ='
  val="${val%%#*}"       # drop inline TOML comment
  val="${val//\"/}"      # drop double quotes
  val="${val//\'/}"      # drop single quotes
  printf '%s' "$(printf '%s' "$val" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
}

# valid_decision KEY VALUE -> 0 if VALUE is allowed for KEY, else 1 (closed-world).
valid_decision() {
  case "$1" in
    odw_runtime | observability_stack | cd_docker | notebooks)
      [[ "$2" == "keep" || "$2" == "strip" ]] ;;
    gitnexus_license)
      [[ "$2" == "keep-noncommercial" || "$2" == "remove-mcp" || "$2" == "licensed-commercial" ]] ;;
    defaults_toml_customized | core_docs_filled | secrets_reviewed | plugin_refs_reviewed | python_version_confirmed)
      [[ "$2" == "done" ]] ;;
    project_name | project_slug | license_spdx | ide_scaffolds)
      [[ -n "$2" ]] ;;
    coverage_floor_pct)
      [[ "$2" =~ ^[0-9]+$ ]] ;;
    *) return 0 ;;
  esac
}

# Decision keys validated by S2's closed-world check (must match config/setup.toml).
DECISION_KEYS=(
  project_name project_slug license_spdx gitnexus_license
  observability_stack odw_runtime cd_docker notebooks ide_scaffolds
  coverage_floor_pct
  defaults_toml_customized core_docs_filled secrets_reviewed
  plugin_refs_reviewed python_version_confirmed
)

# --- S1: marker removed -----------------------------------------------------

if [[ -f "$MARKER" ]]; then
  fail "S1 [marker-off]: .template-scaffold still present."
  note "    Delete it to commit; it marks the repo as the pristine template."
  note "    rm .template-scaffold"
fi

# --- S2: setup decisions filled and in range --------------------------------

if [[ ! -f "$SETUP_TOML" ]]; then
  fail "S2 [decisions]: config/setup.toml is missing."
  note "    Create it from the template and fill every field."
else
  todos="$(grep -nE '<TODO>' "$SETUP_TOML" 2>/dev/null)" || true
  if [[ -n "$todos" ]]; then
    fail "S2 [decisions]: config/setup.toml has unresolved <TODO> fields:"
    while IFS= read -r line; do note "    $line"; done <<<"$todos"
    note "    Resolve each, then commit. See docs/agents/template_setup_checklist.md."
  fi
  if [[ ! -s "$SETUP_TOML" ]]; then
    fail "S2 [decisions]: config/setup.toml is empty."
    note "    Fill every field per docs/agents/template_setup_checklist.md."
  fi
  # Closed-world: every decision key must hold a value in its documented set.
  bad=()
  for k in "${DECISION_KEYS[@]}"; do
    v="$(setup_val "$k")"
    valid_decision "$k" "$v" || bad+=("$k='$v'")
  done
  if ((${#bad[@]} > 0)); then
    fail "S2 [decisions]: config/setup.toml has out-of-range or empty decision values:"
    for b in "${bad[@]}"; do note "    $b"; done
    note "    Allowed: keep|strip (subsystems); keep-noncommercial|remove-mcp|licensed-commercial"
    note "    (gitnexus); 'done' (review fields); a non-empty string (names); an integer"
    note "    >=0 (coverage_floor_pct)."
  fi
fi

ODW_DECISION="$(setup_val odw_runtime)"

# --- S3: placeholder sweep --------------------------------------------------
#
# Files where template placeholders are legitimate (documentation ABOUT the
# template, and the template docs themselves). Everything else is scanned.
# Ceiling note: git grep applies git's binary heuristic (NUL byte / .gitattributes),
# so placeholders inside a file git marks binary (built/minified assets) are
# invisible; and the *_template.md exclude is path-based, so any file an integrator
# renames to *_template.md becomes a blind spot.
EXCLUDES=(
  ':(exclude)docs/agents/template_setup_checklist.md'
  ':(exclude)docs/agents/enforcement_matrix.md'
  ':(exclude)scripts/check-template-setup.sh'
  ':(exclude)config/setup.toml'
  ':(exclude).template-scaffold'
  ':(exclude)docs/agents/*_template.md'
  ':(exclude)scripts/hooks/scaffolds'
  ':(exclude)vendor'
)

# scan_for PATTERN — records every file:line hit under one failing header.
scan_for() {
  local pattern="$1" hits line
  hits="$(git grep -nF -- "$pattern" . "${EXCLUDES[@]}" 2>/dev/null)" || true
  [[ -n "$hits" ]] || return 0
  fail "S3 [placeholders]: template literal '$pattern' still present:"
  while IFS= read -r line; do note "    $line"; done <<<"$hits"
}

PLACEHOLDERS=(
  "[Project Name]" "[Project name]" "[Number]" "[Brief"
  "[repo-url]" "[License:" "[type:" "[core purpose" "[key tech" "[e.g.,"
  "yourapp" "YourApp" "YOURAPP_" "Your Name" "PJTemplate" "pjtemplate"
  "example.com"
)
for p in "${PLACEHOLDERS[@]}"; do
  scan_for "$p"
done

# --- S4: git hooks activated and real --------------------------------------

hookspath="$(git config core.hooksPath 2>/dev/null)" || true
if [[ "$hookspath" != ".githooks" ]]; then
  fail "S4 [hooks]: core.hooksPath is '${hookspath:-<unset>}', expected '.githooks'."
  note "    git config core.hooksPath .githooks   # once per clone (setup.sh does this)"
else
  hook="$REPO_ROOT/.githooks/pre-commit"
  if [[ ! -x "$hook" ]]; then
    fail "S4 [hooks]: .githooks/pre-commit is missing or not executable."
    note "    chmod +x .githooks/pre-commit"
  elif [[ ! -s "$hook" ]]; then
    fail "S4 [hooks]: .githooks/pre-commit is empty (core.hooksPath points at nothing)."
  elif ! grep -q 'check-task-compliance' "$hook" || ! grep -q 'check-template-setup' "$hook"; then
    fail "S4 [hooks]: .githooks/pre-commit does not invoke both compliance gates."
    note "    It must call scripts/check-task-compliance.sh and scripts/check-template-setup.sh."
  fi
fi

# --- S5: symlink integrity --------------------------------------------------

check_link() {
  local link="$1" target="$2" import_marker="$3" rl
  if [[ -L "$link" ]]; then
    rl="$(readlink "$link")"
    # Accept both bare and ./-prefixed targets (ln -s ./AGENTS.md is common).
    if [[ "$rl" == "$target" || "$rl" == "./$target" ]]; then
      [[ -e "$link" ]] && return 0   # resolves (not dangling)
      fail "S5 [symlinks]: $link -> $target but the target is missing (dangling link)."
      return
    fi
    fail "S5 [symlinks]: $link -> $rl (expected -> $target)."
    return
  fi
  # Windows fallback: a real file whose first non-blank line is the @import marker.
  if [[ -n "$import_marker" && -f "$link" ]] && grep -Eq "^[[:space:]]*${import_marker}" "$link"; then
    return 0
  fi
  fail "S5 [symlinks]: $link is not a symlink to $target (or an @import fallback)."
  note "    ln -s $target $link   # macOS/Linux; on Windows use a one-line '@${target}' import."
}

check_link "CLAUDE.md" "AGENTS.md" "@AGENTS.md"
# .claude has no @import fallback (it is a directory symlink, not a file import).
check_link ".claude" ".agents" ""

# --- S6/S7: ODW submodule + build (decision-aware) -------------------------
#
# Only enforced when odw_runtime=keep. If the decision is still <TODO> or invalid,
# S2 has already flagged it; if strip, the submodule is expected to be gone.

if [[ "$ODW_DECISION" == "keep" ]]; then
  sub_status="$(git submodule status vendor/open-dynamic-workflows 2>/dev/null)" || true
  if [[ -z "$sub_status" ]]; then
    fail "S6 [submodule]: odw_runtime=keep but vendor/open-dynamic-workflows is not registered."
    note "    git submodule update --init --recursive"
  elif [[ "$sub_status" == -* ]]; then
    fail "S6 [submodule]: odw_runtime=keep but the submodule is not initialized (leading '-')."
    note "    git submodule update --init --recursive"
  fi
  if [[ ! -f "$REPO_ROOT/vendor/open-dynamic-workflows/dist/cli.js" ]]; then
    fail "S7 [odw-build]: odw_runtime=keep but vendor/open-dynamic-workflows/dist/cli.js is missing."
    note "    cd vendor/open-dynamic-workflows && npm ci && npm run build   # Node >= 20"
  fi
fi

# --- S8: coverage floor ----------------------------------------------------
#
# Filter comment lines before grepping: the shipped pyproject has a comment that
# literally contains `--cov-fail-under=0` above the real addopts line.
cov="$(grep -vE '^[[:space:]]*#' "$REPO_ROOT/pyproject.toml" 2>/dev/null | grep -oE 'cov-fail-under=[0-9]+' | head -1 || true)"
cov="${cov#*=}"
if [[ -z "$cov" ]]; then
  fail "S8 [coverage]: no --cov-fail-under found in pyproject.toml (non-comment lines)."
  note "    Set it (testing_guidelines.md mandates >= 80)."
elif ((cov < 80)); then
  fail "S8 [coverage]: --cov-fail-under=$cov is below the 80 floor (testing_guidelines.md)."
  note "    Raise it in [tool.pytest.ini_options] addopts."
fi
# A coverage floor is vacuous without tests to measure.
if ! git ls-files | grep -qE '(^|/)(test_[^/]*|[^/]*_test)\.py$'; then
  fail "S8 [coverage]: no test files found; a coverage floor measures nothing."
  note "    Add tests under tests/ (unit/integration/e2e)."
fi

# --- report -----------------------------------------------------------------

if [[ $FAILED -eq 0 ]]; then
  printf 'template-setup: OK (no setup violations)\n'
  exit 0
fi

{
  printf 'template-setup: FAIL (%d incomplete-setup issue group(s))\n' "$FAILED"
  printf -- '------------------------------------------------------------------------\n'
  for line in "${REPORT[@]}"; do printf '%s\n' "$line"; done
  printf -- '------------------------------------------------------------------------\n'
  printf 'Resolve the above, then re-commit. Walk through every item in\n'
  printf 'docs/agents/template_setup_checklist.md. One-off override:\n'
  printf '    SKIP_SETUP_GATE=1 git commit ...\n'
} >&2
exit 1
