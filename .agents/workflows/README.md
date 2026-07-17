# Workflow scripts (open-dynamic-workflows)

Optional home for **committed, re-runnable** dynamic-workflow JavaScript scripts
executed by the vendored ODW runtime:

```bash
./scripts/odw run .agents/workflows/<name>.js
# or with args:
./scripts/odw run .agents/workflows/<name>.js --args '{"branch":"feat/x"}'
```

## Contract (upstream)

Scripts are plain JS (not TypeScript). Required shape:

- Leading `export const meta = { name, description, … }` as a **pure literal**
- Body uses injected hooks: `agent`, `parallel`, `pipeline`, `phase`, `log`, `args`, `workflow`
- Every `agent(prompt, { executor: 'claude' | 'codex' | … })` **must** name an executor

See `.agents/skills/open-dynamic-workflows/SKILL.md` and
`vendor/open-dynamic-workflows/README.en.md`.

## Journals

Runs write under `.odw/<meta.name>/` (script snapshot + `runs/<runId>/`).
`runs/` is gitignored; do not commit traces or secrets.
