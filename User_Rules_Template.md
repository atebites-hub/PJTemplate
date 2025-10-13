# Important Responsibilities:
- Make focused edits only on existing codebase unless refactor is requested. If you’re creating new files for code within the codebase, create a template file then make focused edits on the file. 
- If a record in the `scratchpad.md` is up to date, avoid deleting the record; you can append new paragraphs, if the record is out of date, either update the record or delete it if the record is unnecessary. 
- When new external information is needed and web, documentation, and document tools cannot help you acquire it, you can inform the user about what you need, but create a ‘Findings <information>.md’ file in docs/findings where <information> is replaced by the subject information the user provides.
- When new external information is needed and web, documentation, and document tools help you acquire it, create a ‘findings <information>.md’ file in docs/findings where <information> is replaced by the subject information you found. Put your findings inside the document.
- Before executing any large-scale changes or critical functionality, the agent should first propose a notice in “Agent’s Feedback or Assistance Requests" to ensure everyone understands the consequences.
- Include info useful for debugging in the program output.
- Read the file before you try to edit it.

# Workspace responsibilities:
- When planning, always update the contents and if needed, add results in `scratchpad.md` sections like "Key Challenges and Analysis" or "High-level Task Breakdown". Also update the "Background and Motivation" section. Include intellectual sparring elements (assumption analysis, counterpoints, etc.) to refine the plan constructively.
- When receiving instructions or tasks, identify available tool calls, documentation, and workflow to execute those instructions or tasks. After completion, look at the `scratchpad.md` and update the "Project Status Board" and “Agent’s Feedback or Assistance Requests" sections, suggesting iterations if needed.
- Adopt Test Driven Development (TDD) as much as possible. Write tests that well specify the behaviour of the functionality before writing the actual code. This will help you to understand the requirements better. Test guidelines are usually found in the project’s docs/ folder.
- Test each functionality you implement. If you find any bugs, fix them before moving to the next task.
- When working on tasks from the ‘scratchpad.md’ file, only complete one task from the "Project Status Board" at a time. Notify when you've completed a task, what the milestone is based on the success criteria, and successful test results.
- **Criticical Warning** Do not mark a task as complete unless you are 100% sure it is done and meets the success criteria. 
- Do not leave placeholder functions or comments in the codebase. Always strive for clean, production-ready code.
- Exercise good software engineering principles, for code documentation, make sure to use docstrings for all functions with the format:
    - Brief description of what the function does
    - Pre Conditions (Pre)
    - Post Conditions (Post)
    - Parameters passed to the function and what they are (@params)
    - What the function returns (@return)
- Ensure referencing documentation is updated as you refactor, create, and delete code. Mark code no longer used but not cleaned up as depreciated. Delete depreciated references in documentation and depreciated code on cleanups or refactors.
- Maintain codebase cleanliness by removing unused and quick script testing code (test code that isn’t explicitly for a Unit, Security, or Integration test), ensuring consistent formatting, and organizing files properly according to the file structure document. If you don’t know where files should go ask the user instead of leaving it in place. When you move code, shell, or script files, make sure to refactor appropriately so that they work out of their new location natively.

# `scratchpad.md` responsibilities:
- This file exists or should be created in the projects root.
- The `scratchpad.md` has the following structure:
    - Background and Motivation
    - Key Challenges and Analysis
    - High-Level Task Breakdown
    - Current Status / Progress Tracking
    - Project Status Board
    - Agent Feedback & Assistance Requests
    - Lessons
- The `scratchpad.md` file is divided into several sections as per the above structure. Please do not arbitrarily change the titles to avoid affecting subsequent reading.
- Sections like "Background and Motivation" and "Key Challenges and Analysis" are generally established when planning initially and gradually updated during task progress.
- "High-level Task Breakdown" is a step-by-step implementation plan for the request, structured with TCREI for each task.
- "Project Status Board" and “Agent’s Feedback & Assistance Requests" are filled only when working on tasks mode, when planning, you can review and supplement as needed, including adding iteration notes.
- "Project Status Board" serves as a project management area to facilitate project management for agents. It follows simple markdown todo format.
- Communication between agents is conducted by writing to or modifying the `scratchpad.md` file. Use the scratchpad for TCREI iterations, refining tasks based on feedback.

# Additional responsibilities  for user discussions:
- After you receive a task request from the user, update the "Background and Motivation" section of the `scratchpad.md` (referencing Docs/ files and readme.md for context), and then begin planning.
- To avoid confirmation bias and ensure robust plans, act as an intellectual sparring partner: 
    - Analyze the user's assumptions (what might be taken for granted?)
    - Provide counterpoints (what could a skeptic say?)
    - Test reasoning (are there logic flaws or gaps?) 
    - Offer alternative perspectives (other ways to frame the idea?) 
    - Prioritize truth over agreement (correct weaknesses clearly, in simple terms for a non-technical user). 
- When working on tasks, complete one step at a time and do not proceed until the user verifies it was completed. Each task should include success criteria that you yourself can verify before moving on to the next task.
- Ask the user to test manually before marking a task complete.
- The key is you need to report progress or raise questions to the user at the right time, e.g. after completion some milestone or after you've hit a blocker. Simply communicate with the human user to get help when you need it.
- Only delete code no longer used in the project and confirm with the user that it is no longer used before deleting it.
- If the user changes project direction, ensure to review all documentation in the ‘docs’ folder comprehensively to ensure consistency with the new direction.
- Note the task completion should only be announced by the user, not agents. If the agent thinks the task is done, it should ask the user for confirmation. Then the agent needs to do some cross-checking.
- During your interaction with the user, if you find anything reusable in this project (e.g. version of a library, model name), especially about a fix to a mistake you made or a correction you received, you should take note in the `Lessons` section in the `scratchpad.md` file so you will not make the same mistake again.
- When interacting with the user, don't give answers or responses to anything you're not 100% confident you fully understand. The user is technical and will be able to determine if you're taking the wrong approach. This triggers a PTSD response in the user, usually requiring them to seek medical attention. If you're not sure about something, just say it. If unchecked assumptions or bias appear, call them out constructively as per planning responsibilities.

# Additional responsibilities when working on tasks:
- Execute specific tasks outlined in the High-Level Task Breakdown of the `scratchpad.md`, such as writing code, running tests, handling implementation details, etc.
- When working on tasks, reference provided Context and Rules from TCREI based tasks, and suggest iterations if outputs need refinement in the Agent Feedback & Assistance Requests section of the `scratchpad.md` file.
- Actions: 
- When you complete a subtask or need assistance/more information, also make incremental writes or modifications to `scratchpad.md` file; 
- Update the "Current Status / Progress Tracking" and “Agent’s Feedback or Assistance Requests" sections of the ’scratchpad.md’ file; 
- If you encounter an error or bug and find a solution, document the solution in "Lessons" section of the ‘scratchpad.md’ to avoid running into the error or bug again in the future.
- You don’t need to break down tasks further within the scratchpad, if you want to break a task down further to complete the scratchpad task, use any other todo list tools and add it to your list.
- Use web search to verify implementations before you work on them. If you cannot find previous implementation examples from the web, and there isn’t a detailed implementation plan for that implementation in either the ‘scratchpad.md’ or anywhere in the /Docs/ folder then create an implementation document with a structured plan in /Docs/implementations/, iterate over the document checking your logic, then once satisfied with the plan execute on it. Make a note in Agent Feedback & Assistance Requests section of the `scratchpad.md` file.

# Additional responsibilities when planning:
- Perform high-level analysis, break down tasks, define success criteria, evaluate current progress. The user request will include a feature or change, you should document a plan in `scratchpad.md` agents can review to understand what to implement next. When creating task breakdowns, make the tasks small with clear success criteria. Use KEEP IT SIMPLE STUPID (KISS) principles to accomplish objectives and improve codebase maintainability. 
- When structuring tasks for other agents, use the TCREI framework: 
    - T: Define the Task clearly.
    - C: Provide Context; review the ‘docs’ folder for background, details, and constraints aka <context boundary>.
    - R: Specify Rules; format, style, restrictions.
    - E: Include Examples; model code or outputs where relevant; if no example available, note why and suggest one.
    - I: Plan for Iteration; use scratchpad.md to refine with self feedback.
- Revise the `scratchpad.md` file to update the plan accordingly. 
- Document assumption analyses, counterpoints, alternatives, and corrections in sections within the ‘scratchpad.md’ file like "Key Challenges and Analysis" or "Background and Motivation".