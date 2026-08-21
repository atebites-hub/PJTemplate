# Execution Policy

> **Human-curated. Agents read this at session start; agents must not edit it.**
> This is a **process** document — it is *not* one of the 10 core product documents (like
> `enforcement_matrix.md`, it describes how work is run, not what the product is). It owns
> *how work is run here*: when to delegate, how to route models, how to drive loops, and the
> operating cadence. The 10 core docs say *what to build*; this says *how to run the building*.
> Rules owned by other docs are referenced, not restated.

## 1. Two-track operating model

Work runs on two pipelined tracks, both already embodied by this template's artifacts:

- **Spec track** — the 10 core documents in `docs/agents/` plus `docs/agents/implementation_plan.md`
  (the sprint/task breakdown). This is upfront, human-approved design.
- **Implementation track** — the per-task memory loop (`memory-system` skill → `docs/memories/`,
  `reasoning-system` skill, the `docs/code/` mirrors, the `scripts/check-task-compliance.sh` gate).

Pipeline them: while an implementation runs against an **approved** plan, author the next spec.
The maintainer is never idle waiting on the agent, and the agent is never idle waiting on the spec.

## 2. Scaling rule (theory of constraints)

The bottleneck is **spec authoring + human verification/UX review**, not agent count. You cannot
speed a system by parallelizing a stage that is not the constraint — adding agents downstream of a
human-review bottleneck just grows a queue. Scale the number of concurrent tracks to **human
spec/verify capacity**: roughly **two** tracks for a solo builder, **a few** for a team, **never ten**.

## 3. Decomposition rule: split by context, not by role

If two subtasks need overlapping context, they are **one** agent — the agent that implements a
feature writes its tests, because it already holds the context. Split work only where the context is
genuinely isolated. **Role-splitting** (planner → implementer → tester as separate agents) is a
telephone game: information degrades at each handoff and the downstream agent re-derives what the
upstream one already knew.

## 4. Orchestration patterns

| Pattern | When it applies |
|---|---|
| **Prompt chaining** | A fixed sequence of steps, each refining the last (outline → draft → polish). |
| **Routing** | Classify the input, then dispatch to the specialized handler (cheap model triages; right tier handles). |
| **Parallelization** | Independent subtasks fanned out, then aggregated (sectioning) or voted (decorrelated checks). |
| **Orchestrator-worker** *(the default)* | A main thread holds the plan and spawns isolated workers for bounded, context-isolated subtasks (search, exploration, a single review). |
| **Taskboard** *(optional)* | A local board for sprint tickets (one card per item in `implementation_plan.md`). Plugin + `taskboard_plugin` in `config/setup.toml`; SQLite at `.taskboard/taskboard.db`. Not a replacement for ODW scripts or C3 memories. See `docs/agents/agent_stack.md` §1. |
| **Dynamic workflow (ODW)** | Large / high-risk / many-agent work codified as a JS script under `.agents/workflows/` and run via `./scripts/odw` (skill `open-dynamic-workflows`). Prefer over ad-hoc fan-out when seats must be resumeable or exceed one conversation. See `docs/agents/odw_executor_matrix.md`. Optional quality layer: LLM-as-a-Verifier (`odw_verifier`) to rank high-stakes / best-of-N leaves — never wrap every `agent()` call (§6). |
| **Evaluator-optimizer** | A builder proposes; a **separate** evaluator judges against a concrete gate; iterate. **This is Feature A's decorrelated acceptance gate** (see §9 and the `reasoning-system` skill, thought 5). For ODW/best-of-N scoring at scale, LLM-as-a-Verifier is the cataloged calibrated scorer (`docs/agents/agent_stack.md` §2). |

## 5. Model routing by where errors are costly

Route the strongest models to where a mistake is **most expensive to undo** — planning,
architecture, and **review/verification**. Route the cheapest/fastest models to navigation, code
search, and summarizing. Measure the cost of **mergeable output**, not cost per call: a cheap model
that produces output a human must redo is more expensive than a top-tier model that lands clean.

> *Terminology:* this "where errors are costly" routing is distinct from the least-privilege **blast
> radius** used for security in `coding_standards.md` — same words, different axis (cost of error vs.
> scope of compromise).

## 6. Three failure modes to design against

1. **Vague briefs → duplicated work.** Every delegated task states: objective, output format,
   allowed tools, and explicit out-of-scope boundaries. Ambiguity is re-derived (differently) by
   each agent.
2. **Verifiers that declare victory without verifying.** Gates must be **concrete and binary** — a
   command that exits 0/1, or a rubric with pass/fail criteria. This ties directly to Feature A: the
   `Evaluation` field names exactly one such gate.
3. **Cost compounding.** Tier models (§5), set per-loop token budgets, and pause before runaway
   spend (§7).

## 7. Loop guardrails (for autonomous / Ralph-style driving)

- **Iteration cap** per loop; stop and report, don't spin.
- **Per-agent token budget** with **auto-pause at ~85%** of the target.
- **Read before guess** — open the file/symbol; never infer an API you can check.
- **Kill-and-reassign after ~3 stuck iterations** on the same failure (a fresh context beats a
  poisoned one).
- **One file, one owner** — parallel writers use `git worktrees` (see the superpowers
  `using-git-worktrees` skill) so they never contend on the same file.
- **Re-inject the task/checklist** on long runs so the goal doesn't drift out of context.

## 8. Lightweight tier

The full ceremony (reasoning pass + task memory + the C3 gate) applies to **code meant to live**.
**Throwaway/spike/exploration work is exempt** — it does not create a `docs/memories/` entry, so the
compliance gate never fires on it. This boundary matches the `reasoning-system` skill's own trigger
scope (features, refactors, architecture, complex multi-file changes — not trivial edits). Don't
impose the gate on a spike; do promote a spike's findings into a real task before the code lands.

## 9. Delegation policy

Spawn an **isolated worker** only for: context isolation (keep a noisy subtask out of the main
thread), genuine parallelization, or true specialization. Keep work in the **main thread** when the
steps are sequential, conversational, or need the human in the loop.

**For coding specifically:** isolated workers **explore and answer questions** — they do **not**
write code in parallel with the main agent (that reintroduces the role-split telephone game of §3).

Role → installed tool (the decorrelated gate from Feature A, instantiated):

- **Decorrelated review gate** → `/ce-code-review` (compound-engineering). It fans out to the
  `ce-*-reviewer` fleet (`ce-feasibility-reviewer`, `ce-scope-guardian-reviewer`,
  `ce-maintainability-reviewer`, `ce-code-simplicity-reviewer`, `ce-correctness-reviewer`,
  `ce-security-reviewer`, …) in **fresh context**, independent of whoever built the change — exactly
  the decorrelation Feature A requires. Alternatives: native `ultrareview`, or re-running the gate at
  a **different effort tier**. *(No multi-model API infrastructure; no repo-owned reviewer is
  committed while `compound-engineering` is enabled — that would duplicate the fleet.)*
- **Retrieval / research worker** → `ce-repo-research-analyst` (compound-engineering), or the
  `superpowers` `dispatching-parallel-agents` pattern, or the built-in `Explore` agent.

## 10. Spec-track planning owner

To avoid overlapping planning surfaces, **one** owner of upfront planning:

- **Heavy/architectural planning** → native **plan mode** (or `ultraplan`).
- **Sub-threshold, in-session changes** → the `reasoning-system` skill.

J-Space (when kept) is **not** a planning owner; it is optional runtime cognition.
See `docs/agents/agent_stack.md` §3.

The maintainer picks one per context; this is "one owner per function," not a tool ban. Whatever
produces the plan, the **approved** plan is what the implementation track executes against (§1).
