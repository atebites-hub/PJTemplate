# Documentation Guidelines Template

This document details how to maintain and use documentation for [Project Name], ensuring cohesion as the project scales. Docs live in `/docs/`, updated alongside code changes. Agents must follow these rules: Reference context-boundary docs (e.g., Tech Stack) strictly; create/update docs for new code/tests; only edit with explicit user instruction. Use this as the single source for format/policy.

## Guidelines for Filling Out This Template
- Replace [Project Name] with your project's name.
- Customize structure to your tech (e.g., for Python: add Sphinx for auto-docs; for JS: JSDoc).
- Adapt docstrings to language (e.g., Python: Google/Numpy style; Rust: rustdoc).
- Tailor .md files to modules (e.g., for blockchain: add `contracts.md` with Anchor examples).
- Add sprint policy examples specific to your plan (e.g., "Update after Sprint 4").
- Reference repo structure: Store this in /docs/agents/documentation_guidelines.md; link to /file_structure.md for doc locations in /docs/.

## Repo Documentation Structure
- **/docs/agents/**: Agent resources (guidelines, context boundaries).
  - Files: project_requirements_doc.md, app_flow_doc.md, tech_stack_doc.md, frontend_guidelines.md, backend_structure_doc.md, implementation_plan.md, file_structure_doc.md, testing_guidelines.md, this file.
- **/docs/code/**: Per-module .md files with Mermaid diagrams + details.
  - Example: `renderer.md`—Mermaid ER diagram of modules, description of how it works, function breakdowns (name, location, params, returns).
- **/docs/tests/**: Test docs (what/how to test).
  - Files: unit.md, security.md, integration.md—describe test scope, run commands, edge cases.

## Format and Policy
- **Docstrings for All Functions**: Include in code files ([language: e.g., JS/Rust/Python]).
  - Description: What the function does.
  - Preconditions: Input assumptions.
  - Postconditions: Expected output/state.
  - Parameters: List with types/descriptions.
  - Returns: Type and description.
  - Example ([language: e.g., JS]):
    ```
    /**
     * Draws a sprite on the canvas.
     * Preconditions: Sprite image loaded, valid position.
     * Postconditions: Canvas updated with sprite.
     * @param {Image} sprite - The sprite image.
     * @param {number} x - X position.
     * @param {number} y - Y position.
     * @returns {void}
     */
    function drawSprite(sprite, x, y) { ... }
    ```
- **.md Files in /docs/code and /docs/tests**:
  - Start with Mermaid diagram (e.g., sequence for function flow).
  - Brief description of module.
  - Reference functions/classes by name/location, with docstring excerpts.
  - Update: New code → new .md; edits → update .md; deletions → remove .md.
- **Sprint Policy**: End each sprint with doc updates (e.g., add `battle_system.md` after Sprint 4).

Agents: Always update docs with code changes. Reference Implementation Plan for sprint alignment.