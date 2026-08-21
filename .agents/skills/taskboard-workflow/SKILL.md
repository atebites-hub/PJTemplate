---
name: taskboard-workflow
description: >
  Per-repo Taskboard coordination: one ticket per sprint item, C3 memories stay
  the ledger, link via Taskboard: <uuid>. Use after a plan is approved, when
  creating or claiming sprint tickets, and when marking a task complete.
---

# Taskboard workflow

Coordination board for this repo. **Not** a replacement for task memory (C3) or
git pre-commit compliance (C1/C3).

## Data mapping

| Taskboard | This repo |
| --- | --- |
| Project | One per clone (`project_slug` in `config/setup.toml`, else the repo name) |
| Ticket | One sprint item in `docs/agents/implementation_plan.md` |
| Subtask | Optional checklist; not a memory file |
| SQLite | **Always** `.taskboard/taskboard.db` in the project root |

Never use the default `~/Library/Application Support/taskboard/taskboard.db`
(Linux: `~/.config/taskboard/taskboard.db`). Every CLI call takes `--db` first:

```bash
taskboard --db "${CLAUDE_PROJECT_DIR:-.}/.taskboard/taskboard.db" <subcommand>
```

The Claude plugin MCP server already passes that `--db`. Cursor/Codex must pass
it on every CLI invocation.

## Link to C3 memory

After `create_ticket` / `taskboard ticket create`, write this line on the
matching `docs/memories/*.md` file:

```text
Taskboard: <ticket-uuid>
```

Use the **UUID** (`id` in MCP / the parenthetical id in CLI output), not the
display key (`AUTH-1`). `ticket move` looks up UUID only.

Hooks only auto-move tickets that have this line. No ID → no auto-move.

Memories keep `Context` / `Evaluation` / `Key Challenges`. Do not copy workflow
steps onto the board.

## When to create tickets

After the human approves the plan, create or claim tickets for **current sprint
items**. Do not file one ticket per memory file. Do not spawn agents from the
Taskboard UI.

Statuses: `todo` | `in_progress` | `done`.

When the memory `state:` becomes `completed`, move the linked ticket to `done`
(the Stop/commit hook does this if the CLI is on PATH; do it yourself if not).

## MCP vs CLI

Prefer MCP tools when they are connected (`create_project`, `create_ticket`,
`move_ticket`, `list_tickets`, `get_board`, …). Otherwise CLI with `--db`.

Install the binary (not vendored):

```bash
brew tap tcarac/taskboard && brew install taskboard
# or: clone atebites-hub/taskboard && make build
```

`taskboard start` serves the UI on `:3010` against the same `--db`.
