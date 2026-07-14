# PJTemplate bindings (example)

Optional reference for **this** template repo. Other clones should replace with
their own table in task memory — the skill itself stays harness- and project-neutral.

| Binding | PJTemplate value |
|---------|------------------|
| Agent rules | `AGENTS.md` |
| Standards | `docs/agents/` |
| Local gate | `./scripts/test-suite.sh` |
| Process artifacts | `scripts/check-task-compliance.sh` |
| Security scan | `bandit -c config/security/bandit.yaml -r src` |
| Secrets | `config/secrets/` (never commit) |
| Non-secret config | `config/defaults.toml` |
| Task memory | `memory-system` → `docs/memories/` |
| Pre-code reasoning | `reasoning-system` skill |
| Code docs mirror | `docs/code/**` per `src/**` change |
| Doc site | `mkdocs build -f config/docs/mkdocs.yml --strict` |
| Merge gate | test-suite + compliance + `.github/PULL_REQUEST_TEMPLATE.md` + human approval |

**Origin playbook:** [HarborRunner PR #29](https://github.com/BlackSwanCollective/HarborRunner/pull/29).