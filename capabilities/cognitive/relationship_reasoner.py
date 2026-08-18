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


class RelationshipReasoner(BaseReasoner):
    """
    Infers the social dynamics and relationships between characters over time.
    Outputs to semantic.knowledge_graph.edges.
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
        context_data = {
            "characters": [c.model_dump() for c in world_state.visual.characters],
            "activities": [a.model_dump() for a in world_state.visual.activities],
            "scenes": world_state.visual.scenes,
        }

        # Infer structured output
        output = inference_provider.infer_structured(
            context_data=context_data, prompt=prompt, execution_context=context
        )

        # Build Delta Operations
        ops = []
        if hasattr(output, "edges"):
            for edge in output.edges:
                ops.append(
                    DeltaChange(
                        operation=Operation.LINK,
                        domain="semantic.knowledge_graph.edges",
                        origin="inference",
                        reasoner="relationship_reasoner",
                        payload=edge.model_dump(),
                        confidence=ConfidenceScore(
                            confidence=edge.confidence * parent_confidence,
                            parent_confidence=parent_confidence,
                            derived_confidence=edge.confidence,
                            reason="Inferred relationship from character interactions",
                        ),
                    )
                )

        return WorldStateDelta(
            capability="relationship_reasoning",
            provider="inference_provider",
            version="1.0",
            trace_id=context.trace_id,
            parent_world_state_id="todo",
            operations=ops,
        )
