import threading
from abc import ABC, abstractmethod

from contracts.schemas.workflow import Workflow
from core.workflow.runtime import WorkflowRuntime


class ExecutionDispatcher(ABC):
    """
    Abstract interface for dispatching workflow execution to a worker mechanism.
    """
    @abstractmethod
    def dispatch(self, run_id: str, workflow: Workflow, replay_from_stage: str | None = None) -> None:
        pass


class InProcessExecutionDispatcher(ExecutionDispatcher):
    """
    Temporary M4.1 dispatcher that executes workflows in a background thread.
    """
    def __init__(self, runtime: WorkflowRuntime):
        self._runtime = runtime

    def dispatch(self, run_id: str, workflow: Workflow, replay_from_stage: str | None = None) -> None:
        # Spin up a thread to hide the blocking execution from the API
        thread = threading.Thread(
            target=self._runtime.execute_run, 
            args=(run_id, workflow, replay_from_stage)
        )
        thread.start()
