# Enforcement Capability Matrix

## 1. The problem and the three-tier design

This template enforces *process artifacts* — task memories (`docs/memories/`), `docs/code/` mirrors for every code file, and recorded reasoning — through a single script, `scripts/check-task-compliance.sh`. The script is the one source of truth for "is this change compliant?"; everything else is just a *trigger* that runs it.

The core constraint: **there is no universal, cross-agent hook standard.** Each coding harness (Claude Code, Cursor, Codex, Copilot CLI, Droid, etc.) ships its *own* hook schema, event names, and config location, and several popular tools (notably Google Antigravity at time of writing) have *no stable, documented* hook mechanism at all. Hook event names are even superficially similar across tools — `PreToolUse`/`Stop` appear in Claude Code, Codex, and Droid — but the JSON shapes, config paths, and exit-code semantics differ, and none is contractually stable. Building authoritative enforcement on any single harness's hooks would (a) break the moment a teammate uses a different agent, and (b) silently disappear if that harness changes or drops its hook API.

Because of this, enforcement is layered into three tiers, ordered by authority:

- **Tier 1 — Authoritative, portable spine: a native committed git hook.** `.githooks/pre-commit` (activated per clone with `git config core.hooksPath .githooks`) calls `scripts/check-task-compliance.sh --staged`. This depends only on git itself — no Python framework, no Node, no per-harness API — and runs identically regardless of which agent (or human) produced the commit. It is the layer we treat as definitive locally.
- **Tier 2 — Fast in-loop accelerators: optional per-harness adapters.** Where a harness *does* expose a documented "the agent just finished" lifecycle event, we can wire that event to the same script (`--task`) so the agent gets feedback *during* its loop instead of waiting for `git commit`. These are conveniences, not guarantees; they are opt-in and harness-specific. We ship exactly one: the Claude Code `Stop` hook.
- **Tier 3 — Non-bypassable backstop: CI.** Any client-side git hook — native, husky, or pre-commit framework — is trivially skipped with `git commit --no-verify` ([git docs: githooks](https://git-scm.com/docs/githooks); [Adam Johnson: Git skip hooks](https://adamj.eu/tech/2023/02/13/git-skip-hooks/)). The only enforcement a developer *cannot* locally bypass is a server-side / CI gate. CI re-runs the same script over the PR commit range (`--range BASE..HEAD`) and branch protection blocks the merge on failure.

The tables below document the current capabilities that justify this split.

## 2. Table 1 — Per-harness lifecycle hooks

| Harness | Lifecycle events available | Can run shell command? | Config location | Tier-2 adapter feasible? | Source |
| --- | --- | --- | --- | --- | --- |
| **Claude Code** | `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `Notification`, `PreCompact`, and more. `Stop` fires "when Claude finishes responding." `SessionStart` (matcher `startup\|resume\|clear\|compact`) reinjects workflow context after compact. | **Yes** — `"type": "command"` handler runs a shell command/executable via stdin-JSON; supports `${CLAUDE_PROJECT_DIR}`. Exit code **2** = blocking error, stderr is fed back to the model; exit 0 parses stdout JSON; other codes are non-blocking. | `.claude/settings.json` (project, committable), `.claude/settings.local.json` (gitignored), `~/.claude/settings.json` (user), plugin `hooks/hooks.json`. | **Yes — shipped.** `SessionStart` → `scripts/hooks/session-workflow-checklist.sh` (workflow nudge; non-blocking). `Stop` → `scripts/check-task-compliance.sh --task`. | [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks), [hooks-guide](https://code.claude.com/docs/en/hooks-guide) |
| **Cursor** (>= 1.7) | `sessionStart`, `sessionEnd`, `preToolUse`, `postToolUse`, `subagentStart`, `subagentStop`, `beforeShellExecution`, `afterFileEdit`, `beforeSubmitPrompt`, `preCompact`, `stop`, `afterAgentResponse`, and more. `stop` fires "when the agent loop ends." | **Yes** — hooks are "spawned processes that communicate over stdio using JSON in both directions" (bash, Python, TS/Bun, any executable). | `<project-root>/.cursor/hooks.json` (committable, loads "for all team members in trusted workspaces") and `~/.cursor/hooks.json` (global). | **Yes** — `stop` hook → `--task`. (Not shipped; optional.) | [cursor.com/docs/hooks](https://cursor.com/docs/hooks), [InfoQ](https://www.infoq.com/news/2025/10/cursor-hooks/) |
| **Codex CLI** (OpenAI) | `SessionStart`, `SubagentStart`, `SubagentStop`, `PreToolUse`, `PostToolUse`, `PreCompact`, `PostCompact`, `UserPromptSubmit`, `Stop`. `Stop` fires "when a conversation turn stops" and can return `"decision": "block"` to continue. | **Yes** — only `type: "command"` handlers run today (prompt/agent handlers are parsed and skipped). Commands run with the session `cwd`; `timeout` default 600s. | `~/.codex/hooks.json` or `~/.codex/config.toml`; repo-level `<repo>/.codex/hooks.json` or `<repo>/.codex/config.toml`. | **Yes** — `Stop` hook → `--task`. (Not shipped; optional.) | [developers.openai.com/codex/hooks](https://developers.openai.com/codex/hooks), [config-advanced](https://developers.openai.com/codex/config-advanced) |
| **Droid / Factory CLI** | `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Notification`, `Stop`, `SubagentStop`, `PreCompact`, `SessionStart`, `SessionEnd`. `Stop` fires "when Droid finishes responding." | **Yes** — "user-defined shell commands that execute at various points in Droid's lifecycle." Exit code 2 blocks (e.g. file-protection example `sys.exit(2 ...)`). | `~/.factory/hooks.json` (user) and project-level `.factory/` config. | **Yes** — `Stop` hook → `--task`. (Not shipped; optional.) | [docs.factory.ai/cli/configuration/hooks-guide](https://docs.factory.ai/cli/configuration/hooks-guide) |
| **GitHub Copilot CLI** | Documented: `preToolUse` ("can deny or modify tool calls"), `postToolUse` ("custom post-processing"). A `Stop`/completion event is **not** clearly documented. | **Yes** — hooks "deterministically execute custom shell commands at each lifecycle point." | `.agent.md` files / interactive wizard. | **Partial** — feasible only if a completion-class event exists; verify before relying. | [github.blog GA changelog](https://github.blog/changelog/2026-02-25-github-copilot-cli-is-now-generally-available/) |
| **Gemini CLI** | Tool-execution lifecycle internally; no first-party, stable *user-configurable* "Stop"-style shell hook clearly documented as a public contract at this time. | Unclear / not first-party documented as a stable shell-hook surface. | Historically `.gemini/`; the `.agents/` + `AGENTS.md` convention is superseding it. | **Unverified** — treat as "no stable documented Stop hook (as of June 2026)" until confirmed. | [aipositive: Gemini CLI execution engine](https://aipositive.substack.com/p/from-prompt-to-code-part-1-inside) |
| **Google Antigravity** | **Conflicting signals.** I/O 2026 material and SDK write-ups describe a `hooks.json` with `Stop`-style events; the official AI-dev forum thread treats hooks as a **feature request** and points to `.agent/workflows/` + `.agent/rules/` as the current mechanism. The `antigravity.google/docs/hooks` page returned no extractable schema when fetched. | If/where hooks exist: JSON over stdin/stdout; shell execution implied but not confirmed from primary docs. | Reported: workspace `.agents/hooks.json`. Not verified against a stable spec. | **Do not rely on it.** Treat as **no confirmed, documented hook mechanism (as of June 2026)**; use Tier 1/Tier 3 only. Re-check when official docs stabilize. | [I/O 2026 deep-dive](https://antigravity.google/blog/google-io-2026-feature-deep-dive), [AI-dev forum](https://discuss.ai.google.dev/t/hooks-in-antigravity/120458) |
| **Windsurf** | A hook/rules-style customization surface is referenced by multi-tool config frameworks, but no primary Windsurf doc enumerating a stable `Stop`-class shell-execution event was located. | Not confirmed from primary docs. | `.windsurf/` rules; hook spec not confirmed. | **Unverified** — treat as undocumented until a primary source is found. | [agent-skills multi-tool support](https://deepwiki.com/addyosmani/agent-skills/1.1-getting-started-and-installation) |
| **Zed** | **No documented agent-lifecycle shell-hook mechanism found (as of June 2026).** Zed's extensibility is editor/extension-oriented. | No documented mechanism found. | n/a | **No.** | (no primary hook doc located) |

> **Honesty note.** Rows marked "unverified," "conflicting," or "no documented mechanism found" mean exactly that — this matrix distinguishes *documented to exist* (Claude Code, Cursor, Codex, Droid, Copilot CLI pre/post-tool) from *no primary, stable doc found* (Gemini CLI Stop hook, Windsurf, Zed, and Antigravity's whole hook surface). Do not build a Tier-2 adapter on an unverified row without first confirming against that tool's current primary docs.

## 3. Table 2 — Portable enforcement layer

| Mechanism | How shared across clones | Added dependency | Survives `--no-verify`? | Notes | Source |
| --- | --- | --- | --- | --- | --- |
| **Native git hooks + `core.hooksPath`** (Tier 1) | Hooks committed to an in-repo dir (`.githooks/`). Each clone runs **`git config core.hooksPath .githooks`** once to activate (git >= 2.9). | **None** — git only. | **No** — `git commit --no-verify` skips all client-side hooks. | One-time per-clone activation is the only caveat; automated in `scripts/setup.sh`. Fully in-repo, runs for humans and every agent identically. | [git core.hooksPath](https://www.brandonpugh.com/til/git/config-hookspath/), [git githooks](https://git-scm.com/docs/githooks) |
| **pre-commit framework** (pre-commit.com) | `.pre-commit-config.yaml` committed; each developer runs **`pre-commit install`** per clone, which writes `.git/hooks/pre-commit`. | **Python** + the `pre-commit` package. | **No** — bypassed by `--no-verify`; also skippable via the `SKIP` env var. | More machinery than a single shell script needs; adds a runtime + tool we would not otherwise require. | [pre-commit.com](https://pre-commit.com/) |
| **husky** (JS ecosystem) | `.husky/` committed; activated by the npm `prepare` script, so **`npm install`** per clone wires it up. Uses `core.hooksPath` under the hood. | **Node.js / npm**. | **No** — still a client-side git hook; `--no-verify` skips it. | Natural only if the repo is already a Node project; this template's frontend is optional, so requiring npm for enforcement would be backwards. | [typicode.github.io/husky](https://typicode.github.io/husky/) |
| **Server-side / CI gate** (Tier 3) | Lives in CI config (`.github/workflows/ci.yml`) + branch protection; nothing to install per clone. | CI minutes only. | **Yes** — `--no-verify` does not skip server-side checks or CI. Branch protection blocks the merge. | The *only* non-bypassable layer. Re-runs the same script over the PR range so a locally-skipped check still fails the PR. | [Adam Johnson](https://adamj.eu/tech/2023/02/13/git-skip-hooks/) |

## 4. Conclusion

The matrix confirms the three-tier split:

- **Tier 1 — native git hook is the authoritative spine.** It is the only portable trigger with **zero added dependencies** (git itself), fully in-repo, and identical across every harness and for human commits. Its sole caveat — per-clone activation — is one command:

  ```bash
  git config core.hooksPath .githooks
  ```

  with `.githooks/pre-commit` calling `scripts/check-task-compliance.sh --staged`.

- **Tier 2 — per-harness adapters are optional accelerators.** They give the agent in-loop feedback *before* it reaches `git commit`, but they are non-authoritative (each harness has its own schema, and several have none). **Claude Code ships two adapters** in `.agents/settings.json` (read via the `.claude` symlink):
  - **`SessionStart`** (matcher `startup|resume|clear|compact`) → `scripts/hooks/session-workflow-checklist.sh` reinjects the memory/reasoning/open-dynamic-workflows checklist after compact (Ponytail-style context injection; non-blocking).
  - **`Stop`** → `scripts/check-task-compliance.sh --task` (exit code 2 feeds stderr back to the model).

  ```json
  {
    "hooks": {
      "SessionStart": [
        {
          "matcher": "startup|resume|clear|compact",
          "hooks": [
            {
              "type": "command",
              "command": "${CLAUDE_PROJECT_DIR}/scripts/hooks/session-workflow-checklist.sh"
            }
          ]
        }
      ],
      "Stop": [
        {
          "matcher": "",
          "hooks": [
            {
              "type": "command",
              "command": "${CLAUDE_PROJECT_DIR}/scripts/check-task-compliance.sh --task"
            }
          ]
        }
      ]
    }
  }
  ```

  **Also shipped (project hooks):** Cursor — `.cursor/hooks.json` (`sessionStart` + `stop`); GitHub Copilot CLI — `.github/hooks/session-workflow.json` (`sessionStart` + `agentStop`). Copy-paste scaffolds for Codex, Grok, Gemini, Droid, Windsurf live under `scripts/hooks/scaffolds/`.

  Other harnesses (`stop` / `Stop` / `agentStop`) expose equivalent completion events and can use the same `--task` script — see scaffolds README — but remain optional until verified against current docs.

- **Tier 3 — CI is the non-bypassable backstop.** Because every client-side hook is skippable with `git commit --no-verify`, the merge gate must live server-side. CI re-runs the same script over the PR commit range, and branch protection blocks the merge on failure:

  ```yaml
  - name: Task-compliance gate (process artifacts)
    run: scripts/check-task-compliance.sh --range "origin/${{ github.base_ref }}..HEAD"
  ```

  Routing all three tiers through the *same* `scripts/check-task-compliance.sh` with three flags (`--staged`, `--task`, `--range`) keeps one source of truth: improving the check improves all tiers at once.

## 5. Sibling gate — template-setup completeness

A second gate, `scripts/check-template-setup.sh`, runs in the same Tier-1 hook
immediately after `check-task-compliance.sh`. Where the task-compliance gate
enforces *process artifacts per change*, the setup gate enforces *template-to-
project transformation* — it blocks commits until the scaffold has been turned
into a real project:

- **placeholder sweep** — no `[Project Name]`, `yourapp`, `Your Name`,
  `PJTemplate`, `[Number]`, `--cov-fail-under=0`, etc. left in tracked files;
- **required tooling** — `core.hooksPath` set, `CLAUDE.md → AGENTS.md` and
  `.claude → .agents` links intact, the ODW submodule initialized (and built if
  kept);
- **decisions** — `config/setup.toml` has no unresolved `<TODO>` fields, so every
  subsystem (observability, ODW, CD, notebooks, IDE scaffolds) has an explicit
  keep/strip decision and the GitNexus noncommercial license is addressed.

It is **dormant by design**: while the marker file `.template-scaffold` exists the
repo is the pristine template, so the gate prints one line and exits 0. Step 1 of
deriving a project is `rm .template-scaffold`, which activates the gate. A one-off
override is `SKIP_SETUP_GATE=1 git commit ...`. The canonical map for every item
is [`docs/agents/template_setup_checklist.md`](template_setup_checklist.md). Add
the same script to `.github/workflows/ci.yml` if you want a Tier-3 backstop for
setup (the template ships Tier-1 only, since the template repo's own CI must stay
green against the dormant gate).

## 6. Maintenance note

Harness hook APIs are young and moving fast — event names, config paths, and exit-code semantics change between releases, and tools add or drop hook support (Antigravity's hook surface is unsettled as of June 2026). **This matrix is a snapshot.** Before relying on any Tier-2 adapter:

1. Re-verify the harness's current hook docs (the cited URLs may have changed).
2. Confirm a completion-class event (`Stop`/`stop`/`afterAgentResponse`) still exists and still runs a shell command.
3. Confirm the config file path and the exit-code/stdin contract.
4. Pin the harness version where possible, and never let a Tier-2 adapter become load-bearing — Tier 1 (native git hook) and Tier 3 (CI) must stand alone if every adapter were deleted.

Re-check this document whenever a harness ships a major version, or quarterly, whichever comes first.
