from typing import Any

from contracts.schemas.world import Certainty, DocumentUnderstanding
from core.telemetry.logging import get_logger

logger = get_logger("providers.easyocr")


class EasyOCRProvider:
    __version__: str = "1.0"

    def extract_text(self, media_path: str) -> list[DocumentUnderstanding]:
        # Simulated EasyOCR response
        logger.info("extracting_text_mock", path=media_path)

        return [
            DocumentUnderstanding(
                detected_text="WARNING",
                language="en",
                location=[100, 100, 200, 200],
                certainty=Certainty(confidence=0.98, source="easyocr_v1.0"),
            ),
            DocumentUnderstanding(
                detected_text="STOP",
                language="en",
                location=[300, 300, 400, 400],
                certainty=Certainty(confidence=0.95, source="easyocr_v1.0"),
            ),
        ]

    def health(self) -> bool:
        return True

    def capabilities(self) -> dict[str, Any]:
        return {"languages": ["en", "es", "fr", "de", "zh"]}
