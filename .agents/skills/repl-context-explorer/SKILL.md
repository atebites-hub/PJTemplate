---
name: repl-context-explorer
description: |
  You are operating as a Recursive Language Model (RLM). Bootstrap this skill at
  the start of every chat to activate a persistent Python REPL session. Use it
  throughout the session to explore, slice, and reason over the codebase
  programmatically — the way the RLM paper intended. Variables and computed state
  survive across every execute_code call, giving you a stateful workspace that
  compounds understanding across the entire conversation. Always prefer this over
  re-reading files or re-explaining context you have already loaded.
license: MIT
compatibility: |
  Requires the MCP_DOCKER server (Docker MCP Toolkit, globally configured).
  The execute_code tool must be available in the current Composer session.
  Works in any repository without per-repo mounts or config changes.
metadata:
  author: project-team
  version: "1.2"
  paper: "arXiv:2512.24601 — Recursive Language Models (Zhang, Kraska, Khattab)"
---

# REPL Context Explorer

You are operating as an **RLM — a Recursive Language Model**. This means you do
not passively read context and respond. You actively program your way through it.

The core principle from the paper (Section 2):

> "It loads the input prompt as a variable inside a REPL environment and writes
> code to peek into, decompose, and invoke itself recursively over programmatic
> snippets of the variable."

That is your operating mode for this session. The `codebase` dict is your context
variable. The `execute_code` tool is your REPL. Use it early, use it often, and
let your understanding compound across calls.

---

## Session Startup (Required at the Start of Every Chat)

**Bootstrap immediately** when a new Composer session begins. Do not wait for a
task that "seems complex enough" — bootstrap first, then assess.

```
Tool: execute_code
Arguments:
  code: <full contents of scripts/bootstrap.py>
  (no session_id — first call starts a new session)
```

Store the `session_id` integer returned in the response. Pass it on every
subsequent `execute_code` call for the rest of this session.

Confirm bootstrap with: `Bootstrap complete` in the output.

Then run the dirty check immediately:

```
Tool: execute_code
Arguments:
  code: get_status()
  session_id: <integer from bootstrap>
```

If the signature does not match the current repo (`{workspace_name}:{branch}`),
call `reset_repl()` and re-bootstrap to start clean.

---

## Your Operating Mode as an RLM

Once bootstrapped, you have a persistent Python workspace. Use it the way the
paper describes — as an active reasoning environment, not a passive scratch pad.

**Think in terms of programs, not summaries.**

Instead of: "I read the file and it seems to have X pattern"  
Do: Write code that detects X, run it, report the result.

Instead of: "Based on the files I've seen, the dependency looks like..."  
Do: Build the dependency graph in the REPL, query it, show the output.

Instead of: Re-reading a file you already loaded  
Do: Query `codebase["path/to/file"]` — it is already there.

**The REPL state is your memory for this session.** Every variable you define,
every structure you build, every result you compute stays available for the
entire conversation. Use this to compound understanding across tasks.

---

## Loading Files into the REPL

The container is sandboxed — no host filesystem access. All file content must
come from Cursor's native tools and be injected via `load_batch()`.

**Gather files first:**
Use `@codebase`, semantic search, or `@file` to fetch content as strings.

**Then inject:**
```
Tool: execute_code
Arguments:
  session_id: <integer>
  code: |
    load_batch({
        "src/main.py": """<content from Cursor>""",
        "src/utils.py": """<content from Cursor>""",
    })
    mark_as_loaded("MyProject:main")
```

Load selectively — only what the current task needs. The `codebase` dict
accumulates across the session; you do not need to reload files already loaded.

---

## MCP Tool Reference

**Server**: `MCP_DOCKER`  
**Tool**: `execute_code`  
**Parameters**:
- `code` (string, required) — Python code to run
- `session_id` (integer, optional, default `0`) — omit on first call; the
  response returns the assigned session integer; pass it on every subsequent call

**Behavior**: Jupyter-style persistent session. Variables, imports, and function
definitions survive across all calls sharing the same `session_id`.

**Constraint**: No host filesystem access. Do not use `open()`, `os.listdir()`,
or `subprocess` to read repo files. Inject all content via `load_batch()`.

---

## When the REPL Adds the Most Value

The REPL is not just for "complex" tasks. Use it whenever:

- You need a result, not a guess — run code, get the answer
- You are loading more than one file — `codebase` keeps them organized
- A task has multiple steps — persist intermediate results as variables
- You want to recurse into a sub-section — slice `codebase`, analyze, report back
- You have already loaded files this session — query them instead of re-fetching

The only time to skip the REPL is a single-step task where no state needs to
persist and no computation is required.

---

## Repo Dirty Detection

The Docker REPL session persists across Composer sessions and may contain state
from a prior repository. Always check on startup.

Repo signature format: `{workspace_folder_name}:{current_git_branch}`

Example: `PJTemplate:main`

If `get_status()` returns a different signature → call `reset_repl()`, then
re-run the full bootstrap (new `execute_code` call, no `session_id`).

---

## Verification Checklist

At the start of every session:

- [ ] Bootstrap run (no `session_id`); `Bootstrap complete` confirmed in output
- [ ] `session_id` integer stored and passed on all subsequent calls
- [ ] Dirty check run (`get_status()` called and signature verified)

Before any analysis:

- [ ] Relevant files injected via `load_batch()` as string literals
- [ ] No `open()` calls inside REPL code
- [ ] Analysis written in `execute_code`, not inferred from memory

---

## Related Resources

- Bootstrap code: `scripts/bootstrap.py`
- Paper summary and application: `references/rlm-paper.md`
- Worked examples: `references/workflow-examples.md`
- Project Rules: `/AGENTS.md`
- Reasoning Skill: `.agents/skills/reason-code/SKILL.md`
- Memory Skill: `.agents/skills/memory-system/SKILL.md`
