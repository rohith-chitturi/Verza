import os

from pydantic import BaseModel

try:
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

from core.telemetry.logging import get_logger

logger = get_logger("providers.shared.gemini")


class SharedGeminiClient:
    """
    Shared execution layer for Gemini integration (used by VLM and Inference providers).
    """
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. Real API calls will fail.")
            
        if not HAS_GENAI:
            logger.warning("google-genai is not installed. Gemini calls will fail.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)

    def generate_structured(
        self, 
        model_name: str, 
        full_prompt: str, 
        expected_schema: type[BaseModel]
    ) -> BaseModel:
        """
        Calls Gemini API with the given full prompt, returning a parsed Pydantic object.
        """
        logger.info(f"Invoking Gemini model: {model_name}")

        if not HAS_GENAI or not self.client:
            raise RuntimeError("google-genai is not installed. Please install [cognitive] extras.")

        response = self.client.models.generate_content(
            model=model_name,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=expected_schema,
                temperature=0.0,
            ),
        )
        
        # In newer versions of the google-genai SDK, parsed field contains the Pydantic instance if response_schema is passed as a BaseModel.
        if hasattr(response, "parsed") and response.parsed:
            if isinstance(response.parsed, BaseModel):
                return response.parsed
            elif isinstance(response.parsed, dict):
                return expected_schema.model_validate(response.parsed)
             
        # Fallback in case it returns raw json string and doesn't auto-parse
        if response.text:
             return expected_schema.model_validate_json(response.text)
             
        raise RuntimeError("Gemini API returned an empty or unparseable response.")
