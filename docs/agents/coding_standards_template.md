# Coding Standards Template

This document defines mandatory coding standards for [Project Name]. It adapts two foundational frameworks into actionable, language-agnostic rules that all source code, scripts, and tests must follow.

Sources:
- The Power of 10 - Rules for Developing Safety-Critical Code (Holzmann, NASA/JPL): https://web.eecs.umich.edu/~imarkov/10rules.pdf
- Clean Code summary (Martin): https://gist.github.com/wojteklu/73c6914cc446146b8b533c0988cf8d29

## Guidelines for Filling Out This Template
- Replace [Project Name] with your project's name.
- Replace [language/framework] and [tool:*] placeholders with your stack specifics.
- Tune numeric thresholds (line limits, coverage, complexity budgets) to your team's norms.
- Add domain-specific constraints in "Repository-Specific Rules."
- Keep this document focused on code-level behavior. Move process/test/doc details to the dedicated docs linked below.
- Reference repo structure: Store this in `/docs/agents/coding_standards.md`.

## Document Ownership and Boundaries

To avoid overlap with other core documents:
- This document owns code-level standards: control flow, function design, naming, error handling, security coding, concurrency coding, and code smells.
- `documentation_guidelines.md` owns comment, docstring, and documentation maintenance standards.
- `testing_guidelines.md` owns test strategy, test architecture, and test-code quality standards.
- `AGENTS.md` owns project-level quality gates, workflow requirements, and consultation boundaries.

If content overlaps, keep the normative rule in one place and cross-reference from others.

## Rule Severity and Exceptions

Use RFC-style severity labels:
- MUST: Mandatory. Violations block merge.
- SHOULD: Expected default. Deviations require written rationale.
- MAY: Optional guidance.

Exception process for MUST/SHOULD deviations:
1. Document reason and risk in the task/PR.
2. Add compensating controls (tests, runtime guardrails, monitoring).
3. Include rollback/remediation plan.
4. Obtain reviewer approval before merge.

## Scope and Intent

These standards apply to all modules, scripts, and tests in this repository. Goals:
- Keep control flow simple and predictable
- Reduce fragile over-configuration
- Improve readability and testability
- Prevent regressions in safety-critical or business-critical paths

---

## General Engineering Principles (Clean Code Foundation)

### CS-GEN-01 Follow conventions (MUST)
Use language and framework conventions unless the team standard explicitly overrides them.

### CS-GEN-02 Keep it simple (MUST)
Prefer simpler designs over clever abstractions. Eliminate unnecessary complexity before adding new layers.

### CS-GEN-03 Boy Scout rule (SHOULD)
Leave touched code cleaner than you found it (naming, small refactors, dead code removal).

### CS-GEN-04 Find root cause (MUST)
Fix the underlying defect, not only the symptom. Include root-cause notes for production-impacting incidents.

---

## Power of 10 Adaptation (Core Reliability Rules)

The original rules target safety-critical C code. These adaptations preserve intent for [language/framework].

### CS-P10-01 Simple control flow (MUST)
Avoid recursion in runtime-critical paths unless depth is provably bounded. Avoid hidden branching, bare exception handlers, and `goto`-equivalent constructs.

Example:
```text
Bad:
try:
    run_operation()
except:
    pass

Good:
try:
    run_operation()
except NetworkError as err:
    logger.error("operation failed", {"operation": "run_operation", "error": str(err)})
    raise
```

### CS-P10-02 Bounded loops (MUST)
Each loop must have explicit progress and termination criteria. Polling loops require timeout/backoff or explicit daemon designation with shutdown strategy.

### CS-P10-03 Bounded runtime resources and memory (MUST)
Do not spawn unbounded threads/processes/connections. Avoid unbounded memory growth in hot paths; pre-size collections when bounds are known and cap queues/buffers.

### CS-P10-04 Small functions (SHOULD)
Target <= [40-60] lines per function. Split mixed concerns (parse/validate/side effect). Exception: linear orchestration flows may exceed limit with written justification.

### CS-P10-05 Assertions for invariants (MUST)
Assert domain invariants at boundaries (inputs, outputs, protocol constraints, unit assumptions, id derivation).

### CS-P10-06 Narrow scope (MUST)
Declare variables and helpers at smallest practical scope. Avoid mutable globals and ambient hidden state.

### CS-P10-07 Check return values and parameters (MUST)
Validate external responses (status, schema, nullability, units) before use. Validate function/module inputs at boundaries.

Example:
```text
Bad:
response = http_get(url)
price = response.json()["price"]

Good:
response = http_get(url, timeout=5)
if response.status_code != 200:
    raise UpstreamError("price endpoint failed", {"status": response.status_code, "url": url})
payload = response.json()
if "price" not in payload:
    raise UpstreamError("price missing", {"url": url, "payload_keys": list(payload.keys())})
price = payload["price"]
```

### CS-P10-08 Avoid dynamic/meta patterns in critical paths (MUST)
Do not use `eval`, `exec`, runtime code injection, or deep dynamic config indirection in critical paths.

### CS-P10-09 Limit indirection depth (SHOULD)
Keep critical execution paths traceable in <= [3] conceptual hops from entry to side effect.

### CS-P10-10 Zero-warning quality gate (MUST)
Changed files must pass lint/static-analysis/tests with zero new warnings. Treat warnings as errors in CI.

---

## Clean Code Adaptation

### Naming Standards

#### CS-NAM-01 Descriptive and searchable names (MUST)
Use names that reveal intent and can be found by search.

#### CS-NAM-02 Named constants over magic literals (MUST)
Replace repeated literals with named constants in a dedicated constants module (e.g., `constants.[ext]`).

#### CS-NAM-03 Explicit module names (MUST)
Module/file names should reflect behavior (e.g., `auth_service`, `pricing_engine`) rather than generic buckets (`misc`, `helpers2`).

Example:
```text
Bad: nfee, cfg2, doStuff()
Good: native_tx_fee_base, pricing_config, calculate_quote()
```

### Design and Architecture Rules

#### CS-DES-01 Keep configurable data at high levels (SHOULD)
Centralize configuration composition near application boundaries. Keep core logic explicit and minimally configurable.

#### CS-DES-02 Prefer polymorphism/strategy over branch explosion (SHOULD)
When behavior varies by type/state, favor clear strategy objects/interfaces over large switch/if chains.

#### CS-DES-03 Separate concurrency code (MUST)
Isolate thread/async coordination from business logic. Keep synchronization and cancellation semantics explicit.

#### CS-DES-04 Prevent over-configurability (SHOULD)
Do not expose every behavior as configuration. Add configuration only when there is a validated use case.

#### CS-DES-05 Use explicit dependency injection (SHOULD)
Inject collaborators instead of constructing hidden dependencies in deep internals.

#### CS-DES-06 Follow Law of Demeter (SHOULD)
A module should interact with direct collaborators, not long chains of nested internals.

### Understandability Rules

#### CS-UND-01 Consistency (MUST)
Apply similar patterns consistently across modules.

#### CS-UND-02 Explanatory variables (SHOULD)
Use intermediate names to clarify complex expressions and conditions.

#### CS-UND-03 Encapsulate boundary conditions (SHOULD)
Keep range/edge-case logic in one place instead of scattering checks.

#### CS-UND-04 Value objects over primitives where meaningful (SHOULD)
Wrap units/identifiers with validation when mistakes are costly.

#### CS-UND-05 Avoid logical dependency (MUST)
Do not make a method's correctness depend on implicit side effects from unrelated calls.

#### CS-UND-06 Avoid negative conditionals when possible (SHOULD)
Prefer positive conditions that read naturally.

Example:
```text
Bad: if not is_invalid_user:
Good: if is_valid_user:
```

### Function and Module Rules

#### CS-FN-01 Single responsibility functions (MUST)
A function should do one thing. If explanation needs "and", split it.

#### CS-FN-02 Explicit inputs/outputs (MUST)
Prefer explicit parameters and returns over hidden global/environment reads in hot paths.

#### CS-FN-03 No flag arguments for behavior switching (SHOULD)
Split boolean-mode functions into named variants.

Example:
```text
Bad: send_notification(user, is_urgent=True)
Good: send_standard_notification(user) / send_urgent_notification(user)
```

#### CS-FN-04 Cohesive modules (MUST)
Group related behavior together. A module should have one primary reason to change.

### Error Handling Rules

#### CS-ERR-01 Fail loudly and actionably (MUST)
Errors must include enough context to debug without stepping through source.

#### CS-ERR-02 Structured context in logs (MUST)
Log relevant identifiers (`request_id`, `user_id`, `endpoint`, `correlation_id`, key parameters).

#### CS-ERR-03 No silent exception swallowing (MUST)
Catch-all handlers must log context and either re-raise or apply explicit recovery.

### Source Code Structure Rules

#### CS-STR-01 Vertical density (SHOULD)
Keep related code close. Declare variables near first use.

#### CS-STR-02 Downward readability (SHOULD)
Place high-level flow above lower-level details to support top-down reading.

#### CS-STR-03 Line length and formatting (MUST)
Use project formatter and keep lines within [80-120] chars unless readability clearly improves.

### Objects and Data Structure Rules

#### CS-DATA-01 Hide internals (SHOULD)
Expose behavior through stable interfaces rather than leaking mutable internals.

#### CS-DATA-02 Avoid hybrid object/data anti-patterns (SHOULD)
Prefer clear object behavior or clear data containers; avoid half-and-half ambiguity.

#### CS-DATA-03 Keep classes/modules small (SHOULD)
Limit responsibilities and instance state.

### Security Coding Standards

#### CS-SEC-01 Input validation at trust boundaries (MUST)
Validate and normalize external inputs before use.

#### CS-SEC-02 Safe output handling (MUST)
Apply output encoding/escaping appropriate to target context (HTML, SQL, shell, logs).

#### CS-SEC-03 Secrets handling (MUST)
Never hardcode secrets. Use approved secret stores/env patterns and redact secrets in logs/errors.

#### CS-SEC-04 Avoid unsafe deserialization/execution (MUST)
Do not deserialize untrusted payloads into executable/object graphs without strict allowlists.

#### CS-SEC-05 Least privilege defaults (SHOULD)
Grant minimal runtime permissions and credentials needed for each component.

### Concurrency and Async Standards

#### CS-CON-01 Bounded concurrency (MUST)
Use bounded pools/semaphores. Document max in-flight work and queue limits.

#### CS-CON-02 Shared state minimization (MUST)
Prefer immutable messages and ownership transfer over shared mutable state.

#### CS-CON-03 Timeouts and cancellation (MUST)
All network/IPC/async waits must have explicit timeout and cancellation semantics.

#### CS-CON-04 Idempotent retries and backoff (SHOULD)
Retry only safe operations with jittered backoff and max-attempt limits.

---

## Repository-Specific Rules (Customize for [Project Name])

Use this section for domain-specific standards. Keep each rule testable and auditable.

Recommended categories:
1. Constants/config policy (where constants live, what belongs in env)
2. Data contract policy (schema versioning, backward compatibility)
3. External integration policy (timeouts, retry budgets, circuit breakers)
4. Secret/key handling policy (single canonical source, rotation expectations)
5. Refactor compatibility policy (deprecation windows, adapter/shim requirements)

Template:
- RULE-[ID] [MUST/SHOULD]: [Clear requirement]
- Rationale: [Why this exists]
- Verification: [How to validate in CI/review]

---

## Code Smells to Watch For

These patterns signal degrading code quality and should trigger refactoring discussions:

| Smell | Signal | Suggested response |
|---|---|---|
| Rigidity | Small change cascades broadly | Refactor at change boundary; reduce coupling |
| Fragility | Unrelated behavior breaks frequently | Add characterization tests; isolate side effects |
| Immobility | Reuse is expensive due to dependencies | Extract stable module interfaces |
| Needless Complexity | Abstractions with no demonstrated consumer | Remove speculative layers |
| Needless Repetition | Copy-paste divergence | Consolidate shared behavior |
| Opacity | Hard to explain behavior path | Improve naming, structure, and boundary contracts |

---

## Enforcement and Automation

### Rule-to-Tool Mapping

Map standards to automated checks:

| Area | Example tools | Gate type |
|---|---|---|
| Formatting | [tool: Prettier/Black/rustfmt] | Required pre-commit + CI |
| Lint/style | [tool: ESLint/ruff/pylint/clippy] | Required CI, warnings as errors |
| Static analysis | [tool: mypy/pyright/Sonar/CodeQL] | Required for critical modules |
| Security checks | [tool: bandit/npm audit/cargo-audit] | Required CI for changed scope |
| Complexity checks | [tool: radon/eslint complexity] | Threshold alerts + reviewer sign-off |
| Test gates | [tool: pytest/jest/cargo test] | Required CI status checks |

### Pull Request Compliance Checklist

Before merge:
1. All MUST rules satisfied or approved exception documented.
2. All changed files pass lint/format/static analysis with zero new warnings.
3. New/changed behavior covered by tests per `testing_guidelines.md`.
4. Documentation updates completed per `documentation_guidelines.md`.
5. Domain-specific repository rules verified for touched components.

---

## Verification Checklist

Before marking a task complete:
1. Run targeted tests for changed modules (see `testing_guidelines.md`).
2. Run lint/format/static checks for changed files; no new warnings.
3. Validate security and concurrency requirements for changed boundaries.
4. Verify no stale references remain in docs/config/dependent modules.
5. Update task memory with decisions, blockers, and lessons.

Assumptions:
- Standards apply to all contributors (human and AI).
- Teams may tailor SHOULD thresholds per project.

Known tradeoffs:
- Stricter standards improve reliability but can slow early prototyping.
- Exception paths should stay rare and fully documented.
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
