import time
import uuid
from typing import Any

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """
    Strictly typed Base Event class with tracing headers.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    
    workflow_id: str
    job_id: str | None = None
    task_id: str | None = None
    
    trace_id: str
    correlation_id: str

class WorkflowStarted(BaseEvent):
    tenant_id: str
    
class StageFinished(BaseEvent):
    stage_name: str
    duration_ms: int
    success: bool
    metrics: dict[str, Any] = {}
