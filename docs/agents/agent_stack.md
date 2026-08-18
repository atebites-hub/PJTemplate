# Agent stack — Kanban, ODW verifier, J-Space

> **Process doc** (not one of the 10 core product documents). One map of three
> **independent** layers this template cares about. Record the corresponding
> decisions in `config/setup.toml`. Only J-Space is vendored.

Three jobs, three decisions. Do not merge them.

| Layer | What it decides | Setup field | In this repo |
| --- | --- | --- | --- |
| **Coordination (Kanban)** | What work happens, who runs it, card status | `agent_kanban` | Catalog only — no vendor |
| **Orchestration quality (ODW + verifier)** | Which parallel trajectories are actually good | `odw_verifier` | Catalog only — no vendor |
| **Cognition (J-Space)** | How a long-running model holds goals, seams, and recovery | `jspace_skill` | Optional submodule + skill symlink |

`reasoning-system` is **not** a fourth catalog entry. It is a required project gate
(C3 task-memory fields). J-Space does not fill TCREI; `reasoning-system` does not
speak J-Space. They may both run on one task because they write to different places.

Canonical pointers: this file (catalog), `docs/agents/odw_executor_matrix.md`
(executors), `docs/agents/execution_policy.md` (when to orchestrate),
`docs/agents/template_setup_checklist.md` §5g–5i (keep/strip / attest).

---

## 1. Agent Kanban (coordination)

Role: a board that assigns cards to CLI coding agents, usually with a git
worktree per card. **Not** a replacement for ODW scripts (`./scripts/odw`). Use a
board to see and dispatch work; use ODW when the fan-out must be a rerunnable JS
workflow.

`config/setup.toml` `agent_kanban` (closed-world):

`none | kanbots | cline | hermes | nerkoman | slayzone | taskboard | openkanban | u2dia | faru | other`

If you have no existing board, pick **`kanbots`**. Pick `none` if a board would
only add ceremony. Pick `other` if you use a board not listed here.

A local KanBots workspace writes `.kanbots/` next to the repo; that path is
gitignored. Do not commit agent DBs.

### Ranked FOSS boards

| Rank | Project | License | Why it is in this list | Best for | `agent_kanban` |
| --- | --- | --- | --- | --- | --- |
| 1 (recommended default) | [KanBots OSS](https://github.com/leodavinci1/kanbots) | MIT | Local-first desktop; parallel agents on worktrees; 11+ CLIs; autopilot/personas; MCP; no telemetry in OSS | Polished multi-CLI local board | `kanbots` |
| 2 | [Cline Kanban](https://github.com/cline/kanban) | Apache-2.0 | Official Cline team board (`npx kanban`); worktree + terminal per card; dependency linking; research preview | Closest match to Cline’s own stack | `cline` |
| 3 | [Hermes Kanban](https://github.com/NousResearch/hermes-agent) (built-in) | MIT | Durable SQLite board (`~/.hermes/kanban.db`); dispatcher/workers/heartbeats; survives restarts | Already on (or willing to use) Hermes Agent | `hermes` |
| 4 | [SlayZone](https://github.com/debuglebowski/slayzone) | Open source (local) | Desktop board: real PTY + browser panel + worktree per card; MCP for agents | Terminals-first visual control | `slayzone` |
| 5 | [nerkoman/agent-kanban](https://github.com/nerkoman/agent-kanban) | MIT | Local SQLite + FastAPI; MCP + OpenAPI; drag to Approved and the agent drives the card | Simple MCP-native, no cloud | `nerkoman` |

### Also worth knowing

| Project | License / shape | Notes | `agent_kanban` |
| --- | --- | --- | --- |
| [tcarac/taskboard](https://github.com/tcarac/taskboard) | Single binary, SQLite, Homebrew | Kanban UI + CLI + MCP (22 tools); embedded terminal | `taskboard` |
| [TechDufus/openkanban](https://github.com/TechDufus/openkanban) | TUI | Tickets = worktrees + embedded terminals; any CLI agent | `openkanban` |
| [U2SY26/u2dia-kanban](https://github.com/U2SY26/u2dia-kanban) | Zero-dep Python, MCP | Claude Code teams; real-time SSE | `u2dia` |
| [fluado/faru](https://github.com/fluado/faru) | Markdown + Git | Ultra-minimal; cards are files | `faru` |

[saltbo/agent-kanban](https://github.com/saltbo/agent-kanban) (agent-kanban.dev) is
self-hostable (leader-worker, Ed25519 identities, Cloudflare). It is **not** the
recommended primary for this template: the FOSS boards above are closer in
maturity, local-first posture, and integration depth.

Nothing in this section is installed by `./scripts/setup.sh`.

---

## 2. LLM-as-a-Verifier (ODW quality layer)

Role: rank candidate trajectories and monitor progress with calibrated scores
instead of a discrete 1–5 “LLM-as-a-Judge.” Orthogonal to Kanban. **Complementary
to ODW**: ODW fans out `agent()` leaves; the verifier helps pick the good ones.

`config/setup.toml` `odw_verifier`: `none | llm-as-a-verifier`

Independent of `odw_runtime`. Most useful when ODW is `keep`. Do **not** wrap
every `agent()` call — N candidates times M leaves compounds cost
(`execution_policy.md` §6). Use it on high-stakes leaves and best-of-N, not on
cheap navigation.

| Piece | URL | Use |
| --- | --- | --- |
| Framework | [llm-as-a-verifier/llm-as-a-verifier](https://github.com/llm-as-a-verifier/llm-as-a-verifier) | Fine-grained logprob scoring, ranking, progress signals |
| Coding-agent install | [TurboAgent](https://github.com/llm-as-a-verifier/TurboAgent) | Drop-in API proxy for Claude Code / Codex-class clients |

Executor names and headless CLI flags stay in `docs/agents/odw_executor_matrix.md`.
This layer does not add an ODW builtin executor.

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

- Want a local multi-CLI board → `agent_kanban = "kanbots"` (or `cline` / `hermes` if you already live there).
- Want durable many-agent scripts → keep `odw_runtime`; optionally `odw_verifier = "llm-as-a-verifier"` for high-stakes leaves.
- Want long-horizon workspace control → `jspace_skill = "keep"`; leave `reasoning-system` required either way.
