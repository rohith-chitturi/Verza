import threading
from abc import ABC, abstractmethod

from contracts.schemas.execution import ExecutionContext
from contracts.schemas.workflow import Workflow
from core.telemetry.logging import get_logger
from core.workflow.runtime import WorkflowRuntime

logger = get_logger("workflow.dispatcher")


class ExecutionDispatcher(ABC):
    """
    Abstract interface for dispatching workflow execution to a worker mechanism.
    """
    @abstractmethod
    def dispatch(self, run_id: str, workflow: Workflow, replay_from_stage: str | None = None) -> None:
        pass
        
    @abstractmethod
    def cancel(self, run_id: str) -> None:
        pass
        
    @abstractmethod
    def pause(self, run_id: str) -> None:
        pass
        
    @abstractmethod
    def resume(self, run_id: str) -> None:
        pass

    @abstractmethod
    def shutdown(self, timeout_seconds: int = 10) -> None:
        pass


class InProcessExecutionDispatcher(ExecutionDispatcher):
    """
    Temporary M4.1 dispatcher that executes workflows in a background thread.
    M4.2 adds cancellation, pausing, and graceful shutdown.
    """
    def __init__(self, runtime: WorkflowRuntime):
        self._runtime = runtime
        self._active_contexts: dict[str, ExecutionContext] = {}
        self._active_threads: dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

    def dispatch(self, run_id: str, workflow: Workflow, replay_from_stage: str | None = None) -> None:
        with self._lock:
            # Check if there is already a paused context we can resume, otherwise create new
            if run_id in self._active_contexts:
                exec_context = self._active_contexts[run_id]
                exec_context.pause.resume()
            else:
                exec_context = ExecutionContext(run_id=run_id)
                self._active_contexts[run_id] = exec_context

            def _run_wrapper():
                try:
                    self._runtime.execute_run(run_id, workflow, exec_context, replay_from_stage)
                finally:
                    with self._lock:
                        # Clean up context when run naturally finishes or fails
                        if run_id in self._active_contexts and not exec_context.is_pause_requested():
                            self._active_contexts.pop(run_id, None)
                        if run_id in self._active_threads:
                            self._active_threads.pop(run_id, None)

            thread = threading.Thread(target=_run_wrapper)
            self._active_threads[run_id] = thread
            thread.start()
            
    def cancel(self, run_id: str) -> None:
        with self._lock:
            if run_id in self._active_contexts:
                self._active_contexts[run_id].cancellation.cancel()
                
    def pause(self, run_id: str) -> None:
        with self._lock:
            if run_id in self._active_contexts:
                self._active_contexts[run_id].pause.pause()
                
    def resume(self, run_id: str) -> None:
        # For in-process, resume just dispatches again since the thread might have exited
        # This will clear the pause token in dispatch()
        pass

    def shutdown(self, timeout_seconds: int = 10) -> None:
        logger.info("Initiating graceful shutdown of execution dispatcher")
        with self._lock:
            for context in self._active_contexts.values():
                context.cancellation.cancel()
            threads_to_wait = list(self._active_threads.values())
            
        for t in threads_to_wait:
            t.join(timeout=timeout_seconds)
            if t.is_alive():
                logger.error(f"Thread {t.name} did not exit gracefully within {timeout_seconds}s")
