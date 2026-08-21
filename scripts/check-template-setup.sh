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
#   S9 homoglyphs     NFKC + ASCII-fold pass: catches placeholders left in place
#                     but disguised with a lookalike Unicode char (Cyrillic a,
#                     Greek o, smart dash). Reports only near-misses the raw
#                     S3 sweep missed. FAIL, same contract as S3.
#   S10 jspace        (only if jspace_skill=keep) J-Space submodule initialized
#                     and .agents/skills/j-space/SKILL.md resolves (symlink)
#   S11 taskboard     (only if taskboard_plugin=keep) marketplace atebites-hub/taskboard
#                     enabled as taskboard@taskboard and skill SKILL.md present
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
    odw_runtime | observability_stack | cd_docker | notebooks | jspace_skill | taskboard_plugin)
      [[ "$2" == "keep" || "$2" == "strip" ]] ;;
    odw_verifier)
      [[ "$2" == "none" || "$2" == "llm-as-a-verifier" ]] ;;
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
  observability_stack odw_runtime cd_docker notebooks jspace_skill
  taskboard_plugin odw_verifier ide_scaffolds
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
    note "    Allowed: keep|strip (subsystems, jspace_skill, taskboard_plugin); keep-noncommercial|remove-mcp|licensed-commercial"
    note "    (gitnexus); none|llm-as-a-verifier (odw_verifier); 'done' (review fields);"
    note "    a non-empty string (names); an integer >=0 (coverage_floor_pct)."
  fi
fi

ODW_DECISION="$(setup_val odw_runtime)"
JSPACE_DECISION="$(setup_val jspace_skill)"
TASKBOARD_DECISION="$(setup_val taskboard_plugin)"

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
  ':(exclude)docs/agents/upgrade.md'
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

# --- S9: homoglyph placeholder sweep (NFKC + ASCII-fold) --------------------
#
# S3 is a byte-exact ASCII grep, so a placeholder left in place but disguised
# with a lookalike Unicode char (Cyrillic a U+0430 for ASCII a, Greek o, a
# smart dash) slips past it. S9 NFKC-normalizes + ASCII-folds each tracked text
# file (same EXCLUDES pathspec as S3) and re-greps for PLACEHOLDERS, reporting
# only near-misses: lines where the raw ASCII token is absent but the folded
# form is present. python3 (>=3.12, guaranteed by pyproject) + stdlib
# unicodedata only; uconv/ICU not required.
#
# Ceiling (ponytail): the fold map covers Latin-letter Cyrillic/Greek
# homoglyphs plus the placeholder punctuation set (- , .). It is NOT the full
# Unicode TR-39 confusables table; NFKC already folds fullwidth letters/digits
# and most spaces, which is why those are absent from the map. Smart-quote
# folds are omitted because no current placeholder contains an ASCII quote;
# add U+2018/2019->' and U+201C/201D->" the day one does. Exhaustive coverage
# means vendoring Unicode confusables.txt; named here as the upgrade path.
#
# The python source is pure ASCII (hex-point/ASCII pairs, no literal non-ASCII
# glyphs) so the .sh stays editor-safe; the assert keeps the pairs aligned.
s9_py='import sys,unicodedata
PH=[a for a in sys.argv[1:] if a!="--"]
_SPEC=[
("0430 0435 0456 0458 0455 043e 0440 0441 0443 0445 051b","aeijsopcyxq"),
("0410 0412 0415 041a 041c 041d 041e 0420 0421 0422 0425 0405 0406 0408","ABEKMHOPCTXSIJ"),
("03b1 03b5 03b9 03ba 03bf 03c1 03bd 03f2 03c7","aeikopvsx"),
("0391 0392 0395 0396 0397 0399 039a 039c 039d 039f 03a1 03a4 03a7","ABEZHIKMNOPTX"),
("2010 2011 2012 2013 2014 2015 2212","-"*7),
("201a 201e",",,"),
("2024","."),
]
_fd={}
for pts,asc in _SPEC:
    cps=pts.split()
    assert len(cps)==len(asc),(pts,asc)
    for cp,ch in zip(cps,asc): _fd[chr(int(cp,16))]=ch
FOLD=str.maketrans(_fd)
def fold(s): return unicodedata.normalize("NFKC",s).translate(FOLD)
out=[]
for path in sys.stdin.buffer.read().split(b"\x00"):
    if not path: continue
    p=path.decode("utf-8","replace")
    try: raw=open(p,"rb").read()
    except OSError: continue
    if b"\x00" in raw[:8192]: continue
    try: text=raw.decode("utf-8")
    except UnicodeDecodeError: continue
    for i,line in enumerate(text.splitlines(),1):
        fl=fold(line)
        for ph in PH:
            if ph in line: continue
            if ph in fl: out.append("%s:%d:%s"%(p,i,line)); break
sys.stdout.write(("\n".join(out)+"\n") if out else "")'

near="$(git ls-files -z -- . "${EXCLUDES[@]}" | python3 -c "$s9_py" "${PLACEHOLDERS[@]}")" && s9_rc=0 || s9_rc=$?
if (( s9_rc != 0 )); then
  fail "S9 [homoglyphs]: scanner crashed (rc=$s9_rc) -- a python crash silently \
disables this check; verify the _SPEC hex/ASCII pairs in this script are aligned."
fi
if [[ -n "$near" ]]; then
  fail "S9 [homoglyphs]: placeholder near-miss(es) -- ASCII-fold hit where the raw S3 sweep missed:"
  while IFS= read -r ln; do
    note "    $ln"
  done <<<"$near"
  note "    A placeholder looks present but disguised with a lookalike Unicode char"
  note "    (Cyrillic/Greek letter, smart dash). Replace the whole token with the real value."
fi

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

# --- S10: J-Space submodule + skill symlink (decision-aware) --------------
#
# Only enforced when jspace_skill=keep. If strip, the submodule is expected to
# be gone (checklist §5g); the gate does not fail a leftover tree on strip.
# No npm build — upstream is a skill + stdlib controller.

if [[ "$JSPACE_DECISION" == "keep" ]]; then
  sub_status="$(git submodule status vendor/j-space-cognition-suite 2>/dev/null)" || true
  if [[ -z "$sub_status" ]]; then
    fail "S10 [jspace]: jspace_skill=keep but vendor/j-space-cognition-suite is not registered."
    note "    git submodule update --init --recursive"
  elif [[ "$sub_status" == -* ]]; then
    fail "S10 [jspace]: jspace_skill=keep but the submodule is not initialized (leading '-')."
    note "    git submodule update --init --recursive"
  fi
  skill_link="$REPO_ROOT/.agents/skills/j-space"
  if [[ ! -L "$skill_link" ]]; then
    fail "S10 [jspace]: jspace_skill=keep but .agents/skills/j-space is not a symlink."
    note "    ln -s ../../vendor/j-space-cognition-suite/j-space .agents/skills/j-space"
  elif [[ ! -f "$skill_link/SKILL.md" ]]; then
    fail "S10 [jspace]: jspace_skill=keep but .agents/skills/j-space/SKILL.md does not resolve."
    note "    git submodule update --init --recursive"
    note "    ln -s ../../vendor/j-space-cognition-suite/j-space .agents/skills/j-space"
  fi
fi

# --- S11: Taskboard plugin marketplace + skill (decision-aware) -----------
#
# Only enforced when taskboard_plugin=keep. Strip means remove the marketplace
# keys and skill copy (checklist §5h); the gate does not fail leftovers on strip.
# The Go binary is PATH-only and is not checked here.

if [[ "$TASKBOARD_DECISION" == "keep" ]]; then
  settings="$REPO_ROOT/.agents/settings.json"
  if [[ ! -f "$settings" ]] || ! grep -q 'atebites-hub/taskboard' "$settings"; then
    fail "S11 [taskboard]: taskboard_plugin=keep but .agents/settings.json does not register atebites-hub/taskboard."
    note "    Add extraKnownMarketplaces.taskboard -> github atebites-hub/taskboard (ref main)."
  fi
  if [[ ! -f "$settings" ]] || ! grep -q 'taskboard@taskboard' "$settings"; then
    fail "S11 [taskboard]: taskboard_plugin=keep but taskboard@taskboard is not enabled in .agents/settings.json."
    note "    Add enabledPlugins[\"taskboard@taskboard\"] = true."
  fi
  if [[ ! -f "$REPO_ROOT/.agents/skills/taskboard-workflow/SKILL.md" ]]; then
    fail "S11 [taskboard]: taskboard_plugin=keep but .agents/skills/taskboard-workflow/SKILL.md is missing."
    note "    Restore the skill copy from atebites-hub/taskboard skills/taskboard-workflow/SKILL.md."
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
