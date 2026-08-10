
from contracts.schemas.context import ExecutionContext
from contracts.schemas.delta import (
    ConfidenceScore,
    DeltaChange,
    Operation,
    WorldStateDelta,
)
from contracts.schemas.prompt import PromptAsset
from contracts.schemas.world import WorldState
from interfaces.cognitive.inference import InferenceProvider
from interfaces.cognitive.reasoner import BaseReasoner


class IntentReasoner(BaseReasoner):
    """
    Infers character intents by observing their actions and the current scenes.
    """
    
    def reason(
        self,
        world_state: WorldState,
        prompt: PromptAsset,
        context: ExecutionContext,
        inference_provider: InferenceProvider,
        parent_confidence: float = 1.0
    ) -> WorldStateDelta:
        
        # Prepare context from world state
        context_data = {
            "characters": [c.model_dump() for c in world_state.visual.characters],
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
        if hasattr(output, "intentions"):
            for intent in output.intentions:
                ops.append(
                    DeltaChange(
                        operation=Operation.ADD,
                        domain="semantic.intentions",
                        origin="inference",
                        reasoner="intent_reasoner",
                        payload=intent.model_dump(),
                        confidence=ConfidenceScore(
                            confidence=intent.confidence * parent_confidence,
                            parent_confidence=parent_confidence,
                            derived_confidence=intent.confidence,
                            reason="Inferred from character activities"
                        )
                    )
                )
                
        return WorldStateDelta(
            capability="intent_reasoning",
            provider="inference_provider",
            version="1.0",
            trace_id=context.trace_id,
            parent_world_state_id="todo",
            operations=ops
        )
