from typing import Protocol

from pydantic import BaseModel

from contracts.schemas.prompt import PromptAsset
from contracts.schemas.world import Evidence


class VLMProvider(Protocol):
    """
    Protocol for Vision-Language Models.
    Enforces that providers return structured Pydantic models based on the prompt's expected schema,
    rather than returning free text.
    """
    def generate_structured(self, evidence: Evidence, prompt: PromptAsset) -> BaseModel:
        """
        Processes visual/audio evidence through a VLM and returns a Pydantic object
        matching prompt.expected_schema.
        """
        ...
