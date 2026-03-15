# RLM Paper Summary and Application

**Title**: Recursive Language Models  
**Authors**: Alex L. Zhang, Tim Kraska, Omar Khattab  
**Published**: arXiv:2512.24601 (December 2025; updated January 2026)  
**Link**: https://arxiv.org/abs/2512.24601

---

## Problem the Paper Solves

Standard LLMs process context as a fixed-length string passed into a single prompt
window. When a document (or codebase) exceeds that window, the model must either
truncate it, summarize it (losing fidelity), or use retrieval-augmented generation
(which requires pre-built indexes and loses structural relationships).

None of these approaches let the model *choose* what to look at, *how* to look at
it, or *recurse* into sub-sections on demand. The model is a passive reader.

---

## Core Idea: The Model as an Active Programmer

RLM makes the model an **active programmer** over its own context. Instead of
receiving a static string, the model receives:

1. A persistent Python REPL environment (variables survive across calls)
2. The long context pre-loaded as a Python variable (e.g. `context = "..."`)
3. A system prompt that instructs it to use the REPL to navigate the context

The exact system prompt from the paper (Section 2 / Appendix C):

> "You can access, transform, and analyze this context interactively in a REPL
> environment, which you are strongly encouraged to use as much as possible."

The model can then write code like:

```python
context[0:50000]                          # slice a chunk
re.findall(r"def \w+", context)           # search for functions
sub_llm_call(context[10000:20000])        # recurse on a sub-section
```

Each code block runs in the persistent session. Variables, intermediate results,
and helper functions accumulate across calls — exactly like a Jupyter notebook.

---

## Why This Achieves "Near-Infinite" Context

The key insight is that context depth is no longer bounded by the prompt window.
The model can:

- **Slice on demand**: only load the part it needs right now
- **Build indexes programmatically**: create dicts, graphs, or search structures
  from the raw context and query them in later calls
- **Recurse**: call itself (or a sub-model) on a focused snippet, then integrate
  the result back into the main session
- **Accumulate state**: store findings as variables and reference them later
  without re-reading the original context

The paper demonstrates this on tasks requiring reasoning over documents far larger
than any single context window, with significantly better accuracy than
summarization or naive chunking approaches.

---

## How This Skill Applies the Paper

| Paper concept | This skill's implementation |
|---|---|
| Long context as a Python variable | `codebase` dict mapping file paths to content strings |
| Persistent REPL session | `MCP_DOCKER` → `execute_code` tool with `session_id` integer |
| Model writes code to navigate context | Agent writes Python in subsequent `execute_code` calls |
| Recursive sub-calls on snippets | Agent loads sub-dicts from `codebase` and recurses over them |
| Context injected before reasoning begins | `load_batch()` injects Cursor-fetched files as strings |
| Variables survive across calls | All state persists as long as `session_id` is passed |

**One key difference from the paper**: the paper injects a single monolithic string.
This skill injects a structured `dict` keyed by file path. This is strictly better
for codebase analysis because it preserves file identity, enables path-based lookup,
and allows the agent to load only the files relevant to the current sub-task.

**One constraint vs. the paper**: the paper's REPL can read files from disk.
The `mcp-code-interpreter` container is sandboxed — no host filesystem access.
All file content must be injected from Cursor's native tools via `load_batch()`.
This is a deliberate trade-off: it keeps the setup zero-config and globally
reusable across all repositories without mounting volumes.

---

## The Bootstrap as the RLM System Prompt

In the paper, the system prompt tells the model what tools it has and how to use
them. In this skill, `scripts/bootstrap.py` plays the same role: it runs once at
the start of the session and establishes the `codebase` variable, the helper
functions, and the conventions the agent will use throughout the session.

The agent reading this skill file is equivalent to the model reading the paper's
system prompt — it learns the available "API" (`load_batch`, `get_status`, etc.)
and the expected workflow before any analysis begins.

---

## Relationship to Cursor's Native Sub-Agents

Cursor's Composer Agent already spawns parallel sub-agents with isolated context
windows and uses semantic embedding for retrieval. This covers the majority of
everyday tasks. The RLM skill adds what native sub-agents cannot provide:

- **Stateful accumulation**: results from one `execute_code` call are available
  in the next without re-passing them through the prompt
- **Programmatic navigation**: the agent writes code to search, filter, and
  restructure context rather than relying on embedding similarity
- **No summarization loss**: the raw file content stays in the `codebase` dict
  for the entire session; the agent can re-examine it at any granularity
- **Computed artifacts**: dependency graphs, import trees, coupling matrices —
  built once and queried many times within the same session
