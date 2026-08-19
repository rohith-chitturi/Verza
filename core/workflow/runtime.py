import threading
import uuid

from contracts.schemas.runtime import ExecutionState
from contracts.schemas.workflow import Workflow
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

    def start_run(self, workflow: Workflow, parent_run_id: str | None = None) -> str:
        """Starts a workflow execution in the background."""
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        version_id = f"{workflow.name}-v{workflow.version}"
        
        self._run_repo.create_run(run_id, version_id, parent_run_id=parent_run_id)
        self._run_repo.update_run_status(run_id, ExecutionState.QUEUED)
        
        # Fire and forget thread for M4 local baseline
        thread = threading.Thread(target=self._execute_run, args=(run_id, workflow))
        thread.start()
        
        return run_id

    def resume_run(self, run_id: str, workflow: Workflow) -> None:
        """Resumes a paused or crashed run."""
        self._run_repo.update_run_status(run_id, ExecutionState.QUEUED)
        thread = threading.Thread(target=self._execute_run, args=(run_id, workflow))
        thread.start()

    def replay_run(self, parent_run_id: str, workflow: Workflow, from_stage: str) -> str:
        """Forks a run and restarts from a specific stage."""
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        version_id = f"{workflow.name}-v{workflow.version}"
        
        self._run_repo.create_run(run_id, version_id, parent_run_id=parent_run_id)
        self._run_repo.update_run_status(run_id, ExecutionState.QUEUED)
        
        thread = threading.Thread(target=self._execute_run, args=(run_id, workflow, from_stage))
        thread.start()
        
        return run_id

    def _execute_run(self, run_id: str, workflow: Workflow, replay_from_stage: str | None = None) -> None:
        logger.info(f"Starting workflow execution: {run_id}")
        self._run_repo.update_run_status(run_id, ExecutionState.RUNNING)
        
        try:
            waves = self._dag_resolver.resolve(workflow)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to resolve DAG: {e}")
            self._run_repo.update_run_status(run_id, ExecutionState.FAILED)
            return

        existing_stage_runs = {sr.stage_id: sr for sr in self._run_repo.get_stage_runs(run_id)}
        
        # Determine which stages to skip (for replay)
        skip_stages = set()
        if replay_from_stage:
            # Find the index of the wave containing from_stage
            target_wave_idx = -1
            for i, wave in enumerate(waves):
                if replay_from_stage in wave:
                    target_wave_idx = i
                    break
            
            if target_wave_idx >= 0:
                for i in range(target_wave_idx):
                    for stage_id in waves[i]:
                        skip_stages.add(stage_id)
                        logger.info(f"Replay: Reusing stage {stage_id}")
                        # Insert mock COMPLETED stage run for the new run
                        sr_id = f"SR-{uuid.uuid4().hex[:8].upper()}"
                        self._run_repo.create_stage_run(sr_id, run_id, stage_id)
                        self._run_repo.update_stage_status(sr_id, ExecutionState.QUEUED)
                        self._run_repo.update_stage_status(sr_id, ExecutionState.RUNNING)
                        self._run_repo.update_stage_status(sr_id, ExecutionState.COMPLETED)

        for wave in waves:
            for stage_id in wave:
                if stage_id in skip_stages:
                    continue
                    
                stage_def = next(s for s in workflow.stages if s.id == stage_id)
                
                # Check run status
                run = self._run_repo.get_run(run_id)
                if run and run.status in [ExecutionState.PAUSED.value, ExecutionState.CANCELLED.value, ExecutionState.FAILED.value]:
                    logger.info(f"Run {run_id} halted. Status: {run.status}")
                    return

                # For resume: if stage is already completed in this run, skip
                if stage_id in existing_stage_runs and existing_stage_runs[stage_id].status == ExecutionState.COMPLETED.value:
                    logger.info(f"Resume: Skipping already completed stage {stage_id}")
                    continue

                stage_run_id = existing_stage_runs.get(stage_id, None)
                if stage_run_id:
                    stage_run_id = stage_run_id.id
                    self._run_repo.update_stage_status(stage_run_id, ExecutionState.RUNNING)
                else:
                    stage_run_id = f"SR-{uuid.uuid4().hex[:8].upper()}"
                    self._run_repo.create_stage_run(stage_run_id, run_id, stage_id)
                    self._run_repo.update_stage_status(stage_run_id, ExecutionState.QUEUED)
                    self._run_repo.update_stage_status(stage_run_id, ExecutionState.RUNNING)
                
                logger.info(f"Executing stage {stage_id} via {stage_def.capability}")
                
                success = False
                attempts = 0
                max_attempts = stage_def.retry_policy.max_attempts
                
                # Provider resolution
                primary_provider = stage_def.provider_policy.primary
                fallback_providers = stage_def.provider_policy.fallback
                
                providers_to_try = [primary_provider] + fallback_providers
                
                for provider in providers_to_try:
                    if success: break
                    
                    while attempts < max_attempts and not success:
                        attempts += 1
                        try:
                            # In real system, we'd pass the provider to the capability execution context
                            capability = self._registry.get(stage_def.capability)
                            capability.execute()
                            self._run_repo.update_stage_status(stage_run_id, ExecutionState.COMPLETED)
                            logger.info(f"Stage {stage_id} completed successfully via {provider}.")
                            success = True
                        except Exception as e:  # noqa: BLE001
                            logger.warning(f"Stage {stage_id} attempt {attempts} failed with provider {provider}: {e}")
                            if attempts < max_attempts:
                                self._run_repo.update_stage_status(stage_run_id, ExecutionState.FAILED)
                                self._run_repo.update_stage_status(stage_run_id, ExecutionState.RETRYING)
                                # backoff simulation
                                self._run_repo.update_stage_status(stage_run_id, ExecutionState.RUNNING)
                            else:
                                logger.error(f"Exhausted attempts for provider {provider}")

                if not success:
                    self._run_repo.update_stage_status(stage_run_id, ExecutionState.FAILED)
                    self._run_repo.update_run_status(run_id, ExecutionState.FAILED)
                    return # Fail fast sequentially
                    
        self._run_repo.update_run_status(run_id, ExecutionState.COMPLETED)
        logger.info(f"Workflow execution {run_id} completed successfully.")

    def pause_run(self, run_id: str) -> None:
        self._run_repo.update_run_status(run_id, ExecutionState.PAUSED)
        
    def cancel_run(self, run_id: str) -> None:
        self._run_repo.update_run_status(run_id, ExecutionState.CANCELLED)
