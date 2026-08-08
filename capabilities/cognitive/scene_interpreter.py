from typing import cast

from pydantic import BaseModel, ConfigDict

from contracts.schemas.context import ExecutionContext
from contracts.schemas.delta import (
    ConfidenceScore,
    DeltaChange,
    Operation,
    WorldStateDelta,
)
from contracts.schemas.prompt import PromptAsset
from contracts.schemas.world import Evidence, WorldState
from interfaces.cognitive.interpreter import BaseInterpreter
from interfaces.cognitive.vlm_provider import VLMProvider


class SceneOutputSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    summary: str
    mood: str
    confidence: float

class SceneInterpreter(BaseInterpreter):
    @property
    def name(self) -> str: return "SceneInterpreter"
    
    @property
    def consumes(self) -> list[str]: return ["media", "visual.frames"]
    
    @property
    def produces(self) -> list[str]: return ["visual.scenes"]

    def interpret(
        self, 
        world_state: WorldState, 
        evidence: Evidence, 
        prompt: PromptAsset, 
        context: ExecutionContext,
        vlm_provider: VLMProvider
    ) -> WorldStateDelta:
        
        # Invoke VLM
        output = cast(SceneOutputSchema, vlm_provider.generate_structured(evidence, prompt))
        
        # Build Delta
        change = DeltaChange(
            operation=Operation.ADD,
            domain="visual.scenes",
            payload={
                "summary": output.summary,
                "mood": output.mood,
                "evidence": evidence.model_dump()
            },
            confidence=ConfidenceScore(
                confidence=output.confidence,
                reason="VLM Scene Analysis"
            ),
            evidence=evidence
        )
        
        return WorldStateDelta(
            capability=self.name,
            provider="VLM",
            version="1.0.0",
            trace_id=context.trace_id,
            parent_world_state_id="todo-hash", # Hashing logic deferred
            operations=[change]
        )
