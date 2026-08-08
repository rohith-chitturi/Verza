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


class ActivityTraitSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    action: str
    confidence: float

class ActivityOutputSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    activities: list[ActivityTraitSchema]

class ActivityInterpreter(BaseInterpreter):
    @property
    def name(self) -> str: return "ActivityInterpreter"
    
    @property
    def consumes(self) -> list[str]: return ["visual.scenes"]
    
    @property
    def produces(self) -> list[str]: return ["visual.activities"]

    def interpret(
        self, 
        world_state: WorldState, 
        evidence: Evidence, 
        prompt: PromptAsset, 
        context: ExecutionContext,
        vlm_provider: VLMProvider,
        parent_confidence: float = 1.0
    ) -> WorldStateDelta:
        
        output: ActivityOutputSchema = vlm_provider.generate_structured(evidence, prompt)
        
        ops = []
        for act in output.activities:
            derived_conf = parent_confidence * act.confidence
            
            ops.append(DeltaChange(
                operation=Operation.ADD,
                domain="visual.activities",
                payload={
                    "type": act.action,
                    "evidence": evidence.model_dump()
                },
                confidence=ConfidenceScore(
                    confidence=derived_conf,
                    parent_confidence=parent_confidence,
                    derived_confidence=derived_conf,
                    reason="VLM Activity Detection"
                ),
                evidence=evidence
            ))
            
        return WorldStateDelta(
            capability=self.name,
            provider="VLM",
            version="1.0.0",
            trace_id=context.trace_id,
            parent_world_state_id="todo-hash",
            operations=ops
        )
