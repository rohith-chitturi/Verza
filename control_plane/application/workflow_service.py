from typing import Any

from contracts.schemas.runtime import ExecutionState
from contracts.schemas.workflow import Workflow
from control_plane.application.errors import (
    DuplicateWorkflowError,
    RunNotFoundError,
    WorkflowNotFoundError,
)
from core.workflow.dispatcher import ExecutionDispatcher
from core.workflow.runtime import WorkflowRuntime
from storage.catalog.sql_repository import RunSqlRepository, WorkflowSqlRepository


class WorkflowService:
    """
    Application service layer orchestrating workflows.
    Shields the presentation layer (FastAPI/Typer) from runtime internals and database mechanics.
    """
    def __init__(
        self,
        workflow_repo: WorkflowSqlRepository,
        run_repo: RunSqlRepository,
        runtime: WorkflowRuntime,
        dispatcher: ExecutionDispatcher,
    ):
        self._workflow_repo = workflow_repo
        self._run_repo = run_repo
        self._runtime = runtime
        self._dispatcher = dispatcher

    def register_workflow(self, workflow: Workflow) -> None:
        """Registers a new workflow definition."""
        existing = self._workflow_repo.get_version(workflow.name, workflow.version)
        if existing:
            raise DuplicateWorkflowError(workflow.name, workflow.version)
        self._workflow_repo.save_definition(workflow)

    def get_workflow(self, name: str, version: str) -> Workflow:
        """Retrieves a registered workflow definition."""
        version_model = self._workflow_repo.get_version(name, version)
        if not version_model:
            raise WorkflowNotFoundError(name, version)
        return Workflow(**version_model.definition)

    def start_run(self, workflow_name: str, version: str) -> str:
        """Creates a run for a workflow and dispatches it asynchronously."""
        workflow = self.get_workflow(workflow_name, version)
        run_id = self._runtime.create_run(workflow)
        self._dispatcher.dispatch(run_id, workflow)
        return run_id

    def pause_run(self, run_id: str) -> None:
        """Requests a cooperative pause for a run."""
        run = self._run_repo.get_run(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        self._runtime.pause_run(run_id)

    def resume_run(self, run_id: str) -> None:
        """Resumes a paused or crashed run."""
        run = self._run_repo.get_run(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        
        # Need workflow definition to resume
        # The run stores workflow_version_id e.g. "name-v1.0"
        wf_name, wf_version = self._parse_version_id(run.workflow_version_id)
        workflow = self.get_workflow(wf_name, wf_version)
        
        self._runtime.prepare_resume(run_id)
        self._dispatcher.dispatch(run_id, workflow)

    def cancel_run(self, run_id: str) -> None:
        """Requests cancellation for a run."""
        run = self._run_repo.get_run(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        self._runtime.cancel_run(run_id)

    def replay_run(self, run_id: str, from_stage: str) -> str:
        """Forks a completed/failed run and replays from a specific stage."""
        run = self._run_repo.get_run(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        
        wf_name, wf_version = self._parse_version_id(run.workflow_version_id)
        workflow = self.get_workflow(wf_name, wf_version)
        
        new_run_id = self._runtime.prepare_replay(run_id, workflow)
        self._dispatcher.dispatch(new_run_id, workflow, replay_from_stage=from_stage)
        return new_run_id

    def get_run_status(self, run_id: str) -> dict[str, Any]:
        """Gets the status of a run."""
        run = self._run_repo.get_run(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        return {
            "run_id": run.id,
            "workflow_version_id": run.workflow_version_id,
            "status": run.status,
            "parent_run_id": run.parent_run_id
        }

    def get_stage_runs(self, run_id: str) -> list[dict[str, Any]]:
        """Gets the stages for a run."""
        run = self._run_repo.get_run(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        stages = self._run_repo.get_stage_runs(run_id)
        return [{"id": s.id, "stage_id": s.stage_id, "status": s.status} for s in stages]

    def get_world_state(self, run_id: str) -> dict[str, Any]:
        """Gets the materialized WorldState snapshot for a run."""
        run = self._run_repo.get_run(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        state = self._run_repo.get_world_state(run_id)
        return state or {}

    def _parse_version_id(self, version_id: str) -> tuple[str, str]:
        # Format: "name-v1.0"
        parts = version_id.rsplit("-v", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid version ID format: {version_id}")
        return parts[0], parts[1]
