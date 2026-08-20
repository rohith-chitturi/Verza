from contracts.schemas.context import ExecutionContext
from contracts.schemas.delta import WorldStateDelta
from contracts.schemas.prompt import PromptAsset
from contracts.schemas.world import WorldState
from interfaces.cognitive.inference import InferenceProvider


class BaseReasoner:
    """
    Unlike Interpreters that look at raw media evidence, Reasoners
    infer meaning strictly from the current structured WorldState.
    """

    def reason(
        self,
        world_state: WorldState,
        prompt: PromptAsset,
        context: ExecutionContext,
        inference_provider: InferenceProvider,
        parent_confidence: float = 1.0,
    ) -> WorldStateDelta:
        raise NotImplementedError
