---
name: reasoning-system
description: |
  Structured reasoning after planning and before editing code: requirements, retrieval (docs, memory, code), design, implementation plan, and testing/decision (risks and regressions expressed as tests and checks). Uses the sequentialthinking tool. Triggers before implementing a feature, refactoring, making an architectural decision, or complex multi-file changes.
compatibility: Requires the sequentialthinking tool. The skill id is reasoning-system; the host may expose the tool under any server prefix—use the tool name your environment documents.
---

# Reasoning System

Structured reasoning immediately before you write or edit code—parallel in role to the **Memory System** skill for task memory. This workflow is the **reasoning system**; invoke the **`sequentialthinking`** tool for each thought step (see Step 2). Your agent host may register it under different server names; the tool identifier to call is **`sequentialthinking`**.

## When to Use

Invoke **after planning but before writing/editing code**:

- Implementing new features or modules
- Refactoring existing code
- Complex architectural decisions
- Changes affecting multiple files

---

## Instructions

### Step 1: Identify Relevant Documents

Select applicable documents from `/docs/agents/` based on task type. See [references/document-mapping.md](references/document-mapping.md) for detailed mapping.

This step produces a **candidate** set of sources. **Thought 2 (Retrieval)** turns that into a concrete list: which docs to open, which task memory to recall, and which parts of the codebase to search or read.

Quick reference:

| Task Type | Primary Documents |
|-----------|-------------------|
| New feature | Requirements, App Flow, Tech Stack |
| Refactor | Coding Standards, File Structure, Server Structure |
| Bug fix | Testing Guidelines, Server Structure |
| UI work | Client Guidelines, App Flow |

### Step 2: Invoke the `sequentialthinking` tool

Call **`sequentialthinking`** with the parameters below. Server or package names differ by host; use the registration that exposes this tool identifier in your environment.

| Parameter | Value |
|-----------|-------|
| `thought` | Current reasoning with doc references, constraints, alternatives |
| `thoughtNumber` | Current step (1, 2, 3...) |
| `totalThoughts` | Estimated steps (typically 5–7; adjust up or down as you go) |
| `nextThoughtNeeded` | `true` if more reasoning is needed |

Optional parameters on the tool (e.g. revision or branching) may be used when you need to reconsider an earlier thought; they are not required for a linear pass.

### Step 3: Follow the reasoning framework

| Thought | Focus |
|---------|--------|
| 1 | **Requirements** — What, constraints, acceptance criteria; confirm **Scope** (`inline` vs `dynamic-workflows`) in task memory |
| 2 | **Retrieval** — Which core docs, task memory entries, and codebase areas (files, symbols, prior art) you must read or search before design; what stays unknown until retrieved |
| 3 | **Design** — Patterns, boundaries, file locations, alternatives (grounded in retrieved context) |
| 4 | **Implementation** — Ordered steps, touchpoints, migration or rollback notes if relevant |
| 5 | **Testing and decision** — Test levels (unit, integration, E2E per `Testing Guidelines.md`), regression risks (refactors, concurrency, feature flags), mapping **risks and edge cases to specific tests or verification steps**, counterpoints, **final approach**. Then the **verifiable-gate** questions: classify the task **verifiable** (a machine check can decide "done") or **non-verifiable** (needs human judgment/taste); where fuzzy, convert "make it good" into a concrete check (this conversion is the bulk of the work); name **exactly one acceptance gate** — a command/check (e.g. `./scripts/test-suite.sh`, a specific test, a benchmark threshold) or, for non-verifiable work, "human review against rubric: \<criteria>"; and for **non-trivial** changes, state that the gate is **decorrelated from the builder** (fresh-context judge / `/ce-code-review` / `ultrareview` / a different effort tier — see `execution_policy.md`) |

Use `nextThoughtNeeded: true` for extra thoughts if you need more refinement after thought 5.

See [references/reasoning-examples.md](references/reasoning-examples.md) for detailed examples.

### Step 4: Persist the output into the task memory

Record the reasoning output in the task's memory file (see the `memory-system`
skill), mapped onto existing fields so there is **one home, not a parallel record**:

| Reasoning output | Memory field (`assets/memory_template.md`) |
|------------------|--------------------------------------------|
| **Retrieval plan** — docs, memory, code paths you consulted or will consult | `- **Context**:` under `## Task (TCREI)` |
| **Test and regression plan** — what must not break; how tests/checks lock it in | `- **Evaluation**:` under `## Task (TCREI)` |
| **Verifiability class + named acceptance gate** (`Gate:` command/check or rubric) | `- **Evaluation**:` under `## Task (TCREI)` (same bullet as the test plan) |
| Assumptions, counterpoints, alternatives, risks | `### Key Challenges & Analysis` |
| Ordered implementation steps; files to create/modify | `- **Plan**:` under `## Task (TCREI)` |
| Non-obvious insights, docs to update | `### Learnings` |

The compliance check (`scripts/check-task-compliance.sh`, check **C3**) verifies that
**Context**, **Evaluation**, and **Key Challenges & Analysis** are filled with real
content — the same fields named here, so what you record is exactly what is checked.

---

## Verification checklist

Before proceeding to code:

- [ ] `sequentialthinking` invoked with at least **five** thoughts (or fewer only if every theme above is explicitly covered)
- [ ] Retrieval targets identified (docs, memory, code)
- [ ] Relevant core documents referenced
- [ ] Implementation approach documented
- [ ] Tests and regressions tied to risks and edge cases
- [ ] Task classified verifiable/non-verifiable; exactly one acceptance gate named; decorrelated review specified for non-trivial work
- [ ] File locations align with `File Structure Doc.md`
- [ ] Code style aligns with `Coding Standards.md`

---

## Related resources

- Project rules: `/AGENTS.md`
- Core documents: `/docs/agents/`
- Task memory skill: `.agents/skills/memory-system/SKILL.md`
