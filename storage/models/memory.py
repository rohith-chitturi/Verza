from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Column, Float, Integer, String

from storage.models.runtime import Base


class MemoryProvenanceMixin:
    tenant_id = Column(String, nullable=True)
    project_id = Column(String, nullable=True)
    workflow_run_id = Column(String, nullable=True)
    stage_run_id = Column(String, nullable=True)
    world_state_id = Column(String, nullable=True)
    source_entity_id = Column(String, nullable=True)
    source_event_id = Column(String, nullable=True)
    source_timestamp = Column(Float, nullable=True)
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    confidence = Column(Float, default=1.0)


class MemoryFragmentMixin:
    id = Column(String, primary_key=True)
    content = Column(String, nullable=False)
    lifecycle = Column(String, nullable=False, default="ACTIVE")
    embedding = Column(Vector(384)) # Using 384 for all-MiniLM-L6-v2
    embedding_model = Column(String, nullable=True)
    embedding_version = Column(String, nullable=True)
    embedding_dimension = Column(Integer, nullable=True)
    metadata_json = Column(JSON, nullable=True)


class EpisodicMemoryModel(Base, MemoryFragmentMixin, MemoryProvenanceMixin):
    __tablename__ = "episodic_memory"
    
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    entities = Column(JSON, nullable=True)


class SemanticMemoryModel(Base, MemoryFragmentMixin, MemoryProvenanceMixin):
    __tablename__ = "semantic_memory"
    
    fact_type = Column(String, nullable=True)
    entities = Column(JSON, nullable=True)
