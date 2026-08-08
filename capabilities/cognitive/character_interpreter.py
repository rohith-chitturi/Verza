import uuid
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


class CharacterTraitSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    visual_description: str
    clothing: str
    confidence: float

class CharacterOutputSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    characters: list[CharacterTraitSchema]

class CharacterInterpreter(BaseInterpreter):
    @property
    def name(self) -> str: return "CharacterInterpreter"
    
    @property
    def consumes(self) -> list[str]: return ["visual.scenes"]
    
    @property
    def produces(self) -> list[str]: return ["visual.characters"]

    def interpret(
        self, 
        world_state: WorldState, 
        evidence: Evidence, 
        prompt: PromptAsset, 
        context: ExecutionContext,
        vlm_provider: VLMProvider,
        parent_confidence: float = 1.0
    ) -> WorldStateDelta:
        
        output = cast(CharacterOutputSchema, vlm_provider.generate_structured(evidence, prompt))
        
        ops = []
        for char in output.characters:
            char_id = f"character-{uuid.uuid4().hex[:8]}"
            derived_conf = parent_confidence * char.confidence
            
            ops.append(DeltaChange(
                operation=Operation.ADD,
                domain="visual.characters",
                entity_id=char_id,
                payload={
                    "id": char_id,
                    "appearances": evidence.shots,
                    "traits": {
                        "visual": char.visual_description,
                        "clothing": char.clothing
                    }
                },
                confidence=ConfidenceScore(
                    confidence=derived_conf,
                    parent_confidence=parent_confidence,
                    derived_confidence=derived_conf,
                    reason="VLM Character Identification"
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
