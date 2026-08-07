import time
import uuid
from typing import Any

from pydantic import BaseModel, Field


class Snapshot(BaseModel):
    """
    Strongly typed Snapshot model for pipeline reproducibility.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    job_id: str
    stage: str
    input_data: dict[str, Any]
    output_data: dict[str, Any]
    metrics: dict[str, float] = {}
    timestamp_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    context: dict[str, Any]
    provider: str
    model: str
    version: str
