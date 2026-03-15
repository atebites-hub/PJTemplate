---
name: memory-system
description: Manage task memories using TCREI framework for tracking progress, decisions, and lessons. Use when planning tasks, starting work, conducting searches, receiving user feedback, or completing todos. Triggers on task lifecycle events.
---

# Memory System

Track every task with structured memories for continuity, accountability, and learning.

## Trigger Conditions

Execute this workflow when:
- **Planning**: Breaking down a new task
- **Search**: After codebase or web search
- **Task Start**: Beginning implementation
- **User Response**: Receiving feedback or clarifications
- **Completion**: Finishing a todo list or task

## Workflow

### Step 1: Retrieve or Create Memory

Check for existing task memory. If none exists, create one using the template in [assets/memory_template.md](assets/memory_template.md).

### Step 2: Update Based on Trigger

| Trigger | Sections to Update |
|---------|-------------------|
| Planning | Task, Context, Rules, Evaluation |
| Search | Analysis, Feedback, Lessons |
| Task Start | Status → `in_progress`, branch info, commit hash |
| User Response | Analysis, Feedback, Lessons |
| Completion | Status → `completed`, PR URL |

### Step 3: Persist Changes

Use MCP Docker tools to persist memory updates.

## TCREI Framework

Structure every task memory with:

- **T (Task)**: Step-by-step process with clear todo list
- **C (Context)**: Reference `docs/` folder for background and constraints
- **R (Rules)**: Project standards from `docs/agents/` folder
- **E (Evaluation)**: Instructions for test creation (unit/integration/e2e)
- **I (Iteration)**: Plan for refinement after completion

## Memory Bindings

Use MCP Docker knowledge graph tools:

| Operation | Tool |
|-----------|------|
| Create entities | `create_entities` |
| Update entities | `add_observations`, `create_relations` |
| Delete entities | `delete_entities`, `delete_observations`, `delete_relations` |
| Search/Inspect | `search_nodes`, `open_nodes`, `read_graph` |

## Task Requirements

Every task must:
1. Be a sprint task from `docs/agents/Implementation Plan.md`
2. Have a corresponding memory entry
3. Track state: `pending` | `in_progress` | `completed` | `cancelled`

## Best Practices

- **Concise entries**: Link to code/docs instead of duplicating
- **Intellectual sparring**: Include assumptions, counterpoints, alternatives
- **Lesson capture**: Document reusable insights and corrections
- **Branch tracking**: On task start, if on main branch, create feature branch and record in memory
