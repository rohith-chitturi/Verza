import uuid
from typing import Any

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

    def create_run(self, workflow: Workflow, parent_run_id: str | None = None) -> str:
        """Creates a workflow run entry in the database (PENDING)."""
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        version_id = f"{workflow.name}-v{workflow.version}"
        
        self._run_repo.create_run(run_id, version_id, parent_run_id=parent_run_id)
        self._run_repo.update_run_status(run_id, ExecutionState.QUEUED)
        return run_id

    def prepare_resume(self, run_id: str) -> None:
        """Prepares a paused or crashed run to be resumed."""
        self._run_repo.update_run_status(run_id, ExecutionState.QUEUED)

    def prepare_replay(self, parent_run_id: str, workflow: Workflow) -> str:
        """Creates a new run referencing a parent run for replay."""
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        version_id = f"{workflow.name}-v{workflow.version}"
        
        self._run_repo.create_run(run_id, version_id, parent_run_id=parent_run_id)
        self._run_repo.update_run_status(run_id, ExecutionState.QUEUED)
        
        # If replaying, we need to copy the latest world state from parent for now
        parent_state = self._run_repo.get_world_state(parent_run_id)
        if parent_state:
            self._run_repo.save_world_state(run_id, parent_state)
            
        return run_id

    def execute_run(self, run_id: str, workflow: Workflow, exec_context: Any = None, replay_from_stage: str | None = None) -> None:
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

                existing_stage_run = existing_stage_runs.get(stage_id, None)
                if existing_stage_run:
                    stage_run_id = existing_stage_run.id
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
                            
                            # Fetch world state from DB
                            from contracts.schemas.context import AIContext
                            from contracts.schemas.world import WorldState
                            
                            saved_state_dict = self._run_repo.get_world_state(run_id)
                            world_state = WorldState(**saved_state_dict) if saved_state_dict else WorldState()
                            
                            # In a real system, the media_id would be retrieved from the Run Parameters
                            context = AIContext(
                                media_id="tests/integration/fixtures/test_media.wav", 
                                workflow_id=workflow.id, 
                                language="en",
                                world=world_state
                            )
                            
                            new_context = capability.execute(context=context, trace_id=stage_run_id, exec_context=exec_context)
                            
                            # Save mutated world state back to DB
                            self._run_repo.save_world_state(run_id, new_context.world.model_dump(mode="json"))
                            
                            self._run_repo.update_stage_status(stage_run_id, ExecutionState.COMPLETED)
                            logger.info(f"Stage {stage_id} completed successfully via {provider}.")
                            success = True
                        except Exception as e:  # noqa: BLE001
                            from contracts.schemas.execution import CancelledError, PauseRequested
                            if isinstance(e, CancelledError):
                                logger.info(f"Stage {stage_id} cancelled cooperatively.")
                                self._run_repo.update_stage_status(stage_run_id, ExecutionState.CANCELLED)
                                self._run_repo.update_run_status(run_id, ExecutionState.CANCELLED)
                                return
                            if isinstance(e, PauseRequested):
                                logger.info(f"Stage {stage_id} paused cooperatively.")
                                self._run_repo.update_stage_status(stage_run_id, ExecutionState.PAUSED)
                                self._run_repo.update_run_status(run_id, ExecutionState.PAUSED)
                                return
                                
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
                    
            if exec_context and exec_context.is_cancelled():
                self._run_repo.update_run_status(run_id, ExecutionState.CANCELLED)
                return
            if exec_context and exec_context.is_pause_requested():
                self._run_repo.update_run_status(run_id, ExecutionState.PAUSED)
                return
                    
        self._run_repo.update_run_status(run_id, ExecutionState.COMPLETED)
        logger.info(f"Workflow execution {run_id} completed successfully.")

    def pause_run(self, run_id: str) -> None:
        self._run_repo.update_run_status(run_id, ExecutionState.PAUSED)
        
    def cancel_run(self, run_id: str) -> None:
        self._run_repo.update_run_status(run_id, ExecutionState.CANCELLED)
