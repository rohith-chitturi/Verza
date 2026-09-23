from typing import Any

from pydantic import BaseModel, Field

from contracts.schemas.workflow import Workflow


class WorkflowCreateRequest(BaseModel):
    workflow: Workflow


class WorkflowResponse(BaseModel):
    id: str
    name: str
    version: str


class RunCreateRequest(BaseModel):
    workflow_name: str
    version: str


class RunResponse(BaseModel):
    run_id: str
    workflow_name: str
    workflow_version: str
    status: str


class RunStatusResponse(BaseModel):
    run_id: str
    workflow_version_id: str
    status: str
    parent_run_id: str | None = None


class ReplayRequest(BaseModel):
    from_stage: str


class StageRunResponse(BaseModel):
    id: str
    stage_id: str
    status: str


class WorldStateResponse(BaseModel):
    world_state: dict[str, Any]
