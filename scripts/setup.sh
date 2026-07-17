#!/usr/bin/env bash
set -Eeuo pipefail

WITH_NOTEBOOKS=false
for arg in "$@"; do
  case "$arg" in
    --with-notebooks) WITH_NOTEBOOKS=true ;;
    -h | --help)
      cat <<'EOF'
Usage: scripts/setup.sh [--with-notebooks]

  --with-notebooks  Also compile/install dev notebook deps (JupyterLab, httpx,
                    nbstripout) and register the project ipykernel.
EOF
      exit 0
      ;;
  esac
done

PYTHON_VERSION="${PYTHON_VERSION:-3.12.12}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"

is_debian_like() {
  command -v apt-get >/dev/null 2>&1
}

install_debian_build_deps() {
  echo "==> Installing Debian/Ubuntu packages for pyenv/Python builds"
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends \
    make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev curl git \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
    libffi-dev liblzma-dev ca-certificates
}

install_macos_build_deps() {
  if ! xcode-select -p >/dev/null 2>&1; then
    echo "==> Xcode Command Line Tools not found."
    echo "    Install with: xcode-select --install"
    echo "    Then re-run this script."
    exit 1
  fi

  if command -v brew >/dev/null 2>&1; then
    echo "==> Installing Homebrew packages for pyenv/Python builds"
    brew list openssl &>/dev/null || brew install openssl
    brew list readline &>/dev/null || brew install readline
    brew list sqlite &>/dev/null || brew install sqlite
    brew list xz &>/dev/null || brew install xz
    brew list zlib &>/dev/null || brew install zlib
    # Optional but helps some Python builds
    brew list pkg-config &>/dev/null || brew install pkg-config
  else
    echo "==> Homebrew not found; pyenv may still work with Xcode CLT alone."
    echo "    If Python build fails, install https://brew.sh and re-run this script."
  fi
}

append_pyenv_init_bash() {
  local file=$1
  touch "$file"
  grep -qxF 'export PYENV_ROOT="$HOME/.pyenv"' "$file" 2>/dev/null || echo 'export PYENV_ROOT="$HOME/.pyenv"' >>"$file"
  grep -qxF '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' "$file" 2>/dev/null ||
    echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >>"$file"
  grep -qxF 'eval "$(pyenv init - bash)"' "$file" 2>/dev/null || echo 'eval "$(pyenv init - bash)"' >>"$file"
}

append_pyenv_init_zsh() {
  local file=$1
  touch "$file"
  grep -qxF 'export PYENV_ROOT="$HOME/.pyenv"' "$file" 2>/dev/null || echo 'export PYENV_ROOT="$HOME/.pyenv"' >>"$file"
  grep -qxF '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' "$file" 2>/dev/null ||
    echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >>"$file"
  grep -qxF 'eval "$(pyenv init - zsh)"' "$file" 2>/dev/null || echo 'eval "$(pyenv init - zsh)"' >>"$file"
}

case "$(uname -s)" in
Darwin)
  install_macos_build_deps
  ;;
Linux)
  if is_debian_like; then
    install_debian_build_deps
  else
    echo "==> Non-Debian Linux: skipping apt-get. Install pyenv build deps for your distro, then re-run if needed."
  fi
  ;;
*)
  echo "Unsupported OS: $(uname -s)" >&2
  exit 1
  ;;
esac

echo "==> Installing pyenv (if needed)"
if [ ! -d "$PYENV_ROOT" ]; then
  curl -fsSL https://pyenv.run | bash
fi

echo "==> Ensuring pyenv is initialized for this shell"
export PYENV_ROOT="$PYENV_ROOT"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - bash)"

echo "==> Persisting pyenv shell init (idempotent)"
append_pyenv_init_bash "$HOME/.bashrc"
append_pyenv_init_bash "$HOME/.profile"
if [ "$(uname -s)" = Darwin ] || [ -n "${ZSH_VERSION:-}" ] || [ -f "$HOME/.zshrc" ]; then
  append_pyenv_init_zsh "$HOME/.zshrc"
fi

echo "==> Installing Python ${PYTHON_VERSION} via pyenv"
# Help pyenv find Homebrew OpenSSL/readline on macOS
if [ "$(uname -s)" = Darwin ] && command -v brew >/dev/null 2>&1; then
  export LDFLAGS="-L$(brew --prefix openssl)/lib -L$(brew --prefix readline)/lib"
  export CPPFLAGS="-I$(brew --prefix openssl)/include -I$(brew --prefix readline)/include"
  export PKG_CONFIG_PATH="$(brew --prefix openssl)/lib/pkgconfig:$(brew --prefix readline)/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
fi
pyenv install -s "$PYTHON_VERSION"

cd "$PROJECT_ROOT"

echo "==> Writing local .python-version"
printf '%s\n' "$PYTHON_VERSION" >.python-version
pyenv local "$PYTHON_VERSION"

echo "==> Activating project git hooks (Tier-1 compliance gate)"
git config core.hooksPath .githooks

echo "==> Initialising git submodules (vendor/open-dynamic-workflows)"
if [ -f "${PROJECT_ROOT}/.gitmodules" ]; then
  if [ ! -f "${PROJECT_ROOT}/vendor/open-dynamic-workflows/package.json" ]; then
    git -C "${PROJECT_ROOT}" submodule update --init --recursive || {
      echo "WARNING: git submodule update failed — run: git submodule update --init --recursive" >&2
    }
  fi
fi

if [ -f "${PROJECT_ROOT}/vendor/open-dynamic-workflows/package.json" ]; then
  if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    node_major="$(node -p "process.versions.node.split('.')[0]" 2>/dev/null || echo 0)"
    if [ "${node_major}" -ge 20 ] 2>/dev/null; then
      echo "==> Building vendor/open-dynamic-workflows (Node ${node_major})"
      (cd "${PROJECT_ROOT}/vendor/open-dynamic-workflows" && npm ci && npm run build) || {
        echo "WARNING: ODW build failed — ./scripts/odw will retry on first use" >&2
      }
    else
      echo "WARNING: Node >=20 required for open-dynamic-workflows (found major=${node_major:-none}); skip ODW build" >&2
    fi
  else
    echo "WARNING: node/npm not found — skip ODW build; install Node >=20 for ./scripts/odw" >&2
  fi
else
  echo "WARNING: vendor/open-dynamic-workflows missing after submodule init" >&2
fi

echo "==> Creating virtual environment"
python -m venv .venv
# shellcheck source=/dev/null
source .venv/bin/activate

echo "==> Upgrading pip tooling"
python -m pip install --upgrade pip setuptools wheel pip-tools

echo "==> Compiling pinned+hashed requirements"
python -m piptools compile --generate-hashes --resolver=backtracking -o requirements.txt requirements.in
python -m piptools compile --generate-hashes --allow-unsafe --resolver=backtracking -o requirements-dev.txt requirements-dev.in

echo "==> Installing dev environment from hashed lockfiles"
python -m pip install --require-hashes -r requirements-dev.txt

echo "==> Installing the project itself"
python -m pip install -e . --no-deps

if [[ "$WITH_NOTEBOOKS" == true ]]; then
  echo "==> Compiling pinned+hashed notebook requirements"
  python -m piptools compile --generate-hashes --resolver=backtracking \
    -o requirements-notebooks.txt requirements-notebooks.in

  echo "==> Installing notebook environment from hashed lockfile"
  python -m pip install --require-hashes -r requirements-notebooks.txt

  echo "==> Registering Jupyter kernel and nbstripout git filter"
  python -m ipykernel install --user --name yourapp --display-name "yourapp (.venv)"
  nbstripout --install --attributes notebooks/.gitattributes
fi

echo "==> Sanity checks"
python -m pip check
python -m pip list

cat <<EOF

Bootstrap complete.

Next shell:
  source .venv/bin/activate

Common commands:
  ./scripts/test-suite.sh          # one-command gate: lint, types, tests + coverage
  ./scripts/check-task-compliance.sh --staged   # process-artifact gate (also runs pre-commit)
  ruff check .
  ruff format .
  basedpyright
  bandit -c config/security/bandit.yaml -r src
  pip-audit -r requirements.txt
  interrogate -c pyproject.toml
  mkdocs build -f config/docs/mkdocs.yml --strict
  pytest
$( [[ "$WITH_NOTEBOOKS" == true ]] && printf '  ./scripts/notebook.sh           # JupyterLab on :8888 (dev only)\n' )

Git hooks are active (core.hooksPath=.githooks): commits run the compliance gate.

EOF
