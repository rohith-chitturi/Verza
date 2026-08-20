from typing import Any

from contracts.schemas.memory import (
    EpisodicMemory,
    MemoryLifecycle,
    MemoryProvenance,
    SemanticMemory,
)
from contracts.schemas.world import WorldState
from core.registry.capability import BaseCapability
from interfaces.memory.embedding import EmbeddingInterface
from storage.catalog.memory_repository import PostgresMemoryRepository


class MemoryIndexerCapability(BaseCapability):
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
        # We need provenance data. Normally this would be passed in context or derived from world_state.
        run_id = context.get("run_id") if context else None
        stage_run_id = context.get("stage_run_id") if context else None
        project_id = context.get("project_id") if context else None
        tenant_id = context.get("tenant_id") if context else None
        
        # 1. Index Episodic Memories (e.g. Activities, Audio Segments)
        for activity in world_state.visual.activities:
            content = f"Activity: {activity.type} involving {', '.join(activity.participants)}"
            if activity.location:
                content += f" at {activity.location}"
                
            prov = MemoryProvenance(
                tenant_id=tenant_id,
                project_id=project_id,
                workflow_run_id=run_id,
                stage_run_id=stage_run_id,
                world_state_id=str(hash(world_state)),  # Mock ID for now
                source_entity_id=None,
                source_event_id=None,
                source_timestamp=activity.evidence.frames[0] if activity.evidence and activity.evidence.frames else 0.0,
                provider=self._embedding_provider.model_name,
                model=self._embedding_provider.model_name,
                confidence=1.0,
            )
            
            embedding = self._embedding_provider.embed(content)
            
            # Simple assumption: activities without explicit temporal bounds are point-in-time
            start_t = 0.0
            end_t = 0.0
            
            memory = EpisodicMemory(
                id=f"ep-act-{hash(content)}",
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

        # 2. Index Semantic Memories (e.g. Knowledge Graph Edges, Intentions)
        for edge in world_state.semantic.relationships:
            content = f"{edge.source} {edge.relation} {edge.target}"
            prov = MemoryProvenance(
                tenant_id=tenant_id,
                project_id=project_id,
                workflow_run_id=run_id,
                stage_run_id=stage_run_id,
                world_state_id=str(hash(world_state)),
                source_entity_id=edge.id,
                source_event_id=None,
                source_timestamp=None,
                provider=self._embedding_provider.model_name,
                model=self._embedding_provider.model_name,
                confidence=edge.confidence,
            )
            
            embedding = self._embedding_provider.embed(content)
            
            memory_semantic = SemanticMemory(
                id=f"sem-rel-{edge.id}",
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

        return {"status": "success", "indexed_episodes": len(world_state.visual.activities), "indexed_semantics": len(world_state.semantic.relationships)}
