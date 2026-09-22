from typing import Any

from pydantic import BaseModel

from contracts.schemas.context import ExecutionContext
from contracts.schemas.prompt import PromptAsset
from core.telemetry.logging import get_logger
from interfaces.cognitive.inference import InferenceProvider
from providers.shared.gemini.client import SharedGeminiClient

logger = get_logger("providers.inference.gemini")


class GeminiInferenceProvider(InferenceProvider):
    """
    Real Inference Provider using the Google Gemini SDK via SharedGeminiClient.
    """

    provider_type = "gemini"

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.client = SharedGeminiClient()

    def get_metadata(self) -> dict[str, Any]:
        return {
            "name": "gemini-inference",
            "type": self.provider_type,
            "version": "1.0",
            "model": self.model_name
        }

    def infer_structured(
        self,
        input_text: str,
        prompt: PromptAsset,
        expected_schema: type[BaseModel],
        execution_context: ExecutionContext | None = None,
    ) -> BaseModel:
        """
        Calls Gemini API with the given text and prompt, returning a parsed Pydantic object.
        """
        full_prompt = f"{prompt.system_prompt}\n\nContext to reason over:\n{input_text}"
        return self.client.generate_structured(
            model_name=self.model_name,
            full_prompt=full_prompt,
            expected_schema=expected_schema
        )
