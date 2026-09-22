from typing import Any

from contracts.schemas.world import Certainty, DocumentUnderstanding
from core.telemetry.logging import get_logger

logger = get_logger("providers.easyocr")


class EasyOCRProvider:
    """
    Real Provider implementation for Vision/OCR using EasyOCR.
    """

    __version__: str = "1.0"

    def __init__(self, languages: list[str] | None = None):
        self.languages = languages or ["en"]
        self._model = None

        # Enforce fail-fast dependency check per M2 Real Media Understanding architecture
        try:
            import easyocr  # type: ignore # noqa: F401
        except ImportError:
            raise RuntimeError(
                "ENVIRONMENT DEPENDENCY FAILURE: easyocr is not installed. "
                "Please install it via the [vision] optional dependency."
            )

    def _get_model(self):
        if self._model is None:
            try:
                import easyocr
                logger.info("loading_easyocr_model", languages=self.languages)
                # Setting gpu=False ensures it runs deterministically in CI environments
                # without requiring CUDA drivers, unless the environment explicitly supports it.
                self._model = easyocr.Reader(self.languages, gpu=False)
            except Exception as e:  # noqa: BLE001
                raise RuntimeError(
                    f"ENVIRONMENT / MODEL PROVISIONING FAILURE: Failed to initialize EasyOCR model weights. "
                    f"Details: {e}"
                )
        return self._model

    def extract_text(self, media_path: str) -> list[DocumentUnderstanding]:
        logger.info("ocr_recognition_started", provider="easyocr", media_path=media_path)
        model = self._get_model()

        # Execute OCR
        results = model.readtext(media_path)
        
        documents = []
        for bbox, text, prob in results:
            # bbox is typically a list of 4 points: [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
            # We flatten it to a standard [min_x, min_y, max_x, max_y] bounding box format for our schema.
            try:
                xs = [pt[0] for pt in bbox]
                ys = [pt[1] for pt in bbox]
                location = [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]
            except Exception:  # noqa: BLE001
                location = []

            doc = DocumentUnderstanding(
                detected_text=text,
                language=self.languages[0],
                location=location,
                certainty=Certainty(confidence=float(prob), source=f"easyocr_v{self.__version__}"),
            )
            documents.append(doc)

        return documents

    def health(self) -> bool:
        try:
            import easyocr  # noqa: F401
            return True
        except ImportError:
            return False

    def capabilities(self) -> dict[str, Any]:
        return {"languages": ["en", "es", "fr", "de", "zh", "ja", "ko"], "real_execution": True}
