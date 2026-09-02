# [Project Name]

[Brief 1-2 sentence overview of the project. E.g., "[Project Name] is a [type: web app/API/game] that [core purpose], built with [key tech]."]

## Quick Start
1. Clone the repo: `git clone [repo-url]`.
2. Install dependencies: `./scripts/setup.sh` (add `--with-notebooks` for optional Jupyter dev exploration).
3. Set up secrets: add files under `config/secrets/` as needed (see `config/secrets/README.MD`).
4. Launch dev mode: `./scripts/start.sh` (or `uvicorn server.runtime.main:app --reload`).
5. Run tests: `./scripts/test-suite.sh`.

### Dev notebooks (optional)

For fetching data, testing transforms, and prototyping before promoting logic into
`src/server/`:

```bash
./scripts/setup.sh --with-notebooks
./scripts/notebook.sh          # JupyterLab at http://127.0.0.1:8888/
```

See `notebooks/README.md` and `docs/tests/notebooks.md`. Notebook deps live in
`requirements-notebooks.in` and are **not** installed in the production Docker image.

## Project Structure
Follow the layout in `/docs/agents/file_structure_doc.md` for modularity.

## Key Documents
- **AGENTS.md**: Rules for AI agents (e.g., Cursor, Claude). `CLAUDE.md` and `.claude/` are symlinks to `AGENTS.md` / `.agents/`, so there is one source of truth.
- **Dynamic Workflows** (`/open-dynamic-workflows`): [open-dynamic-workflows](https://github.com/imsai-sh/open-dynamic-workflows) runtime, vendored at `vendor/open-dynamic-workflows` (git submodule). Skill: `.agents/skills/open-dynamic-workflows/`. Run: `./scripts/odw run <script.js>`. Executor matrix: `docs/agents/odw_executor_matrix.md`.
- **Agent stack** (Taskboard plugin, ODW, J-Space): `docs/agents/agent_stack.md`. Setup fields: `taskboard_plugin`, `odw_runtime`, `jspace_skill` in `config/setup.toml`.
- **Agent Tooling & Integrations** (in AGENTS.md): auto-enabled Claude plugins (compound-engineering, superpowers, ponytail, taskboard), the GitNexus MCP code-intelligence server, and the cross-tool skill/symlink model.
- **Memory System**: Tasks and progress via per-task memories and agent todos.
- **Implementation Plan**: Sprint roadmap in `/docs/agents/implementation_plan.md`.

## Security
Supply-chain hardening is built in (pinned deps, OSV-Scanner, GuardDog, OpenGrep, Bandit, npm worm/persistence audit). Run the full local gate with `./scripts/security/supply-chain-audit.sh`; see `SECURITY.md`.

## Contributing
- Reference AGENTS.md for scope.
- Run the full local gate before PRs: `./scripts/test-suite.sh` (lint, types, tests + coverage).
- Process artifacts (task memory, `docs/code` mirrors, recorded reasoning) are enforced by
  `scripts/check-task-compliance.sh` via a git pre-commit hook. `scripts/setup.sh` activates it
  (`git config core.hooksPath .githooks`); CI re-checks the PR range as a backstop. See
  `docs/agents/enforcement_matrix.md`.
- The PR checklist lives in `.github/PULL_REQUEST_TEMPLATE.md`.
- Update docs/code/tests as per `/docs/agents/documentation_guidelines.md`.

## License
[License: e.g., MIT]

Assumptions: [e.g., "Node.js v18+"]; Known Issues: [e.g., "Beta mobile support"].