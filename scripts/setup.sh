#!/usr/bin/env bash
set -Eeuo pipefail

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

echo "==> Sanity checks"
python -m pip check
python -m pip list

cat <<'EOF'

Bootstrap complete.

Next shell:
  source .venv/bin/activate

Common commands:
  ruff check .
  ruff format .
  basedpyright
  bandit -c config/security/bandit.yaml -r src
  pip-audit -r requirements.txt
  interrogate -c pyproject.toml
  mkdocs build -f config/docs/mkdocs.yml --strict
  pytest

EOF
