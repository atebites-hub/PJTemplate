# Agent stack — Taskboard, ODW, J-Space

> **Process doc** (not one of the 10 core product documents). One map of three
> **independent** layers this template cares about. Record the corresponding
> decisions in `config/setup.toml`. ODW and J-Space are vendored; Taskboard is
> a plugin plus a PATH binary.

Three jobs, three decisions. Do not merge them.

| Layer | What it decides | Setup field | In this repo |
| --- | --- | --- | --- |
| **Coordination (Taskboard)** | What work happens, card status for sprint items | `taskboard_plugin` | Claude plugin marketplace + in-tree skill/hooks; binary on PATH |
| **Orchestration (ODW)** | How many-agent work is fanned out as a rerunnable JS workflow | `odw_runtime` | Vendored submodule + skill symlink + `scripts/odw` |
| **Cognition (J-Space)** | How a long-running model holds goals, seams, and recovery | `jspace_skill` | Optional submodule + skill symlink |

`reasoning-system` is **not** a fourth catalog entry. It is a required project gate
(C3 task-memory fields). J-Space does not fill TCREI; `reasoning-system` does not
speak J-Space. They may both run on one task because they write to different places.

Canonical pointers: this file (map), `docs/agents/odw_executor_matrix.md`
(executors), `docs/agents/execution_policy.md` (when to orchestrate),
`docs/agents/template_setup_checklist.md` §5b and §5g–5h (keep/strip),
`docs/superpowers/specs/2026-08-20-taskboard-plugin-design.md` (plugin design).

---

## 1. Taskboard (coordination)

Role: a local board for sprint tickets. **Not** a replacement for ODW scripts
(`./scripts/odw`) and **not** a replacement for `docs/memories/` (C3). Use the
board to see ticket status; use memories for reasoning; use ODW when the fan-out
must be a rerunnable JS workflow.

`config/setup.toml` `taskboard_plugin`: `keep | strip`

| Piece | Where |
| --- | --- |
| Fork / marketplace | [atebites-hub/taskboard](https://github.com/atebites-hub/taskboard) (upstream [tcarac/taskboard](https://github.com/tcarac/taskboard), MIT) |
| Claude plugin | `taskboard@taskboard` via `.agents/settings.json` |
| Skill (Cursor/Codex too) | `.agents/skills/taskboard-workflow/` |
| SQLite | `.taskboard/taskboard.db` (gitignored; **never** the default Application Support DB) |
| Binary | PATH — `brew tap tcarac/taskboard && brew install taskboard` or `make build` in the fork |

**Tickets** = one per sprint item in `docs/agents/implementation_plan.md`.
After create, write `Taskboard: <ticket-uuid>` on the matching memory. Hooks
only auto-move tickets with that link.

**keep:** leave the marketplace + `enabledPlugins` entry, keep the skill copy.
The setup gate's **S11** checks those. Install the binary on PATH yourself.

**strip:** remove `taskboard` from `.agents/settings.json`
(`extraKnownMarketplaces` and `enabledPlugins`), delete
`.agents/skills/taskboard-workflow/`, and drop Taskboard rows from `AGENTS.md`.
Hook scripts may stay (they exit 0 without the binary).

`taskboard start --db .taskboard/taskboard.db` serves the UI on `:3010`.

The Go binary is **not** vendored. MCP's 22 tools stay upstream; this template
does not reimplement them.

---

## 2. Open-dynamic-workflows (orchestration)

Role: a model-/harness-agnostic runtime that executes a plain JS workflow
script (`export const meta` + `agent()` / `parallel()` / `pipeline()` /
`phase()`), fanning each leaf out to a named CLI executor. **Not** a replacement
for Taskboard tickets or `docs/memories/` (C3). Use ODW when the fan-out must be
a rerunnable script; use Taskboard for sprint-card status; use memories for
reasoning.

`config/setup.toml` `odw_runtime`: `keep | strip`

| Piece | Path |
| --- | --- |
| Submodule | `vendor/open-dynamic-workflows` (commit-pinned) |
| Skill | `.agents/skills/open-dynamic-workflows` → upstream skill in that tree |
| CLI | `./scripts/odw` (wraps `vendor/.../dist/cli.js`) |
| Committed scripts | Optional `.agents/workflows/*.js` |
| Executor matrix | `docs/agents/odw_executor_matrix.md` |

Every `agent()` **must** set `{ executor: '…' }` to a name in the host registry
(bundled: `claude`, `codex`, `grok`, `cursor`). Leaf quality is **Feature A**:
the `reasoning-system` Evaluation field names a concrete command that exits
0/1 (see `execution_policy.md` §6 and §9). Do not substitute a second model
scoring how finished transcripts look.

**keep:** initialize the submodule (`git submodule update --init --recursive`),
then `npm ci && npm run build` in the vendor tree (Node ≥ 20). The setup gate's
**S6/S7** check registration and `dist/cli.js`.

**strip:** `git submodule deinit -f vendor/open-dynamic-workflows`, `git rm`
that path, remove `.agents/skills/open-dynamic-workflows`, `scripts/odw`, and
the ODW sections of `AGENTS.md`.

---

## 3. J-Space (optional cognition skill)

Role: inference-time workspace control for long-horizon work (selective loading,
ledger at seams, named verification + coverage, recovery). Apache-2.0.
Upstream: [Tiger3807861189/J-Space-Cognition-Suite-V3.6](https://github.com/Tiger3807861189/J-Space-Cognition-Suite-V3.6).

`config/setup.toml` `jspace_skill`: `keep | strip`

| Piece | Path |
| --- | --- |
| Submodule | `vendor/j-space-cognition-suite` (commit-pinned, like ODW) |
| Skill | `.agents/skills/j-space` → `../../vendor/j-space-cognition-suite/j-space` |
| Runtime ledger | `.jspace/` in the task workspace (gitignored) |

No npm build. Optional controller: stdlib `j-space/scripts/jspace.py`.

**Independent of `reasoning-system`.** `reasoning-system` produces C3 fields
(`Context`, `Evaluation`, `Plan`, `Key Challenges`) before code lands. J-Space
keeps the live workspace from drifting during a long run. Do not rewrite one to
speak the other. If both fire, that is fine. Small tasks: `reasoning-system`
skips spikes; J-Space `fast` loads nothing.

`keep`: initialize the submodule (`git submodule update --init --recursive`).
The setup gate’s **S10** checks the submodule is registered and
`.agents/skills/j-space/SKILL.md` resolves.

`strip`: `git submodule deinit -f vendor/j-space-cognition-suite`, `git rm` that
path, remove `.agents/skills/j-space`, and drop J-Space rows from `AGENTS.md`.

Upgrade (pin rotation): `docs/agents/upgrade.md` (no `npm run build`).

---

## Quick guidance

- Want sprint tickets on a local board → `taskboard_plugin = "keep"` and put
  `taskboard` on PATH.
- Want durable many-agent scripts → `odw_runtime = "keep"`; build `dist/cli.js`.
- Want long-horizon workspace control → `jspace_skill = "keep"`; leave `reasoning-system` required either way.
