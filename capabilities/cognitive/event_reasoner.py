from pydantic import BaseModel

from contracts.schemas.context import ExecutionContext
from contracts.schemas.delta import (
    ConfidenceScore,
    DeltaChange,
    Operation,
    WorldStateDelta,
)
from contracts.schemas.prompt import PromptAsset
from contracts.schemas.world import StructuredEvent, WorldState
from core.workflow.reasoning_context import ReasoningContextBuilder
from interfaces.cognitive.inference import InferenceProvider
from interfaces.cognitive.reasoner import BaseReasoner


class EventOutputSchema(BaseModel):
    events: list[StructuredEvent]


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
        parent_confidence: float = 1.0,
    ) -> WorldStateDelta:

        # Prepare context from world state
        input_text = ReasoningContextBuilder.build_event_context(world_state)

        # Infer structured output
        output = inference_provider.infer_structured(
            input_text=input_text, 
            prompt=prompt, 
            expected_schema=EventOutputSchema,
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
                            reason="Inferred event from intentions and activities",
                        ),
                    )
                )

        return WorldStateDelta(
            capability="event_reasoning",
            provider="inference_provider",
            version="1.0",
            trace_id=context.trace_id,
            parent_world_state_id="todo",
            operations=ops,
        )
