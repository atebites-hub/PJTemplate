#!/usr/bin/env bash
# scripts/security/supply-chain-audit.sh — incident and PR supply-chain gate.
#
# Runs the project's supply-chain security gates: Python dependency/audit checks,
# OSV-Scanner over lockfiles, GuardDog malicious-package heuristics, OpenGrep
# secure-coding policy, an npm worm/persistence audit, and a git submodule
# inventory. Frontend (npm) gates run only when src/client/package.json exists,
# so the script is a no-op-friendly gate for backend-only checkouts.
#
# Tools are acquired in a pinned, reproducible way: OSV-Scanner and GuardDog run
# from digest-pinned containers (or an osv-scanner binary on PATH), and OpenGrep
# is downloaded at a pinned version and verified by SHA-256 before it runs.

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CLIENT_DIR="$REPO_ROOT/src/client"
REPORT_DIR="${SUPPLY_CHAIN_REPORT_DIR:-$REPO_ROOT/logs/current/supply-chain}"
OSV_SCANNER_IMAGE="${OSV_SCANNER_IMAGE:-ghcr.io/google/osv-scanner@sha256:64e86bec6df2466feea5137fc7c78fb3b7c21ec077f014d7130f64810e50676b}"
GUARDDOG_IMAGE="${GUARDDOG_IMAGE:-ghcr.io/datadog/guarddog@sha256:1679817551670ab3665cd0e0192e16d1c871bb29658010052378df026033df3e}"
OPENGREP_VERSION="${OPENGREP_VERSION:-v1.21.0}"
OPENGREP_LINUX_X86_SHA256="${OPENGREP_LINUX_X86_SHA256:-9ed0ceee4a3a406d27d40894bcce85ea151be21e6d4b180689689224faff2a3e}"
OPENGREP_LINUX_ARM64_SHA256="${OPENGREP_LINUX_ARM64_SHA256:-eb7f11d153b55de9482795b0f5a63388018b2bea982ab5d251f8e116625af892}"
OPENGREP_OSX_ARM64_SHA256="${OPENGREP_OSX_ARM64_SHA256:-3e7cd30b71a15ca895189737746545eafcf443f08d04b670b44ee901e6a2bb7a}"
OPENGREP_OSX_X86_SHA256="${OPENGREP_OSX_X86_SHA256:-ac35bc7b6bdf860902b1df5ab7c6778fee7eaf3a87ee011efe8838216b16ce09}"
mkdir -p "$REPORT_DIR"

FAILURES=0

log() {
  printf '==> %s\n' "$*"
}

mark_failure() {
  printf 'ERROR: %s\n' "$*" >&2
  FAILURES=1
}

run_gate() {
  local name=$1
  shift
  log "$name"
  if "$@"; then
    printf '    %s OK\n' "$name"
  else
    mark_failure "$name failed"
  fi
}

run_capture() {
  local name=$1
  local stdout_path=$2
  shift 2
  local stderr_path="${stdout_path}.stderr"

  log "$name -> $stdout_path"
  if "$@" >"$stdout_path" 2>"$stderr_path"; then
    printf '    %s OK\n' "$name"
  else
    mark_failure "$name failed; see $stdout_path and $stderr_path"
  fi
}

activate_venv() {
  if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    export PATH="$VIRTUAL_ENV/bin:$PATH"
    return 0
  fi

  if [[ -f "$REPO_ROOT/.venv/bin/activate" ]]; then
    # shellcheck source=/dev/null
    source "$REPO_ROOT/.venv/bin/activate"
    export PATH="$VIRTUAL_ENV/bin:$PATH"
    return 0
  fi

  mark_failure "no .venv found; Python supply-chain gates require scripts/setup.sh first"
  return 1
}

run_frontend_gates() {
  # The npm worm/persistence audit always runs: even without a frontend it
  # checks repo-wide worm persistence vectors (.vscode/tasks.json, .claude/settings.json).
  run_gate "npm worm/persistence audit" python "$REPO_ROOT/scripts/security/npm_worm_audit.py" \
    --repo-root "$REPO_ROOT" \
    --config "$REPO_ROOT/config/security/npm-worm-audit.json" \
    --report-path "$REPORT_DIR/npm-worm-audit.json"

  if [[ ! -f "$CLIENT_DIR/package.json" ]]; then
    log "no $CLIENT_DIR/package.json; skipping npm install/audit/SBOM gates"
    return 0
  fi

  cd "$CLIENT_DIR"
  run_gate "npm clean install without lifecycle scripts" npm ci --ignore-scripts
  run_capture "npm vulnerability audit" "$REPORT_DIR/npm-audit.json" \
    npm audit --json
  run_capture "npm registry signature audit" "$REPORT_DIR/npm-signatures.json" \
    npm audit signatures --json
  cd "$REPO_ROOT"
}

run_python_gates() {
  cd "$REPO_ROOT"
  activate_venv || return 0
  run_gate "pip environment sanity" python -m pip check
  run_capture "pip dependency inventory" "$REPORT_DIR/pip-inspect.json" \
    python -m pip inspect --local
  run_capture "pip-audit with hashes" "$REPORT_DIR/pip-audit.json" \
    pip-audit --require-hashes -r requirements.txt -f json
  # Dev lockfile is scanned REPORT-ONLY locally (mirrors CI): run_capture treats a
  # nonzero exit as fatal, and pip-audit exits 1 on any finding, so a fatal dev
  # scan would conflate dev-scoped vulns with a real runtime failure. Dev
  # visibility comes from this report plus the OSV-Scanner run over both lockfiles.
  log "pip-audit (dev, report-only) -> $REPORT_DIR/pip-audit-dev.json"
  pip-audit --require-hashes -r requirements-dev.txt -f json \
    >"$REPORT_DIR/pip-audit-dev.json" 2>"$REPORT_DIR/pip-audit-dev.json.stderr" \
    || log "    pip-audit (dev) reported findings; see pip-audit-dev.json"
  run_capture "bandit JSON report" "$REPORT_DIR/bandit.json" \
    bandit -q -c config/security/bandit.yaml -r src -f json
}

run_osv_scanner() {
  cd "$REPO_ROOT"
  local stdout_path="$REPORT_DIR/osv-scanner.stdout"

  # Scan whichever lockfiles exist. requirements*.txt are always present;
  # the frontend package-lock is included only when a frontend is set up.
  local host_locks=("$REPO_ROOT/requirements.txt" "$REPO_ROOT/requirements-dev.txt")
  local container_locks=(/src/requirements.txt /src/requirements-dev.txt)
  if [[ -f "$CLIENT_DIR/package-lock.json" ]]; then
    host_locks+=("$CLIENT_DIR/package-lock.json")
    container_locks+=(/src/src/client/package-lock.json)
  fi

  local host_args=(scan)
  local lock
  for lock in "${host_locks[@]}"; do host_args+=(-L "$lock"); done
  host_args+=(--config "$REPO_ROOT/config/security/osv-scanner.toml" --format json --output-file "$REPORT_DIR/osv-scanner.json")

  local container_args=(scan)
  for lock in "${container_locks[@]}"; do container_args+=(-L "$lock"); done
  container_args+=(--config /src/config/security/osv-scanner.toml --format json --output-file /reports/osv-scanner.json)

  log "OSV-Scanner lockfile audit -> $REPORT_DIR/osv-scanner.json"
  if command -v osv-scanner >/dev/null 2>&1; then
    if osv-scanner "${host_args[@]}" >"$stdout_path" 2>"$stdout_path.stderr"; then
      printf '    OSV-Scanner lockfile audit OK\n'
    else
      mark_failure "OSV-Scanner lockfile audit failed; see $REPORT_DIR/osv-scanner.json and $stdout_path.stderr"
    fi
    return 0
  fi
  if command -v docker >/dev/null 2>&1; then
    if docker run --rm \
      -v "$REPO_ROOT:/src:ro" \
      -v "$REPORT_DIR:/reports" \
      "$OSV_SCANNER_IMAGE" \
      "${container_args[@]}" \
      >"$stdout_path" 2>"$stdout_path.stderr"; then
      printf '    OSV-Scanner lockfile audit OK\n'
    else
      mark_failure "OSV-Scanner lockfile audit failed; see $REPORT_DIR/osv-scanner.json and $stdout_path.stderr"
    fi
    return 0
  fi
  mark_failure "OSV-Scanner requires either osv-scanner on PATH or Docker for the pinned image"
}

run_guarddog() {
  cd "$REPO_ROOT"
  log "GuardDog direct dependency malware heuristics -> $REPORT_DIR/guarddog-*.json"
  if GUARDDOG_IMAGE="$GUARDDOG_IMAGE" SUPPLY_CHAIN_REPORT_DIR="$REPORT_DIR" \
    python scripts/security/guarddog_audit.py \
      --repo-root "$REPO_ROOT" \
      --report-dir "$REPORT_DIR" \
      --config "$REPO_ROOT/config/security/guarddog.json"; then
    printf '    GuardDog direct dependency malware heuristics OK\n'
  else
    mark_failure "GuardDog direct dependency malware heuristics failed; see $REPORT_DIR/guarddog-*.json"
  fi
}

sha256_file() {
  python3 - "$1" <<'PY'
import hashlib
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
print(hashlib.sha256(path.read_bytes()).hexdigest())
PY
}

ensure_opengrep() {
  if command -v opengrep >/dev/null 2>&1; then
    command -v opengrep
    return 0
  fi

  local os arch asset expected binary_dir binary_path url actual
  os="$(uname -s)"
  arch="$(uname -m)"
  case "$os:$arch" in
    Linux:x86_64|Linux:amd64)
      asset="opengrep_manylinux_x86"
      expected="$OPENGREP_LINUX_X86_SHA256"
      ;;
    Linux:aarch64|Linux:arm64)
      asset="opengrep_manylinux_aarch64"
      expected="$OPENGREP_LINUX_ARM64_SHA256"
      ;;
    Darwin:arm64)
      asset="opengrep_osx_arm64"
      expected="$OPENGREP_OSX_ARM64_SHA256"
      ;;
    Darwin:x86_64|Darwin:amd64)
      asset="opengrep_osx_x86"
      expected="$OPENGREP_OSX_X86_SHA256"
      ;;
    *)
      mark_failure "unsupported OpenGrep platform $os/$arch; install opengrep on PATH"
      return 1
      ;;
  esac

  binary_dir="$REPORT_DIR/bin"
  binary_path="$binary_dir/opengrep"
  url="https://github.com/opengrep/opengrep/releases/download/$OPENGREP_VERSION/$asset"
  mkdir -p "$binary_dir"
  if [[ ! -x "$binary_path" ]]; then
    printf '==> download OpenGrep %s %s -> %s\n' "$OPENGREP_VERSION" "$asset" "$binary_path" >&2
    if ! curl -fL --retry 3 --connect-timeout 10 -o "$binary_path" "$url"; then
      mark_failure "failed to download OpenGrep from $url"
      return 1
    fi
    chmod 0755 "$binary_path"
  fi
  actual="$(sha256_file "$binary_path")"
  if [[ "$actual" != "$expected" ]]; then
    rm -f "$binary_path"
    mark_failure "OpenGrep checksum mismatch for $asset: expected $expected got $actual"
    return 1
  fi
  printf '%s\n' "$binary_path"
}

run_opengrep() {
  cd "$REPO_ROOT"
  local json_stdout_path="$REPORT_DIR/opengrep-json.stdout"
  local sarif_stdout_path="$REPORT_DIR/opengrep-sarif.stdout"
  local opengrep_bin
  if ! opengrep_bin="$(ensure_opengrep)"; then
    return 0
  fi
  local opengrep_common_args=(
    scan
    --config "$REPO_ROOT/config/security/opengrep.yml"
    --disable-version-check
    --error
    --exclude .git
    --exclude .venv
    --exclude .venv-ci
    --exclude logs
    --exclude site
    --exclude dist
    --exclude vendor
    --exclude src/client/node_modules
  )
  local target_args=(
    "$REPO_ROOT"
  )

  log "OpenGrep policy scan JSON -> $REPORT_DIR/opengrep.json"
  if "$opengrep_bin" "${opengrep_common_args[@]}" \
    --json \
    --output "$REPORT_DIR/opengrep.json" \
    "${target_args[@]}" >"$json_stdout_path" 2>"$json_stdout_path.stderr"; then
    printf '    OpenGrep JSON policy scan OK\n'
  else
    mark_failure "OpenGrep JSON policy scan failed; see $REPORT_DIR/opengrep.json and $json_stdout_path.stderr"
  fi

  log "OpenGrep policy scan SARIF -> $REPORT_DIR/opengrep.sarif"
  if "$opengrep_bin" "${opengrep_common_args[@]}" \
    --sarif \
    --output "$REPORT_DIR/opengrep.sarif" \
    "${target_args[@]}" >"$sarif_stdout_path" 2>"$sarif_stdout_path.stderr"; then
    printf '    OpenGrep SARIF policy scan OK\n'
  else
    mark_failure "OpenGrep SARIF policy scan failed; see $REPORT_DIR/opengrep.sarif and $sarif_stdout_path.stderr"
  fi
}

run_git_inventory() {
  cd "$REPO_ROOT"
  run_capture "git submodule inventory" "$REPORT_DIR/git-submodules.txt" \
    git submodule status --recursive
}

run_frontend_gates
run_python_gates
run_osv_scanner
run_guarddog
run_opengrep
run_git_inventory

if [[ "$FAILURES" -ne 0 ]]; then
  printf 'Supply-chain audit failed. Reports: %s\n' "$REPORT_DIR" >&2
  exit 1
fi

printf 'Supply-chain audit passed. Reports: %s\n' "$REPORT_DIR"
