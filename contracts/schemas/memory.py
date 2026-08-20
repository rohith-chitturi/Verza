from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MemoryLifecycle(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    INVALIDATED = "INVALIDATED"
    ARCHIVED = "ARCHIVED"


class MemoryProvenance(BaseModel):
    tenant_id: str | None = None
    project_id: str | None = None
    workflow_run_id: str | None = None
    stage_run_id: str | None = None
    world_state_id: str | None = None
    source_entity_id: str | None = None
    source_event_id: str | None = None
    source_timestamp: float | None = None
    provider: str | None = None
    model: str | None = None
    confidence: float = 1.0


class MemoryFragment(BaseModel):
    id: str
    memory_type: str
    content: str
    provenance: MemoryProvenance
    lifecycle: MemoryLifecycle = MemoryLifecycle.ACTIVE
    embedding_model: str | None = None
    embedding_version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EpisodicMemory(MemoryFragment):
    memory_type: str = "episodic"
    start_time: float
    end_time: float
    entities: list[str] = Field(default_factory=list)


class SemanticMemory(MemoryFragment):
    memory_type: str = "semantic"
    fact_type: str | None = None
    entities: list[str] = Field(default_factory=list)


class RetrievalQuery(BaseModel):
    query: str
    top_k: int = 10
    memory_types: list[str] = Field(default_factory=list)
    entity_ids: list[str] = Field(default_factory=list)
    start_time: float | None = None
    end_time: float | None = None
    min_confidence: float = 0.0


class RetrievedMemory(BaseModel):
    memory: MemoryFragment
    similarity: float
    temporal_score: float
    confidence_score: float
    final_score: float
