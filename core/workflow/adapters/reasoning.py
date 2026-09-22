from capabilities.base import BaseCapability
from contracts.schemas.context import AIContext, ExecutionContext
from core.workflow.reasoning import ReasoningEngine


class ReasoningCapability(BaseCapability):
    """
    Adapter bridging the M4 Runtime to the M3.2 ReasoningEngine.
    """
    def __init__(self, engine: ReasoningEngine):
        self._engine = engine

    @property
    def name(self) -> str:
        return "ReasoningCapability"

    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext:
        # ReasoningEngine expects initial_state and ExecutionContext, returning WorldState
        exec_ctx = ExecutionContext(
            trace_id=trace_id,
            workflow_id=context.workflow_id,
            tenant_id=context.tenant_id
        )
        
        new_world_state = self._engine.run(context.world, exec_ctx)
        
        return context.with_world(new_world_state)
