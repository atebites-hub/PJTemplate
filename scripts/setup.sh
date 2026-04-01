#!/usr/bin/env bash
set -Eeuo pipefail

PYTHON_VERSION="${PYTHON_VERSION:-3.12.12}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"

echo "==> Installing Debian system packages for pyenv/Python builds"
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  make build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev curl git \
  libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
  libffi-dev liblzma-dev ca-certificates

echo "==> Installing pyenv (if needed)"
if [ ! -d "$PYENV_ROOT" ]; then
  curl -fsSL https://pyenv.run | bash
fi

echo "==> Ensuring pyenv is initialized for this shell"
export PYENV_ROOT="$PYENV_ROOT"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - bash)"

echo "==> Persisting pyenv shell init to ~/.bashrc and ~/.profile (idempotent)"
grep -qxF 'export PYENV_ROOT="$HOME/.pyenv"' "$HOME/.bashrc" 2>/dev/null || echo 'export PYENV_ROOT="$HOME/.pyenv"' >> "$HOME/.bashrc"
grep -qxF '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' "$HOME/.bashrc" 2>/dev/null || echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> "$HOME/.bashrc"
grep -qxF 'eval "$(pyenv init - bash)"' "$HOME/.bashrc" 2>/dev/null || echo 'eval "$(pyenv init - bash)"' >> "$HOME/.bashrc"

touch "$HOME/.profile"
grep -qxF 'export PYENV_ROOT="$HOME/.pyenv"' "$HOME/.profile" 2>/dev/null || echo 'export PYENV_ROOT="$HOME/.pyenv"' >> "$HOME/.profile"
grep -qxF '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' "$HOME/.profile" 2>/dev/null || echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> "$HOME/.profile"
grep -qxF 'eval "$(pyenv init - bash)"' "$HOME/.profile" 2>/dev/null || echo 'eval "$(pyenv init - bash)"' >> "$HOME/.profile"

echo "==> Installing Python ${PYTHON_VERSION} via pyenv"
pyenv install -s "$PYTHON_VERSION"

cd "$PROJECT_ROOT"

echo "==> Writing local .python-version"
printf '%s\n' "$PYTHON_VERSION" > .python-version
pyenv local "$PYTHON_VERSION"

echo "==> Creating virtual environment"
python -m venv .venv
source .venv/bin/activate

echo "==> Upgrading pip tooling"
python -m pip install --upgrade pip setuptools wheel pip-tools

echo "==> Compiling pinned+hashed requirements"
python -m piptools compile --generate-hashes --resolver=backtracking -o requirements.txt requirements.in
python -m piptools compile --generate-hashes --resolver=backtracking -o requirements-dev.txt requirements-dev.in

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