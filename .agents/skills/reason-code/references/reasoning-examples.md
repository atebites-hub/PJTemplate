# Reasoning Examples

Detailed examples of sequential thinking for common code tasks.

---

## Example 1: New Feature Implementation

### Task
Implement user notification preferences API endpoint.

### Thought 1: Requirements Analysis
```
From project_requirements_doc.md:
- Users need notification preferences per channel (email, push, in-app)
- Preferences should be granular per notification type
- Default preferences required on account creation

From app_flow_doc.md:
- User accesses settings page
- Selects notification types and channels
- Changes persist immediately (no save button)

Constraints:
- Must not expose other users' preferences
- Changes must be reflected within 5 seconds
- Support both individual and bulk preference updates
```

### Thought 2: Design Considerations
```
From server_structure_doc.md:
- Follow REST conventions for API endpoints
- Use repository pattern for data access
- Validate at controller level

From file_structure_doc.md:
- Controller: /src/api/controllers/notification-preferences.controller.ts
- Service: /src/services/notification-preferences.service.ts
- Repository: /src/repositories/notification-preferences.repository.ts
- Types: /src/types/notification-preferences.types.ts

Existing patterns:
- Similar to user-settings endpoint (can reference)
- Uses same authentication middleware
```

### Thought 3: Implementation Approach
```
1. Define types in notification-preferences.types.ts
2. Create repository with CRUD operations
3. Implement service layer with business logic
4. Add controller with validation
5. Register routes
6. Write unit tests for service
7. Write integration tests for API

Tests needed (from testing_guidelines.md):
- Unit: preference validation logic
- Integration: API endpoint responses
- E2E: full user flow
```

### Thought 4: Risk Assessment
```
Risks:
1. Concurrent updates could cause conflicts
   Mitigation: Use optimistic locking with version field

2. Large preference objects could impact performance
   Mitigation: Implement pagination for bulk reads

3. Invalid preference combinations
   Mitigation: Add schema validation at service layer

Edge cases:
- User with no preferences (new account)
- Deprecated notification types in database
- Partial update failures
```

### Thought 5: Final Decision
```
Implementation plan:
1. Create types file with strict TypeScript definitions
2. Repository: implement with optimistic locking
3. Service: add validation and default handling
4. Controller: use existing auth middleware
5. Tests: follow 80% coverage requirement

Files to create:
- /src/api/controllers/notification-preferences.controller.ts
- /src/services/notification-preferences.service.ts
- /src/repositories/notification-preferences.repository.ts
- /src/types/notification-preferences.types.ts
- /tests/unit/notification-preferences.test.ts
- /tests/integration/notification-preferences.test.ts

Documentation to update:
- /docs/api/notification-preferences.md (new)
- /docs/code/notification-preferences.md (new)
```

---

## Example 2: Refactoring

### Task
Refactor user authentication module to use dependency injection.

### Thought 1: Requirements Analysis
```
From coding_standards.md:
- Prefer dependency injection for testability
- Single responsibility principle
- Clear separation of concerns

Current issues:
- Hard-coded dependencies make testing difficult
- Multiple responsibilities in AuthService class
- Tight coupling to database implementation
```

### Thought 2: Design Considerations
```
From server_structure_doc.md:
- Use IoC container for dependency management
- Interfaces for all external dependencies
- Factory pattern for complex object creation

From file_structure_doc.md:
- /src/auth/interfaces/ - auth-related interfaces
- /src/auth/services/ - auth service implementations
- /src/auth/containers/ - IoC configuration

Existing patterns:
- Other modules already use DI
- Can reference payment module as example
```

### Thought 3: Implementation Approach
```
1. Extract interfaces for dependencies
2. Create factory functions for service creation
3. Refactor AuthService to accept dependencies
4. Configure IoC container
5. Update all consumers
6. Add integration tests

Breaking changes:
- AuthService constructor signature changes
- Require updates to all instantiation points
```

### Thought 4: Risk Assessment
```
Risks:
1. Breaking existing functionality during refactor
   Mitigation: Comprehensive test suite before changes

2. Performance impact from DI container
   Mitigation: Benchmark before/after

3. Circular dependency issues
   Mitigation: Careful interface design, lazy loading

Rollback plan:
- Keep old implementation as deprecated
- Feature flag for gradual rollout
```

---

## Example 3: Bug Fix

### Task
Fix race condition in order processing.

### Thought 1: Requirements Analysis
```
From testing_guidelines.md:
- Reproduce bug with test case first
- Add regression test

Bug description:
- Multiple concurrent requests can process same order twice
- Results in duplicate charges

From server_structure_doc.md:
- Orders use optimistic locking
- Transactions should be atomic
```

### Thought 2: Design Considerations
```
Current implementation:
- Order status check before processing
- Status update after processing
- Gap between check and update allows race

From tech_stack_doc.md:
- Database supports row-level locking
- Redis available for distributed locks
```

### Thought 3: Implementation Approach
```
Solution: Add distributed lock before order processing

1. Acquire Redis lock with order ID
2. Check and update order status atomically
3. Process order
4. Release lock

This ensures only one process can handle an order at a time.
```

### Thought 4: Risk Assessment
```
Risks:
1. Lock not released on failure
   Mitigation: Set TTL on Redis lock, use try/finally

2. Deadlock from lock ordering
   Mitigation: Consistent lock acquisition order

3. Performance impact from locking
   Mitigation: Keep lock duration minimal

Edge cases:
- Redis unavailable (fallback to DB lock)
- Long-running processes (lock refresh)
```
