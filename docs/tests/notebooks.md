# Notebook development workflow

Dev exploration notebooks live under `notebooks/`. They are optional, dev-only,
and excluded from the production dependency lockfile (`requirements.in`).

## Install

```bash
./scripts/setup.sh --with-notebooks
```

## Run

```bash
./scripts/notebook.sh
```

Default URL: `http://127.0.0.1:8888/` (local bind; no token in dev).

Override port:

```bash
NOTEBOOK_PORT=8889 ./scripts/notebook.sh
```

## Verification

With the venv active and notebook deps installed:

```bash
python -c "import runpy; ns=runpy.run_path('notebooks/_bootstrap.py'); print(ns['settings'].app.name)"
jupyter kernelspec list | grep -F 'yourapp'
```

## Edge cases

| Case | Expected behavior |
|------|-------------------|
| `jupyter` missing | `scripts/notebook.sh` exits 1 with install hint |
| Kernel not registered | Select `.venv` Python manually or re-run `--with-notebooks` |
| Committed notebook outputs | `nbstripout` filter strips on commit when installed |
| Large datasets | Store under `notebooks/data/` (gitignored), not in cells |

## Promote-to-src workflow

1. Prototype fetch/transform logic in `notebooks/explore/`.
2. Extract stable functions to `src/server/modules/`.
3. Add `tests/unit/` coverage.
4. Thin the notebook to call the module (or move to `notebooks/examples/`).

## CI

Notebook execution is **not** gated in CI by default. Add `nbmake` later if
`notebooks/examples/` should be enforced on every PR.