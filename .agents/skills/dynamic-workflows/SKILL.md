---
name: dynamic-workflows
description: Orchestrate large high-risk builds as one dynamic multi-agent workflow — isolated worktree, recon spec, staged TDD with interface contracts, 6-lens adversarial review, refute-panel verification, fix→gate loop, docs lane, orchestrator-led simplify pass, then merge gate. Harness-agnostic (Grok, Cursor, Codex, Claude). Use when a build is too big or too risky for one agent to self-report at merge time.
---

# Dynamic Workflows

A harness-agnostic playbook for builds where a single agent cannot safely own
implementation **and** merge verification. One **orchestrator** (the main
session) plans, delegates a bounded multi-agent build, then personally lands the
result. Delegated seats use the **strongest reasoning tier the host offers** for
that seat type; the orchestrator may use a different tier.

> **Origin.** Battle-tested on a capital-critical production repo ([HarborRunner
> PR #29](https://github.com/BlackSwanCollective/HarborRunner/pull/29)). The
> phases below are portable; names, gates, and lenses are filled from **this
> repo's** `AGENTS.md`, CI, and domain docs.

## When to use

- Multi-module builds (>3 files or >500 lines expected).
- Irreversible or high-stakes paths (money, auth, data loss, production config,
  safety interlocks).
- Anything where optimistic self-report at merge time is unacceptable.

**Not for:** doc-only edits, one-file fixes, config flips — do those inline.

## Harness map (same playbook, different primitives)

| Role | Claude Code | Cursor / Codex | Grok |
|------|-------------|----------------|------|
| Orchestrator | Main session | Main chat / agent | Main session |
| Read-only recon | Explore subagent | `explore` / readonly subagent | `generalPurpose` (readonly) |
| Staged implementers | Subagents / plugin workflow | `Task` subagents | `Task` subagents |
| Parallel review lenses | Parallel subagent fan-out | Parallel `Task` calls | Parallel `Task` calls |
| Gate runner | Dedicated subagent | Dedicated `Task` | Dedicated `Task` |
| Simplify pass | Parallel report-only agents | Parallel report-only `Task`s | Parallel report-only `Task`s |

**Invoke:** skill name `dynamic-workflows`, slash `/dynamic-workflows`, or explicit
"run the dynamic-workflows skill" — whichever the host supports.

**Prompt hygiene (all harnesses):** build prompts with **string concatenation**,
not template interpolation that can leave `undefined` in paths. Always embed the
**branch name** and **absolute worktree path** so a seat can self-recover via
`git worktree list`.

## Project bindings (read before Phase 0)

Resolve these from **this repository** before launching the workflow. Do not
hard-code another project's paths.

| Binding | Where to find it |
|---------|------------------|
| Agent rules & quality gates | `AGENTS.md` (or host equivalent: `CLAUDE.md`, rules files) |
| Coding / doc / test standards | `docs/agents/` (or project's standards docs) |
| **CI gate command(s)** | `.github/workflows/`, `scripts/test-suite.sh`, `Makefile`, `package.json` scripts |
| Secrets & local-only config | `.gitignore`, `config/secrets/`, `.env.example` — **never commit or overwrite** |
| Task memory / reasoning skills | `.agents/skills/`, project memory docs |
| Docs mirror convention | `docs/code/`, module READMEs, whatever this repo enforces |
| Doc site build | `mkdocs`, `docusaurus`, `vitepress` — whatever CI runs |
| Merge / release gate | PR template, `CONTRIBUTING.md`, domain runbooks (e2e, staging, operator sign-off) |

Record the resolved commands in the task memory before Phase 1 so every seat
shares one gate definition.

## Phase 0 — Orchestrator prep (inline, before delegation)

1. **Isolated worktree** in session scratchpad — **not** a host-managed worktrees
   folder that other jobs reap or clobber:
   `git worktree add "$SCRATCH/wt-<name>" -b <branch> <base-ref>`.
   Smoke a fast import/test in the worktree to prove the tree resolves.
2. **Recon spec** — read-only exploration produces a **file:line-cited** build
   spec: machinery to reuse, seams, hard parts, risks. The spec is the context
   pack; every seat re-verifies citations (lines drift).
3. **Context pack** — repo rules + spec, embedded verbatim in every seat prompt:
   - TDD; project docstring/comment standard
   - Lint, format, typecheck **zero errors** on touched files
   - No placeholders; new behavior **flag-gated default off** + **byte-identical
     off parity test** when flags exist
   - Never touch secrets, live-only config, or operator-local files
   - Commit on the branch; **do not push**

## Phase 1 — The build workflow (one orchestrated run)

One coordinated multi-agent pass. Parallelize independent seats; sequence stages
that share **interface contracts**.

1. **Implement in stages** — each stage returns schema-forced JSON: commit hash +
   exact field/param semantics the next stage consumes. Typical split: Stage A =
   pure model/leaf + tests; Stage B = integration/execution machinery + tests.
   Use the host's highest-effort / longest-context setting for implementers.
2. **Review — 6 parallel adversarial lenses** on `git diff <base>...HEAD`,
   schema-forced findings (`file`, `line`, `severity`, `detail`). Pick lenses
   for **this project's failure modes**. Examples:
   - **Domain integrity** (conservation, invariants, oscillation)
   - **Durability & recovery** (crash mid-flight, idempotent resume)
   - **Fail-closed gates** (caps, permissions, untouchable state)
   - **Flag discipline** (default off, parity when off)
   - **Concurrency** (leases, races, hot-path blocking)
   - **Repo standards & test honesty** (tautologies, missing regressions)
3. **Verify — 3-refuter panel** per deduped finding. Kill a finding only if
   **≥2** refuters disprove it. On high-stakes paths, **fail toward fixing**.
4. **Fix → Gate loop** (max 3 rounds). Gate agent runs **this repo's CI parity**
   commands and reports structured `green: true|false` with raw output excerpts.
   Minimum pattern (adapt to stack):
   - Fast test slice that mirrors CI (**not** unit-only if CI is broader)
   - Slow/e2e at least `--collect-only` or project's smoke equivalent
   - Lint, format, typecheck
   - Security/static scan if CI runs one
   - `git status --porcelain` clean
   **`green=true` only if all configured gates pass.** Gate agent must never
   claim green on a failure.
5. **Docs lane** (after green) — per project convention: module docs, plan/sprint
   doc, canonical state doc, doc-site strict build if applicable.

## Phase 2 — Orchestrator lands it (never skip)

1. **Independent verification** — orchestrator re-runs touched tests and parity
   tests; do not trust delegated self-report.
2. **High-stakes seam read** — orchestrator personally reads every irreversible
   seam: abort paths, exactly-once semantics, recovery that never double-applies,
   non-blocking contracts on hot paths. For domain-specific risk (e.g. money),
   add an **executability check**: each real-world effect verified against the
   environment where it runs (not a stand-in).
3. **Simplify pass** — **before push/PR** so branch tip is final SHA. Four
   parallel report-only angles (reuse, simplification, efficiency, altitude).
   Hard carve-out: **deliberate guards are not "simplification"** (double gates,
   leases, fail-closed recovery, deterministic ids). Dedupe findings; one surgical
   fixer applies survivors; re-verify; one follow-up commit.
4. **Push + PR** under the project's **merge gate** (CI green on FINAL SHA +
   human approval / checklist / domain sign-off as required).
5. **Memory + anchor** — record verdicts, skips, rollout plan in the project's
   task-memory system before any production flip.

## Hard rules

- Delegated seats: strongest reasoning tier available for that seat; document model
  in task memory if the host allows choice.
- Prompts: absolute paths + branch name (self-recovery fallback).
- Stages: schema-forced interface contracts, not prose handoffs.
- Reviewers: explicit **do-not-flag** list for intentional redundancy (guards).
- Risky rollouts: staged arming (plan → probe → arm → master gate), never
  big-bang enable — **orchestrator-owned**, not inside the build workflow.
- Live / production validation: orchestrator, probe-first, minimal blast radius —
  never delegated as part of Phase 1.