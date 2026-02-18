# Coding Standards Template

This document defines mandatory coding standards for [Project Name]. It adapts two foundational frameworks into actionable, language-agnostic rules that all source code, scripts, and tests must follow.

**Sources**:
- The Power of 10 — Rules for Developing Safety-Critical Code (Holzmann, NASA/JPL): https://web.eecs.umich.edu/~imarkov/10rules.pdf
- Clean Code summary (Martin): https://gist.github.com/wojteklu/73c6914cc446146b8b533c0988cf8d29

## Guidelines for Filling Out This Template
- Replace [Project Name] with your project's name.
- Replace [language/framework] placeholders with your stack specifics.
- Tune numeric thresholds (line limits, coverage targets) to your team's norms.
- Add domain-specific rules under "Repository-Specific Rules" for your project's unique constraints.
- Remove or adapt examples that don't apply to your chosen language.
- Reference repo structure: Store this in `/docs/agents/coding_standards.md`.

## Scope and Intent

These standards are required for all modules, scripts, and tests in this repository. The goals are:

- Keep control flow simple and predictable
- Reduce fragile over-configuration
- Improve readability and testability
- Prevent regressions in safety-critical or business-critical paths

---

## Power of 10 Adaptation

The original rules target safety-critical C code at NASA/JPL. The adaptations below preserve the intent while generalizing for [language/framework].

### 1. Simple Control Flow
Avoid recursion in runtime paths unless the language idiomatically requires it (e.g., tree traversal with guaranteed bounded depth). Avoid hidden branching, bare exception handlers, and `goto`-equivalent patterns.

**Why**: Simple control flow is easier to trace, test, and verify. Static analyzers and reviewers can reason about all paths.

### 2. Bounded Loops
Every loop must have clear progress toward termination. Long-running or polling loops must include a timeout, backoff strategy, or explicit daemon designation with a documented shutdown path.

**Why**: Unbounded loops are the most common source of hangs and resource exhaustion. Explicit bounds make failure modes visible.

### 3. Bounded Runtime Resources
Do not spawn unbounded threads, processes, or connections. Use deterministic worker pools and connection limits. Document capacity assumptions.

**Why**: Unbounded resource creation leads to unpredictable memory and CPU usage, making the system fragile under load.

### 4. Small Functions
Target <= [40–60] lines per function. Split logic when a function mixes parsing, validation, and side effects into one body. Exception: linear orchestration sequences where splitting would scatter a naturally sequential flow may exceed the limit with justification.

**Why**: Small functions are easier to name, test, review, and reuse. They force single-responsibility design.

### 5. Assertions for Invariants
Assert protocol assumptions and domain invariants at module boundaries. Validate inputs at entry points; validate outputs at integration seams. Use the language's assertion or contract mechanism.

**Why**: Assertions catch violated assumptions early, before they propagate into subtle bugs. They also serve as executable documentation.

### 6. Narrow Scope
Declare data and helpers at the smallest possible scope. Avoid mutable global or module-level state. Prefer passing dependencies explicitly over relying on ambient context.

**Why**: Narrow scope reduces the surface area for bugs, makes data flow visible, and improves testability.

### 7. Check Return Values
Validate HTTP status codes, JSON structure, RPC responses, file I/O results, and any external call return values before use. Never assume a call succeeded without checking.

**Why**: Unchecked return values are the root cause of silent corruption and cascading failures.

### 8. Avoid Dynamic and Meta Patterns
Do not use `eval`, `exec`, runtime code generation, or deep dynamic configuration indirection in critical paths. Prefer explicit, statically analyzable code.

**Why**: Dynamic patterns defeat static analysis, make debugging difficult, and introduce security risks.

### 9. Limit Indirection Depth
Keep critical paths direct and readable. Avoid chains of wrappers, decorators, or middleware layers that hide the actual behavior. If you must abstract, ensure a reader can trace from entry to effect in <= [3] hops.

**Why**: Deep indirection makes code hard to follow, debug, and profile. It hides the cost and behavior of operations.

### 10. Zero-Warning Quality Gate
Changed files must pass linting and tests with zero new warnings. Treat warnings as errors in CI. Enable all relevant compiler/linter warnings for your language.

**Why**: Warnings are early signals of real bugs. Allowing warning accumulation normalizes broken windows and hides new issues in noise.

---

## Clean Code Adaptation

The original principles (Robert C. Martin) are summarized below with project-specific guidance.

### Naming

- **Descriptive and searchable**: Use names that reveal intent and can be found with text search. Avoid abbreviations unless they are universally understood in your domain.
- **Named constants over magic values**: Replace magic literals with named constants in a dedicated constants module (e.g., `constants.[ext]`).
- **Explicit module names**: Module names should describe their contents (`chain_config`, `pricing`, `user_service`), not generic labels (`utils2`, `helpers`, `misc`).
- **Consistent conventions**: Follow the language's idiomatic casing (`snake_case` for Python, `camelCase` for JS/TS, `PascalCase` for classes, etc.).

### Functions and Modules

- **Single responsibility**: Functions should do one thing. If the description requires "and", split it.
- **Explicit inputs/outputs**: Prefer explicit parameters and return values over hidden reads from environment variables or global state in hot paths.
- **No flag arguments**: When a boolean parameter selects between two behaviors, split into two named functions instead.
- **Cohesive modules**: Keep related logic together. Pricing logic stays in pricing modules, auth logic stays in auth modules. A module should have one reason to change.

### Comments and Documentation

- **Explain intent and constraints**, not obvious mechanics. Good: "Retry 3x because the upstream API has transient 503s under load." Bad: "Increment i by 1."
- **Remove dead code**: Do not keep commented-out code or historical fragments inline. Use version control for history.
- **Keep docs in sync**: Update matching documentation in `docs/code/` and `docs/tests/` for every functional change.

### Error Handling

- **Fail loudly**: Errors should produce actionable messages with enough context to diagnose the problem without reading the source.
- **Include context in logs**: Log relevant identifiers (`user_id`, `request_id`, `endpoint`, `input_hash`) to enable debugging in production.
- **Never swallow exceptions silently**: In critical paths (transactions, I/O, authentication), every exception must be logged, re-raised, or handled with an explicit recovery strategy. Bare catch-all handlers are prohibited.

### Source Code Structure

- **Vertical density**: Related code should appear close together. Declare variables near their first use. Place helper functions near their callers.
- **Downward flow**: Public/high-level functions at the top of a module, private/implementation details below. A reader should be able to scan top-down.
- **Short lines**: Keep lines within [80–120] characters. Long lines often signal excessive nesting or expression complexity.
- **Consistent formatting**: Use the project's formatter ([tool: Prettier/Black/rustfmt]) with a shared configuration. Do not manually override formatting.

### Objects, Data Structures, and Types

- **Hide internal structure**: Expose behavior through methods, not raw data. Avoid reaching through chains of properties.
- **Prefer value objects over primitives**: When a concept has validation rules or units (email, currency amount, coordinate), wrap it in a dedicated type.
- **Small classes/modules**: Each should have a single responsibility and a small number of instance variables.

### Tests

- **One assertion per test**: Each test verifies one behavior. This makes failures immediately diagnostic.
- **Readable**: Test names describe the scenario and expected outcome. Test bodies read like specifications.
- **Fast and independent**: Tests must not depend on execution order or shared mutable state.
- **Repeatable**: Tests produce the same result regardless of environment or run count.

---

## Repository-Specific Rules

Customize this section for [Project Name]'s domain-specific constraints.

1. **Constants first**: Protocol constants and default runtime configuration belong in a dedicated constants module, not scattered across files.
2. **Environment minimization**: If a value is effectively static or derivable at runtime, keep it out of `.env`. Reserve environment variables for secrets and deployment-specific overrides.
3. **Runtime-derived configuration**: Prefer fetching configuration from authoritative runtime sources (APIs, service discovery) over hardcoding values that may drift.
4. **Single source for secrets**: Sensitive key material (API keys, mnemonics, credentials) must use one canonical environment source. Do not duplicate across multiple env vars or config files.
5. **Backward-compatible refactors**: During package consolidation or restructuring, maintain import shims and backward-compatible aliases until all tests pass and downstream consumers are updated.

---

## Code Smells to Watch For

These patterns signal degrading code quality and should be addressed during review:

| Smell | Signal | Response |
|---|---|---|
| **Rigidity** | A small change cascades through many files | Introduce abstractions at the change boundary |
| **Fragility** | Unrelated code breaks after a change | Increase test coverage, reduce coupling |
| **Immobility** | Logic cannot be reused without dragging in dependencies | Extract into standalone modules |
| **Needless Complexity** | Abstractions with no current consumers | Remove speculative generalization |
| **Needless Repetition** | Copy-pasted logic with minor variations | Extract shared function, parameterize differences |
| **Opacity** | Code requires extensive context to understand | Rename, restructure, add intent comments |

---

## Verification Checklist

Before marking a task complete:

1. Run targeted tests for changed modules
2. Run lint/format checks for changed files — zero new warnings
3. Verify no stale references remain in docs, config, or dependent modules
4. Update `docs/code/` and `docs/tests/` for any functional changes
5. Update task memory with decisions, blockers, and lessons learned

---

**Assumptions**: These standards apply to all contributors (human and AI agent). Deviations require explicit approval and a documented rationale.
**Known Tradeoffs**: Stricter rules increase verification confidence but reduce flexibility. The escape hatches noted above (e.g., function length for orchestration) are intentional pressure valves.
