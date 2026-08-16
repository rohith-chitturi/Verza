from pydantic import BaseModel

from contracts.schemas.prompt import PromptAsset
from contracts.schemas.world import Evidence
from core.telemetry.logging import get_logger
from interfaces.cognitive.vlm_provider import VLMProvider

logger = get_logger("interfaces.cognitive.mock_vlm")

class MockVLMProvider(VLMProvider):
    """
    A mock implementation of VLMProvider that returns statically defined 
    structured responses based on the prompt's expected schema.
    """
    provider_type = "mock"
    
    def get_metadata(self) -> dict:
        return {
            "name": "mock-vlm",
            "type": "mock",
            "version": "1.0"
        }

    def generate_structured(self, evidence: Evidence, prompt: PromptAsset) -> BaseModel:
        logger.info(f"Mocking VLM response for prompt version {prompt.version}")
        
        # In a real provider, we'd call openai.chat.completions.create(..., response_format=prompt.expected_schema)
        # Here we just instantiate the expected schema with dummy data.
        
        expected = prompt.expected_schema
        name = expected.__name__
        
        if name == "SceneOutputSchema":
            return expected(summary="A tense confrontation in an alley.", mood="tense", confidence=0.88)
            
        elif name == "CharacterOutputSchema":
            from capabilities.cognitive.character_interpreter import (
                CharacterTraitSchema,
            )
            return expected(
                characters=[
                    CharacterTraitSchema(visual_description="Tall man in black coat", clothing="Black coat, hat", confidence=0.92)
                ]
            )
            
        elif name == "ActivityOutputSchema":
            from capabilities.cognitive.activity_interpreter import ActivityTraitSchema
            return expected(
                activities=[
                    ActivityTraitSchema(action="Walking aggressively", confidence=0.85)
                ]
            )
            
        raise ValueError(f"Unknown expected schema: {name}")
