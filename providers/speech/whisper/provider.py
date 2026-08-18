from typing import Any

from contracts.schemas.context import AIContext
from contracts.schemas.result import SpeechRecognitionResult
from core.telemetry.logging import get_logger

logger = get_logger("providers.whisper")


class WhisperRecognizer:
    """
    Reference Provider implementation for Speech Recognition using Whisper.
    """

    def recognize(self, audio_path: str, context: AIContext) -> SpeechRecognitionResult:
        logger.info(
            "speech_recognition_started",
            provider="whisper",
            model="large-v3",
            audio_path=audio_path,
            language=context.language,
        )

        return SpeechRecognitionResult(
            transcript="This is a simulated transcript from Whisper.",
            confidence=0.99,
            success=True,
            duration_ms=100,
            provider="whisper",
            model="large-v3",
        )

    def health(self) -> bool:
        return True

    def capabilities(self) -> dict[str, Any]:
        return {"supported_languages": ["en", "es", "fr"]}

    def version(self) -> str:
        return "1.0"
