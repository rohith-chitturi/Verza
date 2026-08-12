import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from contracts.schemas.world import Evidence


class Operation(str, Enum):
    ADD = "ADD"
    UPDATE = "UPDATE"
    REMOVE = "REMOVE"
    MERGE = "MERGE"
    SPLIT = "SPLIT"
    LINK = "LINK"
    UNLINK = "UNLINK"

class ConfidenceScore(BaseModel):
    model_config = ConfigDict(frozen=True)
    confidence: float
    parent_confidence: float | None = None
    derived_confidence: float | None = None
    reason: str | None = None

class DeltaChange(BaseModel):
    model_config = ConfigDict(frozen=True)
    change_id: str = Field(default_factory=lambda: f"change-{uuid.uuid4().hex[:8]}")
    operation: Operation
    domain: str  # e.g., 'visual.characters', 'semantic.knowledge_graph'
    entity_id: str | None = None # The specific entity being modified
    origin: str = "interpretation" # e.g., interpretation, inference, user
    reasoner: str | None = None # e.g., relationship_reasoner
    payload: dict[str, Any] = Field(default_factory=dict)
    confidence: ConfidenceScore
    evidence: Evidence | None = None

class WorldStateDelta(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=lambda: f"delta-{uuid.uuid4().hex[:8]}")
    capability: str
    provider: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trace_id: str
    parent_world_state_id: str # Hash or ID of the world state before delta
    target_world_state_id: str | None = None # ID after merging, filled by merger
    operations: list[DeltaChange] = Field(default_factory=list)
