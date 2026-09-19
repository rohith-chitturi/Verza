import time
from typing import Any

from contracts.schemas.context import AIContext
from contracts.schemas.result import SpeechRecognitionResult
from core.telemetry.logging import get_logger

logger = get_logger("providers.whisper")


class WhisperRecognizer:
    """
    Real Provider implementation for Speech Recognition using faster-whisper.
    """

    def __init__(self, model_size: str = "tiny", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
        
        # Enforce fail-fast dependency check per M2 Real Media Understanding architecture
        try:
            import faster_whisper
        except ImportError:
            raise RuntimeError(
                "ENVIRONMENT DEPENDENCY FAILURE: faster-whisper is not installed. "
                "Please install it via the [speech] optional dependency."
            )

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            logger.info("loading_whisper_model", model_size=self.model_size, device=self.device)
            self._model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        return self._model

    def recognize(self, audio_path: str, context: AIContext) -> SpeechRecognitionResult:
        logger.info(
            "speech_recognition_started",
            provider="whisper",
            model=self.model_size,
            audio_path=audio_path,
            language=context.language,
        )
        
        start_time = time.time()
        model = self._get_model()
        
        kwargs = {}
        if context.language:
            kwargs["language"] = context.language
            
        # We use a small beam size for deterministic/faster local testing
        segments, info = model.transcribe(audio_path, beam_size=5, **kwargs)
        
        transcript = ""
        for segment in segments:
            transcript += segment.text + " "
            
        transcript = transcript.strip()
        duration_ms = int((time.time() - start_time) * 1000)

        return SpeechRecognitionResult(
            transcript=transcript,
            confidence=info.language_probability,
            success=True,
            duration_ms=duration_ms,
            provider="whisper",
            model=self.model_size,
        )

    def health(self) -> bool:
        try:
            import faster_whisper
            return True
        except ImportError:
            return False

    def capabilities(self) -> dict[str, Any]:
        return {"supported_languages": ["en", "es", "fr", "de", "zh", "ja", "ko", "auto"], "real_execution": True}

    def version(self) -> str:
        return "1.0"
