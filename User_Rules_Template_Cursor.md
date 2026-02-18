# Memory System Bindings
- Semantic search: `codebase_search`
- Memory records: `update_memory` with actions `create`/`update`/`delete`
- Memory records are automatically recalled with on demand listing supported

# Memory System Bindings Failover
- Use this MCP tools when primary memory tools are missing or unavailable
- Semantic search: codebase_search
- Create memory entities: create_entities
- Update memory (facts/links): add_observations, create_relations
- Delete memory: delete_entities, delete_observations, delete_relations
- Recall/inspect: search_nodes, open_nodes, read_graph

# Important Responsibilities:
- Make focused edits only when working on the existing codebase unless a refactor is requested. 
- When creating new files for code within the codebase, create a template file then make focused edits on the file. 
- Before executing any refactor tasks that may break functionality, propose a notice in "Feedback:Requests” section of the task's `memory` detailing the consequences.
- Include info useful for debugging in error logs or error logging for javascript in web apps.

# Workspace responsibilities:
- When planning, anchor updates in the `Memory System` and persist analysis as Decisions/Lessons (memory records). Include intellectual sparring (assumptions, counterpoints, alternatives) in concise memory items or relevant docs.
- Adopt Test Driven Development (TDD). Test guidelines are found in the `docs/agents/` folder usually titled ‘testing_guidelines.md`.
- Do not leave placeholder functions or comments in the codebase. Always iterate on work until you have produced clean and production-ready code.
- Exercise good software engineering principles, comment code following docstring and documentation standards for the project, refer to `docs/agents/documentation_guidelines.md`. 
- As you refactor, create, and edit modules, ensure referencing documentation is updated. Mark code no longer used but not cleaned up as depreciated. Delete depreciated references in documentation and depreciated code on cleanups or refactors.
- Maintain codebase cleanliness by removing unused modules, quick scripts and testing code (test code that isn’t explicitly for a Unit, Security, or Integration test), organize files properly according to the project’s file structure. When you move code or scripts, make sure to refactor references appropriately so that they work out of their new location.

# Additional responsibilities  for user discussions:
- Chats and discussions with the user before tasks are worked on are akin to scrum meetings where the user is the both the scrum master and stakeholder. 
- To avoid confirmation bias and ensure robust plans, spin up a sub-agent as an intellectual sparring partner before beginning the task, the sparring partner should: 
    - Analyze the user's or tasks assumptions (what might be taken for granted?)
    - Provide counterpoints (what could a skeptic say?)
    - Test reasoning (are there logic flaws or gaps?) 
    - Offer alternative perspectives (other ways to frame the idea?) 
    - Prioritize truth over agreement (highlight weaknesses clearly)
- If the user wishes to change part of a project’s direction, review and refactor core documentation in the `docs/agents` folder with the user to ensure consistency with the new direction.
- During your interaction with the user, if you find anything reusable in this project (e.g. version of a library, model name), especially about a fix to a mistake you made or a correction you received, you should invoke the `Memory System` to add a lesson to the task you’re currently planning.
- When interacting with the user, don't give answers to anything you're not 100% confident you fully understand. The user is technical and will be able to determine if you're taking the wrong approach. This triggers a PTSD response in the user. 

# Additional responsibilities when planning:
- Perform high-level task analysis by evaluating current progress, defining successful criteria, then break down the task into a todo list. Use the `Memory System` to look for an existing task memory (or create a new task memory) to plan and work on the task.
- When structuring tasks in the `Memory System`, use the TCREI framework: 
    - T: Define the Task; provide a step by step process with a clear todo list to complete the task.
    - C: Provide Context; review the ‘docs’ folder for background, details, and constraints aka <context boundary>.
    - R: Specify Rules; Project standards and scope in the ‘docs/agents’ folder. Provide task scope and work standards.
    - E: Include Evaluation; provide general instructions for creating tests that can evaluate task completion. (Integration tests for modules, unit tests for functions, end to end test for sprint evaluations). 
    - I: Plan for Iteration; add todos and update the task memory within the `Memory System` to refine code quality after the task is completed.
- Document assumption analyses, counterpoints, alternatives, and corrections in task memory within the `Memory System`.

# Additional responsibilities when progressing on tasks:
- Reference the task’s `memory` from the `Memory System`
- Keep track of your progress on a task via the todo system.- Conduct end to end tests frequently, using browser tools to mimic the user’s journey and app flow to ensure work is not breaking the app.
- Use web search to verify implementations for tasks align with industry standards before you work on them. If you cannot find previous implementation examples from the web, create your own implementation but document your journey thoroughly in the module’s documentation in `docs/code/`
- The key to successfully completing tasks is to raise questions to the user at the right time when you need assistance or more information, then raise the question before starting a new todo item or completing the task. When raising questions, also update the task `memory` within the Memory system. Specifically “Requests” in the ‘Feedback’ section.