---
name: reason-code
description: |
  Use sequential thinking to reason through code implementations before writing.
  Invoke after planning but before editing code. References core documents in
  /docs/agents/ for project alignment. Triggers on "implement feature", "refactor",
  "architectural decision", or complex code changes.
license: MIT
compatibility: Designed for Cursor IDE with sequential-thinking MCP integration
metadata:
  author: project-team
  version: "1.0"
---

# Reason Code

Deep reasoning for code quality using sequential thinking MCP.

## When to Use

Invoke this skill **after planning but before writing/editing code**:

- Implementing new features or modules
- Refactoring existing code
- Complex architectural decisions
- Changes affecting multiple files

---

## Instructions

### Step 1: Identify Relevant Documents

Select applicable documents from `/docs/agents/` based on task type. See [references/document-mapping.md](references/document-mapping.md) for detailed mapping.

Quick reference:

| Task Type | Primary Documents |
|-----------|-------------------|
| New feature | Requirements, App Flow, Tech Stack |
| Refactor | Coding Standards, File Structure, Server Structure |
| Bug fix | Testing Guidelines, Server Structure |
| UI work | Client Guidelines, App Flow |

### Step 2: Invoke Sequential Thinking MCP

Call `sequential-thinking___sequentialthinking`:

| Parameter | Value |
|-----------|-------|
| `thought` | Current reasoning with doc references, constraints, alternatives |
| `thoughtNumber` | Current step (1, 2, 3...) |
| `totalThoughts` | Estimated steps (typically 3-7) |
| `nextThoughtNeeded` | `true` if more reasoning needed |

### Step 3: Follow Reasoning Framework

| Thought | Focus |
|---------|-------|
| 1 | **Requirements** - What, constraints, acceptance criteria |
| 2 | **Design** - Patterns, existing code, file locations |
| 3 | **Implementation** - Step-by-step plan, tests needed |
| 4 | **Risk Assessment** - What could break, edge cases |
| 5+ | **Refinement** - Counterpoints, final decision |

See [references/reasoning-examples.md](references/reasoning-examples.md) for detailed examples.

### Step 4: Document Output

After reasoning completes, record:

- Clear implementation approach
- Files to create/modify
- Tests to write
- Documentation to update
- Identified risks and mitigations

---

## Verification Checklist

Before proceeding to code:

- [ ] Sequential thinking invoked with at least 3 thoughts
- [ ] Relevant core documents referenced
- [ ] Implementation approach documented
- [ ] Risks and alternatives considered
- [ ] File locations align with `file_structure_doc.md`
- [ ] Code style aligns with `coding_standards.md`

---

## Related Resources

- Project Rules: `/AGENTS.md`
- Core Documents: `/docs/agents/`
- Task Memory Skill: `.agents/skills/memory-system/SKILL.md`
