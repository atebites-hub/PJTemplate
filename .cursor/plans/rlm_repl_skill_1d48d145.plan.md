---
name: RLM REPL Skill
overview: Add a new `rlm-hybrid-repl` agent skill to the template repo following the existing `.agents/skills/` pattern. The skill enables persistent stateful Python execution (RLM-style recursive reasoning) via the user's globally-configured `mcp-code-interpreter` Docker MCP tool, without requiring per-repo filesystem mounts.
todos:
  - id: skill-md
    content: Create .agents/skills/rlm-hybrid-repl/SKILL.md with frontmatter, activation conditions, 3-step workflow, dirty detection, and verification checklist
    status: completed
  - id: bootstrap-py
    content: Create .agents/skills/rlm-hybrid-repl/scripts/bootstrap.py with load_batch, reset_repl, get_status, mark_as_loaded helpers
    status: completed
  - id: references
    content: Create references/rlm-paper.md (paper citation + core mechanism) and references/workflow-examples.md (two worked examples)
    status: completed
  - id: agents-md
    content: Update AGENTS.md to register the new skill under a new REPL Reasoning System section
    status: completed
isProject: false
---

# RLM Hybrid REPL Skill Integration

## Background
The RLM paper (arXiv:2512.24601) uses a persistent Python REPL as the core mechanism — context lives as variables, and the model writes code to slice, search, and recurse over it. Your `mcp-code-interpreter` (Docker MCP Toolkit, globally configured) is already the right tool; it just needs a skill to wire the workflow.

## Prerequisite (already satisfied)
- `mcp-code-interpreter` enabled in Docker MCP Toolkit — provides the `execute_code` tool with stateful `session_id` across Composer calls.
- No filesystem mount needed: Cursor's native indexing fetches files first; the skill injects that content into the REPL as Python variables.

## New Files to Create

```
.agents/skills/rlm-hybrid-repl/
├── SKILL.md
├── scripts/
│   └── bootstrap.py
└── references/
    ├── rlm-paper.md
    └── workflow-examples.md
```

### 1. `.agents/skills/rlm-hybrid-repl/SKILL.md`
Main skill file. Frontmatter + workflow sections matching the `reason-code` pattern:
- **When to Activate**: programmatic slicing, recursive analysis, dependency graphing, stateful multi-step computation
- **Prerequisite check**: `mcp-code-interpreter` must be available (note it in frontmatter compatibility)
- **Core Workflow** (3 steps):
  1. Cursor native tools fetch relevant files/context
  2. Agent runs bootstrap via `execute_code` (paste `scripts/bootstrap.py` content into the REPL once per session)
  3. Agent calls `load_batch({path: content})` to inject fetched files, then runs analysis
- **Repo dirty detection**: Agent computes a repo signature (workspace name + current branch), calls `get_status()` — if signature differs, calls `reset_repl()` and reloads
- **Verification checklist** (matches reason-code style)

### 2. `.agents/skills/rlm-hybrid-repl/scripts/bootstrap.py`
Python code the agent pastes into `execute_code` to initialize the REPL session. Defines:
- `codebase: dict` — persistent path→content store
- `repo_signature: str | None` — dirty detection state
- `load_batch(files_dict)` — inject files from Cursor
- `reset_repl()` — clean state for repo switch
- `get_status()` — returns loaded file count and signature
- `mark_as_loaded(signature)` — commit current repo state

This is **REPL code, not a standalone script** — it's run by the agent via `execute_code`, not via shell.

### 3. `.agents/skills/rlm-hybrid-repl/references/rlm-paper.md`
Brief notes: paper citation, core mechanism, why REPL = the paper's mechanism, link to arXiv.

### 4. `.agents/skills/rlm-hybrid-repl/references/workflow-examples.md`
Two concrete worked examples showing the agent's step-by-step tool calls:
- Example 1: Dependency graph analysis across a module
- Example 2: Recursive refactoring plan for a large file

## File to Update

### `AGENTS.md`
Add a new **Reasoning System** subsection (alongside the existing memory-system and reason-code entries) pointing to the new skill, similar to:
```markdown
## REPL Reasoning System
Stateful Python REPL for recursive, programmatic exploration using the `rlm-hybrid-repl` skill. See [.agents/skills/rlm-hybrid-repl/SKILL.md](.agents/skills/rlm-hybrid-repl/SKILL.md).

**Requirement**: Use when deep programmatic analysis, multi-step computation, or recursive codebase exploration is needed beyond what native Cursor indexing provides.
```

## What is NOT changing
- The 10 core docs in `docs/agents/` — project-specific, untouched
- MCP config — already globally configured by user, no per-repo file needed
- Existing `memory-system` and `reason-code` skills — no modifications
- The `source/`, `tests/`, `docs/code/` scaffolding — out of scope