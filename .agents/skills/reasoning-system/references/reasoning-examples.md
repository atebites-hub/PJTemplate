# Reasoning examples

Examples of the **reasoning system** workflow using the **`sequentialthinking`** tool for common code tasks.

---

## Example 1: New feature implementation

### Task

Implement user notification preferences API endpoint.

### Thought 1: Requirements

```
From Project Requirements Doc.md:
- Users need notification preferences per channel (email, push, in-app)
- Preferences should be granular per notification type
- Default preferences required on account creation

From App Flow Doc.md:
- User accesses settings page
- Selects notification types and channels
- Changes persist immediately (no save button)

Constraints:
- Must not expose other users' preferences
- Changes must be reflected within 5 seconds
- Support both individual and bulk preference updates
```

### Thought 2: Retrieval

```
Docs to read next:
- Server Structure Doc.md — API and validation conventions
- File Structure Doc.md — where controllers, services, repositories live
- Testing Guidelines.md — required test levels and coverage expectations
- Implementation Plan.md — current sprint task scope

Task memory:
- Recall sprint task entry for this feature (acceptance criteria, dependencies)

Codebase:
- Read existing user-settings endpoint (pattern reference)
- Locate auth middleware registration and route table
- Search for "notification" or "preferences" to avoid duplicate modules
```

### Thought 3: Design

```
From Server Structure Doc.md:
- Follow REST conventions for API endpoints
- Use repository pattern for data access
- Validate at controller level

From File Structure Doc.md:
- Controller: /src/api/controllers/notification-preferences.controller.ts
- Service: /src/services/notification-preferences.service.ts
- Repository: /src/repositories/notification-preferences.repository.ts
- Types: /src/types/notification-preferences.types.ts

Existing patterns:
- Similar to user-settings endpoint (reference implementation)
- Same authentication middleware as other account endpoints
```

### Thought 4: Implementation

```
1. Define types in notification-preferences.types.ts
2. Create repository with CRUD operations
3. Implement service layer with business logic and defaults for new accounts
4. Add controller with validation
5. Register routes

Breaking or sensitive areas:
- Authz must match user-settings (only self-access)
```

### Thought 5: Testing and decision

```
Risks and edge cases → tests/checks:
- Concurrent updates / conflicts → unit or integration test with optimistic locking (version field); assert failure modes
- Large bulk reads → pagination tests or contract test for response size limits
- Invalid preference combinations → schema validation tests at service layer
- New user with no rows → default creation path covered by unit test
- Deprecated notification types in DB → migration-safe read path tested

Regression:
- Existing user-settings and auth flows still pass integration suite

Counterpoint:
- Could skip optimistic locking initially; rejected — conflict risk is explicit in requirements for concurrent settings.

Final approach:
- Implement with optimistic locking, strict types, auth middleware parity with user-settings, unit + integration tests as above; E2E for settings flow per Testing Guidelines.md

Documentation to update:
- /docs/api/notification-preferences.md (new)
- /docs/code/notification-preferences.md (new)
```

---

## Example 2: Refactoring

### Task

Refactor user authentication module to use dependency injection.

### Thought 1: Requirements

```
From Coding Standards.md:
- Prefer dependency injection for testability
- Single responsibility principle
- Clear separation of concerns

Current issues:
- Hard-coded dependencies make testing difficult
- Multiple responsibilities in AuthService class
- Tight coupling to database implementation
```

### Thought 2: Retrieval

```
Docs:
- Server Structure Doc.md — IoC or module conventions
- File Structure Doc.md — auth module layout
- Testing Guidelines.md — how refactors must preserve coverage

Memory:
- Task memory for this refactor (consumers of AuthService listed if available)

Code:
- List all AuthService instantiation sites (grep constructor / new AuthService)
- Read payment module (DI reference mentioned in codebase lore)
- Map current test files that mock AuthService
```

### Thought 3: Design

```
From Server Structure Doc.md:
- Use IoC container for dependency management
- Interfaces for all external dependencies
- Factory pattern for complex object creation

From File Structure Doc.md:
- /src/auth/interfaces/ — auth-related interfaces
- /src/auth/services/ — auth service implementations
- /src/auth/containers/ — IoC configuration

Existing patterns:
- Other modules already use DI
- Payment module as concrete reference
```

### Thought 4: Implementation

```
1. Extract interfaces for dependencies
2. Create factory functions for service creation
3. Refactor AuthService to accept dependencies via constructor
4. Configure IoC container
5. Update all consumers found in retrieval

Breaking changes:
- AuthService constructor signature changes — every instantiation point must be updated
```

### Thought 5: Testing and decision

```
Regression risks → tests:
- Any missed consumer → compile-time + integration test suite covering login, token refresh, protected routes
- DI mis-wiring → container bootstrap test or smoke test that resolves AuthService
- Performance regression → optional benchmark only if Server Structure or task requires it; default: run existing perf-sensitive tests if any

Edge cases:
- Circular dependencies → covered by container resolution test and lazy loading where needed

Counterpoint:
- Feature flag dual path — only if rollout is risky; else single cut with full test green.

Final approach:
- Mechanical refactor with interfaces first, then container, then consumers; no merge until auth integration tests and consumer tests pass; deprecate old entry points only after callers migrated

Rollback:
- Keep previous commit revert-friendly; avoid long-lived dual implementation unless policy requires it
```

---

## Example 3: Bug fix

### Task

Fix race condition in order processing.

### Thought 1: Requirements

```
From Testing Guidelines.md:
- Reproduce bug with a test case first
- Add a regression test that fails before fix and passes after

Bug description:
- Multiple concurrent requests can process same order twice
- Results in duplicate charges

From Server Structure Doc.md:
- Orders use optimistic locking
- Transactions should be atomic
```

### Thought 2: Retrieval

```
Docs:
- Tech Stack Doc.md — Redis, DB locking, transaction APIs
- Testing Guidelines.md — concurrency or integration test patterns

Code:
- Read order processing handler and status transition code
- Find existing lock or transaction utilities in repo
- Locate prior race-related tests as templates
```

### Thought 3: Design

```
Current implementation:
- Order status check before processing
- Status update after processing
- Gap between check and update allows race

From Tech Stack Doc.md:
- Database supports row-level locking
- Redis available for distributed locks

Chosen direction:
- Distributed lock keyed by order ID before processing branch
```

### Thought 4: Implementation

```
1. Acquire Redis lock with order ID (with TTL)
2. Re-check and update order status inside critical section / transaction as appropriate
3. Process order
4. Release lock in finally (or equivalent) so failures do not leak locks

Fallback if Redis unavailable:
- Document and implement DB-side lock or advisory lock per Server Structure Doc.md
```

### Thought 5: Testing and decision

```
Tests mapping risks:
- Duplicate processing under concurrency → integration test with parallel requests on same order ID; assert single charge
- Lock not released on failure → test exception path; assert lock TTL or explicit release
- Lock ordering / deadlock → if multiple locks exist, add test with fixed acquisition order or simplify to single lock
- Redis down → test fallback path or graceful failure per product rules

Regression:
- Happy-path order processing still passes; no added latency beyond acceptable threshold (measure if SLO exists)

Final decision:
- Implement Redis lock + try/finally + TTL; add concurrent integration test as regression; add fallback test only if fallback is in scope for this task
```
