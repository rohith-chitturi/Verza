from typing import Protocol

from pydantic import BaseModel

from contracts.schemas.prompt import PromptAsset


class VLMProvider(Protocol):
    """
    Protocol for Vision-Language Models.
    Enforces that providers return structured Pydantic models based on the prompt's expected schema,
    rather than returning free text.
    """

    def generate_structured(
        self, input_text: str, prompt: PromptAsset, expected_schema: type[BaseModel]
    ) -> BaseModel:
        """
        Processes textual evidence through a VLM and returns a Pydantic object
        matching expected_schema.
        """
        ...
