# AGENTS.md - Project Rules

## Guidelines for Filling Out This Template
- Replace [Project Name] with your project's name (e.g., "My API Service" or "Game App").
- Set [Number] to the count of core docs (default 10; adjust if needed).
- Customize consultation/quality gates for your domain (e.g., add "API rate limits" for server-heavy projects).
- For multi-agent use: Ensure links work across tools (e.g., mdc: for Markdown previews); test in Cursor/Claude.
- Reference repo structure: Store this as root/AGENTS.md; link to /file_structure.md for agent file impacts.
- When transforming this template repository into the user's desired repository, first consult with the user in detail their project requirements.
- For each template file being updated, iterate in detail with the user over each section, ensuring that the document matches the user's preferences.

## Memory System

Task memory tracking is handled by the `memory-system` skill. See [.agents/skills/memory-system/SKILL.md](.agents/skills/memory-system/SKILL.md) for workflow.

**Requirement**: Every task must have a memory entry. Tasks must be sprint tasks from `docs/agents/Implementation Plan.md`.

## Reasoning System

Structured reasoning before implementation is handled by the `reasoning-system` skill. See [.agents/skills/reasoning-system/SKILL.md](.agents/skills/reasoning-system/SKILL.md) for workflow and bindings.

**Requirement**: Use the `reasoning-system` skill before implementing features, refactoring, or making architectural decisions. Invoke after planning but before editing code. The pass must cover retrieval (docs, task memory, code to read) and testing/regression strategy, not only design.

## Development Workflow Requirements

### Before Starting Any Work

1. **Read Current State**: Identify the current sprint and task in `/docs/agents/implementation_plan.md`, then read memories in the `./docs/memories/` folder.
2. **Reference Documents**: Consult the 10 core documents for requirements, flows, and standards.
3. **Test Coverage**: Achieve **100% unit test coverage of public functions** (and equivalent public surface: exported functions, public methods, public API entry points—language-dependent). Private helpers and implementation details are out of scope unless your coding standards require otherwise. Run `/scripts/test-suite.sh` before commits.
4. **Security Review**: Run security scans (e.g., [tool: cargo-audit for Rust, ESLint-plugin-security for JS]) before completion.

### Documentation Requirements

**MANDATORY**: Update documentation as you work:
- **Memory Records**: Persist decisions, lessons, and preferences using the `memory-system` skill (write to `docs/memories/`).
- **Code Documentation**: For every new/edit/deleted code file (e.g., `renderer.js`), create/update/delete the corresponding `/docs/code/renderer.md` with Mermaid diagram, description, and function breakdowns.
- **Test Documentation**: Update `/docs/tests/` (e.g., `unit.md`) for new tests, including run commands and edge cases.

**CRITICAL**: Ensure these tasks are done before marking your current objective as complete.
- **Task Completion**: Mark tasks complete in the agent todo system and persist a "Lesson: <topic>" memory; keep `/docs/agents/implementation_plan.md` current by adding additional tasks that were completd to the sprint currently being worked on, and moving tasks that were not completed as well as adding new tasks that emerged to the next sprint. If all tasks for all sprints are complete, create a new sprint and add the new tasks as discovered to it.
- **Agents**: As project scope changes, review and update all docs in `/docs/agents/` to match.

## Consultation Requirements

**MANDATORY**: Consult the human user before:

1. **Working Outside Scope**: Any work not explicitly covered in the 10 reference documents.
2. **Technology Changes**: Introducing new technologies or libraries.
3. **Architecture Modifications**: Changing server structure or file organization.
4. **Sprint Deviations**: Working on tasks outside current sprint in Implementation Plan.md.
5. **Security Exceptions**: Any deviation from security requirements.
6. **Feature Additions**: Adding features not listed in requirements.

## Quality Gates

### Before Marking Tasks Complete

1. **Unit Tests**: All tests pass; **100% coverage of public functions** (same definition as in Development Workflow). Run `/scripts/test-suite.sh`.
2. **Security Scan**: No high/critical vulnerabilities (e.g., [tool: bandit/pip-audit] clean).
3. **Code Review**: Follow coding standards (docstrings/comments with Description, Preconditions, Postconditions, Parameters, Returns).
4. **Documentation**: All code documented with proper docstrings; `/docs/code/` and `/docs/tests/` updated.
5. **Integration**: Works with existing system components.
6. **Audit Compliance**: Meets security, documentation and coding standards, and testing requirements.

## Responsibilities:

### Core Responsibilities:
- Make focused edits only when working on the existing codebase unless a refactor is requested.
- When creating new files for code within the codebase, create a template file then make focused edits on the file.
- Before executing any refactor tasks that may break functionality, propose a notice in "Feedback:Requests" section of the task's `memory` detailing the consequences.
- Include info useful for debugging in error logs or error logging for javascript in web apps.

### Workspace responsibilities:
- When planning, anchor updates using the `memory-system` skill and persist analysis as Decisions/Lessons (memory records). Include intellectual sparring (assumptions, counterpoints, alternatives) in concise memory items or relevant docs.
- Adopt Test Driven Development (TDD). Test guidelines are found in the `docs/agents/` folder usually titled 'testing_guidelines.md'.
- Do not leave placeholder functions or comments in the codebase. Always iterate on work until you have produced clean and production-ready code.
- Exercise good software engineering principles, comment code following docstring and documentation standards for the project, refer to `docs/agents/documentation_guidelines.md`.
- As you refactor, create, and edit modules, ensure referencing documentation is updated. Mark code no longer used but not cleaned up as depreciated. Delete depreciated references in documentation and depreciated code on cleanups or refactors.
- Maintain codebase cleanliness by removing unused modules, quick scripts and testing code (test code that isn't explicitly for a Unit, Security, or Integration test), organize files properly according to the project's file structure. When you move code or scripts, make sure to refactor references appropriately so that they work out of their new location.

### Responsibilities for user discussions:
- Chats and discussions with the user before tasks are worked on are akin to scrum meetings where the user is the both the scrum master and stakeholder.
- To avoid confirmation bias and ensure robust plans, act as an intellectual sparring partner before beginning the task, you should:
    - Analyze the user's or tasks assumptions (what might be taken for granted?)
    - Provide counterpoints (what could a skeptic say?)
    - Test reasoning (are there logic flaws or gaps?)
    - Offer alternative perspectives (other ways to frame the idea?)
    - Prioritize truth over agreement (highlight weaknesses clearly)
- If the user wishes to change part of a project's direction, review and refactor core documentation in the `docs/agents` folder with the user to ensure consistency with the new direction.
- During your interaction with the user, if you find anything reusable in this project (e.g. version of a library, model name), especially about a fix to a mistake you made or a correction you received, you should use the `memory-system` skill to add a lesson to the task you're currently planning.
- When interacting with the user, don't give answers to anything you're not 100% confident you fully understand. The user is technical and will be able to determine if you're taking the wrong approach.

### Responsibilities when planning:
- Perform high-level task analysis by evaluating current progress, defining successful criteria, then break down the task into a todo list. Use the `memory-system` skill to look for an existing task memory (or create a new task memory) to plan and work on the task.
- When structuring task memories, follow the `memory-system` skill and [`.agents/skills/memory-system/assets/memory_template.md`](.agents/skills/memory-system/assets/memory_template.md) (includes **Task (TCREI)** in one place).
- Document assumption analyses, counterpoints, alternatives, and corrections in task memory.

### Responsibilities when progressing on tasks:
- Reference the task's `memory` using the `memory-system` skill
- Keep track of your progress on a task via the todo system. Conduct end to end tests frequently, using browser tools to mimic the user's journey and app flow to ensure work is not breaking the app.
- Use web search to verify implementations for tasks align with industry standards before you work on them. If you cannot find previous implementation examples from the web, create your own implementation but document your journey thoroughly in the module's documentation in `docs/code/`
- The key to successfully completing tasks is to raise questions to the user at the right time when you need assistance or more information, then raise the question before starting a new todo item or completing the task. When raising questions, also update the task `memory`. Specifically "Requests" in the 'Feedback' section.
