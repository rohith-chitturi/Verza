import threading
import uuid
from typing import Any

from contracts.schemas.runtime import ExecutionState
from contracts.schemas.workflow import WorkflowDefinition
from core.registry.capability import CapabilityRegistry
from core.telemetry.logging import get_logger
from core.workflow.dag import DAGResolver
from storage.catalog.sql_repository import RunSqlRepository

logger = get_logger("core.workflow.runtime")

class WorkflowRuntime:
    """
    Executes M4 Workflow Definitions orchestrating stages via the DAG Engine.
    """
    def __init__(self, capability_registry: CapabilityRegistry, run_repository: RunSqlRepository):
        self._registry = capability_registry
        self._run_repo = run_repository
        self._dag_resolver = DAGResolver()

    def start_run(self, workflow: WorkflowDefinition, parent_run_id: str | None = None) -> str:
        """Starts a workflow execution in the background."""
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        version_id = f"{workflow.name}-v{workflow.version}"
        
        self._run_repo.create_run(run_id, version_id, parent_run_id=parent_run_id)
        
        # Fire and forget thread for M4 local baseline
        thread = threading.Thread(target=self._execute_run, args=(run_id, workflow))
        thread.start()
        
        return run_id

    def _execute_run(self, run_id: str, workflow: WorkflowDefinition) -> None:
        logger.info(f"Starting workflow execution: {run_id}")
        self._run_repo.update_run_status(run_id, ExecutionState.RUNNING)
        
        try:
            waves = self._dag_resolver.resolve(workflow)
        except Exception as e:
            logger.error(f"Failed to resolve DAG: {e}")
            self._run_repo.update_run_status(run_id, ExecutionState.FAILED)
            return

        for wave in waves:
            for stage_id in wave:
                stage_def = next(s for s in workflow.stages if s.id == stage_id)
                
                # Check status
                run = self._run_repo.get_run(run_id)
                if run and run.status in [ExecutionState.PAUSED.value, ExecutionState.CANCELLED.value, ExecutionState.FAILED.value]:
                    logger.info(f"Run {run_id} halted. Status: {run.status}")
                    return

                stage_run_id = f"SR-{uuid.uuid4().hex[:8].upper()}"
                self._run_repo.create_stage_run(stage_run_id, run_id, stage_id)
                self._run_repo.update_stage_status(stage_run_id, ExecutionState.RUNNING)
                
                logger.info(f"Executing stage {stage_id} via {stage_def.capability}")
                
                try:
                    capability = self._registry.get(stage_def.capability)
                    # For M4 prototype, we assume execute() takes no args or uses a context
                    # In reality, inputs/outputs are passed.
                    capability.execute()
                    self._run_repo.update_stage_status(stage_run_id, ExecutionState.COMPLETED)
                    logger.info(f"Stage {stage_id} completed successfully.")
                except Exception as e:
                    logger.error(f"Stage {stage_id} failed: {e}")
                    self._run_repo.update_stage_status(stage_run_id, ExecutionState.FAILED)
                    self._run_repo.update_run_status(run_id, ExecutionState.FAILED)
                    return # Fail fast sequentially
                    
        self._run_repo.update_run_status(run_id, ExecutionState.COMPLETED)
        logger.info(f"Workflow execution {run_id} completed successfully.")

    def pause_run(self, run_id: str) -> None:
        self._run_repo.update_run_status(run_id, ExecutionState.PAUSED)
        
    def cancel_run(self, run_id: str) -> None:
        self._run_repo.update_run_status(run_id, ExecutionState.CANCELLED)
