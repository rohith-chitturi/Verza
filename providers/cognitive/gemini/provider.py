
from pydantic import BaseModel

from contracts.schemas.prompt import PromptAsset
from core.telemetry.logging import get_logger
from interfaces.cognitive.vlm_provider import VLMProvider
from providers.shared.gemini.client import SharedGeminiClient

logger = get_logger("providers.cognitive.gemini")


class GeminiVLMProvider(VLMProvider):
    """
    Real VLM Provider using the Google Gemini SDK (google-genai).
    """

    provider_type = "gemini"

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.client = SharedGeminiClient()

    def get_metadata(self) -> dict:
        return {
            "name": "gemini-vlm",
            "type": self.provider_type,
            "version": "1.0",
            "model": self.model_name
        }

    def generate_structured(
        self, input_text: str, prompt: PromptAsset, expected_schema: type[BaseModel]
    ) -> BaseModel:
        """
        Calls Gemini API with the given text and prompt, returning a parsed Pydantic object.
        """
        full_prompt = f"{prompt.system_prompt}\n\nEvidence to interpret:\n{input_text}"
        return self.client.generate_structured(
            model_name=self.model_name,
            full_prompt=full_prompt,
            expected_schema=expected_schema
        )
