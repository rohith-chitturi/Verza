from typing import Any, Protocol

from contracts.schemas.world import DetectedObject


class ObjectDetectionProvider(Protocol):
    """
    Protocol for real object detection models (e.g., YOLO, DETR).
    Must support failure-fast instantiation and deterministic visual contract extraction.
    """

    __version__: str

    def health(self) -> bool:
        """Returns True if the provider dependencies and models are correctly installed."""
        ...

    def detect_objects(self, media_path: str, exec_context: Any = None) -> list[DetectedObject]:
        """
        Executes real object detection inference on the physical media.
        """
        ...
