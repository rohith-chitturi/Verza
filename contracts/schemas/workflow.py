from typing import Any

from pydantic import BaseModel, Field


class RetryPolicy(BaseModel):
    max_attempts: int = 3
    backoff: float = 1.0
    max_backoff: float = 60.0
    retryable_errors: list[str] = Field(default_factory=list)


class ProviderPolicy(BaseModel):
    primary: str
    fallback: list[str] = Field(default_factory=list)


class Stage(BaseModel):
    id: str
    capability: str
    provider_policy: ProviderPolicy
    depends_on: list[str] = Field(default_factory=list)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    timeout: float | None = None
    failure_policy: str = "abort"  # e.g. "abort", "continue"


class Workflow(BaseModel):
    id: str
    version: str
    name: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    stages: list[Stage] = Field(default_factory=list)
    policies: dict[str, Any] = Field(default_factory=dict)


# Execution Metadata Models (for tracking and replayability)
class StageRunMetadata(BaseModel):
    workflow_id: str
    workflow_version: str
    run_id: str
    stage_id: str
    attempt: int
    capability_id: str
    capability_version: str
    provider_id: str
    provider_version: str
    model_id: str
    model_version: str
    input_snapshot_id: str
    output_snapshot_id: str | None = None
    world_state_version: str
    prompt_version: str
    configuration_hash: str
    started_at: str | None = None
    completed_at: str | None = None
