
from sqlalchemy import select

from contracts.schemas.memory import (
    EpisodicMemory,
    MemoryLifecycle,
    MemoryProvenance,
    RetrievalQuery,
    RetrievedMemory,
    SemanticMemory,
)
from storage.models.memory import EpisodicMemoryModel, SemanticMemoryModel


class PostgresMemoryRepository:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    def save_episodic_memory(self, memory: EpisodicMemory) -> None:
        with self._session_factory() as session:
            model = EpisodicMemoryModel(
                id=memory.id,
                content=memory.content,
                lifecycle=memory.lifecycle.value,
                embedding=memory.metadata.get("embedding"),
                embedding_model=memory.embedding_model,
                embedding_version=memory.embedding_version,
                metadata_json=memory.metadata,
                start_time=memory.start_time,
                end_time=memory.end_time,
                entities=memory.entities,
                tenant_id=memory.provenance.tenant_id,
                project_id=memory.provenance.project_id,
                workflow_run_id=memory.provenance.workflow_run_id,
                stage_run_id=memory.provenance.stage_run_id,
                world_state_id=memory.provenance.world_state_id,
                source_entity_id=memory.provenance.source_entity_id,
                source_event_id=memory.provenance.source_event_id,
                source_timestamp=memory.provenance.source_timestamp,
                provider=memory.provenance.provider,
                model=memory.provenance.model,
                confidence=memory.provenance.confidence,
            )
            session.add(model)
            session.commit()

    def save_semantic_memory(self, memory: SemanticMemory) -> None:
        with self._session_factory() as session:
            model = SemanticMemoryModel(
                id=memory.id,
                content=memory.content,
                lifecycle=memory.lifecycle.value,
                embedding=memory.metadata.get("embedding"),
                embedding_model=memory.embedding_model,
                embedding_version=memory.embedding_version,
                metadata_json=memory.metadata,
                fact_type=memory.fact_type,
                entities=memory.entities,
                tenant_id=memory.provenance.tenant_id,
                project_id=memory.provenance.project_id,
                workflow_run_id=memory.provenance.workflow_run_id,
                stage_run_id=memory.provenance.stage_run_id,
                world_state_id=memory.provenance.world_state_id,
                source_entity_id=memory.provenance.source_entity_id,
                source_event_id=memory.provenance.source_event_id,
                source_timestamp=memory.provenance.source_timestamp,
                provider=memory.provenance.provider,
                model=memory.provenance.model,
                confidence=memory.provenance.confidence,
            )
            session.add(model)
            session.commit()

    def retrieve(self, query: RetrievalQuery, query_embedding: list[float] | None = None) -> list[RetrievedMemory]:
        """
        Hybrid retrieval combining vector similarity (if query_embedding is provided)
        with temporal, entity, and confidence filtering.
        """
        results = []
        with self._session_factory() as session:
            # 1. Retrieve Episodic Memories
            if not query.memory_types or "episodic" in query.memory_types:
                stmt = select(EpisodicMemoryModel).where(
                    EpisodicMemoryModel.lifecycle == MemoryLifecycle.ACTIVE.value
                )
                if query.start_time is not None:
                    stmt = stmt.where(EpisodicMemoryModel.end_time >= query.start_time)
                if query.end_time is not None:
                    stmt = stmt.where(EpisodicMemoryModel.start_time <= query.end_time)
                if query.min_confidence > 0:
                    stmt = stmt.where(EpisodicMemoryModel.confidence >= query.min_confidence)
                
                # Note: Exact entity overlap via JSON containment is dialect specific, 
                # skipping complex JSON overlap in basic stmt for now to keep it portable, 
                # we'll filter entity in memory or with simpler string match.
                
                # If we have an embedding, we can order by cosine similarity using pgvector
                # l2_distance (<->), cosine_distance (<=>), inner_product (<#>)
                if query_embedding is not None:
                    stmt = stmt.order_by(EpisodicMemoryModel.embedding.cosine_distance(query_embedding))
                    stmt = stmt.limit(query.top_k)

                episodic_models = session.execute(stmt).scalars().all()
                for model in episodic_models:
                    # In-memory entity filtering fallback
                    if query.entity_ids and not any(e in (model.entities or []) for e in query.entity_ids):
                        continue
                        
                    prov = MemoryProvenance(
                        tenant_id=model.tenant_id,
                        project_id=model.project_id,
                        workflow_run_id=model.workflow_run_id,
                        stage_run_id=model.stage_run_id,
                        world_state_id=model.world_state_id,
                        source_entity_id=model.source_entity_id,
                        source_event_id=model.source_event_id,
                        source_timestamp=model.source_timestamp,
                        provider=model.provider,
                        model=model.model,
                        confidence=model.confidence
                    )
                    fragment = EpisodicMemory(
                        id=model.id,
                        content=model.content,
                        lifecycle=MemoryLifecycle(model.lifecycle),
                        embedding_model=model.embedding_model,
                        embedding_version=model.embedding_version,
                        metadata=model.metadata_json or {},
                        start_time=model.start_time,
                        end_time=model.end_time,
                        entities=model.entities or [],
                        provenance=prov
                    )
                    
                    # Calculate dummy similarity if no vector math is available in memory
                    similarity = 1.0 # This would be fetched from the DB if queried with embedding
                    results.append(RetrievedMemory(
                        memory=fragment,
                        similarity=similarity,
                        temporal_score=1.0,
                        confidence_score=model.confidence,
                        final_score=similarity * model.confidence
                    ))

            # 2. Retrieve Semantic Memories
            if not query.memory_types or "semantic" in query.memory_types:
                stmt = select(SemanticMemoryModel).where(
                    SemanticMemoryModel.lifecycle == MemoryLifecycle.ACTIVE.value
                )
                if query.min_confidence > 0:
                    stmt = stmt.where(SemanticMemoryModel.confidence >= query.min_confidence)
                    
                if query_embedding is not None:
                    stmt = stmt.order_by(SemanticMemoryModel.embedding.cosine_distance(query_embedding))
                    stmt = stmt.limit(query.top_k)

                semantic_models = session.execute(stmt).scalars().all()
                for model in semantic_models:
                    if query.entity_ids and not any(e in (model.entities or []) for e in query.entity_ids):
                        continue
                        
                    prov = MemoryProvenance(
                        tenant_id=model.tenant_id,
                        project_id=model.project_id,
                        workflow_run_id=model.workflow_run_id,
                        stage_run_id=model.stage_run_id,
                        world_state_id=model.world_state_id,
                        source_entity_id=model.source_entity_id,
                        source_event_id=model.source_event_id,
                        source_timestamp=model.source_timestamp,
                        provider=model.provider,
                        model=model.model,
                        confidence=model.confidence
                    )
                    fragment = SemanticMemory(
                        id=model.id,
                        content=model.content,
                        lifecycle=MemoryLifecycle(model.lifecycle),
                        embedding_model=model.embedding_model,
                        embedding_version=model.embedding_version,
                        metadata=model.metadata_json or {},
                        fact_type=model.fact_type,
                        entities=model.entities or [],
                        provenance=prov
                    )
                    
                    similarity = 1.0
                    results.append(RetrievedMemory(
                        memory=fragment,
                        similarity=similarity,
                        temporal_score=1.0,
                        confidence_score=model.confidence,
                        final_score=similarity * model.confidence
                    ))

        # Sort combined results
        results.sort(key=lambda x: x.final_score, reverse=True)
        return results[:query.top_k]
