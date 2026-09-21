import os

from pydantic import BaseModel

try:
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

from contracts.schemas.prompt import PromptAsset
from core.telemetry.logging import get_logger
from interfaces.cognitive.vlm_provider import VLMProvider

logger = get_logger("providers.cognitive.gemini")


class GeminiVLMProvider(VLMProvider):
    """
    Real VLM Provider using the Google Gemini SDK (google-genai).
    """

    provider_type = "gemini"

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. Real API calls will fail.")
            
        if not HAS_GENAI:
            logger.warning("google-genai is not installed. GeminiVLMProvider will fail if used.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)

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
        logger.info(f"Invoking Gemini model: {self.model_name}")

        full_prompt = f"{prompt.system_prompt}\n\nEvidence to interpret:\n{input_text}"

        if not HAS_GENAI or not self.client:
            raise RuntimeError("google-genai is not installed. Please install [cognitive] extras.")

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=expected_schema,
                temperature=0.0,
            ),
        )
        
        # In newer versions of the google-genai SDK, parsed field contains the Pydantic instance if response_schema is passed as a BaseModel.
        if hasattr(response, "parsed") and response.parsed:
             return response.parsed
             
        # Fallback in case it returns raw json string and doesn't auto-parse
        if response.text:
             return expected_schema.model_validate_json(response.text)
             
        raise RuntimeError("Gemini API returned an empty or unparseable response.")
