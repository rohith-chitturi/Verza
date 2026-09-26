# VERZA AI AGENT ENTRY POINT

Before making any changes:

1. Read this file.
2. Read docs/agent-context/00_MASTER_CONTEXT.md
3. Read docs/agent-context/04_CURRENT_STATE.md
4. Read docs/agent-context/05_HANDOFF.md
5. Read relevant architecture documentation.
6. Inspect actual source before modifying it.
7. Check git status and current branch.
8. Run relevant tests.

## Repository Development Rules
- **No AI assumptions:** Do not assume a component exists or is functional just because it's documented. Inspect the code.
- **Follow the architecture:** Verza is provider-agnostic, event-driven, and relies heavily on Dependency Injection and the WorldState architecture. 
- **Context Boundaries:** `AIContext` describes the computation (WorldState/Metadata); `ExecutionContext` controls the computation (Cancellation/Pausing/Progress).
- **Lifecycle Authority:** Capabilities request/observe execution control via `ExecutionContext`. The `WorkflowRuntime` remains authoritative for all lifecycle state transitions and DB persistence.
- **Persist your context:** Update `04_CURRENT_STATE.md` and `05_HANDOFF.md` before ending your turn.
- **Test everything:** Ensure the M4 runtime tests pass after modifying core components.
