# Scratchpad.md Template

This file serves as the central hub for task planning, progress tracking, and agent communication in [Project Name]. It evolves with the project—update sections as you plan, execute, and iterate. Agents use it for TCREI breakdowns, status updates, and feedback. Do not edit without explicit user instruction; reference AGENTS.md for rules.

## Guidelines for Filling Out This Template
- Replace [Project Name] with your project's name.
- Use this for each sprint or major task—create a dated version if needed (e.g., scratchpad_sprint1.md).
- **Background and Motivation**: Summarize user request and why it matters (1-2 paras).
- **Key Challenges and Analysis**: Intellectual sparring—assumptions, counterpoints, alternatives (bullet lists).
- **High-Level Task Breakdown**: TCREI for each task (numbered; keep 5-10 tasks max).
- **Current Status / Progress Tracking**: Narrative log of what's done/pending.
- **Project Status Board**: Markdown todo list for tasks (e.g., - [ ] Task 1).
- **Agent Feedback & Assistance Requests**: Notes for iterations or user input.
- **Lessons**: Key learnings/fixes to avoid repeats.
- Reference repo structure: This lives in root/; link to /docs/agents/ for context boundaries.

## Background and Motivation
[1-2 paragraphs: Summarize the current user request or sprint goal, tying to project overview from Project Requirements Doc. E.g., "Sprint 1 focuses on canvas setup to enable basic rendering, aligning with mobile-first goals." Include why it's important (e.g., "Builds foundation for AI-generated sprites").]

## Key Challenges and Analysis
[Intellectual sparring: Bullet points on assumptions/counterpoints/alternatives.]
- **Assumptions**: [E.g., "Assumes browser supports Canvas API."]
- **Counterpoints**: [E.g., "Skeptic: What if mobile WebView lags? Alternative: Optimize with requestAnimationFrame."]
- **Alternatives**: [E.g., "Option: Use WebGL for faster rendering, but increases complexity."]
- **Risks**: [E.g., "Known issue: Touch input precision on small screens."]

## High-Level Task Breakdown
[Numbered TCREI tasks; 5-10 max, small and verifiable. E.g.,]
1. **T**: Set up canvas in index.html. **C**: From App Flow Doc's launch flow. **R**: Use full-screen CSS; no frameworks. **E**: <code><canvas id="game" width="1179" height="2556"></canvas></code>. **I**: Test on mobile; iterate if scaling off.
2. [Next task...]

## Current Status / Progress Tracking
[Narrative log: "Task 1 complete—canvas renders at 1179x2556px. Pending: Input handling. Progress: 40%." Update chronologically.]

## Project Status Board
[Markdown todo list for tasks from Breakdown.]
- [ ] Task 1: Canvas setup
- [x] Task 2: Game loop (completed 09/30/2025)
- [ ] Task 3: Asset loading

## Agent Feedback & Assistance Requests
[Notes for iterations/user input. E.g., "Task 1 feedback: Scaling works, but add assumptions check. Request: User confirm viewport dims." Add dated entries.]

## Lessons
[Bullet points on learnings/fixes. E.g., "- Lesson: Always preventDefault on keydown to avoid scrolling; fixed in input_handler.js."]