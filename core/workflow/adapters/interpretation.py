from capabilities.base import BaseCapability
from contracts.schemas.context import AIContext
from core.workflow.interpretation import InterpretationEngine


class InterpretationCapability(BaseCapability):
    """
    Adapter bridging the M4 Runtime (BaseCapability) to the M3.1 InterpretationEngine.
    """
    def __init__(self, engine: InterpretationEngine):
        self._engine = engine

    @property
    def name(self) -> str:
        return "InterpretationCapability"

    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext:
        # Engine's execute method already accepts and returns an AIContext, 
        # but internally it does validation/merging and returns a context with a mutated world state.
        # We also want to make sure it traces using the provided trace_id from M4, 
        # so we will temporarily override context.id or similar, or just let the engine do it.
        # Since InterpretationEngine generates its own trace_id based on context.id, 
        # we can just pass the context.
        # Note: The BaseCapability wrapper will log the WorldState diff.
        
        # We can just call engine.execute directly, it returns the mutated context.
        return self._engine.execute(context)
