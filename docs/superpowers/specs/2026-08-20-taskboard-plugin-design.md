# Taskboard plugin — design

Date: 2026-08-20

Coordination for this template is **Taskboard only**. There is no Kanban-board shopping list.

## Goal

Agents see sprint work as tickets, without replacing the C3 task-memory ledger.

| Store | Owns |
| --- | --- |
| `docs/agents/implementation_plan.md` | Sprint items (one Taskboard ticket each) |
| `docs/memories/` | C3 reasoning (`Context`, `Evaluation`, `Key Challenges`) |
| `.taskboard/taskboard.db` | Ticket status (todo / in_progress / done) |

Link, do not mirror: the matching memory file contains `Taskboard: <ticket-uuid>`. Hooks only move tickets that have that line. No ID means no auto-move.

## Packaging

Fork [tcarac/taskboard](https://github.com/tcarac/taskboard) → [atebites-hub/taskboard](https://github.com/atebites-hub/taskboard). The fork remains a working Taskboard (Go CLI + UI) **and** a one-plugin Claude marketplace (ponytail pattern: repo root is the plugin).

| Piece | Location (fork) |
| --- | --- |
| Marketplace | `.claude-plugin/marketplace.json` |
| Manifest | `.claude-plugin/plugin.json` |
| Skill | `skills/taskboard-workflow/SKILL.md` |
| Hooks | `hooks/hooks.json` |
| MCP | `.mcp.json` — `taskboard --db ${CLAUDE_PROJECT_DIR}/.taskboard/taskboard.db mcp` |
| Scripts | `scripts/session-sync.sh`, `scripts/commit-sync.sh` |

Do **not** vendor the Go binary in the template. Install via PATH (`brew tap tcarac/taskboard && brew install taskboard` or `make build` in the fork). Homebrew-tap-from-fork is out of scope.

Per-repo SQLite is mandatory. Never use the default `~/Library/Application Support/taskboard/taskboard.db`.

## Template wiring

`config/setup.toml` field `taskboard_plugin` = `keep | strip`.

- **keep:** `.agents/settings.json` registers marketplace `atebites-hub/taskboard` (`ref: main`) and enables `taskboard@taskboard`. Skill copy at `.agents/skills/taskboard-workflow/` for Cursor/Codex. Gate **S11** checks those. Cursor/Copilot hooks call the same fail-open scripts.
- **strip:** remove the marketplace + enabled plugin keys and the skill copy. Scripts may remain (they no-op without the binary).

Tickets = sprint items. Memories stay C3. Taskboard hooks are **Tier 2** only; C1/C3 stay git pre-commit. Missing `taskboard` binary → exit 0.

## Out of scope

Replacing C3; autopilot/spawning agents from the Taskboard UI; rewriting the 22 MCP tools; editing `reasoning-system`.
