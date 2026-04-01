# Coding Standards Template

This document defines mandatory coding standards for [Project Name]. It adapts two foundational frameworks into actionable, language-agnostic rules that all source code, scripts, and tests must follow.

**Sources**:
- The Power of 10 — Rules for Developing Safety-Critical Code (Holzmann, NASA/JPL): https://web.eecs.umich.edu/~imarkov/10rules.pdf
- Clean Code summary (Martin): https://gist.github.com/wojteklu/73c6914cc446146b8b533c0988cf8d29

## Guidelines for Filling Out This Template

- Replace `[Project Name]` with your project's name.
- Replace `[language/framework]` and `[tool:*]` placeholders with your stack specifics.
- Tune numeric thresholds (line limits, coverage, complexity budgets) to your team's norms.
- Add domain-specific constraints under "Repository-Specific Rules."
- Keep this document focused on code-level behavior. Move process, test, and documentation maintenance details to the dedicated docs linked in "Document Ownership and Boundaries."
- Reference repo structure: store the filled copy as `/docs/agents/coding_standards.md`.

## Document Ownership and Boundaries

To avoid overlap with other core documents:

- This document owns **code-level** standards: control flow, function design, naming, error handling, security coding, concurrency coding, and code smells.
- `documentation_guidelines.md` owns comment, docstring, and documentation maintenance standards.
- `testing_guidelines.md` owns test strategy, test architecture, and test-code quality standards.
- `AGENTS.md` owns project-level quality gates, workflow requirements, and consultation boundaries.

If content overlaps, keep the normative rule in one place and cross-reference from others.

**Related standards**: For comments, docstrings, and keeping `docs/code/` / `docs/tests/` in sync, follow `documentation_guidelines.md`. For how to write and organize tests, follow `testing_guidelines.md`.

## Scope and Intent

These standards apply to all modules, scripts, and tests in this repository. Goals:

- Keep control flow simple and predictable
- Reduce fragile over-configuration
- Improve readability and testability
- Prevent regressions in safety-critical or business-critical paths

---

## General engineering habits

- **Follow conventions**: Use language and framework conventions unless the team standard explicitly overrides them. **Why**: Consistency lowers cognitive load and matches ecosystem tooling expectations.
- **Keep it simple**: Prefer simpler designs over clever abstractions; remove unnecessary complexity before adding layers. **Why**: Simple code is easier to review, test, and change safely.
- **Leave code cleaner**: When you touch a file, improve naming, small structure, or remove dead code when practical. **Why**: Small improvements compound and prevent rot.
- **Fix root cause**: Address the underlying defect, not only the symptom; document root cause for production-impacting incidents. **Why**: Symptom fixes hide recurring failure modes.

---

## Power of 10 Adaptation

The original rules target safety-critical C code at NASA/JPL. The adaptations below preserve the intent while generalizing for `[language/framework]`.

### 1. Simple control flow

Avoid recursion in runtime paths unless depth is provably bounded (or the language idiomatically requires it, e.g. bounded tree walks). Avoid hidden branching, bare exception handlers, and `goto`-equivalent patterns.

**Why**: Simple control flow is easier to trace, test, and verify. Reviewers and analyzers can reason about all paths.

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

### 2. Bounded loops

Every loop must have clear progress toward termination. Long-running or polling loops need a timeout, backoff strategy, or explicit daemon designation with a documented shutdown path.

**Why**: Unbounded loops are a common source of hangs and resource exhaustion; explicit bounds make failure modes visible.

### 3. Bounded runtime resources and memory

Do not spawn unbounded threads, processes, or connections. Use pools, limits, and documented capacity assumptions. Avoid unbounded memory growth in hot paths; pre-size collections when bounds are known and cap queues/buffers.

**Why**: Unbounded resources make behavior unpredictable under load and complicate operations.

### 4. Small functions

Target ≤ [40–60] lines per function. Split when parsing, validation, and side effects are mixed. Exception: linear orchestration where splitting would scatter a naturally sequential flow may exceed the limit with written justification.

**Why**: Small functions are easier to name, test, review, and reuse; they encourage single-responsibility design.

### 5. Assertions for invariants

Assert protocol assumptions and domain invariants at module boundaries. Validate inputs at entry points and outputs at integration seams using the language's assertion or contract mechanisms.

**Why**: Assertions catch violated assumptions early and act as executable documentation.

### 6. Narrow scope

Declare data and helpers at the smallest practical scope. Avoid mutable global or module-level state. Prefer explicit dependency passing over ambient context.

**Why**: Narrow scope reduces bug surface, makes data flow visible, and improves testability.

### 7. Check return values and parameters

Validate HTTP status codes, JSON structure, RPC responses, file I/O results, and external call outcomes before use. Validate function and module inputs at boundaries.

**Why**: Unchecked return values cause silent corruption and cascading failures.

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

### 8. Avoid dynamic and meta patterns in critical paths

Do not use `eval`, `exec`, runtime code generation, or deep dynamic configuration indirection in critical paths. Prefer explicit, statically analyzable code.

**Why**: Dynamic patterns weaken static analysis, complicate debugging, and increase security risk.

### 9. Limit indirection depth

Keep critical paths direct. Avoid long chains of wrappers, decorators, or middleware that obscure behavior. If you abstract, a reader should trace from entry to side effect in ≤ [3] conceptual hops.

**Why**: Deep indirection hides cost and behavior and slows debugging and profiling.

### 10. Zero-warning quality gate

Changed files must pass linting and tests with zero new warnings. Treat warnings as errors in CI. Enable relevant compiler or linter warnings for your language.

**Why**: Warnings are early signals of real bugs; accumulated warning noise hides new issues.

---

## Clean Code Adaptation

Principles from Robert C. Martin, adapted for this project.

### Naming

- **Descriptive and searchable**: Names should reveal intent and be findable with text search. Avoid abbreviations unless they are universally understood in your domain.
- **Named constants over magic values**: Replace repeated literals with named constants in a dedicated module (e.g. `constants.[ext]`).
- **Explicit module names**: Names should describe behavior (`chain_config`, `pricing`, `user_service`), not generic labels (`utils2`, `helpers`, `misc`).
- **Consistent conventions**: Follow idiomatic casing for your language (e.g. `snake_case` / `camelCase` / `PascalCase` for classes).

Example:

```text
Bad: nfee, cfg2, doStuff()
Good: native_tx_fee_base, pricing_config, calculate_quote()
```

### Design and architecture

- **Configurable data at high levels**: Compose configuration near application boundaries; keep core logic explicit and minimally configurable. **Why**: Prevents hidden behavior and "magic" defaults deep in the stack.
- **Polymorphism or strategy over branch explosion**: When behavior varies by type or state, prefer clear strategies or interfaces over huge `if`/`switch` chains. **Why**: Extensibility and testing improve when variation is explicit.
- **Separate concurrency from business logic**: Isolate thread/async coordination; keep synchronization and cancellation explicit (see also "Concurrency and async standards"). **Why**: Mixed concerns are hard to reason about and test.
- **Avoid over-configurability**: Do not expose every behavior as configuration; add configuration only for validated use cases. **Why**: Too many knobs increase failure modes and support burden.
- **Explicit dependency injection**: Pass collaborators in rather than constructing hidden dependencies deep in internals. **Why**: Makes dependencies visible and replaceable in tests.
- **Law of Demeter**: Interact with direct collaborators, not long chains of nested internals. **Why**: Reduces coupling and brittle refactors.

### Understandability

- **Consistency**: Apply similar patterns across modules. **Why**: Readers build a mental model once.
- **Explanatory variables**: Use intermediate names to clarify complex expressions. **Why**: Conditionals and formulas become self-documenting.
- **Encapsulate boundary conditions**: Centralize range and edge-case logic instead of scattering checks. **Why**: One place to fix and test edge behavior.
- **Value objects over primitives**: When units, identifiers, or validation matter, use dedicated types. **Why**: Prevents category errors at compile or validation time.
- **Avoid logical dependency**: Do not make correctness depend on implicit side effects from unrelated calls. **Why**: Order-dependent bugs are hard to reproduce.
- **Prefer positive conditionals**: When it reads naturally, use positive conditions.

Example:

```text
Bad: if not is_invalid_user:
Good: if is_valid_user:
```

### Functions and modules

- **Single responsibility**: If the description needs "and", split the function. **Why**: One reason to change, one clear test story.
- **Explicit inputs and outputs**: Prefer parameters and return values over hidden environment or global reads in hot paths. **Why**: Data flow stays visible and testable.
- **Avoid flag arguments for behavior modes**: Split into named functions (e.g. `send_standard_notification` vs `send_urgent_notification`). **Why**: Call sites document intent; boolean parameters hide branches.

Example:

```text
Bad: send_notification(user, is_urgent=True)
Good: send_standard_notification(user) / send_urgent_notification(user)
```

- **Cohesive modules**: Keep related logic together; a module should have one primary reason to change. **Why**: Changes stay localized.

### Error handling

- **Fail loudly and actionably**: Errors should carry enough context to debug without stepping through source. **Why**: Production incidents need fast diagnosis.
- **Structured context in logs**: Include identifiers such as `request_id`, `user_id`, `endpoint`, `correlation_id`, and key parameters. **Why**: Correlates distributed failures.
- **No silent swallowing**: Catch-all handlers must log, re-raise, or apply explicit recovery—never empty `except` or equivalent. **Why**: Silent failures mask data loss and security issues.

### Source code structure

- **Vertical density**: Keep related code close; declare variables near first use; place helpers near callers. **Why**: Readers see complete stories without jumping.
- **Downward flow**: Public or high-level flow at the top of a module, implementation details below. **Why**: Top-down reading matches how people navigate code.
- **Line length and formatting**: Use the project formatter (`[tool: Prettier/Black/rustfmt]`) and shared config; target [80–120] characters unless a longer line clearly improves readability. **Why**: Consistent formatting removes style debates and improves diffs.

### Objects, data structures, and types

- **Hide internals**: Expose behavior through stable interfaces; avoid leaking mutable internals. **Why**: Encapsulation preserves invariants.
- **Avoid hybrid object/data ambiguity**: Prefer clear objects with behavior or clear data containers; avoid half-and-half designs. **Why**: Ambiguous types confuse callers about contracts.
- **Small classes and modules**: Limit responsibilities and instance state. **Why**: Easier to test and reason about lifecycles.

---

## Security standards

- **Input validation at trust boundaries**: Validate and normalize external input before use. **Why**: Most injection and logic bugs start at untrusted boundaries.
- **Safe output handling**: Encode or escape output for its target context (HTML, SQL, shell, logs). **Why**: Prevents injection and data leakage in the wrong channel.
- **Secrets**: Never hardcode secrets; use approved stores and patterns; redact secrets in logs and errors. **Why**: Credential leaks are high-impact and hard to revoke everywhere.
- **Unsafe deserialization and execution**: Do not deserialize untrusted payloads into rich object graphs without strict allowlists. **Why**: Remote code execution and gadget chains are common failure modes.
- **Least privilege**: Grant minimal runtime permissions and credentials per component. **Why**: Limits blast radius when something is compromised.

---

## Concurrency and async standards

- **Bounded concurrency**: Use bounded pools or semaphores; document max in-flight work and queue limits. **Why**: Prevents resource exhaustion under spikes.
- **Minimize shared mutable state**: Prefer immutable messages and clear ownership transfer. **Why**: Reduces races and deadlocks.
- **Timeouts and cancellation**: All network, IPC, and async waits need explicit timeouts and cancellation semantics. **Why**: Hung work ties up resources and obscures failures.
- **Idempotent retries with backoff**: Retry only safe operations; use jittered backoff and max attempts. **Why**: Prevents retry storms and duplicate side effects.

---

## Repository-specific rules (customize for [Project Name])

Use this section for domain-specific standards. Keep each rule testable and auditable.

**Suggested categories**:

1. Constants and config policy (where constants live, what belongs in env)
2. Data contract policy (schema versioning, backward compatibility)
3. External integration policy (timeouts, retry budgets, circuit breakers)
4. Secret and key handling (canonical source, rotation expectations)
5. Refactor compatibility (deprecation windows, shims)

**Template per rule**:

- RULE-[ID]: [Clear requirement]
- Rationale: [Why this exists]
- Verification: [How to validate in CI or review]

**Example starter rules** (replace or extend for your domain):

1. **Constants first**: Protocol constants and default runtime configuration live in a dedicated constants module, not scattered across files.
2. **Environment minimization**: If a value is static or derivable at runtime, keep it out of `.env`. Reserve environment variables for secrets and deployment-specific overrides.
3. **Runtime-derived configuration**: Prefer authoritative runtime sources (APIs, service discovery) over hardcoded values that may drift.
4. **Single source for secrets**: Sensitive material uses one canonical environment or secret-store path; do not duplicate across env vars or config files.
5. **Backward-compatible refactors**: During consolidation, maintain import shims and compatible aliases until tests pass and downstream consumers are updated.

---

## Code smells to watch for

These patterns signal degrading code quality and should trigger refactoring discussion:

| Smell | Signal | Suggested response |
|---|---|---|
| Rigidity | Small change cascades broadly | Refactor at the change boundary; reduce coupling |
| Fragility | Unrelated behavior breaks often | Add characterization tests; isolate side effects |
| Immobility | Reuse is expensive due to dependencies | Extract stable module interfaces |
| Needless complexity | Abstractions with no demonstrated consumer | Remove speculative layers |
| Needless repetition | Copy-paste divergence | Consolidate shared behavior |
| Opacity | Hard to explain the behavior path | Improve naming, structure, and boundary contracts |

---

## Enforcement and automation

### Rule-to-tool mapping

Map standards to automated checks:

| Area | Example tools | Gate type |
|---|---|---|
| Formatting | [tool: Prettier/Black/rustfmt] | Required pre-commit + CI |
| Lint/style | [tool: ESLint/ruff/pylint/clippy] | Required CI; warnings as errors |
| Static analysis | [tool: mypy/pyright/Sonar/CodeQL] | Required for critical modules |
| Security checks | [tool: bandit/npm audit/cargo-audit] | Required CI for changed scope |
| Complexity checks | [tool: radon/eslint complexity] | Threshold alerts + reviewer sign-off |
| Test gates | [tool: pytest/jest/cargo test] | Required CI status checks |

---

## Verification checklist

Use this before merge and before marking a task complete.

**Before merge**

1. Standards in this document satisfied, or deviations documented with rationale, risk, compensating controls, and reviewer approval (if your team uses mandatory vs. default rules).
2. Changed files pass lint, format, and static analysis with **zero new warnings**.
3. New or changed behavior covered by tests per `testing_guidelines.md`.
4. Documentation updates completed per `documentation_guidelines.md` where applicable.
5. Domain-specific repository rules verified for touched components.

**Before marking a task complete**

1. Run targeted tests for changed modules (see `testing_guidelines.md`).
2. Re-run lint/format for changed files; confirm no new warnings.
3. Validate security and concurrency expectations for changed trust boundaries and async paths.
4. Verify no stale references in docs, config, or dependent modules.
5. Update task memory with decisions, blockers, and lessons.

**Assumptions**

- Standards apply to all contributors (human and agent).
- Numeric targets (e.g. function length) are tunable by team agreement.

**Known tradeoffs**

- Stricter standards improve reliability but can slow early prototyping.
- Documented exceptions should stay rare; prefer fixing the underlying constraint when possible.
