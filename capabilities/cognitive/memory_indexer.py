import uuid
from typing import Any

from contracts.schemas.memory import (
    EpisodicMemory,
    MemoryLifecycle,
    MemoryProvenance,
    SemanticMemory,
)
from contracts.schemas.world import WorldState
from interfaces.memory.embedding import EmbeddingInterface
from storage.catalog.memory_repository import PostgresMemoryRepository

VERZA_MEMORY_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "verza.ai")

def _generate_memory_id(memory_type: str, canonical_content: str, start_time: float | None = None) -> str:
    """Generate deterministic UUIDv5 for a memory."""
    ts_str = f"{start_time:.3f}" if start_time is not None else "none"
    canonical_str = f"{memory_type}:{canonical_content}:{ts_str}"
    return str(uuid.uuid5(VERZA_MEMORY_NAMESPACE, canonical_str))

class MemoryIndexerCapability:
    """
    Parses a WorldState and extracts/indexes Episodic and Semantic memories into the MemoryRepository.
    """

    def __init__(
        self,
        repository: PostgresMemoryRepository,
        embedding_provider: EmbeddingInterface,
    ):
        self._repository = repository
        self._embedding_provider = embedding_provider

    def execute(self, world_state: WorldState, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Extract memories from world_state and persist them.
        """
        run_id = context.get("run_id") if context else None
        stage_run_id = context.get("stage_run_id") if context else None
        project_id = context.get("project_id") if context else None
        tenant_id = context.get("tenant_id") if context else None
        world_state_id = context.get("world_state_id", str(uuid.uuid4())) if context else str(uuid.uuid4())
        
        indexed_episodes = 0
        indexed_semantics = 0

        # 1. EPISODIC MEMORIES (Time-bound events and activities)
        
        # Activities
        for activity in world_state.visual.activities:
            content = f"Activity: {activity.type} involving {', '.join(activity.participants)}"
            if activity.location:
                content += f" at {activity.location}"
            
            start_t = activity.evidence.frames[0] if activity.evidence and activity.evidence.frames else 0.0
            end_t = activity.evidence.frames[-1] if activity.evidence and activity.evidence.frames else start_t
            
            memory_id = _generate_memory_id("episodic", content, start_t)
            
            prov = MemoryProvenance(
                tenant_id=tenant_id,
                project_id=project_id,
                workflow_run_id=run_id,
                stage_run_id=stage_run_id,
                world_state_id=world_state_id,
                source_entity_id=None,
                source_timestamp=start_t,
                provider=self._embedding_provider.model_name,
                model=self._embedding_provider.model_name,
                confidence=1.0,
            )
            
            embedding = self._embedding_provider.embed(content)
            
            memory = EpisodicMemory(
                id=memory_id,
                content=content,
                lifecycle=MemoryLifecycle.ACTIVE,
                embedding_model=self._embedding_provider.model_name,
                embedding_version="1.0",
                start_time=start_t,
                end_time=end_t,
                entities=activity.participants,
                provenance=prov,
                metadata={"embedding": embedding},
            )
            self._repository.save_episodic_memory(memory)
            indexed_episodes += 1

        # Events
        for event in world_state.semantic.events:
            content = f"Event: {event.type} involving {', '.join(event.participants)}. Causes: {', '.join(event.causes)}. Consequences: {', '.join(event.consequences)}"
            start_t = float(event.start) if event.start else 0.0
            end_t = float(event.end) if event.end else start_t
            
            memory_id = _generate_memory_id("episodic", content, start_t)
            
            prov = MemoryProvenance(
                tenant_id=tenant_id,
                project_id=project_id,
                workflow_run_id=run_id,
                stage_run_id=stage_run_id,
                world_state_id=world_state_id,
                source_entity_id=event.id,
                source_timestamp=start_t,
                provider=self._embedding_provider.model_name,
                model=self._embedding_provider.model_name,
                confidence=event.confidence,
            )
            
            embedding = self._embedding_provider.embed(content)
            
            memory = EpisodicMemory(
                id=memory_id,
                content=content,
                lifecycle=MemoryLifecycle.ACTIVE,
                embedding_model=self._embedding_provider.model_name,
                embedding_version="1.0",
                start_time=start_t,
                end_time=end_t,
                entities=event.participants,
                provenance=prov,
                metadata={"embedding": embedding},
            )
            self._repository.save_episodic_memory(memory)
            indexed_episodes += 1

        # 2. SEMANTIC MEMORIES (Relationships, Concepts, Persistent Intentions)
        
        # Relationships
        for edge in world_state.semantic.relationships:
            content = f"{edge.source} {edge.relation} {edge.target}"
            memory_id = _generate_memory_id("semantic", content)
            
            prov = MemoryProvenance(
                tenant_id=tenant_id,
                project_id=project_id,
                workflow_run_id=run_id,
                stage_run_id=stage_run_id,
                world_state_id=world_state_id,
                source_entity_id=edge.id,
                provider=self._embedding_provider.model_name,
                model=self._embedding_provider.model_name,
                confidence=edge.confidence,
            )
            
            embedding = self._embedding_provider.embed(content)
            
            memory_semantic = SemanticMemory(
                id=memory_id,
                content=content,
                lifecycle=MemoryLifecycle.ACTIVE,
                embedding_model=self._embedding_provider.model_name,
                embedding_version="1.0",
                fact_type="relationship",
                entities=[edge.source, edge.target],
                provenance=prov,
                metadata={"embedding": embedding, "properties": edge.properties},
            )
            self._repository.save_semantic_memory(memory_semantic)
            indexed_semantics += 1

        # Intentions
        for intent in world_state.semantic.intentions:
            content = f"{intent.actor} intends to {intent.intent} towards {intent.target}"
            memory_id = _generate_memory_id("semantic", content)
            
            prov = MemoryProvenance(
                tenant_id=tenant_id,
                project_id=project_id,
                workflow_run_id=run_id,
                stage_run_id=stage_run_id,
                world_state_id=world_state_id,
                source_entity_id=None,
                provider=self._embedding_provider.model_name,
                model=self._embedding_provider.model_name,
                confidence=intent.confidence,
            )
            
            embedding = self._embedding_provider.embed(content)
            
            memory_semantic = SemanticMemory(
                id=memory_id,
                content=content,
                lifecycle=MemoryLifecycle.ACTIVE,
                embedding_model=self._embedding_provider.model_name,
                embedding_version="1.0",
                fact_type="intention",
                entities=[x for x in [intent.actor, intent.target] if x is not None],
                provenance=prov,
                metadata={"embedding": embedding},
            )
            self._repository.save_semantic_memory(memory_semantic)
            indexed_semantics += 1

        return {"status": "success", "indexed_episodes": indexed_episodes, "indexed_semantics": indexed_semantics}
