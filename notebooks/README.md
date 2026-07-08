# Dev notebooks

Optional **development-only** workspace for fetching data, testing transformations,
and prototyping logic before promoting it into `src/server/`.

Notebooks are **not** part of the production runtime image or `requirements.in`.

## Setup

After the base dev environment:

```bash
./scripts/setup.sh --with-notebooks
```

Or, on an existing venv:

```bash
source .venv/bin/activate
pip-compile --generate-hashes --resolver=backtracking \
  -o requirements-notebooks.txt requirements-notebooks.in
pip install --require-hashes -r requirements-notebooks.txt
python -m ipykernel install --user --name yourapp --display-name "yourapp (.venv)"
nbstripout --install --attributes notebooks/.gitattributes
```

## Launch

```bash
./scripts/notebook.sh
```

Opens JupyterLab at `http://127.0.0.1:8888/` (token printed in the terminal).
You can also open `.ipynb` files in VS Code with the Jupyter extension and select
the **yourapp (.venv)** kernel.

## Layout

| Path | Purpose |
|------|---------|
| `_bootstrap.py` | Shared paths, data dirs, and `get_settings()` |
| `explore/` | Scratch notebooks — outputs stripped before commit |
| `examples/` | Kept-clean reference notebooks |
| `data/raw/` | Fetched source data (gitignored) |
| `data/interim/` | In-progress transforms (gitignored) |
| `data/compiled/` | Aggregated outputs for local use (gitignored) |

## Conventions

1. **Cell 1** — bootstrap the environment:

   ```python
   %run _bootstrap.py
   ```

2. **Promote stable logic** — move functions into `src/server/modules/` and add
   `tests/unit/` coverage; keep the notebook as a thin caller.

3. **Secrets** — use `config/secrets/` (same as the app). Never hard-code API keys.

4. **Git hygiene** — `nbstripout` (installed by `--with-notebooks`) strips outputs
   on commit. Do not commit large datasets; use `data/` paths instead.

## Optional data stack

When you need tables or Parquet, add packages to `requirements-notebooks.in` (e.g.
`pandas`, `polars`, `pyarrow`), recompile the lockfile, and reinstall. Keep heavy
deps out of the default notebook install.