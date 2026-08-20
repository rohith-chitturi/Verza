from enum import Enum


class ExecutionState(str, Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    CHECKPOINTED = "CHECKPOINTED"
    PAUSED = "PAUSED"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    ABORTED = "ABORTED"


VALID_TRANSITIONS = {
    ExecutionState.PENDING: {ExecutionState.QUEUED, ExecutionState.CANCELLED},
    ExecutionState.QUEUED: {ExecutionState.RUNNING, ExecutionState.CANCELLED},
    ExecutionState.RUNNING: {ExecutionState.CHECKPOINTED, ExecutionState.FAILED, ExecutionState.COMPLETED, ExecutionState.PAUSED, ExecutionState.CANCELLED},
    ExecutionState.CHECKPOINTED: {ExecutionState.RUNNING, ExecutionState.COMPLETED},
    ExecutionState.FAILED: {ExecutionState.RETRYING, ExecutionState.ABORTED, ExecutionState.QUEUED},
    ExecutionState.RETRYING: {ExecutionState.RUNNING},
    ExecutionState.PAUSED: {ExecutionState.RUNNING, ExecutionState.CANCELLED, ExecutionState.QUEUED},
    ExecutionState.COMPLETED: set(),
    ExecutionState.CANCELLED: set(),
    ExecutionState.ABORTED: set()
}

class IllegalStateTransitionError(Exception):
    pass
