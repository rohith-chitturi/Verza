# MASTER CONTEXT

**Project Identity:** Verza — AI Media Intelligence Platform
**Project Vision:** An OS-inspired, provider-agnostic AI platform that transforms raw media into a persistent, explainable World Model via a workflow-driven cognitive pipeline.

## Core Architectural Layers
1. **Core Runtime (M4):** A DAG-based workflow engine managing the execution lifecycle, state transitions (PENDING, RUNNING, COMPLETED), retries, resumption, and replayability.
2. **Cognitive Pipeline (M2 -> M3.1 -> M3.2):** Raw Media -> Media Understanding -> WorldState -> Interpretation -> Validation -> Merger -> Reasoning.
3. **WorldState:** The central, immutable cognitive substrate storing hierarchical representation of entities (events, shots, characters). Mutations happen exclusively via `WorldStateDelta` and validation.
4. **Provider Abstraction:** Capabilities are interface-driven and injected dynamically. No hardcoded logic to OpenAI or specific models should exist in the core domain.
5. **Event-Driven & DI:** Services are resolved via `VerzaContainer` (dependency-injector). Events are dispatched over an Event Bus (currently `InMemoryEventBus`).

## Implementation State
- **Storage/Persistence:** SQLAlchemy with Alembic migrations are implemented. Full schema including `workflow_runs`, `stage_runs`, `episodic_memory`, and `semantic_memory` (pgvector) exists.
- **M4 Workflow Engine:** Highly implemented. `WorkflowRuntime` supports DAG resolution, crash resumption, replay, and retries. However, local state machine integration is currently tested with mocks (`MockCapability`) in memory, rather than fully deployed with real capabilities end-to-end.
- **Providers:** Initial skeleton/mock providers exist (e.g. `MockVLMProvider`, `FakeSceneAnalyzer`), along with some specific real adapters (`FFmpegMetadataProvider`, `WhisperRecognizer`).
- **Events:** Implemented in memory. No distributed broker (Kafka/RabbitMQ) currently exists.

## Future Steps
The AI must focus on integrating the fully realized capabilities into the M4 runtime using real PostgreSQL storage, followed by implementing the real Cognitive Pipeline (M3.1 / M3.2) providers.

## Forbidden Regressions
- DO NOT couple domain logic directly to concrete AI providers.
- DO NOT bypass the DI container for core capabilities.
- DO NOT mutate `WorldState` directly; always yield a `WorldStateDelta`.
