from abc import ABC, abstractmethod
from typing import Any

from contracts.schemas.context import AIContext
from core.telemetry.logging import get_logger

logger = get_logger("capabilities.base")

class BaseCapability(ABC):
    """
    Base class for all AI capabilities.
    Enforces immutable WorldState transitions and diff logging.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        ...
        
    def execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext:
        """
        Executes the capability, returning a fully updated immutable AIContext.
        Logs a diff of the WorldState mutations.
        """
        logger.info("capability_started", capability=self.name, trace_id=trace_id)
        
        # 1. Capture the "Before" WorldState
        world_before = context.world
        
        # 2. Execute the concrete capability logic
        new_context = self._execute(context, trace_id, **kwargs)
        
        # 3. Capture the "After" WorldState
        world_after = new_context.world
        
        # 4. Generate Diff (Simplified for now - just tracking top-level changes)
        diff = self._generate_diff(world_before, world_after)
        
        logger.info(
            "capability_completed", 
            capability=self.name, 
            trace_id=trace_id,
            world_diff=diff
        )
        
        return new_context
        
    @abstractmethod
    def _execute(self, context: AIContext, trace_id: str, **kwargs) -> AIContext:
        """
        Concrete capabilities must implement this.
        Returns the new AIContext containing the enriched WorldState.
        """
        ...
        
    def _generate_diff(self, before, after) -> dict[str, Any]:
        """
        Generates a simplified JSON diff between two WorldState objects.
        """
        before_dict = before.model_dump()
        after_dict = after.model_dump()
        
        diff: dict[str, Any] = {"added": {}, "changed": {}}
        for domain, content in after_dict.items():
            if before_dict.get(domain) != content:
                diff["changed"][domain] = "Updated"
                
        return diff
