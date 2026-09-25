import threading

from pydantic import BaseModel, Field


class CancellationToken:
    def __init__(self):
        self._event = threading.Event()

    def cancel(self):
        self._event.set()

    def is_cancelled(self) -> bool:
        return self._event.is_set()


class PauseToken:
    def __init__(self):
        self._event = threading.Event()

    def pause(self):
        self._event.set()

    def resume(self):
        self._event.clear()

    def is_pause_requested(self) -> bool:
        return self._event.is_set()


class Progress(BaseModel):
    percent: int = Field(ge=0, le=100, default=0)
    message: str | None = None


class ProgressReporter:
    def __init__(self, run_id: str, stage_id: str | None = None):
        self.run_id = run_id
        self.stage_id = stage_id
        self.current_progress = Progress(percent=0)

    def report(self, percent: int, message: str | None = None):
        self.current_progress = Progress(percent=percent, message=message)
        # Note: Event bus integration or DB flush will happen elsewhere in the dispatcher/runtime.


class CheckpointManager:
    def __init__(self, run_id: str, stage_id: str):
        self.run_id = run_id
        self.stage_id = stage_id

    def checkpoint(self):
        # Defines a capability-controlled safe boundary.
        # Capability logic should check pause tokens around these boundaries.
        pass


class ExecutionContext:
    def __init__(
        self,
        run_id: str,
        stage_id: str | None = None,
        cancellation_token: CancellationToken | None = None,
        pause_token: PauseToken | None = None,
    ):
        self.run_id = run_id
        self.stage_id = stage_id
        self.cancellation = cancellation_token or CancellationToken()
        self.pause = pause_token or PauseToken()
        self.progress = ProgressReporter(run_id, stage_id)
        self.checkpoint_manager = CheckpointManager(run_id, stage_id) if stage_id else None

    def is_cancelled(self) -> bool:
        return self.cancellation.is_cancelled()

    def is_pause_requested(self) -> bool:
        return self.pause.is_pause_requested()

    def report_progress(self, percent: int, message: str | None = None):
        self.progress.report(percent, message)

    def checkpoint(self):
        if self.checkpoint_manager:
            self.checkpoint_manager.checkpoint()

class CancelledError(Exception):
    """Raised by a capability when cancellation is requested."""

class PauseRequested(Exception):
    """Raised by a capability when it cooperatively pauses."""
