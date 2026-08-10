import uuid
from typing import Any

from contracts.schemas.context import ExecutionContext
from contracts.schemas.delta import WorldStateDelta, DeltaChange, Operation, ConfidenceScore
from contracts.schemas.prompt import PromptAsset
from contracts.schemas.world import WorldState
from interfaces.cognitive.inference import InferenceProvider
from interfaces.cognitive.reasoner import BaseReasoner


class EventReasoner(BaseReasoner):
    """
    Aggregates discreet actions and intentions into high-level structured narrative events.
    Outputs to semantic.events.
    """
    
    def reason(
        self,
        world_state: WorldState,
        prompt: PromptAsset,
        context: ExecutionContext,
        inference_provider: InferenceProvider,
        parent_confidence: float = 1.0
    ) -> WorldStateDelta:
        
        # Prepare context from world state (depends on intents and activities)
        context_data = {
            "intentions": [i.model_dump() for i in world_state.semantic.intentions],
            "activities": [a.model_dump() for a in world_state.visual.activities],
            "scenes": world_state.visual.scenes
        }
        
        # Infer structured output
        output = inference_provider.infer_structured(
            context_data=context_data,
            prompt=prompt,
            execution_context=context
        )
        
        # Build Delta Operations
        ops = []
        if hasattr(output, "events"):
            for event in output.events:
                ops.append(
                    DeltaChange(
                        operation=Operation.ADD,
                        domain="semantic.events",
                        origin="inference",
                        reasoner="event_reasoner",
                        payload=event.model_dump(),
                        confidence=ConfidenceScore(
                            confidence=event.confidence * parent_confidence,
                            parent_confidence=parent_confidence,
                            derived_confidence=event.confidence,
                            reason="Inferred event from intentions and activities"
                        )
                    )
                )
                
        return WorldStateDelta(
            capability="event_reasoning",
            provider="inference_provider",
            version="1.0",
            trace_id=context.trace_id,
            parent_world_state_id="todo",
            operations=ops
        )
