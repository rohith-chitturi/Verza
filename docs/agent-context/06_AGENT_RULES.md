# AGENT RULES

1. **Read `00_MASTER_CONTEXT.md`** before doing architectural work.
2. **Read `04_CURRENT_STATE.md`** before continuing implementation.
3. **Read `05_HANDOFF.md`** before continuing unfinished work.
4. **Never assume architecture documents equal implementation.** Always verify the actual source code (e.g., check `bootstrap/container.py` to see what is *actually* bound).
5. **Inspect source before making claims.** Do not claim a provider works unless its adapter is implemented and wired.
6. **Do not bypass provider interfaces.** Domain logic (Capabilities/Reasoners) must never import an external vendor SDK directly.
7. **Do not introduce hardcoded providers.**
8. **Do not mutate WorldState directly.**
9. **Use WorldStateDelta.** Mutations must pass through validation and consistency checks.
10. **Preserve immutability** across all cognitive models.
11. **Preserve DI boundaries.** Rely on `dependency-injector`.
12. **Preserve event-driven boundaries.** Publish to the `EventBus`, do not tightly couple components.
13. **Do not introduce distributed infrastructure prematurely.** Kafka and Temporal are out of scope until the local baseline is exhaustively verified.
14. **Do not rewrite existing architecture without approval.** The M4 execution engine (DAG, Checkpointing, Retry) is stable; extend it, do not replace it.
15. **Run tests before claiming completion.** Use `pytest`.
16. **Update implementation status** (`02_IMPLEMENTATION_STATUS.md`) after significant changes.
17. **Update handoff** (`05_HANDOFF.md`) before ending a major task.
18. **Record architectural decisions** (`03_DECISIONS.md`).
19. **Prefer incremental changes.** Focus on 1 stage/capability at a time.
20. **Never delete existing functionality without explicit approval.**
