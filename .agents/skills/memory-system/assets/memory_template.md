# Task Memory Template

Use this template to create a single memory entry per task. Keep entries concise; prefer links back to code/docs when detail is long.

## Description
[Description of the task or lessons in point form]

## Related Memories
[List of related memories in point form]

## Task (TCREI)
- **Task**: [What to do]
- **Scope**: inline | open-dynamic-workflows — set during planning after harness plan mode; default inline; use open-dynamic-workflows when work needs a rerunnable multi-agent script (see open-dynamic-workflows skill + `./scripts/odw`)
- **Context**: [Reference docs/agents/ + relevant code paths]
- **Rules**: [Constraints, style, security]
- **Evaluation**: [Verifiability class (`verifiable` | `non-verifiable`); then exactly one acceptance gate as `Gate: <command/check>` (e.g. `Gate: ./scripts/test-suite.sh`) or `Gate: human review against rubric: <criteria>`; for non-trivial work, the decorrelation method (e.g. `/ce-code-review`, `ultrareview`, or a different effort tier). See the `reasoning-system` skill, thought 5.]
- **Iteration**: [add todos and update the task memory within the `Memory System` to refine code quality after the task is completed.]
- **Plan**: [Ordered implementation steps from the reasoning pass; see the `reasoning-system` skill, Step 4]

## Status
- state: pending | in_progress | completed | cancelled
- started: [timestamp]
- updated: [timestamp]
- completed: [timestamp]

## Lessons
### Background & Motivation
[Why this task matters; link to requirements]

### Key Challenges & Analysis
- Assumptions: [...]
- Counterpoints: [...]
- Alternatives: [...]
- Risks: [...]

### Feedback & Assistance
[Requests, clarifications, reviewer notes]

### Learnings
[Non-obvious insights; what to reuse next time]
