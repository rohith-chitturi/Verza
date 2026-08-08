import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from contracts.schemas.world import WorldState

class ExecutionContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    trace_id: str
    workflow_id: str
    tenant_id: str = "default"
    project_id: str = "default"
    runtime_metadata: dict[str, Any] = Field(default_factory=dict)


class AIContext(BaseModel):
    """
    Strongly typed AI Context Layer.
    Passed to every capability to ensure cross-pipeline consistency.
    """
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    media_id: str
    tenant_id: str = "default"
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    # The M2 Unified World Model
    world: WorldState = Field(default_factory=WorldState)
    
    def with_world(self, world: WorldState) -> "AIContext":
        return AIContext(
            id=self.id,
            media_id=self.media_id,
            tenant_id=self.tenant_id,
            metadata=self.metadata,
            world=world,
            workflow_id=self.workflow_id,
            language=self.language,
            scene=self.scene,
            characters=self.characters,
            glossary=self.glossary,
            emotion=self.emotion,
            timeline_start_ms=self.timeline_start_ms,
            timeline_end_ms=self.timeline_end_ms
        )

    workflow_id: str
    language: str
    scene: str | None = None
    characters: list[str] = []
    glossary: dict[str, str] = {}
    emotion: str | None = None
    timeline_start_ms: int = 0
    timeline_end_ms: int | None = None
