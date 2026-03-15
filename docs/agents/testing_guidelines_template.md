# Testing Guidelines Template

This document defines testing strategy and test-quality standards for [Project Name]. Tests are the executable safety net for refactoring, deployment confidence, and regression prevention.

## Guidelines for Filling Out This Template
- Replace [Project Name] with your project's name.
- Select frameworks and tools that match your language and CI/CD.
- Set explicit coverage and reliability thresholds.
- Define required checks for local development and CI.
- Keep this file as the source of truth for test architecture and test-code quality.
- Reference repo structure: Store this in `/docs/agents/testing_guidelines.md`.

## Document Ownership and Overlap Rules

To keep standards clear:
- This document owns:
  - Test strategy (unit/integration/e2e/security/performance)
  - Test-code quality conventions
  - Test execution and CI gating
- `coding_standards.md` owns production-code behavior standards.
- `documentation_guidelines.md` owns `/docs/tests/` maintenance and documentation policy.
- `AGENTS.md` owns project-level completion gates.

If overlap appears, keep normative testing detail here and cross-reference elsewhere.

## Test Types and Recommended Tools

### Unit Tests (`/tests/unit/`)
Validate isolated functions/modules.
- JavaScript/TypeScript: Jest + Testing Library
- Python: pytest + pytest-cov
- Rust: built-in `cargo test`

### Integration Tests (`/tests/integration/`)
Validate component interactions and data flow.
- API testing: Supertest (Node.js), requests (Python), reqwest (Rust)
- Data stores/dependencies: Testcontainers or equivalent isolated services

### End-to-End Tests (`/tests/e2e/`)
Validate complete user journeys and system behavior.
- Web: Playwright or Cypress
- Mobile: Detox or Appium

### Security Tests (`/tests/security/`)
Identify vulnerabilities and unsafe defaults.
- Static checks: ESLint plugin security, bandit, cargo-audit
- Dependency checks: npm audit, safety/pip-audit, cargo-audit

### Performance Tests (`/tests/performance/`)
Validate latency, throughput, and memory behavior.
- Load tools: Artillery, k6, JMeter
- Profiling: Clinic.js, memory_profiler, language-native profilers

## Test-Code Quality Standards

Severity levels:
- MUST: mandatory, blocks merge
- SHOULD: expected default, deviations require rationale
- MAY: optional guidance

### TEST-Q-01 One behavior per test (SHOULD)
Each test should validate one behavior. Multiple assertions are acceptable when they validate one coherent outcome.

### TEST-Q-02 Readable tests (MUST)
Test names should encode scenario and expected result. Test body should be easy to scan.

Recommended structure:
- Arrange
- Act
- Assert

### TEST-Q-03 Fast and deterministic (MUST)
Unit tests must run quickly and avoid external dependencies. Remove randomness or control it with fixed seeds.

### TEST-Q-04 Independent tests (MUST)
Tests must not depend on execution order or shared mutable state.

### TEST-Q-05 Repeatable tests (MUST)
A test should pass/fail consistently across runs and environments.

### TEST-Q-06 Explicit fixtures and teardown (SHOULD)
Use clear fixture setup and cleanup to avoid hidden coupling.

### TEST-Q-07 No test logic duplication (SHOULD)
Extract shared setup/assertion helpers when patterns repeat.

### TEST-Q-08 Verify error paths (MUST)
Every critical module should have tests for expected failure modes, retries, and timeout behavior.

## Test Design Patterns

### Unit test template
```text
test_<function>_<scenario>_<expected_result>()
Arrange: build minimal inputs and fakes
Act: call unit under test
Assert: verify behavior/output/error
```

### Integration test template
```text
test_<component_a>_to_<component_b>_<scenario>()
Arrange: start isolated dependencies
Act: execute boundary call
Assert: verify contract, data persistence, side effects
```

### E2E test template
```text
test_<user_journey>_<expected_outcome>()
Arrange: seed environment/state
Act: execute user path
Assert: verify visible outcome and key backend effect
```

## Setup and Configuration

### Installation examples
- JavaScript/TypeScript: `npm install --save-dev jest @testing-library/react playwright eslint-plugin-security`
- Python: `pip install pytest pytest-cov pytest-xdist bandit pip-audit`
- Rust: built-in cargo test tooling; add dev-dependencies in `Cargo.toml`

### Configuration examples
- Jest: `jest.config.js` with coverage thresholds and test environment
- Playwright: `playwright.config.js` with retries/timeouts
- pytest: `pytest.ini` or `pyproject.toml` with markers, discovery, and coverage

## Test Execution Policy

### Local development
- All tests: `npm run test` or `pytest` or `cargo test`
- Focused runs: `test:unit`, `test:integration`, `test:e2e`
- Coverage runs: `test:coverage` with threshold enforcement
- Watch mode for rapid feedback in active development

### CI requirements
- Required checks on every PR for changed scope
- Coverage report generation and threshold validation
- Security/dependency scans for relevant ecosystems
- Flaky test quarantine process with owner and deadline

## Enforcement and Automation

### Rule-to-tool mapping
| Area | Example tools | Gate type |
|---|---|---|
| Unit/integration execution | [tool: pytest/jest/cargo test] | Required PR checks |
| Coverage thresholds | [tool: pytest-cov/nyc/tarpaulin] | Required PR checks |
| Flaky test detection | [tool: retries + quarantine report] | Monitored, owner required |
| Security test checks | [tool: bandit/npm audit/cargo-audit] | Required for changed scope |
| E2E confidence | [tool: Playwright/Cypress] | Required for critical journeys |

### Failure triage policy
1. Reproduce locally.
2. Classify as product bug vs test bug vs infrastructure flake.
3. Fix root cause; avoid blanket retries as a permanent solution.
4. If quarantined, assign owner and removal date.

## Quality Gates

### Coverage requirements
- Unit tests: minimum [X]% line coverage
- Integration tests: all critical boundaries covered
- E2E tests: critical user journeys covered
- Security tests: zero high/critical vulnerabilities in changed scope

### Reliability requirements
- Test suite pass rate in CI: >= [X]%
- Flaky tests: <= [X]% and actively tracked
- Mean test runtime budget per PR: <= [X] minutes

## Test Maintenance Checklist

Before marking a task complete:
1. New behavior has corresponding tests.
2. Existing tests updated for changed contracts/assumptions.
3. Fixtures and snapshots reviewed for relevance.
4. `/docs/tests/` updated with new commands/scenarios as needed.
5. Known test limitations and follow-up actions documented.
