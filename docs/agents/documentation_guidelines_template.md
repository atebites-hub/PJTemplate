# Documentation Guidelines Template

This document defines documentation practices for [Project Name], ensuring maintainability, onboarding speed, and reliable agent comprehension. Documentation is a living artifact and must evolve with code.

## Guidelines for Filling Out This Template
- Replace [Project Name] with your project's name.
- Choose doc tools that integrate with your stack ([tool: JSDoc/Sphinx/rustdoc/Typedoc]).
- Configure automated documentation checks where possible.
- Define clear ownership for comments, docstrings, architecture docs, and test docs.
- Keep this document as the source of truth for comments/docstrings/doc updates.
- Reference repo structure: Store this in `/docs/agents/documentation_guidelines.md`.

## Document Ownership and Overlap Rules

To avoid duplicate standards across core docs:
- This document owns:
  - Inline comments and docstring standards
  - `/docs/code/`, `/docs/tests/`, `/docs/api/` update requirements
  - Documentation quality gates and review workflow
- `coding_standards.md` owns code behavior standards (naming, control flow, errors, security, concurrency).
- `testing_guidelines.md` owns test architecture and test execution policy.
- `AGENTS.md` owns project-level gates and process requirements.

If standards overlap, keep normative detail here and reference from other docs.

## Documentation Structure

- **/docs/agents/**: Context boundary documents (AI and human process docs)
  - Files: `project_requirements_doc.md`, `app_flow_doc.md`, `tech_stack_doc.md`, `client_guidelines.md`, `server_structure_doc.md`, `implementation_plan.md`, `file_structure_doc.md`, `testing_guidelines.md`, `coding_standards.md`, this file.
- **/docs/code/**: Per-module technical documentation
  - Include architecture diagrams, module responsibilities, contracts, and examples.
- **/docs/tests/**: Test documentation and quality notes
  - Include strategy, execution commands, fixtures, and known flake risks.
- **/docs/api/**: API contracts and integration notes
  - OpenAPI/Swagger specs, endpoint docs, versioning/deprecation notes.

## Comment and Inline Documentation Standards

### Severity model
- MUST: Required; violations block merge.
- SHOULD: Strong default; deviations require rationale.
- MAY: Optional guidance.

### Rules

#### DOC-COM-01 Intent over mechanics (MUST)
Comments explain why, constraints, and consequences - not obvious step-by-step behavior.

Example:
```text
Bad: increment i by 1
Good: advance cursor to skip protocol framing byte
```

#### DOC-COM-02 No dead commented code (MUST)
Do not keep commented-out legacy code. Delete it and rely on version history.

#### DOC-COM-03 Warning comments for high-risk behavior (SHOULD)
Add focused warnings before irreversible operations, edge-case assumptions, or non-obvious side effects.

#### DOC-COM-04 Keep comments synchronized with code (MUST)
If code behavior changes, update nearby comments in the same change.

#### DOC-COM-05 Use structured TODOs (SHOULD)
When temporary notes are necessary, include owner/context and expected cleanup condition.

Template:
```text
TODO([owner], [date or issue]): [action to remove debt]
```

## Docstring Standards

Use language-specific standards integrated with tooling.

### JavaScript/TypeScript (JSDoc)
```javascript
/**
 * [What this function does and key constraint]
 * @param {type} param - Parameter description and units if relevant
 * @returns {type} Return value and invariants
 * @throws {ErrorType} Failure conditions
 * @example
 * const result = functionName(input);
 */
function functionName(param) {
  // Implementation
}
```

### Python (Google style)
```python
def function_name(param: type) -> return_type:
    """[Brief purpose and key constraints]

    Args:
        param: Description, expected range/shape, and units when relevant.

    Returns:
        Description of output invariants.

    Raises:
        ErrorType: Conditions under which this is raised.

    Example:
        >>> result = function_name(input)
    """
    # Implementation
```

## Module Documentation Template (`/docs/code/[module].md`)

Each module document SHOULD include:
1. Purpose and scope
2. Key entry points and contracts
3. Mermaid architecture/data-flow diagram
4. Dependencies and side effects
5. Error handling behavior
6. Test coverage mapping and execution commands
7. Known assumptions and limitations

## Documentation Update Triggers

Update docs in the same PR/change when:
- Public module behavior changes
- Interfaces/contracts/schemas change
- Error semantics or retry behavior changes
- Config keys, env vars, or defaults change
- Test strategy or fixture assumptions change

## Cross-Document Synchronization Rules

When updating one area, verify coupled docs:
- Code behavior changed -> update `coding_standards.md` only if policy changed, not implementation.
- Test behavior/process changed -> update `testing_guidelines.md` and `/docs/tests/*`.
- Documentation policy changed -> update this file and any affected checklist references.

## Automation and Tooling

Suggested checks:
- Broken links: [tool: markdown-link-check / lychee]
- Markdown linting: [tool: markdownlint]
- API spec validation: [tool: spectral/openapi-cli]
- Doc freshness check: custom script that flags changed modules without matching `/docs/code/` updates

## Quality Gates

### Documentation completeness
- [X]% of public modules have corresponding `/docs/code/` documents.
- API-facing components have current `/docs/api/` specs.

### Documentation freshness
- Documentation updates are merged with functional code changes (no delayed doc debt).

### Documentation accuracy
- No broken links, stale commands, or outdated interfaces.

### Comment quality
- No dead code comments.
- No misleading or obsolete inline comments.

## Review Checklist

Before marking a task complete:
1. Inline comments match current behavior.
2. Docstrings exist for public APIs and capture params/returns/errors.
3. `/docs/code/` and `/docs/tests/` updated for changed modules/tests.
4. `/docs/api/` updated if contracts changed.
5. Assumptions, caveats, and migration notes are explicit.
