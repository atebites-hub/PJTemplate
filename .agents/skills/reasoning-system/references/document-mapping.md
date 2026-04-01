# Document Mapping

Task-type to core document mapping for `/docs/agents/`.

## Retrieval planning (reasoning-system thought 2)

After you pick a task type below, spell out a **retrieval plan**: which of the numbered documents to open, which **task memory** entries to recall (see the memory-system skill), and which **codebase** paths, symbols, or search queries you need before design (thought 3). Step 1 in the reasoning-system skill gives candidates; thought 2 makes the list actionable.

## The 10 Core Documents

| # | Document | Purpose |
|---|----------|---------|
| 1 | `Project Requirements Doc.md` | Requirements, objectives, tech stack, features |
| 2 | `App Flow Doc.md` | User flows, data flows, state transitions |
| 3 | `Tech Stack Doc.md` | Technologies, dependencies, APIs |
| 4 | `Client Guidelines.md` | Styles, UI components, standards |
| 5 | `Server Structure Doc.md` | Server architecture, security, data management |
| 6 | `Implementation Plan.md` | Sprint breakdown with TCREI tasks |
| 7 | `File Structure Doc.md` | File organization |
| 8 | `Testing Guidelines.md` | Test types, setup, quality gates |
| 9 | `Documentation Guidelines.md` | Doc formats, policies |
| 10 | `Coding Standards.md` | Power of 10 and Clean Code standards |

---

## Task Type Mapping

### New Feature Implementation

**Primary:** 1, 2, 3, 6
**Secondary:** 4, 5, 7, 10

Focus on understanding requirements, user flows, and how the feature fits the tech stack.

### Refactoring

**Primary:** 5, 7, 10
**Secondary:** 3, 8, 9

Focus on maintaining architecture integrity and code standards.

### Bug Fix

**Primary:** 5, 8
**Secondary:** 2, 10

Focus on understanding system behavior and test coverage.

### UI/UX Changes

**Primary:** 2, 4
**Secondary:** 1, 3, 7

Focus on client guidelines and user flow integration.

### API/Backend Changes

**Primary:** 3, 5
**Secondary:** 1, 6, 8

Focus on server structure and tech stack compatibility.

### Database/Data Model Changes

**Primary:** 5, 6
**Secondary:** 2, 8, 10

Focus on data integrity and migration planning.

### Performance Optimization

**Primary:** 3, 5, 10
**Secondary:** 8

Focus on tech stack constraints and coding standards.

### Security Changes

**Primary:** 5, 10
**Secondary:** 1, 8

Focus on server architecture and secure coding practices.

---

## Document Cross-References

When reasoning about changes, consider these common dependencies:

| If modifying... | Also check... |
|-----------------|---------------|
| `App Flow Doc.md` | `Project Requirements Doc.md`, `Client Guidelines.md` |
| `Server Structure Doc.md` | `Tech Stack Doc.md`, `File Structure Doc.md` |
| `Coding Standards.md` | `Testing Guidelines.md`, `Documentation Guidelines.md` |
| `Implementation Plan.md` | All documents for sprint alignment |
