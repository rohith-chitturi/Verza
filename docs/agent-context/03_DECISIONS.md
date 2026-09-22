# ARCHITECTURE DECISIONS

**Decision 1: WorldState Immutability**
- **Why:** To maintain a deterministically auditable history of cognitive perception and reasoning.
- **Alternatives:** Mutable graph DB (rejected due to race conditions and poor rollback support).
- **Consequences:** Requires a Delta journal and Merger component to apply updates safely.
- **Date:** Initial Architecture
- **Status:** Implemented

**Decision 2: Provider Abstraction via DI**
- **Why:** To prevent vendor lock-in with LLM/VLM APIs (OpenAI, Anthropic) and permit local deployment (Whisper, Local LLM).
- **Alternatives:** Direct integration in domain layer (rejected).
- **Consequences:** Slight boilerplate overhead for defining Capabilities and injecting Providers.
- **Date:** Initial Architecture
- **Status:** Implemented

**Decision 3: Local M4 Runtime First (No Kafka/Temporal)**
- **Why:** To validate the DAG, Event, and Capability logic in a single-process deployment before scaling distributed.
- **Alternatives:** Start immediately with Temporal or Kafka (rejected as premature optimization).
- **Consequences:** Relies on `InMemoryEventBus` and multithreading in `WorkflowRuntime`.
- **Date:** Initial Architecture
- **Status:** Implemented

**Decision 4: PostgreSQL + pgvector for Storage**
- **Why:** Unified transactional and vector storage for WorldState memory, checkpoints, and graph relationships.
- **Alternatives:** Milvus/Pinecone + MongoDB (rejected due to operational complexity).
- **Consequences:** Hard dependency on Postgres.
- **Date:** Initial Architecture
- **Status:** Implemented (Schema exists via Alembic, testing relies on SQLite).
