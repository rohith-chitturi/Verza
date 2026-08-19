from fastapi import APIRouter

from contracts.schemas.runtime import ExecutionState
from contracts.schemas.workflow import Workflow

# We would normally use Dependency Injector's FastAPI integration here, 
# but for the prototype we'll keep it simple or assume it's injected.

router = APIRouter(prefix="/api/v1")

@router.post("/workflows")
def create_workflow(definition: Workflow):
    # repo.save_definition(definition)
    return {"status": "ok", "workflow": definition.name}

@router.post("/runs")
def trigger_run(workflow_name: str, version: str):
    # Fetch definition, trigger run
    return {"run_id": "RUN-001"}

@router.get("/runs/{run_id}")
def get_run_status(run_id: str):
    return {
        "id": run_id,
        "status": ExecutionState.RUNNING.value,
        "current_stage": "reasoning",
        "completed_stages": 7,
        "total_stages": 9
    }

@router.post("/runs/{run_id}/pause")
def pause_run(run_id: str):
    return {"status": "paused"}

@router.post("/runs/{run_id}/resume")
def resume_run(run_id: str):
    return {"status": "resumed"}

@router.post("/runs/{run_id}/cancel")
def cancel_run(run_id: str):
    return {"status": "cancelled"}

@router.post("/runs/{run_id}/replay")
def replay_run(run_id: str, from_stage: str):
    return {"status": "replayed", "new_run_id": "RUN-002"}
