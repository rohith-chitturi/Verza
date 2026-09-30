from contracts.schemas.workflow import Workflow
from core.telemetry.logging import get_logger
from core.workflow.dispatcher import ExecutionDispatcher
from bootstrap.worker import celery_app

logger = get_logger("workflow.distributed_dispatcher")


class CeleryExecutionDispatcher(ExecutionDispatcher):
    """
    Distributed M4.3 execution dispatcher using Celery and Redis.
    """
    
    def dispatch(self, run_id: str, workflow: Workflow, replay_from_stage: str | None = None) -> None:
        """
        Publishes the execution task to the Redis broker.
        Rule 1: Passes identifiers instead of serialized objects.
        """
        logger.info(f"Dispatching run {run_id} to Celery broker")
        celery_app.send_task(
            "core.workflow.tasks.execute_workflow_task",
            kwargs={
                "run_id": run_id,
                "workflow_name": workflow.name,
                "workflow_version": workflow.version,
                "replay_from_stage": replay_from_stage
            },
            task_id=f"run-{run_id}"
        )

    def cancel(self, run_id: str) -> None:
        """Deferred to Phase 4: Distributed Control Plane"""
        raise NotImplementedError("Cancel is not yet implemented for Celery Execution Dispatcher (Deferred to Phase 4)")

    def pause(self, run_id: str) -> None:
        """Deferred to Phase 4: Distributed Control Plane"""
        raise NotImplementedError("Pause is not yet implemented for Celery Execution Dispatcher (Deferred to Phase 4)")

    def resume(self, run_id: str) -> None:
        """Deferred to Phase 4: Distributed Control Plane"""
        raise NotImplementedError("Resume is not yet implemented for Celery Execution Dispatcher (Deferred to Phase 4)")

    def shutdown(self, timeout_seconds: int = 10) -> None:
        """
        The API process has no threads to join when using Celery.
        Worker lifecycle is managed independently.
        """
        logger.info("API shutting down. Worker nodes are decoupled and unaffected.")
