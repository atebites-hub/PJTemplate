# Harness hook scaffolds

PJTemplate ships **committed** Tier-2 hooks for the common harnesses. Copy scaffolds
here when your team uses a tool that is not pre-wired.

**Canonical script:** `scripts/hooks/session-workflow-checklist.sh`  
**Checklist text:** `scripts/hooks/workflow-checklist.txt` (edit in one place)

Set `PJ_HOOK_FORMAT` (or pass the first argument) when auto-detect is wrong:

| Format | stdout shape |
|--------|----------------|
| `claude` | plain text (default) |
| `codex` | `hookSpecificOutput.additionalContext` |
| `copilot` | `additionalContext` |
| `cursor` | `additional_context` |

**Stop / turn-end compliance** (all harnesses): `scripts/check-task-compliance.sh --task`
(exit 2 = blocking feedback). Tier 1 remains `.githooks/pre-commit --staged`.

## Shipped in this repo

| Harness | Session checklist | Stop compliance |
|---------|-------------------|-----------------|
| Claude Code | `.agents/settings.json` → `SessionStart` | `.agents/settings.json` → `Stop` |
| Cursor | `.cursor/hooks.json` → `sessionStart` | `.cursor/hooks.json` → `stop` |
| GitHub Copilot CLI | `.github/hooks/session-workflow.json` | same file → `agentStop` |

## Copy-paste scaffolds

| File | Harness | Install |
|------|---------|---------|
| [codex-hooks.json](codex-hooks.json) | Codex CLI | Copy to `<repo>/.codex/hooks.json` or merge into `config.toml` |
| [grok-hooks.json](grok-hooks.json) | Grok Build | Copy to `<repo>/.grok/hooks/session-workflow.json` (may also read `.claude/settings.json`) |
| [gemini-settings-hooks.json](gemini-settings-hooks.json) | Gemini CLI | Merge `hooks` into `.gemini/settings.json` — uses `AfterAgent`, not SessionStart |
| [droid-hooks.json](droid-hooks.json) | Droid / Factory | Copy to `<repo>/.factory/hooks.json` |
| [windsurf-hooks.json](windsurf-hooks.json) | Windsurf Cascade | Copy to `<repo>/.windsurf/hooks.json` — post-response only (no blocking Stop) |

## No shell-hook scaffold (use skills + git/CI only)

- **Hermes** — plugin `pre_verify` / `post_llm_call` or shell hooks in `~/.hermes/config.yaml`
- **Antigravity SDK** — Python `PostTurnHook` / `PreToolCallDecideHook`, not this shell script
- **Zed** — no documented agent lifecycle shell hooks

See `docs/agents/enforcement_matrix.md` for the three-tier model.