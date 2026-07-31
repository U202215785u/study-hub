# Study-Hub Butler Task Card Memory Implementation Plan

**Goal:** Add a concise, memory-backed task card that can be handed from the Butler to another execution Agent.

**Architecture:** Extend the existing case context with optional memory summaries and location notes. Add runtime methods that build and persist a five-line card only after context has been recorded, then expose those methods through the existing MCP adapter.

### Task 1: Add failing runtime and MCP tests

- Create tests for a card that combines task title, user description, feature code, project-memory summary, owner file, scope, and acceptance criteria.
- Create tests that reject card generation before `record_context` and return the persisted card through MCP.
- Run the new tests and verify they fail because the new methods and tools do not yet exist.

### Task 2: Implement the runtime card builder

- Extend `record_context` with optional `memory_summary` and `location_notes` inputs.
- Add `create_task_card` and `get_task_card` to `ButlerRuntime`.
- Persist the structured card in case context, append a handoff event, and render five compact lines with “待查” for absent information.
- Run the focused tests until they pass.

### Task 3: Expose card generation through MCP

- Add `butler_create_task_card` and `butler_get_task_card` definitions and handlers.
- Preserve all existing MCP tool schemas.
- Run MCP tests and a direct runtime/MCP exercise.

### Task 4: Update the project entry guidance and verify end to end

- Instruct the Butler to create a task card after initial location when another Agent will execute the work.
- Run all backend tests, start the stdio server, generate one disposable task card, and confirm its five lines and project-memory evidence.
