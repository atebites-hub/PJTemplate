# Template Setup Checklist

> **Purpose.** This is the canonical, exhaustive manifest for transforming the
> PJTemplate scaffold into a real project. Every feature the template ships is
> listed below as an explicit decision or action. Work top to bottom. The
> **setup gate** (`scripts/check-template-setup.sh`, wired into the pre-commit
> hook) blocks commits until the 🔒 items pass and the ✍️ attestations in
> `config/setup.toml` are filled.
>
> **Lock icons:** 🔒 = auto-verified by the gate · ✍️ = an attestation you record
> in `config/setup.toml` (the gate cannot read your intent) · 🗑️ = delete if you
> chose `strip`.

---

## 0. Activate the gate

- [ ] 🔒 **Delete the marker** to turn the gate on: `rm .template-scaffold`
      (while the marker exists the gate is dormant — the pristine template).
- [ ] Run `./scripts/setup.sh` — installs pyenv, Python, venv, hash-pinned deps,
      activates git hooks, and builds ODW if Node ≥ 20 is present.

---

## 1. Identity & placeholders 🔒

Every literal below is scanned across tracked text files (template docs about the
template are excluded). Replace **all** occurrences project-wide.

- [ ] 🔒 `[Project Name]` / `[Project name]` → your project name (README, AGENTS.md).
- [ ] 🔒 `[Number]` → count of core docs (AGENTS.md "Guidelines" section).
- [ ] 🔒 `yourapp` → your slug. **Files:** `pyproject.toml` (`name`),
      `config/defaults.toml` (`app.name`, `observability.service_name`,
      `metrics.namespace`, `fastapi.title`), `config/infra/grafana/`
      (`provisioning/dashboards/dashboards.yaml`, `dashboards/json/*.json`),
      `config/infra/alloy/config.alloy` (service relabel).
      (Note: `config/infra/prometheus/prometheus.yml` has **no** `yourapp`
      literal — Prometheus job names come from Alloy's relabeling, so there is
      nothing to edit there.)
- [ ] 🔒 `YourApp` / `Your Name` → author (e.g. `pyproject.toml` `authors`).
- [ ] 🔒 `PJTemplate` / `pjtemplate` → any remaining repo-name references.
- [ ] 🔒 README placeholders: `[Brief ...]`, `[repo-url]`, `[License: ...]`,
      `[type: ...]`, plus the two inside the overview block — `[core purpose]`,
      `[key tech]` — and `[e.g., ...]` (Assumptions / Known Issues on line 51).
- [ ] 🔒 **Coverage floor** `--cov-fail-under=0` → `80` in `pyproject.toml`
      (`[tool.pytest.ini_options] addopts`).

---

## 2. Project identity (record in `config/setup.toml`) ✍️

- [ ] ✍️ `project_name` — human name.
- [ ] ✍️ `project_slug` — machine slug (docker / prometheus / grafana).
- [ ] ✍️ `license_spdx` — and set the matching `license` in `pyproject.toml`
      plus the `## License` line in `README.md`.
- [ ] ✍️ `python_version_confirmed` — verify `.python-version` (currently
      `3.12.12`) matches your target runtime; update `pyproject.toml`
      `requires-python` + `target-version` if you change it.

---

## 3. Licensing & the GitNexus noncommercial trap ⚠️

GitNexus MCP (`.mcp.json`) is **PolyForm Noncommercial 1.0.0**. Personal, hobby,
research, and study use — including using this template personally — is fine.
**Only genuinely commercial use needs a separate license from the GitNexus
author.** This is easy to miss because nothing else in the repo is noncommercial.

- [ ] ✍️ `gitnexus_license` — one of:
      - `keep-noncommercial` — your use qualifies; leave `.mcp.json` as-is.
      - `remove-mcp` — delete the `gitnexus` entry from `.mcp.json` (and
        `.gitnexusignore` if unused). **Do this if your project is commercial
        and you have no GitNexus license.**
      - `licensed-commercial` — you obtained a commercial GitNexus license.

---

## 4. Required tooling & activation 🔒

These must work for the project to function; the gate verifies them.

- [ ] 🔒 **Git hooks** active: `git config core.hooksPath .githooks`
      (run once per clone; `setup.sh` does it).
- [ ] 🔒 **Symlinks intact**: `CLAUDE.md → AGENTS.md`, `.claude → .agents`.
      On Windows (no Developer Mode/admin) replace with a one-line
      `@AGENTS.md` import file for `CLAUDE.md`.
- [ ] 🔒 **ODW submodule** initialized:
      `git submodule update --init --recursive`.

---

## 5. Subsystem keep/strip decisions ✍️ + 🗑️

For each subsystem decide `keep` or `strip` in `config/setup.toml`. If `strip`,
delete the listed files so they cannot rot. The audit found these are the most
commonly forgotten because they are present-but-optional.

### 5a. Observability stack (LGT+P) — `observability_stack`
Code: `src/server/logging/` (`logging`, `metrics`, `tracing`, `profiling`,
`telemetry`), infra: `config/infra/` (loki, tempo, pyroscope, grafana, alloy),
deps (8): `prometheus-client`, `opentelemetry-api`, `-sdk`,
`-exporter-otlp-proto-grpc`, `-instrumentation-fastapi`,
`-instrumentation-logging`, `pyroscope-io`, `pyroscope-otel`.
- [ ] ✍️ Record `keep` or `strip`.
- [ ] 🗑️ If `strip`, **unwire before you delete** — `src/server/runtime/main.py`
      imports `telemetry_lifespan` and passes `lifespan=telemetry_lifespan` to
      the `FastAPI(...)` constructor. Remove that import and kwarg first, or the
      app won't start. Then delete `src/server/logging/{metrics,tracing,profiling,telemetry}.py`,
      `config/infra/`, the 8 deps from `pyproject.toml`, and the
      `[observability]`/`[metrics]`/`[tracing]`/`[profiling]` tables in
      `config/defaults.toml`. (Leave `logging.py` unless you also strip logging.)
- [ ] If `keep`: set `observability.service_name` and `metrics.namespace` to
      your slug; decide `profiling_enabled` (off by default); point
      `otlp_endpoint`/`profiling.server_address` at your collector.

### 5b. Open-dynamic-workflows — `odw_runtime`
Vendor submodule `vendor/open-dynamic-workflows/`, skill
`.agents/skills/open-dynamic-workflows/`, runner `scripts/odw`, matrix
`docs/agents/odw_executor_matrix.md`.
- [ ] ✍️ Record `keep` or `strip`.
- [ ] 🔒 If `keep`: build it — `cd vendor/open-dynamic-workflows && npm ci && npm run build`
      (Node ≥ 20); the gate checks `dist/cli.js` exists.
- [ ] 🗑️ If `strip`: `git submodule deinit -f vendor/open-dynamic-workflows`,
      `git rm`, remove `.agents/skills/open-dynamic-workflows` symlink,
      `scripts/odw`, and the ODW sections of `AGENTS.md`.

### 5c. CD + Docker — `cd_docker`
`.github/workflows/cd.yml`, `Dockerfile`, GHCR push on `v*` tags.
- [ ] ✍️ Record `keep` or `strip`.
- [ ] If `keep`: set the GHCR image name/owner in `cd.yml`; confirm the
      `Dockerfile` healthcheck port matches `config/defaults.toml` `[server].port`.
- [ ] 🗑️ If `strip`: delete `cd.yml` and `Dockerfile`.

### 5d. Notebooks — `notebooks`
`notebooks/`, `requirements-notebooks.*`, `scripts/notebook.sh`,
`docs/tests/notebooks.md`.
- [ ] ✍️ Record `keep` or `strip`.
- [ ] 🗑️ If `strip`: delete the above and the `[project.optional-dependencies].notebooks` block in `pyproject.toml`.

### 5e. IDE / harness scaffolds — `ide_scaffolds`
Three harnesses are pre-wired (no action unless you don't use them): **Claude**
(via the `CLAUDE.md` / `.claude` symlinks), **Cursor** (`.cursor/hooks.json`),
**Copilot** (`.github/hooks/session-workflow.json`). Copy-paste scaffolds for
the rest — **Codex, Droid, Gemini, Grok, Windsurf** — live in
`scripts/hooks/scaffolds/` and are **easily forgotten**.
- [ ] ✍️ List the harnesses you use (comma-separated) — e.g. `claude,cursor,codex`.
- [ ] For each scaffold harness you use, install it per
      `scripts/hooks/scaffolds/README.md`.

### 5f. Dev container — `.devcontainer/devcontainer.json`
No `keep/strip` decision in `setup.toml` — it's a customization, but the gate
scans it for placeholders and two settings warrant a deliberate choice.
- [ ] 🔒 Rename `name: "yourapp-dev"` to your slug.
- [ ] `forwardPorts` includes **8888** (Jupyter). If you stripped notebooks
      (§5d), drop 8888 so the port isn't left dangling.
- [ ] `runArgs` grants `--cap-add=SYS_PTRACE` and
      `--security-opt seccomp=unconfined`. These are deliberate (debugging /
      eBPF runtimes like Tracee need them), but if you stripped observability
      and don't need kernel-level debugging, remove them — they weaken the
      container sandbox.

### 5g. J-Space cognition skill — `jspace_skill`
Vendor submodule `vendor/j-space-cognition-suite/`, skill symlink
`.agents/skills/j-space` → `j-space/` inside that tree. Catalog:
`docs/agents/agent_stack.md` §3. Independent of `reasoning-system` (do not
merge them). No npm build.
- [ ] ✍️ Record `keep` or `strip`.
- [ ] 🔒 If `keep`: `git submodule update --init --recursive`. The gate's **S10**
      checks the submodule is initialized and `.agents/skills/j-space/SKILL.md`
      resolves.
- [ ] 🗑️ If `strip`: `git submodule deinit -f vendor/j-space-cognition-suite`,
      `git rm`, remove `.agents/skills/j-space`, and drop J-Space rows from
      `AGENTS.md`.

### 5h. Taskboard plugin — `taskboard_plugin`
Per-repo Taskboard (fork [atebites-hub/taskboard](https://github.com/atebites-hub/taskboard);
upstream [tcarac/taskboard](https://github.com/tcarac/taskboard)). Catalog:
`docs/agents/agent_stack.md` §1. Tickets = sprint items; memories stay C3.
The Go binary is **not** vendored — put `taskboard` on PATH.
- [ ] ✍️ Record `keep` or `strip`.
- [ ] 🔒 If `keep`: leave `taskboard` in `.agents/settings.json`
      (`extraKnownMarketplaces` + `enabledPlugins` `taskboard@taskboard`) and
      keep `.agents/skills/taskboard-workflow/SKILL.md`. The gate's **S11**
      checks those. Install: `brew tap tcarac/taskboard && brew install taskboard`.
- [ ] 🗑️ If `strip`: remove the `taskboard` marketplace and `taskboard@taskboard`
      keys from `.agents/settings.json`, delete `.agents/skills/taskboard-workflow/`,
      and drop Taskboard rows from `AGENTS.md`.

### 5i. ODW verifier — `odw_verifier`
Catalog only. LLM-as-a-Verifier / TurboAgent as a quality layer on ODW
leaves — not a Taskboard, not every `agent()` call. See
`docs/agents/agent_stack.md` §2.
- [ ] ✍️ Record `none` or `llm-as-a-verifier`. Independent of `odw_runtime`;
      most useful when ODW is `keep`.

---

## 6. Security & supply chain 🔒 + ✍️

The stack runs out of the box, but two decisions are yours.

- [ ] ✍️ `plugin_refs_reviewed` — `.agents/settings.json` marketplace sources
      pin only a branch `ref`, **not** a commit SHA (Claude Code limitation).
      Reviewed HEADs are recorded as comments. For full freeze, fork each
      marketplace. Decide and record `done`.
- [ ] ✍️ `secrets_reviewed` — `config/secrets/` ships only a README. Decide how
      this project loads secrets (files, env, vault) and record `done`.
- [ ] **Optional**: promote OSV-Scanner / GuardDog / Trivy from report-only to
      blocking in `.github/workflows/ci.yml` (curate
      `config/security/osv-scanner.toml`, `guarddog.json`, and `trivyignore`
      first; for Trivy add `--exit-code 1 --severity HIGH,CRITICAL`).
- [ ] **Optional**: Tracee eBPF runtime policy (`config/security/tracee/`) is
      present but not wired into CI — decide if you want runtime monitoring.

---

## 7. Documentation & governance ✍️

- [ ] ✍️ `core_docs_filled` — fill / rename the **10 core template docs** in
      `docs/agents/*_template.md` (Requirements, App Flow, Tech Stack, Client
      Guidelines, Server Structure, Implementation Plan, File Structure, Testing
      Guidelines, Coding Standards, Documentation Guidelines).
- [ ] ✍️ `defaults_toml_customized` — review every table in
      `config/defaults.toml`: `[server]`, `[workers]`, `[logging]`, `[security]`
      (CORS, trusted hosts), `[features]` toggles.
- [ ] Review `docs/agents/execution_policy.md`, `enforcement_matrix.md`, and
      `agent_stack.md` — process docs that should match how this project actually runs.

---

## 8. Final verification

- [ ] `./scripts/check-template-setup.sh` → `template-setup: OK`.
- [ ] `./scripts/test-suite.sh` → lint, types, tests pass.
- [ ] `./scripts/security/supply-chain-audit.sh` → clean.
- [ ] First `git commit` succeeds through both gates (task-compliance + setup).
- [ ] **GitHub branch protection** on `main`: require PR review and require the
      `ci` status check to pass before merge. This makes the local pre-commit
      gates survive `--no-verify` and `git commit --no-verify` (Tier-3 backstop).
      Once the setup gate is promoted to CI (see `enforcement_matrix.md` §5),
      require that check too.

---

## Why this checklist exists

Agents miss template setup for three structural reasons: (1) setup knowledge is
scattered across `AGENTS.md`, `README.md`, `setup.sh`, and 13 template docs;
(2) opt-in subsystems (observability, ODW, CD, Tracee, IDE scaffolds, J-Space, Taskboard) are present
but nothing forces an explicit yes/no; (3) ~18 distinct placeholders must be
replaced with no verification. This checklist + `config/setup.toml` + the gate
close all three gaps. The gate is the machine; this doc is the map.
