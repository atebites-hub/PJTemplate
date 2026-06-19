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

**Requirement**: Sprint tasks live in `docs/agents/implementation_plan.md`. That a task memory accompanies source changes — with its reasoning fields filled — is **enforced** by `scripts/check-task-compliance.sh` (checks C1/C3) via the git pre-commit hook and CI, not by prose. See [`docs/agents/enforcement_matrix.md`](docs/agents/enforcement_matrix.md).

## Reasoning System

Structured reasoning before implementation is handled by the `reasoning-system` skill. See [.agents/skills/reasoning-system/SKILL.md](.agents/skills/reasoning-system/SKILL.md) for workflow and bindings.

**Requirement**: Use the `reasoning-system` skill before implementing features, refactoring, or making architectural decisions. Invoke after planning but before editing code. The pass must cover retrieval (docs, task memory, code to read) and testing/regression strategy, not only design.

## Agent Tooling & Integrations

This template is **tool-agnostic by default and Claude-ready by symlink**. The
canonical files are `AGENTS.md` and the `.agents/` directory; Claude Code reads
them through committed symlinks.

### How each tool reads this repo

| Source of truth | Claude Code | Codex / Cursor / Zed / Copilot / Windsurf | Gemini CLI |
| --- | --- | --- | --- |
| `AGENTS.md` | via `CLAUDE.md` → `AGENTS.md` symlink | natively | via `.gemini/settings.json` (`context.fileName`) |
| `.agents/` | via `.claude` → `.agents` symlink | `.agents/skills/` natively (Codex) | — |

- **`.claude` → `.agents`** and **`CLAUDE.md` → `AGENTS.md`** are committed
  symlinks. One source of truth, no duplicated content. (On Windows, symlinks
  need Developer Mode/admin; otherwise replace `CLAUDE.md` with a one-line
  `@AGENTS.md` import.)
- **Skills** live in `.agents/skills/<name>/SKILL.md` (Agent Skills standard:
  `name` + `description` frontmatter). Claude discovers them at
  `.claude/skills/` (via the symlink); Codex reads `.agents/skills/` directly.
  Current skills: `memory-system`, `reasoning-system`.

### Claude Code plugins (auto-enabled)

`.claude/settings.json` (= `.agents/settings.json` via the symlink) registers and
enables three marketplaces. On first launch Claude prompts each user to trust and
install them (the prompt is per-user and is skipped in headless `-p` mode — see
the manual fallback below).

| Plugin | Marketplace | What it adds |
| --- | --- | --- |
| `compound-engineering` | `EveryInc/compound-engineering-plugin` | "Compound engineering" workflow: planning/review-heavy skills (`/ce-plan`, `/ce-code-review`, `/ce-debug`, …) + review/research subagents. Run `/ce-setup` once after install. |
| `superpowers` | `obra/superpowers-marketplace` | Core skills library (TDD, systematic debugging, brainstorming, writing/executing plans, code review, git worktrees). Ships a SessionStart hook. |
| `ponytail` | `DietrichGebert/ponytail` | "Lazy senior dev mode" — biases toward the simplest, smallest solution (YAGNI, stdlib-first). |

**Manual fallback** (if a plugin isn't auto-installed):

```text
/plugin marketplace add EveryInc/compound-engineering-plugin
/plugin install compound-engineering
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
/plugin marketplace add DietrichGebert/ponytail
/plugin install ponytail@ponytail
```

**Other tools.** Each plugin repo also ships Codex/Cursor adapters, e.g. Codex:
`codex plugin marketplace add EveryInc/compound-engineering-plugin`; Copilot CLI:
`/plugin marketplace add EveryInc/compound-engineering-plugin` then
`/plugin install compound-engineering@compound-engineering-plugin`.

> ⚠️ **Supply-chain note.** These plugins load third-party skills/agents/hooks
> into the agent (superpowers runs a SessionStart shell hook). They track each
> marketplace's default branch — **review and pin to a reviewed commit** before
> relying on them in a sensitive project. `ponytail` is a recently-published
> repo; vet it before trusting it. Any change to `.claude/settings.json` is
> watched by the npm-worm/persistence audit (`config/security/npm-worm-audit.json`).

### GitNexus (MCP code intelligence)

`.mcp.json` registers a version-pinned GitNexus MCP server (graph-based code
intelligence — symbol/impact/context queries). Claude auto-spawns it via `npx`
(**requires Node.js**). For other editors run `gitnexus setup` (auto-configures
Cursor, Codex, Windsurf). `.gitnexusignore` keeps secrets/build output/logs out
of the index.

> ℹ️ **License.** GitNexus is **PolyForm Noncommercial 1.0.0**. Personal, hobby,
> research, and study use is **permitted** — including using this template
> personally. Only genuinely **commercial** use (yours or a downstream cloner's)
> would need a separate license from the author.

### Supply-chain security gates

Defense-in-depth, mostly ported from a hardened sibling project. Configs in
`config/security/`, runners in `scripts/security/`:

- **`./scripts/security/supply-chain-audit.sh`** — one local gate: pip checks +
  `pip-audit`, OSV-Scanner (digest-pinned image), GuardDog malware heuristics
  (digest-pinned image), OpenGrep SAST (SHA-256-pinned binary), npm
  worm/persistence audit, Bandit, and a git submodule inventory. Reports →
  `logs/current/supply-chain/`. Frontend (npm) gates activate automatically once
  `src/client/package.json` exists.
- **CI** (`.github/workflows/ci.yml`) runs the same gates. OSV-Scanner and
  GuardDog ship **report-only** (`continue-on-error`) so the template stays
  green; promote them to blocking after curating
  `config/security/osv-scanner.toml` / `guarddog.json`. OpenGrep and the
  npm-worm/persistence audit are enforcing.
- **Pin everything**: GitHub Actions by commit SHA, scanner containers by image
  digest, the OpenGrep binary by SHA-256, Python deps by hash
  (`pip --require-hashes`). Track CVE floors with comments in `requirements*.in`.

## Development Workflow Requirements

### Before Starting Any Work

1. **Read Current State**: Identify the current sprint and task in `/docs/agents/implementation_plan.md`, then read memories in the `./docs/memories/` folder.
2. **Reference Documents**: Consult the 10 core documents for requirements, flows, and standards.
3. **Test Coverage**: Meet the line-coverage floor owned by `docs/agents/testing_guidelines.md` (template default: **80%**, measured by `--cov`). Run `./scripts/test-suite.sh` before commits.
4. **Security Review**: Run security scans (e.g., [tool: cargo-audit for Rust, ESLint-plugin-security for JS]) before completion.

### Documentation Requirements

Update documentation as you work. The first two are **enforced** by `scripts/check-task-compliance.sh` (pre-commit + CI), so they are stated here once as pointers, not duplicated mandates:

- **Memory Records** (enforced — C1/C3): persist decisions, lessons, and preferences via the `memory-system` skill in `docs/memories/`.
- **Code Documentation** (enforced — C2): for every changed `src/**` code file (e.g., `renderer.js`), create/update/delete the matching `docs/code/renderer.md` (Mermaid diagram, description, function breakdown — convention owned by `documentation_guidelines.md`).
- **Test Documentation**: update `docs/tests/` for new tests (run commands, edge cases). *(Not machine-checked — keep current by hand.)*

- **Task Completion**: Mark tasks complete in the agent todo system and persist a "Lesson: <topic>" memory; keep `docs/agents/implementation_plan.md` current by adding completed tasks to the current sprint, moving unfinished tasks plus newly emerged ones to the next sprint. If all sprints are complete, create a new sprint and add the new tasks to it.
- **Agents**: As project scope changes, review and update all docs in `/docs/agents/` to match.

## Consultation Requirements

**MANDATORY**: Consult the human user before:

1. **Working Outside Scope**: Any work not explicitly covered in the 10 reference documents.
2. **Technology Changes**: Introducing new technologies or libraries.
3. **Architecture Modifications**: Changing server structure or file organization.
4. **Sprint Deviations**: Working on tasks outside the current sprint in `docs/agents/implementation_plan.md`.
5. **Security Exceptions**: Any deviation from security requirements.
6. **Feature Additions**: Adding features not listed in requirements.

## Quality Gates

**Rule ownership (single source of truth — reference, don't restate):**

- **Coverage floor** → `docs/agents/testing_guidelines.md`.
- **Security gates** → the **Supply-chain security gates** section above.
- **Code & docstring standards** → `docs/agents/coding_standards.md` + `documentation_guidelines.md`.
- **Process artifacts** (task memory, `docs/code` mirror, recorded reasoning) → enforced by `scripts/check-task-compliance.sh`; mechanism in `docs/agents/enforcement_matrix.md`.

### Before Marking Tasks Complete

The single completion checklist is [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) — do not duplicate it here. That checklist is **documentation**; the hard gate is the pre-commit hook + CI compliance check (`scripts/check-task-compliance.sh`) plus `./scripts/test-suite.sh`.

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
