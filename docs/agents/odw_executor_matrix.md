# open-dynamic-workflows — harness / executor matrix

> **Process doc** (not one of the 10 core product documents). Records which coding
> harnesses this template cares about, whether they expose a headless CLI that can
> back an ODW `Executor`, and what is **bundled today** vs **feasible to add**.
> Reviewed against local CLIs + primary docs (2026-07).

## How ODW plugs into a harness

ODW does **not** embed models. Each `agent()` call names an **`executor`** string;
the host supplies `RunOptions.executors: Record<string, Executor>`. An `Executor` is
`(ExecOptions) => Promise<ExecResult>` — typically spawn a coding-agent CLI, feed the
prompt (stdin or argv), parse stdout/JSONL, return final text / structured output.

Bundled in `vendor/open-dynamic-workflows` (via `builtinExecutors`):

| Name | Binary / argv sketch | Notes |
| --- | --- | --- |
| `claude` | `claude --print --output-format=stream-json --verbose --permission-mode acceptEdits` | Prompt on stdin; stream-json reducer |
| `codex` | `codex exec --json --skip-git-repo-check --color never --sandbox workspace-write -` | Prompt on stdin (`-`); JSONL reducer |

New harnesses = new adapter under `executor/<name>/` using `makeSubprocessExecutor`
(or a pure-function/SDK executor). **Do not** fork ODW in-tree for adapters unless
upstreaming; prefer PR to [imsai-sh/open-dynamic-workflows](https://github.com/imsai-sh/open-dynamic-workflows)
or a thin project wrapper that builds a custom `executors` map and calls `runWorkflow`.

## Matrix (template-relevant harnesses)

Status legend:

- **Bundled** — ships in ODW `builtinExecutors`
- **Headless-ready** — documented / local CLI supports one-shot non-interactive run; adapter not written yet
- **Partial** — headless exists but output contract is weak/unstable for reliable resume journals
- **IDE-only / no CLI** — not a good ODW leaf executor without another path
- **Unverified** — conflicting or thin primary docs

| Harness | PJTemplate surface today | Headless invoke (if any) | ODW executor status | Notes |
| --- | --- | --- | --- | --- |
| **Claude Code** | Symlinks + plugins + SessionStart/Stop | `claude -p` / `--print` + stream-json | **Bundled (`claude`)** | Reference adapter. Never use `--dangerously-skip-permissions`. |
| **OpenAI Codex CLI** | Hook scaffold (`.codex`) | `codex exec --json` | **Bundled (`codex`)** | Reference adapter. Sandbox `workspace-write`, not full bypass. |
| **Cursor Agent CLI** | `.cursor/hooks.json` | `agent -p` / `--print` (`--output-format text\|json\|stream-json`) | **Headless-ready** | Strong candidate for next bundled executor (`cursor` / `agent`). Auth via API key / login. |
| **Grok Build** | Hook scaffold | `grok -p` / `--single` + `--output-format plain\|json\|streaming-json`; optional `--json-schema` | **Headless-ready** | Excellent ODW fit (schema + streaming-json). Candidate name: `grok`. |
| **Factory Droid** | Hook scaffold | `droid exec` (`-o` format, `--auto`, `--cwd`, worktree) | **Headless-ready** | Built for CI/script; default read-only until `--auto`. Candidate: `droid`. |
| **Gemini CLI** | `.gemini/settings.json` | `gemini -p` / headless docs | **Headless-ready (legacy path)** | Google is migrating terminal experience to **Antigravity CLI**; prefer `agy`/`antigravity` for new adapters. |
| **Google Antigravity** | Mentioned in enforcement matrix (hooks unstable) | CLI + SDK documented; `agy -p` cited in codelabs/community | **Partial / verify install** | Desktop `agy` on some machines is only an app launcher symlink — install **Antigravity CLI** separately before writing an adapter. SDK is Python (`google-antigravity`). |
| **GitHub Copilot CLI** | `.github/hooks/` | Interactive + programmatic modes documented | **Partial** | Programmatic/headless path exists; confirm stable JSON/stream contract before adapter. Auth is OAuth-heavy. |
| **Hermes Agent** | Scaffold note (no shell hook) | `hermes chat -q "…"` (non-interactive single query) | **Headless-ready (thin)** | Good for Q&A leaves; confirm tool-use / workspace edit behavior for coding seats. |
| **Pi (earendil-works)** | Not wired | Print/JSON, RPC, SDK modes | **Headless-ready** | Minimal harness; RPC/JSON modes designed for hosts — strong custom-executor candidate. |
| **Cline / Kilo** | Not wired | IDE + CLI products; Kilo CLI for terminal/CI | **Partial** | Prefer official CLI docs for non-interactive flags before committing an adapter. |
| **Windsurf Cascade** | Hook scaffold (post-response only) | Editor-centric; `windsurf` launcher opens IDE | **IDE-only / no stable leaf CLI** | Use as **orchestrator host** (author scripts), not as ODW leaf, unless a headless Cascade CLI appears. |
| **Zed** | Skills/AGENTS only | No agent lifecycle hooks; no coding-agent CLI found | **IDE-only** | Consume skills/docs; do not plan a Zed executor. |
| **Copilot / VS Code chat** | n/a | Extension UI | **IDE-only** | Prefer Copilot **CLI** if needed as a leaf. |

## Practical guidance for this repo

1. **Authoring** can happen in any harness that reads `.agents/skills/open-dynamic-workflows`
   (Claude, Codex, Cursor, Grok, …).
2. **Running** requires Node ≥20 + built vendor CLI (`./scripts/odw`) and at least one
   installed leaf CLI named in the script (`claude` and/or `codex` out of the box).
3. **Mixed nodes** are first-class: e.g. draft with `{executor:'claude'}`, review with
   `{executor:'codex'}`.
4. **Adding a harness** (e.g. Grok/Cursor): implement adapter → register under a stable
   name → document here → prefer upstream PR so `builtinExecutors` stays the registry.
5. **Do not** pretend IDE-only tools are executors; keep Scope=`inline` and use that
   harness's native subagents if you cannot spawn a headless leaf.

## Related paths

| Path | Role |
| --- | --- |
| `vendor/open-dynamic-workflows/` | Submodule source + `npm run build` / `smoke` |
| `.agents/skills/open-dynamic-workflows/` | Symlink to upstream skill |
| `./scripts/odw` | Wrapper around `vendor/.../dist/cli.js` |
| `.agents/workflows/` | Optional committed `*.js` workflow scripts |
| `AGENTS.md` → Dynamic Workflows | Operator-facing summary |
