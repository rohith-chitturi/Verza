from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from contracts.schemas.api import (
    ReplayRequest,
    RunCreateRequest,
    RunResponse,
    RunStatusResponse,
    StageRunResponse,
    WorkflowCreateRequest,
    WorkflowResponse,
    WorldStateResponse,
)
from control_plane.application.workflow_service import WorkflowService

router = APIRouter(prefix="/api/v1")

@router.post("/workflows", status_code=201, response_model=WorkflowResponse)
@inject
def create_workflow(
    request: WorkflowCreateRequest,
    workflow_service: WorkflowService = Depends(Provide["workflow_service"])
):
    workflow_service.register_workflow(request.workflow)
    return WorkflowResponse(
        id=request.workflow.name, 
        name=request.workflow.name, 
        version=request.workflow.version
    )

@router.get("/workflows/{name}/{version}", response_model=WorkflowCreateRequest)
@inject
def get_workflow(
    name: str, 
    version: str,
    workflow_service: WorkflowService = Depends(Provide["workflow_service"])
):
    workflow = workflow_service.get_workflow(name, version)
    return WorkflowCreateRequest(workflow=workflow)

@router.post("/runs", status_code=202, response_model=RunResponse)
@inject
def trigger_run(
    request: RunCreateRequest,
    workflow_service: WorkflowService = Depends(Provide["workflow_service"])
):
    run_id = workflow_service.start_run(request.workflow_name, request.version)
    return RunResponse(
        run_id=run_id,
        workflow_name=request.workflow_name,
        workflow_version=request.version,
        status="QUEUED"
    )

@router.get("/runs/{run_id}", response_model=RunStatusResponse)
@inject
def get_run_status(
    run_id: str,
    workflow_service: WorkflowService = Depends(Provide["workflow_service"])
):
    status_dict = workflow_service.get_run_status(run_id)
    return RunStatusResponse(**status_dict)

@router.get("/runs/{run_id}/stages", response_model=list[StageRunResponse])
@inject
def get_run_stages(
    run_id: str,
    workflow_service: WorkflowService = Depends(Provide["workflow_service"])
):
    stages = workflow_service.get_stage_runs(run_id)
    return [StageRunResponse(**s) for s in stages]

@router.get("/runs/{run_id}/world-state", response_model=WorldStateResponse)
@inject
def get_run_world_state(
    run_id: str,
    workflow_service: WorkflowService = Depends(Provide["workflow_service"])
):
    state = workflow_service.get_world_state(run_id)
    return WorldStateResponse(world_state=state)

@router.post("/runs/{run_id}/pause", status_code=202)
@inject
def pause_run(
    run_id: str,
    workflow_service: WorkflowService = Depends(Provide["workflow_service"])
):
    workflow_service.pause_run(run_id)
    return {"status": "pause_requested"}

@router.post("/runs/{run_id}/resume", status_code=202)
@inject
def resume_run(
    run_id: str,
    workflow_service: WorkflowService = Depends(Provide["workflow_service"])
):
    workflow_service.resume_run(run_id)
    return {"status": "resume_requested"}

@router.post("/runs/{run_id}/cancel", status_code=202)
@inject
def cancel_run(
    run_id: str,
    workflow_service: WorkflowService = Depends(Provide["workflow_service"])
):
    workflow_service.cancel_run(run_id)
    return {"status": "cancel_requested"}

@router.post("/runs/{run_id}/replay", status_code=202, response_model=RunResponse)
@inject
def replay_run(
    run_id: str,
    request: ReplayRequest,
    workflow_service: WorkflowService = Depends(Provide["workflow_service"])
):
    new_run_id = workflow_service.replay_run(run_id, request.from_stage)
    # Fetch details to populate response
    status_dict = workflow_service.get_run_status(new_run_id)
    wf_name, wf_version = status_dict["workflow_version_id"].rsplit("-v", 1)
    
    return RunResponse(
        run_id=new_run_id,
        workflow_name=wf_name,
        workflow_version=wf_version,
        status=status_dict["status"]
    )
