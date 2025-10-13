# AGENTS.md - Project Rules

## Memory System

This project uses a memory-aware architecture to coordinate agents and persist task context. Each task lives as a single memory item that is updated over time.

Reference template for new tasks in memories: `memory_template.md`.

Workflow:
1. At task start:
   - Look up the task in memory by ID/name. If it exists, open it and resume using its current contents.
   - If it does not exist, read the entry from `/docs/agents/implementation_plan.md`, then create a new task memory using `memory_template.md` as the structure and populate it from the plan.
   - If the task is not present in the Implementation Plan, consult the user or create a new task memory using `memory_template.md` and proceed.
   - Run a broad → scoped `codebase_search` to locate relevant modules/patterns.
2. Retrieval triggers:
   - Task start: recall domain memories; run broad → scoped `codebase_search` to locate modules/patterns.
   - On error: search the failing module/pattern; store a new Lesson if the root cause or fix is novel.
   - On decision: store a Decision with the final choice and rationale.
   - On completion: mark Status=completed; summarize Lessons; reconcile the agent todo.
3. Planning & analysis: Capture Background & Motivation, Key Challenges & Analysis, and Feedback & Assistance within the task memory; promote durable insights into Decisions/Lessons memories when appropriate.

Routine summary (for consistency with User Rules):
- Receive task → consult existing task memories → conduct semantic `codebase_search`.
- If memory found → resume work; else consult Implementation Plan to create a new task memory; if absent from plan → consult user or create the memory and proceed.
- Update task memory incrementally upon every todo during execution (Status and Lessons: Background & Motivation, Key Challenges & Analysis, Feedback & Assistance, Learnings) and manage progress via the agent todo system.
- On completion → mark todo completed and record a final Lesson.

Homogenized tools (program-level):
- **Semantic Code Search (`codebase_search`)**: Find code by meaning (not exact text). Start broad (whole repo) → re-run scoped; optionally limit to PRs.
- **Memory Records**: Persist/recall Decisions, Lessons, Preferences as short, titled notes (one concept per memory). Naming: “Decision: <area> — <final> — <rationale>”, “Lesson: <topic> — <insight/risks/next>”.
- **Agent To-Dos (`todo_write`)**: Maintain a structured list; only one `in_progress`; mark `completed` immediately when done; reconcile before/after edits.

Platform bindings (map program concepts to native tools):
- See `## Memory System Bindings` for platform specific bindings to conduct the Memory System workflow.

## Project Scope Definition

These rules define the limitations and scope for AI agents (e.g., Cursor, Claude, Cline, Kilo) working on [Project Name]. All work must align with the [Number] core documentation files in `/docs/agents/` that serve as the single source of truth for project requirements, architecture, and implementation guidelines. Agents from any tool must reference these rules as the project's global context boundary.

### Core Reference Documents

The following [Number] documents in `/docs/agents/` define your context boundary and must be referenced for all work:

1. **[Project Requirements Doc.md](mdc:docs/agents/Project Requirements Doc.md)** - Defines general requirements, high-level objectives, user flows, tech stack, and core features.
2. **[App Flow Doc.md](mdc:docs/agents/App Flow Doc.md)** - Describes user flows, data flows, and state transitions.
3. **[Tech Stack Doc.md](mdc:docs/agents/Tech Stack Doc.md)** - Describes technologies, dependencies, and APIs to be used.
4. **[Client Guidelines.md](mdc:docs/agents/Client Guidelines.md)** - Describes client styles, standards, and UI components.
5. **[Server Structure Doc.md](mdc:docs/agents/Server Structure Doc.md)** - Defines server architecture, security, and data management.
6. **[Implementation Plan.md](mdc:docs/agents/Implementation Plan.md)** - Provides breakdown into actionable sprints with TCREI task structure.
7. **[File Structure Doc.md](mdc:docs/agents/File Structure Doc.md)** - Defines how files should be organized in the project.
8. **[Testing Guidelines.md](mdc:docs/agents/Testing Guidelines.md)** - Describes test types, setup, and sprint-end checks.
9. **[Documentation Guidelines.md](mdc:docs/agents/Documentation Guidelines.md)** - Defines doc formats, policies, and maintenance.

## Guidelines for Filling Out This Template
- Replace [Project Name] with your project's name (e.g., "My API Service" or "Game App").
- Set [Number] to the count of core docs (default 9; adjust if needed).
- Customize consultation/quality gates for your domain (e.g., add "API rate limits" for server-heavy projects).
- For multi-agent use: Ensure links work across tools (e.g., mdc: for Markdown previews); test in Cursor/Claude.
- Reference repo structure: Store this as root/AGENTS.md; link to /file_structure.md for agent file impacts.
- When transforming this template repository into the user's desired repository, first consult with the user in detail their project requirements.
- For each template file being updated, iterate in detail with the user over each section, ensuring that the document matches the user's preferences.

## Development Workflow Requirements

### Before Starting Any Work

1. **Read Current State**: Identify the current sprint and task in `/docs/agents/implementation_plan.md`, then recall relevant memories using the platform’s memory tool (Cursor Memories or MCP Memory).
2. **Reference Documents**: Consult the [Number] core documents for requirements, flows, and standards.
3. **Task Structure**: Use TCREI format for all tasks (Task, Context, Rules, Examples, Iteration).
4. **Test Coverage**: Achieve 80%+ test coverage for new code; run `/scripts/test-suite.sh` before commits.
5. **Security Review**: Run security scans (e.g., [tool: cargo-audit for Rust, ESLint-plugin-security for JS]) before completion.


### Documentation Requirements

**MANDATORY**: Update documentation as you work:
- **Memory Records**: Persist decisions, lessons, and preferences using the platform’s memory tool (Cursor Memories or MCP Memory).
- **Code Documentation**: For every new/edit/deleted code file (e.g., `renderer.js`), create/update/delete the corresponding `/docs/code/renderer.md` with Mermaid diagram, description, and function breakdowns.
- **Test Documentation**: Update `/docs/tests/` (e.g., `unit.md`) for new tests, including run commands and edge cases.

**CRITICAL**: Ensure these tasks are done before marking your current objective as complete.
- **Task Completion**: Mark tasks complete in the agent todo system and persist a “Lesson: <topic>” memory; keep `/docs/agents/implementation_plan.md` current.
- **Agents**: As project scope changes, review and update all docs in `/docs/agents/` to match. Only edit with explicit user instruction.

## Consultation Requirements

**MANDATORY**: Consult the human user before:

1. **Working Outside Scope**: Any work not explicitly covered in the [Number] reference documents.
2. **Technology Changes**: Introducing new technologies or libraries.
3. **Architecture Modifications**: Changing server structure or file organization.
4. **Sprint Deviations**: Working on tasks outside current sprint in Implementation Plan.md.
5. **Security Exceptions**: Any deviation from security requirements.
6. **Feature Additions**: Adding features not listed in requirements.

## Quality Gates

### Before Marking Tasks Complete

1. **Unit Tests**: All tests pass with 80%+ coverage (run `/scripts/test-suite.sh`).
2. **Security Scan**: No high/critical vulnerabilities (e.g., [tool: cargo-audit] clean).
3. **Code Review**: Follow coding standards (e.g., docstrings with Description, Preconditions, Postconditions, Parameters, Returns).
4. **Documentation**: All code documented with proper docstrings; `/docs/code/` and `/docs/tests/` updated.
5. **Integration**: Works with existing system components.
6. **Audit Compliance**: Meets security and compliance requirements.

---

**Critical**: These rules serve as your context boundary. Performing work outside these boundaries risks breaking the project's architecture and may compromise the system. Always consult before proceeding with any work not explicitly covered in the reference documents.