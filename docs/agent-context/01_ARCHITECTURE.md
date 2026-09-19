# ARCHITECTURE

## Control Plane & Data Plane
- **Control Plane:** Manages workflow definitions, scheduling, capability registration, and telemetry.
- **Data Plane:** Handles execution of specific tasks (Media Extraction, Inference, Generation) and interactions with providers.

## Core M4 Workflow Runtime
Verza operates as a robust workflow orchestrator.
- **DAG Resolver:** Validates and orders stages chronologically based on dependencies.
- **Execution States:** PENDING -> QUEUED -> RUNNING -> COMPLETED / FAILED -> RETRYING.
- **Persistence:** Every execution is backed by PostgreSQL (`storage/catalog/sql_repository.py`), storing `workflow_runs` and `stage_runs`.
- **Resilience:** Built-in crash resumption and stage-level replay. Completed stages are skipped during resume.

## Cognitive Pipeline Flow
```text
Raw Media
    ↓
M2 Media Understanding
    ↓
WorldState
    ↓
M3.1 Interpretation (Scene, Character, Activity)
    ↓
WorldStateDelta
    ↓
Validation -> Consistency Checker -> Merger
    ↓
Immutable WorldState
    ↓
M3.2 Reasoning (Intent, Relationship, Event)
    ↓
InferenceProvider
    ↓
WorldStateDelta -> Validation -> Merger -> Immutable WorldState
```

## Provider Abstraction & DI
- All capabilities register through `CapabilityRegistry`.
- `bootstrap/container.py` holds the declarations for capabilities, providers, repositories, and the event bus.
- **Event Flow:** Synchronous, in-memory `InMemoryEventBus` is used currently. Future states will introduce a distributed broker.
