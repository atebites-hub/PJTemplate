---
name: memory-system
description: Read and write task memories in docs/memories/. Use when planning, starting work, after searches or user feedback, and when completing tasks.
---

# Memory System

Project task memories live in **`docs/memories/`** as Markdown files. This is separate from any host-level memory you may use; follow this skill when this repo requires task memory.

## When to use

- **Before a task**: Create or open the task’s memory file; fill it from the template; set status to `in_progress`.
- **During work**: After searches or user input, update the same file (analysis, feedback, lessons as appropriate).
- **After a task**: Update that file—status, timestamps, lessons—then align `docs/agents/implementation_plan.md` per project rules.

## Recall (scan then read)

Survey all memories cheaply (everything through **Related Memories**, before **Task (TCREI)** or **Status**):

```bash
for f in docs/memories/*.md; do
  echo "=== $f ==="
  awk '/^## Task \(TCREI\)|^## Status/{exit} {print}' "$f"
  echo
done
```

Pick the most relevant paths from context (current sprint task, links in **Related Memories**, descriptions). **Read the full file** only for those.

## Write

1. **Naming**: `YYYY-MM-DD-<short-task-slug>.md` (kebab-case slug).
2. **Template**: Copy [assets/memory_template.md](assets/memory_template.md). Task structure and fields are defined there—do not duplicate that spec in other repo docs.
3. **Before starting**: New file from template; complete **Description**, **Related Memories**, **Task (TCREI)** (including **Scope**: `inline` or `open-dynamic-workflows`), **Status** (`in_progress`, timestamps).
4. **After finishing**: Same file; set **Status** (`completed` / `cancelled`), **Lessons** / **Learnings**, final timestamps.

## Requirements

- Prefer links to code/docs over long pasted content.

Whether a memory accompanies source changes, and whether its reasoning fields
(**Context**, **Evaluation**, **Key Challenges & Analysis**) are filled, is **enforced
by the checker, not by prose**: `scripts/check-task-compliance.sh` (checks C1 and C3)
runs in the git pre-commit hook and in CI. This skill defines *how* to write a good
memory; the check verifies the *artifact*. See `docs/agents/enforcement_matrix.md`.
